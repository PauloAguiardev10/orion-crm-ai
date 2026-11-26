"""Acoes diretas em mensagens WAHA previamente vinculadas ao atendimento."""

import re
from urllib.parse import quote

import requests

from app.models.models import Conversa, Mensagem
from app.services.central_whatsapp_envio import preparar_destino_central
from app.services.waha_destino import ConfiguracaoWahaInvalida, resolver_waha


def executar_acao_mensagem(db, *, empresa_id, usuario_id, conversa_id, mensagem_id, acao, valor):
    if db.query(Conversa.id).filter_by(id=conversa_id, empresa_id=empresa_id).with_for_update().first() is None:
        raise ValueError("mensagem_indisponivel")
    destino, _ = preparar_destino_central(db, empresa_id=empresa_id, usuario_id=usuario_id,
                                        conversa_id=conversa_id)
    if destino is None:
        raise ValueError("mensagem_indisponivel")
    mensagem = db.query(Mensagem).filter_by(
        id=mensagem_id, conversa_id=conversa_id, empresa_id=empresa_id,
        conexao_canal_id=destino["conexao_canal_id"], sessao_waha=destino["sessao"],
    ).one_or_none()
    if mensagem is None or mensagem.tipo == "excluida":
        raise ValueError("mensagem_indisponivel")
    if acao != "reagir" and (
        mensagem.from_me is not True or mensagem.remetente != "humano"
        or mensagem.especialista_id != destino["especialista_id"]
    ):
        raise ValueError("mensagem_indisponivel")
    if acao == "editar" and (not valor.strip() or mensagem.midia_url):
        raise ValueError("edicao_indisponivel")
    identificador = mensagem.mensagem_id_waha or (
        mensagem.mensagem_id_externo if mensagem.from_me is False else None
    )
    prefixo = "true" if mensagem.from_me else "false"
    chat = destino["chat_id"]
    if not identificador or not re.fullmatch(rf"{prefixo}_{re.escape(chat)}_[A-Za-z0-9-]{{1,130}}", identificador):
        raise ValueError("mensagem_indisponivel")
    try:
        rota = resolver_waha(destino["sessao"])
        if not rota.chave_api:
            raise ValueError
        if acao == "reagir":
            metodo, caminho = "PUT", "/api/reaction"
            dados = {"session": rota.sessao, "messageId": identificador, "reaction": valor}
        else:
            caminho = f"/api/{quote(rota.sessao, safe='')}/chats/{quote(chat, safe='')}/messages/{quote(identificador, safe='')}"
            metodo, dados = ("PUT", {"text": valor.strip()}) if acao == "editar" else ("DELETE", None)
        resposta = requests.request(metodo, rota.origem + caminho, json=dados, headers=rota.headers,
                                    allow_redirects=False, timeout=(3, 8))
        if not 200 <= resposta.status_code < 300:
            raise ValueError
    except (requests.RequestException, ConfiguracaoWahaInvalida, ValueError):
        raise ValueError("operacao_waha_indisponivel") from None
    if acao == "editar":
        mensagem.texto = valor.strip()
    elif acao == "excluir":
        mensagem.texto = "Mensagem excluida"
        mensagem.tipo = "excluida"
        mensagem.midia_url = None
        mensagem.midia_tipo = None


def arquivar_conversa_waha(db, *, empresa_id, usuario_id, conversa_id, arquivar):
    conversa = db.query(Conversa).filter_by(id=conversa_id, empresa_id=empresa_id).with_for_update().one_or_none()
    if conversa is None:
        raise ValueError("conversa_indisponivel")
    destino, _ = preparar_destino_central(db, empresa_id=empresa_id, usuario_id=usuario_id,
                                        conversa_id=conversa_id)
    if destino is None:
        raise ValueError("conversa_indisponivel")
    try:
        rota = resolver_waha(destino["sessao"])
        if not rota.chave_api:
            raise ValueError
        sessao = quote(rota.sessao, safe="")
        chat = quote(destino["chat_id"], safe="")
        acao = "archive" if arquivar else "unarchive"
        resposta = requests.post(
            f"{rota.origem}/api/{sessao}/chats/{chat}/{acao}", headers=rota.headers,
            timeout=(3, 8), allow_redirects=False,
        )
        if not 200 <= resposta.status_code < 300:
            raise ValueError
    except (requests.RequestException, ConfiguracaoWahaInvalida, ValueError):
        raise ValueError("arquivo_waha_indisponivel") from None
    conversa.central_arquivada = arquivar


def assinar_presenca_waha(sessao, chat):
    from app.services.followup_destinatario_service import chat_id_whatsapp_valido

    if not chat_id_whatsapp_valido(chat):
        raise ValueError("presenca_indisponivel")
    try:
        rota = resolver_waha(sessao)
        if not rota.chave_api:
            raise ValueError
        resposta = requests.post(
            f"{rota.origem}/api/{quote(rota.sessao, safe='')}/presence/{quote(chat, safe='')}/subscribe",
            headers=rota.headers, timeout=(3, 8), allow_redirects=False,
        )
        if not 200 <= resposta.status_code < 300:
            raise ValueError
    except (requests.RequestException, ConfiguracaoWahaInvalida, ValueError):
        raise ValueError("presenca_indisponivel") from None
