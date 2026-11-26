"""Resolve nomes internos do CRM para destinos WAHA provisionados pelo operador."""

import json
import os
import re
from dataclasses import dataclass, field
from urllib.parse import urlsplit


PREFIXO = "orion-waha:"
NOME = re.compile(r"[a-zA-Z0-9_-]{1,48}")


class ConfiguracaoWahaInvalida(RuntimeError):
    pass


@dataclass(frozen=True)
class DestinoWaha:
    origem: str
    sessao: str
    chave_api: str = field(repr=False)
    chave_hmac: str = field(default="", repr=False)
    webhook: str = field(default="", repr=False)

    @property
    def headers(self):
        return {"X-Api-Key": self.chave_api}


def alias_waha(instancia, sessao):
    if not all(isinstance(valor, str) and NOME.fullmatch(valor) for valor in (instancia, sessao)):
        raise ConfiguracaoWahaInvalida("identificador_waha_invalido")
    return f"{PREFIXO}{instancia}:{sessao}"


def _origem(valor):
    try:
        url = urlsplit(valor)
        if (url.scheme in ("http", "https") and url.hostname and not url.username
                and not url.password and url.path in ("", "/") and not url.query and not url.fragment):
            return valor.rstrip("/")
    except (ValueError, TypeError):
        pass
    raise ConfiguracaoWahaInvalida("origem_waha_invalida")


def resolver_waha(sessao, *, saude_legada=False):
    if not isinstance(sessao, str) or not sessao.strip():
        raise ConfiguracaoWahaInvalida("sessao_waha_invalida")
    sessao = sessao.strip()
    if not sessao.startswith(PREFIXO):
        origem = os.getenv("WAHA_API_URL", "http://localhost:3000")
        if saude_legada:
            origem = os.getenv("WAHA_BASE_URL", origem)
        return DestinoWaha(_origem(origem), sessao, os.getenv("WAHA_API_KEY", "").strip(),
                           os.getenv("WAHA_WEBHOOK_HMAC_KEY", ""))
    instancia, separador, fisica = sessao[len(PREFIXO):].partition(":")
    if not separador or alias_waha(instancia, fisica) != sessao:
        raise ConfiguracaoWahaInvalida("sessao_waha_invalida")
    try:
        cadastro = json.loads(os.getenv("ORION_WAHA_INSTANCIAS", "{}"))
        if not isinstance(cadastro, dict):
            raise ValueError
        dados = cadastro[instancia]
        chave = os.environ[dados["api_key_env"]].strip()
        hmac = os.environ[dados["hmac_env"]].strip()
        if not chave or not hmac or not isinstance(dados["sessoes"], list) or fisica not in dados["sessoes"]:
            raise ValueError
        origem = _origem(dados["origem"])
        if (hmac == os.getenv("WAHA_WEBHOOK_HMAC_KEY", "").strip()
                or chave == os.getenv("WAHA_API_KEY", "").strip()
                or origem == _origem(os.getenv("WAHA_API_URL", "http://localhost:3000"))):
            raise ValueError
        for outra, configuracao in cadastro.items():
            if outra != instancia and (
                os.getenv(configuracao["hmac_env"], "").strip() == hmac
                or os.getenv(configuracao["api_key_env"], "").strip() == chave
                or _origem(configuracao["origem"]) == origem
            ):
                raise ValueError
        webhook = dados.get("webhook_url", "")
        if not isinstance(webhook, str):
            raise ValueError
        return DestinoWaha(origem, fisica, chave, hmac, webhook.strip())
    except (KeyError, TypeError, ValueError):
        raise ConfiguracaoWahaInvalida("instancia_waha_indisponivel") from None
