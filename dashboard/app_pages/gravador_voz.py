import base64
import binascii
from dataclasses import dataclass
from pathlib import Path

from streamlit.components.v1 import declare_component


_gravador = declare_component("orion_gravador_voz", path=str(Path(__file__).with_name("gravador_voz_assets")))


@dataclass(frozen=True)
class Gravacao:
    name: str
    type: str
    dados: bytes

    @property
    def size(self):
        return len(self.dados)

    def getvalue(self):
        return self.dados


def gravar_voz(chave):
    evento = _gravador(key=chave, default=None)
    if not isinstance(evento, dict) or evento.get("cancelado"):
        return None
    dado, formato = evento.get("dados"), evento.get("tipo")
    extensoes = {"audio/ogg": "ogg", "audio/webm": "webm", "audio/mp4": "mp4"}
    if not isinstance(dado, str) or len(dado) > 11_184_812 or formato not in extensoes:
        return None
    try:
        bruto = base64.b64decode(dado, validate=True)
    except (ValueError, binascii.Error):
        return None
    if not 0 < len(bruto) <= 8 * 1024 * 1024:
        return None
    return Gravacao(f"voz.{extensoes[formato]}", formato, bruto)
