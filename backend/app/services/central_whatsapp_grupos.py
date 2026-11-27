"""Grupos comerciais autorizados explicitamente por sessao WAHA."""

import json
import os
import re
from datetime import datetime, timezone

from app.models.models import ConexaoCanal, Conversa, Mensagem
from app.services.followup_conexoes_waha import localizar_conexao_waha
from app.services.followup_destinatario_service import chat_id_whatsapp_valido
from app.services.waha_identificadores import chat_canonico


GRUPO = re.compile(r"[0-9]+(?:-[0-9]+)?@g\.us")


def nome_grupo(sessoes, chat):
    if not isinstance(sessoes, str) or not isinstance(chat, str) or not GRUPO.fullmatch(chat):
        return None
    try:
        nome = json.loads(os.getenv("ORION_WAHA_GRUPOS_AUTORIZADOS", "{}"))[sessoes][chat]
    except (ValueError, KeyError, TypeError):
        return None
    return nome.strip()[:150] if isinstance(nome, str) and nome.strip() else None


def destinatario_central_valido(sessao, chat):
    return chat_id_whatsapp_valido(chat) or nome_grupo(sessao, chat) is not None


def registrar_mensagem_grupo(db, sessao, chat, payload, mensagem_id):
    nome = nome_grupo(sessao, chat)
    texto = payload.get("body")
    participante = payload.get("participant")
    saida = payload.get("fromMe")
    from app.services.central_whatsapp_midia import midia_ativa

    tem_midia = midia_ativa() and payload.get("hasMedia") is True
    texto = texto.strip() if isinstance(texto, str) else ""
    if (not nome or type(saida) is not bool or (not saida and not chat_id_whatsapp_valido(chat_canonico(participante)))
            or not isinstance(mensagem_id, str) or not 0 < len(mensagem_id) <= 180
            or (not texto and not tem_midia)):
        return "grupo_evento_indisponivel"
    if saida and payload.get("source") != "app":
        return "grupo_origem_indisponivel"
    referencia, _ = localizar_conexao_waha(db, sessao)
    if referencia is None:
        return "grupo_indisponivel"
    conexao = db.query(ConexaoCanal).filter_by(
        id=referencia.id, empresa_id=referencia.empresa_id, sessao_waha=sessao, ativo=True,
    ).with_for_update().populate_existing().one_or_none()
    if conexao is None or conexao.operacao_suspensa or conexao.sofia_institucional:
        return "grupo_indisponivel"

    conversas = db.query(Conversa).filter_by(
        empresa_id=conexao.empresa_id, conexao_canal_id=conexao.id, canal="whatsapp", identificador=chat,
    ).limit(2).all()
    if len(conversas) > 1:
        return "grupo_ambiguo"
    conversa = conversas[0] if conversas else Conversa(
        empresa_id=conexao.empresa_id, conexao_canal_id=conexao.id, especialista_id=conexao.especialista_id,
        canal="whatsapp", identificador=chat, nome=nome, etapa="inicio",
        status_atendimento="aguardando_humano", historico="",
    )
    db.add(conversa)
    db.flush()
    existente = db.query(Mensagem.id).filter_by(conversa_id=conversa.id, empresa_id=conexao.empresa_id).filter(
        (Mensagem.mensagem_id_externo == mensagem_id) | (Mensagem.mensagem_id_waha == mensagem_id),
    ).first()
    if existente is not None:
        return "mensagem_duplicada"
    registro = Mensagem(
        empresa_id=conexao.empresa_id, conversa_id=conversa.id, conexao_canal_id=conexao.id,
        sessao_waha=sessao, mensagem_id_externo=mensagem_id,
        remetente="aplicativo" if saida else "cliente", from_me=saida, texto=texto[:4096],
        status_processamento="concluida", central_eventos={"participante": participante} if participante else None,
        tipo="midia" if tem_midia else "texto",
    )
    db.add(registro)
    if tem_midia:
        from app.services.central_whatsapp_midia_entrada import anexar_midia_waha

        anexar_midia_waha(db, registro=registro, empresa_id=conexao.empresa_id,
                          sessao=sessao, mensagem_id=mensagem_id, payload=payload)
    conversa.atualizado_em = datetime.now(timezone.utc)
    return "grupo_mensagem_registrada"
