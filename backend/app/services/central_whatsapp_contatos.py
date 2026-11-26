"""Consultas de contatos limitadas à sessão autorizada pelo CRM."""

from urllib.parse import urlsplit

import requests

from app.services.followup_destinatario_service import chat_id_whatsapp_valido
from app.services.waha_destino import ConfiguracaoWahaInvalida, resolver_waha


def _consulta_contato(sessao, caminho, **params):
    try:
        rota = resolver_waha(sessao)
        if not rota.chave_api:
            raise ValueError
        resposta = requests.get(
            rota.origem + caminho, headers=rota.headers,
            params={"session": rota.sessao, **params}, allow_redirects=False, timeout=(3, 5),
        )
        if resposta.status_code == 200:
            dados = resposta.json()
            if isinstance(dados, dict):
                return dados
    except (ConfiguracaoWahaInvalida, requests.RequestException, ValueError):
        pass
    raise ValueError("contato_waha_indisponivel")


def identificar_telefone_waha(sessao, telefone):
    dados = _consulta_contato(sessao, "/api/contacts/check-exists", phone=telefone)
    chat = dados.get("chatId")
    if dados.get("numberExists") is not True or not chat_id_whatsapp_valido(chat):
        raise ValueError("telefone_nao_confirmado")
    return chat


def obter_foto_waha(sessao, chat):
    if not chat_id_whatsapp_valido(chat):
        raise ValueError("contato_waha_indisponivel")
    dados = _consulta_contato(sessao, "/api/contacts/profile-picture", contactId=chat)
    foto = dados.get("profilePictureURL")
    if not isinstance(foto, str):
        raise ValueError("foto_indisponivel")
    try:
        url = urlsplit(foto)
        dominio = url.hostname or ""
        if (url.scheme != "https" or url.username or url.password or url.port not in (None, 443)
                or not (dominio == "pps.whatsapp.net" or dominio.endswith(".pps.whatsapp.net"))):
            raise ValueError
        with requests.get(foto, timeout=(3, 5), allow_redirects=False, stream=True) as resposta:
            if resposta.status_code != 200:
                raise ValueError
            buffer = bytearray()
            for bloco in resposta.iter_content(chunk_size=16384):
                if len(buffer) + len(bloco) > 512 * 1024:
                    raise ValueError
                buffer.extend(bloco)
            if buffer.startswith(b"\xff\xd8\xff"):
                return bytes(buffer), "image/jpeg"
            if buffer.startswith(b"\x89PNG\r\n\x1a\n"):
                return bytes(buffer), "image/png"
    except (requests.RequestException, ValueError):
        pass
    raise ValueError("foto_indisponivel")


def listar_contatos_waha(sessao, deslocamento, busca=""):
    import re
    from urllib.parse import quote

    try:
        rota = resolver_waha(sessao)
        if not rota.chave_api:
            raise ValueError
        estado = requests.get(
            f"{rota.origem}/api/sessions/{quote(rota.sessao, safe='')}",
            headers=rota.headers, timeout=(3, 6), allow_redirects=False,
        )
        if estado.status_code != 200:
            raise ValueError
        dados = estado.json()
        config = dados.get("config") or {}
        engine = dados.get("engine")
        if isinstance(engine, dict):
            engine = engine.get("engine")
        if (dados.get("name") != rota.sessao or dados.get("status") != "WORKING"
                or engine != "NOWEB" or config.get("noweb", {}).get("store", {}).get("enabled") is not True):
            raise ValueError
        if sessao.startswith("orion-waha:") and (config.get("metadata") or {}).get("orionSessao") != sessao:
            raise ValueError
        encontrados = []
        termo = busca.strip().casefold()
        proxima = deslocamento
        for _ in range(4 if termo else 1):
            resposta = requests.get(
                rota.origem + "/api/contacts/all", headers=rota.headers,
                params={"session": rota.sessao, "limit": 50, "offset": proxima,
                        "sortBy": "id", "sortOrder": "asc"},
                timeout=(3, 5), allow_redirects=False,
            )
            if resposta.status_code != 200:
                raise ValueError
            contatos = resposta.json()
            if not isinstance(contatos, list) or len(contatos) > 50:
                raise ValueError
            for item in contatos:
                if not isinstance(item, dict) or item.get("isMe") or item.get("isGroup"):
                    continue
                chat = item.get("id")
                if not chat_id_whatsapp_valido(chat):
                    continue
                match = re.fullmatch(r"([1-9][0-9]{7,14})@c\.us", chat)
                telefone = match[1] if match else None
                valor = item.get("name") or item.get("pushname")
                nome = valor[:150] if isinstance(valor, str) else None
                if not termo or termo in (nome or "").casefold() or termo.lstrip("+") in (telefone or ""):
                    encontrados.append({"id": chat, "telefone": telefone, "nome": nome})
            proxima = proxima + 50 if len(contatos) == 50 and proxima < 100000 else None
            if encontrados or proxima is None:
                break
        return {"contatos": encontrados, "proxima": proxima}
    except (ConfiguracaoWahaInvalida, requests.RequestException, AttributeError, ValueError):
        raise ValueError("contatos_noweb_indisponiveis") from None


def obter_foto_contato_cadastrado(sessao, chat):
    if not chat_id_whatsapp_valido(chat):
        raise ValueError("contato_waha_indisponivel")
    dados = _consulta_contato(sessao, "/api/contacts", contactId=chat)
    if dados.get("id") != chat or dados.get("isMe") or dados.get("isGroup"):
        raise ValueError("contato_waha_indisponivel")
    return obter_foto_waha(sessao, chat)
