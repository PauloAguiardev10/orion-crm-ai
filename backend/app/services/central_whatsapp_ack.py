import json

from sqlalchemy import or_, text, update

from app.models.models import Conversa, Mensagem
from app.services.estados_mensagem import (
    STATUS_ENVIO_CONFIRMADO_HTTP as ACEITA,
    STATUS_ENVIO_ENVIADA_WAHA as ENVIADA,
    STATUS_ENVIO_ENTREGUE_WAHA as ENTREGUE,
    STATUS_ENVIO_ERRO_WAHA as ERRO,
    STATUS_ENVIO_LIDA_WAHA as LIDA,
)
from app.services.followup_conexoes_waha import localizar_conexao_waha
from app.services.followup_ids_waha import extrair_id_resposta_waha


ACKS = {
    -1: ("ERROR", ERRO, (ACEITA, ENVIADA)),
    1: ("SERVER", ENVIADA, (ACEITA,)),
    2: ("DEVICE", ENTREGUE, (ACEITA, ENVIADA, ERRO)),
    3: ("READ", LIDA, (ACEITA, ENVIADA, ENTREGUE, ERRO)),
    4: ("PLAYED", LIDA, (ACEITA, ENVIADA, ENTREGUE, ERRO)),
}

PRIORIDADE = {1: 1, -1: 2, 2: 3, 3: 4, 4: 5}


def bloquear_correlacao_ack(db, empresa_id, sessao, mensagem_id):
    chave = json.dumps([empresa_id, sessao, mensagem_id], ensure_ascii=True)
    db.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:chave, 0))"), {"chave": chave})


def aplicar_ack_pendente(db, empresa_id, sessao, mensagem_id):
    conexao, _ = localizar_conexao_waha(db, sessao)
    if conexao is None or conexao.empresa_id != empresa_id:
        return
    parametros = {"empresa": empresa_id, "conexao": conexao.id, "sessao": sessao, "mensagem": mensagem_id}
    ack = db.execute(text("""
        DELETE FROM central_ack_pendente WHERE empresa_id = :empresa AND conexao_id = :conexao
          AND sessao = :sessao AND mensagem_waha = :mensagem
        RETURNING ack
    """), parametros).scalar_one_or_none()
    if ack is not None:
        _aplicar_ack(db, conexao, mensagem_id, ack)


def registrar_ack_waha(db, evento):
    dados, sessao = evento.get("payload"), evento.get("session")
    if not isinstance(dados, dict) or dados.get("fromMe") is not True:
        return "ack_invalido"
    if not isinstance(sessao, str) or not sessao.strip() or len(sessao) > 120:
        return "sessao_invalida"
    ack = dados.get("ack")
    if type(ack) is not int or ack not in ACKS:
        return "ack_sem_transicao"
    nome, _, _ = ACKS[ack]
    if "ackName" in dados and dados["ackName"] != nome:
        return "ack_invalido"
    mensagem_id = extrair_id_resposta_waha(dados)
    if not mensagem_id or len(mensagem_id) > 180:
        return "ack_invalido"

    conexao, motivo = localizar_conexao_waha(db, sessao)
    if conexao is None:
        return motivo
    if conexao.pareamento_waha_pendente:
        return "conexao_waha_suspensa"
    bloquear_correlacao_ack(db, conexao.empresa_id, conexao.sessao_waha, mensagem_id)
    return _aplicar_ack(db, conexao, mensagem_id, ack, guardar=True)


def _aplicar_ack(db, conexao, mensagem_id, ack, *, guardar=False):
    _, destino, anteriores = ACKS[ack]
    conversa_autorizada = db.query(Conversa.id).filter(
        Conversa.id == Mensagem.conversa_id,
        Conversa.empresa_id == conexao.empresa_id,
        Conversa.canal == "whatsapp",
        Conversa.conexao_canal_id == conexao.id,
    ).exists()
    escopo = (
        Mensagem.empresa_id == conexao.empresa_id,
        Mensagem.sessao_waha == conexao.sessao_waha,
        Mensagem.mensagem_id_waha == mensagem_id,
        Mensagem.from_me.is_(True),
        or_(Mensagem.conexao_canal_id.is_(None), Mensagem.conexao_canal_id == conexao.id),
        conversa_autorizada,
    )
    candidatas = db.query(Mensagem.id).filter(*escopo).limit(2).all()
    if not candidatas and guardar:
        # A retenção evita crescimento indefinido com ACKs de saídas externas.
        db.execute(text("""
            DELETE FROM central_ack_pendente
            WHERE empresa_id = :empresa AND conexao_id = :conexao
              AND registrado_em < now() - interval '7 days'
        """), {"empresa": conexao.empresa_id, "conexao": conexao.id})
        db.execute(text("""
            INSERT INTO central_ack_pendente (empresa_id, conexao_id, sessao, mensagem_waha, ack)
            VALUES (:empresa, :conexao, :sessao, :mensagem, :ack)
            ON CONFLICT (empresa_id, sessao, mensagem_waha) DO UPDATE
                SET ack = EXCLUDED.ack, registrado_em = now()
            WHERE central_ack_pendente.conexao_id = EXCLUDED.conexao_id
              AND (CASE central_ack_pendente.ack WHEN 1 THEN 1 WHEN -1 THEN 2
                        WHEN 2 THEN 3 WHEN 3 THEN 4 ELSE 5 END) < :prioridade
        """), {"empresa": conexao.empresa_id, "conexao": conexao.id, "sessao": conexao.sessao_waha,
               "mensagem": mensagem_id, "ack": ack, "prioridade": PRIORIDADE[ack]})
        return "ack_pendente"
    if len(candidatas) != 1:
        return "ack_sem_mensagem_univoca"
    resultado = db.execute(
        update(Mensagem).where(
            Mensagem.id == candidatas[0].id, *escopo,
            Mensagem.status_envio.in_(anteriores),
        ).values(status_envio=destino).execution_options(synchronize_session=False)
    )
    return "ack_registrado" if resultado.rowcount == 1 else "ack_sem_transicao"
