"""Validacao conservadora de eventos de saida do WAHA."""


def identificar_saida_waha(
    evento: dict,
) -> tuple[dict | None, str]:
    """Valida um evento sem registrar ou enviar mensagens."""

    if not isinstance(evento, dict):
        return None, "evento_invalido"

    if evento.get("event") != "message":
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
