import os
from pathlib import Path
import subprocess

from app.services.central_whatsapp_midia import LIMITE_MIDIA, validar_midia


def converter_gravacao(dados, tipo):
    """Aceita apenas os contêineres de áudio produzidos pelo gravador."""
    if not 0 < len(dados) <= LIMITE_MIDIA:
        raise ValueError("tamanho_midia_invalido")
    tipo = tipo.partition(";")[0].strip().lower()
    if tipo == "audio/ogg":
        validar_midia("voz.ogg", tipo, dados)
        return dados
    formatos = {
        "audio/webm": ("matroska", dados.startswith(b"\x1a\x45\xdf\xa3")),
        "audio/mp4": ("mov", dados[4:8] == b"ftyp"),
        "audio/wav": ("wav", dados.startswith(b"RIFF") and dados[8:12] == b"WAVE"),
    }
    formato = formatos.get(tipo)
    if formato is None or not formato[1]:
        raise ValueError("gravacao_invalida")
    ffmpeg = Path(os.getenv("ORION_WAHA_FFMPEG", ""))
    if not ffmpeg.is_absolute() or not ffmpeg.is_file():
        raise ValueError("conversor_voz_indisponivel")
    try:
        resultado = subprocess.run(
            [str(ffmpeg), "-nostdin", "-hide_banner", "-loglevel", "error",
             "-protocol_whitelist", "pipe", "-f", formato[0], "-i", "pipe:0",
             "-map", "0:a:0", "-vn", "-sn", "-dn", "-map_metadata", "-1",
             "-t", "120", "-ac", "1", "-ar", "48000", "-c:a", "libopus",
             "-b:a", "32k", "-fflags", "+bitexact", "-f", "ogg", "pipe:1"],
            input=dados, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=15,
            check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.SubprocessError):
        raise ValueError("falha_conversao_voz") from None
    validar_midia("voz.ogg", "audio/ogg", resultado.stdout)
    return resultado.stdout
