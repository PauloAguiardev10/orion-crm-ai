"""Validacao conservadora de eventos de saida do WAHA."""


import hashlib
import hmac


def assinatura_waha_valida(corpo: bytes, chave: str, assinatura: str) -> bool:
    if len(assinatura) != 128 or not assinatura.isascii():
        return False
    esperada = hmac.new(chave.encode(), corpo, hashlib.sha512).hexdigest()
    return hmac.compare_digest(esperada, assinatura)


def identificar_resposta_sem_texto(evento: str, mensagem: dict) -> str | None:
    """Identifica conteúdo enviado pelo cliente sem baixar anexos."""
    if mensagem.get("fromMe") is not False:
        return None

    if evento == "message.reaction":
        reacao = mensagem.get("reaction")
        if isinstance(reacao, dict) and isinstance(reacao.get("text"), str):
            if reacao["text"].strip() and reacao.get("messageId"):
                return "reacao"
        return None

    dados = mensagem.get("_data")
    tipo = mensagem.get("type") or (dados.get("type") if isinstance(dados, dict) else None)
    if tipo in ("protocol", "revoked", "ciphertext", "e2e_notification"):
        return None
    if mensagem.get("hasMedia") is True or tipo in (
        "ptt", "audio", "image", "video", "document", "sticker",
    ):
        return "midia"
    if mensagem.get("vCards") or tipo in ("vcard", "multi_vcard"):
        return "contato"
    if tipo in ("location", "live_location") or isinstance(mensagem.get("location"), dict):
        return "localizacao"
    return None


def identificar_saida_waha(
    evento: dict,
) -> tuple[dict | None, str]:
    """Valida um evento sem registrar ou enviar mensagens."""

    if not isinstance(evento, dict):
        return None, "evento_invalido"

    if evento.get("event") not in ("message", "message.any"):
        return None, "tipo_evento_invalido"

    mensagem = evento.get("payload")

    if not isinstance(mensagem, dict):
        return None, "payload_invalido"

    if mensagem.get("fromMe") is not True:
        return None, "nao_e_saida"

    sessao = evento.get("session")

    if not isinstance(sessao, str) or not sessao.strip():
        return None, "sessao_nao_identificada"

    destinatarios = [
        mensagem.get("to"),
        mensagem.get("chatId"),
    ]

    destinatarios = [
        valor.strip()
        for valor in destinatarios
        if isinstance(valor, str) and valor.strip()
    ]

    if not destinatarios:
        return None, "destinatario_nao_identificado"

    if len(set(destinatarios)) != 1:
        return None, "destinatario_ambiguo"

    destinatario = destinatarios[0]

    if not destinatario.endswith(("@c.us", "@lid")):
        return None, "destinatario_invalido"

    return {
        "sessao": sessao.strip(),
        "destinatario": destinatario,
        "mensagem_id": mensagem.get("id"),
    }, "saida_identificada"
