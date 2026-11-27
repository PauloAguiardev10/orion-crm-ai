"""Identificadores equivalentes do NOWEB, sem inferir telefones a partir de LID."""

import re


def chat_canonico(valor):
    if isinstance(valor, str) and re.fullmatch(r"[0-9]+@s\.whatsapp\.net", valor):
        return valor.split("@", 1)[0] + "@c.us"
    return valor


def jid_noweb(valor):
    canonico = chat_canonico(valor)
    if isinstance(canonico, str) and re.fullmatch(r"[0-9]+@c\.us", canonico):
        return canonico.split("@", 1)[0] + "@s.whatsapp.net"
    return canonico


def aliases_chat(valor):
    return tuple(dict.fromkeys((chat_canonico(valor), jid_noweb(valor))))


def aliases_mensagem(valor, chats_confirmados=()):
    if not isinstance(valor, str):
        return (valor,)
    partes = valor.split("_", 2)
    if len(partes) != 3 or partes[0] not in ("true", "false"):
        return (valor,)
    chats = chats_confirmados if partes[1] in chats_confirmados else aliases_chat(partes[1])
    return tuple(dict.fromkeys((valor, *(f"{partes[0]}_{chat}_{partes[2]}" for chat in chats))))


def chat_no_id_mensagem(valor, saida):
    partes = valor.split("_", 2) if isinstance(valor, str) else ()
    if len(partes) == 3 and partes[0] == str(saida).lower() and partes[2]:
        return partes[1]
    return None
