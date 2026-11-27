"""Referencias de resposta fornecidas pela WAHA em mensagens individuais."""

import re


def extrair_citacao_waha(payload, chat):
    if not isinstance(chat, str):
        return None
    citacao = payload.get("replyTo")
    alvo = citacao.get("id") if isinstance(citacao, dict) else None
    if isinstance(alvo, str) and re.fullmatch(rf"(?:true|false)_{re.escape(chat)}_[A-Za-z0-9-]{{1,130}}", alvo):
        return alvo
    return None
