"""Aplica eventos autenticados a mensagens ja existentes no mesmo chat."""

import re

from sqlalchemy import or_, text

from app.models.models import Conversa, Mensagem
from app.services.followup_conexoes_waha import localizar_conexao_waha


ID = re.compile(r"(true|false)_([0-9]+@(?:c\.us|lid))_([A-Za-z0-9-]{1,130})")
TOKEN = re.compile(r"[A-Za-z0-9-]{1,130}")


def sincronizar_evento_mensagem(db, evento):
    tipo = evento.get("event")
    dados, instante = evento.get("payload"), evento.get("timestamp")
    if not isinstance(dados, dict) or type(instante) not in (float, int) or not 0 < instante < 10**14:
        return False
    acao = ID.fullmatch(dados.get("id") or "") if isinstance(dados.get("id"), str) else None
    if acao is None:
        return False

    direcao, chat, _ = acao.groups()
    if tipo == "message.reaction":
        reacao = dados.get("reaction")
        if not isinstance(reacao, dict):
            return False
        alvo, corpo = reacao.get("messageId"), reacao.get("text")
        if not isinstance(alvo, str) or not isinstance(corpo, str) or len(corpo) > 32:
            return False
        referencia = ID.fullmatch(alvo)
        if referencia is None or referencia[2] != chat:
            return False
        chave = "reacao_conta" if direcao == "true" else "reacao_cliente"
    else:
        campo = {"message.edited": "editedMessageId", "message.revoked": "revokedMessageId"}.get(tipo)
        original = dados.get(campo) if campo else None
        if not isinstance(original, str) or not TOKEN.fullmatch(original):
            return False
        alvo = f"{direcao}_{chat}_{original}"
        corpo = dados.get("body")
        if tipo == "message.edited" and (not isinstance(corpo, str) or len(corpo) > 4096):
            return False
        chave = "alteracao"

    conexao, _ = localizar_conexao_waha(db, evento.get("session"))
    if conexao is None or conexao.operacao_suspensa:
        return False
    bloquear_evento(db, conexao.id, alvo)
    candidatos = db.query(Mensagem.id).join(Conversa, Mensagem.conversa_id == Conversa.id).filter(
        Mensagem.empresa_id == conexao.empresa_id, Conversa.empresa_id == conexao.empresa_id,
        Conversa.conexao_canal_id == conexao.id, Conversa.identificador == chat,
        Mensagem.conexao_canal_id == conexao.id, Mensagem.sessao_waha == conexao.sessao_waha,
        or_(Mensagem.mensagem_id_waha == alvo, Mensagem.mensagem_id_externo == alvo),
    ).limit(2).all()
    if len(candidatos) > 1:
        return False
    mensagem = db.query(Mensagem).filter_by(id=candidatos[0].id).with_for_update(skip_locked=True).one_or_none() if candidatos else None
    if mensagem is None:
        db.execute(text("""
            DELETE FROM central_eventos_mensagem_pendentes
            WHERE conexao_id = :conexao AND registrado_em < now() - interval '7 days'
        """), {"conexao": conexao.id})
        db.execute(text("""
            INSERT INTO central_eventos_mensagem_pendentes
                (conexao_id, alvo, chave, tipo, instante, corpo)
            VALUES (:conexao,:alvo,:chave,:tipo,:instante,:corpo)
            ON CONFLICT (conexao_id, alvo, chave) DO UPDATE
              SET tipo=EXCLUDED.tipo, instante=EXCLUDED.instante, corpo=EXCLUDED.corpo
              WHERE central_eventos_mensagem_pendentes.tipo <> 'message.revoked'
                AND (EXCLUDED.tipo = 'message.revoked'
                     OR EXCLUDED.instante > central_eventos_mensagem_pendentes.instante)
        """), {"conexao": conexao.id, "alvo": alvo, "chave": chave, "tipo": tipo,
               "instante": instante, "corpo": corpo})
        return True
    aplicada = _aplicar(mensagem, tipo, chave, instante, corpo)
    aplicar_eventos_pendentes(db, mensagem, alvo)
    return aplicada


def bloquear_evento(db, conexao_id, alvo):
    db.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:chave, 0))"),
               {"chave": f"central-evento:{conexao_id}:{alvo}"})


def aplicar_eventos_pendentes(db, mensagem, alvo):
    if mensagem.conexao_canal_id is None or not mensagem.sessao_waha or not isinstance(alvo, str) or not ID.fullmatch(alvo):
        return
    chat_alvo = ID.fullmatch(alvo)[2]
    if db.query(Conversa.id).filter_by(
        id=mensagem.conversa_id, empresa_id=mensagem.empresa_id,
        conexao_canal_id=mensagem.conexao_canal_id, identificador=chat_alvo,
    ).first() is None:
        return
    bloquear_evento(db, mensagem.conexao_canal_id, alvo)
    itens = db.execute(text("""
        DELETE FROM central_eventos_mensagem_pendentes
        WHERE conexao_id = :conexao AND alvo = :alvo
        RETURNING tipo, chave, instante, corpo, registrado_em >= now() - interval '7 days' AS vigente
    """), {"conexao": mensagem.conexao_canal_id, "alvo": alvo}).mappings().all()
    for item in sorted(itens, key=lambda i: i["instante"]):
        if item["vigente"]:
            _aplicar(mensagem, item["tipo"], item["chave"], item["instante"], item["corpo"])


def _aplicar(mensagem, tipo, chave, instante, corpo):
    if mensagem.tipo == "excluida":
        return False
    eventos = mensagem.central_eventos or {}
    if tipo != "message.revoked" and instante <= eventos.get(chave, {}).get("em", 0):
        return False
    mensagem.central_eventos = {**eventos, chave: {"em": instante, "texto": corpo if chave.startswith("reacao") else None}}
    if tipo == "message.edited":
        mensagem.texto = corpo
    elif tipo == "message.revoked":
        mensagem.texto, mensagem.tipo = "Mensagem excluida", "excluida"
        mensagem.midia_url = mensagem.midia_tipo = None
    return True


def sincronizar_digitacao(db, evento):
    from datetime import datetime, timedelta, timezone
    from app.services.followup_destinatario_service import chat_id_whatsapp_valido

    dados = evento.get("payload")
    if not isinstance(dados, dict) or not chat_id_whatsapp_valido(dados.get("id")):
        return False
    presencas = dados.get("presences")
    if not isinstance(presencas, list) or len(presencas) != 1 or not isinstance(presencas[0], dict):
        return False

    chat = dados["id"]
    presenca = presencas[0]
    estado = presenca.get("lastKnownPresence")
    if presenca.get("participant") != chat or estado not in ("typing", "paused", "online", "offline"):
        return False
    conexao, _ = localizar_conexao_waha(db, evento.get("session"))
    if conexao is None or conexao.operacao_suspensa:
        return False
    conversas = db.query(Conversa).filter_by(
        empresa_id=conexao.empresa_id, conexao_canal_id=conexao.id, canal="whatsapp", identificador=chat,
    ).with_for_update().limit(2).all()
    if len(conversas) != 1:
        return False
    conversas[0].central_digitando_ate = (
        datetime.now(timezone.utc) + timedelta(seconds=8) if estado == "typing" else None
    )
    return True
