import base64
import os
import re
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit
from uuid import uuid4

import requests

from app.services.followup_ids_waha import extrair_id_resposta_waha


LIMITE_MIDIA = 8 * 1024 * 1024
FORMATOS = {
    "image/jpeg": ("imagem", "sendImage", (".jpg", ".jpeg")),
    "image/png": ("imagem", "sendImage", (".png",)),
    "audio/ogg": ("audio", "sendVoice", (".ogg", ".opus")),
    "video/mp4": ("video", "sendVideo", (".mp4",)),
    "application/pdf": ("documento", "sendFile", (".pdf",)),
}
NOME_SEGURO = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9 ._()-]{0,119}")
CHAVE_SEGURA = re.compile(r"[0-9a-f]{32}")
MIME_VOZ = "audio/ogg; codecs=opus"


def midia_ativa():
    return os.getenv("ORION_CENTRAL_WHATSAPP_MIDIA_ATIVA") == "1"


def validar_midia(nome, mime, dados):
    mime = mime.partition(";")[0].strip().lower()
    extensao = Path(nome).suffix.lower()
    if mime in ("", "application/octet-stream"):
        mime = next((tipo for tipo, formato in FORMATOS.items() if extensao in formato[2]), "")
    if mime == "audio/opus":
        mime = "audio/ogg"
    formato = FORMATOS.get(mime)
    if not formato or not NOME_SEGURO.fullmatch(nome):
        raise ValueError("formato_ou_nome_invalido")
    if extensao not in formato[2]:
        raise ValueError("extensao_incompativel")
    if not 0 < len(dados) <= LIMITE_MIDIA:
        raise ValueError("tamanho_midia_invalido")
    assinatura = {
        "image/jpeg": dados.startswith(b"\xff\xd8\xff"),
        "image/png": dados.startswith(b"\x89PNG\r\n\x1a\n"),
        "audio/ogg": dados.startswith(b"OggS") and dados[28:36] == b"OpusHead",
        "video/mp4": dados[4:8] == b"ftyp",
        "application/pdf": dados.startswith(b"%PDF-"),
    }
    if not assinatura[mime]:
        raise ValueError("conteudo_incompativel")
    return mime


def caminho_midia(empresa_id, referencia):
    chave, separador, nome = (referencia or "").partition(":")
    if (type(empresa_id) is not int or empresa_id <= 0 or not separador
        or not CHAVE_SEGURA.fullmatch(chave) or not NOME_SEGURO.fullmatch(nome)):
        raise ValueError("referencia_invalida")
    raiz = os.getenv("ORION_CENTRAL_WHATSAPP_MIDIA_DIR")
    if not raiz or not Path(raiz).is_absolute():
        raise ValueError("armazenamento_indisponivel")
    diretorio = Path(raiz).resolve() / str(empresa_id)
    caminho = diretorio / chave
    if diretorio.is_symlink() or caminho.is_symlink():
        raise ValueError("referencia_invalida")
    return caminho, nome


def guardar_midia(empresa_id, nome, dados):
    referencia = f"{uuid4().hex}:{nome}"
    caminho, _ = caminho_midia(empresa_id, referencia)
    caminho.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    temporario = caminho.with_suffix(".tmp")
    try:
        descritor = os.open(temporario, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0), 0o600)
        with os.fdopen(descritor, "wb") as arquivo:
            arquivo.write(dados)
        temporario.replace(caminho)
    finally:
        temporario.unlink(missing_ok=True)
    return referencia


def baixar_midia_waha(midia, *, sessao, mensagem_id):
    mime = str(midia.get("mimetype") or "").partition(";")[0].strip().lower()
    if mime not in FORMATOS or midia.get("error"):
        raise ValueError("formato_indisponivel")
    # Reconstrói a URL com a origem configurada e aceita apenas o arquivo
    # do próprio evento, no caminho de mídia documentado pela WAHA.
    segmentos = unquote(urlsplit(midia.get("url") or "").path).split("/")
    if segmentos[:3] != ["", "api", "files"] or len(segmentos) not in (4, 5):
        raise ValueError("caminho_midia_invalido")
    nome_waha = segmentos[-1]
    if (len(segmentos) == 5 and (
        segmentos[3] != sessao or not re.fullmatch(r"[a-zA-Z0-9_-]+", sessao)
    )) or (
        Path(nome_waha).stem != mensagem_id
        or not re.fullmatch(r"[a-zA-Z0-9_@.-]+", nome_waha)
    ):
        raise ValueError("arquivo_waha_divergente")
    nome = midia.get("filename")
    if not isinstance(nome, str) or not NOME_SEGURO.fullmatch(nome):
        nome = "anexo" + FORMATOS[mime][2][0]
    base = os.getenv("WAHA_API_URL", "http://localhost:3000").rstrip("/")
    chave = os.getenv("WAHA_API_KEY", "").strip()
    if not chave:
        raise ValueError("transporte_indisponivel")
    destino = "/".join(quote(seg, safe="") for seg in segmentos)
    dados = bytearray()
    with requests.get(
        base + destino, headers={"X-Api-Key": chave}, stream=True,
        allow_redirects=False, timeout=(3, 8),
    ) as resposta:
        if resposta.status_code != 200:
            raise ValueError("midia_indisponivel")
        for bloco in resposta.iter_content(chunk_size=65536):
            if len(dados) + len(bloco) > LIMITE_MIDIA:
                raise ValueError("tamanho_midia_invalido")
            dados.extend(bloco)
    return nome, validar_midia(nome, mime, dados), bytes(dados)


def enviar_midia_waha(sessao, chat_id, legenda, *, nome, mime, dados):
    chave = os.getenv("WAHA_API_KEY", "").strip()
    if not chave:
        return False, "falha_envio", None
    base = os.getenv("WAHA_API_URL", "http://localhost:3000").rstrip("/")
    tipo, endpoint, _ = FORMATOS[mime]
    corpo = {
        "session": sessao, "chatId": chat_id,
        "file": {
            "mimetype": MIME_VOZ if tipo == "audio" else mime,
            "filename": nome, "data": base64.b64encode(dados).decode("ascii"),
        },
    }
    if legenda and tipo != "audio":
        corpo["caption"] = legenda
    try:
        resposta = requests.post(
            f"{base}/api/{endpoint}", json=corpo, headers={"X-Api-Key": chave},
            timeout=(3, 20), allow_redirects=False,
        )
        if resposta.status_code >= 500 or 300 <= resposta.status_code < 400:
            return False, "timeout_envio_inconclusivo", None
        resposta.raise_for_status()
        mensagem_id = extrair_id_resposta_waha(resposta.json())
        if not mensagem_id:
            return False, "timeout_envio_inconclusivo", None
        return True, None, mensagem_id
    except (requests.Timeout, requests.ConnectionError, ValueError):
        return False, "timeout_envio_inconclusivo", None
    except requests.RequestException:
        return False, "falha_envio", None
