import os
import re
from urllib.parse import quote, urlsplit

import requests


class ErroGestaoWaha(Exception):
    def __init__(self, motivo, status=503):
        super().__init__(motivo)
        self.motivo = motivo
        self.status = status


class TransporteGestaoWaha:
    def _requisitar(self, metodo, caminho, *, corpo=None, imagem=False):
        if os.getenv("ORION_WAHA_GESTAO_ATIVA") != "1":
            raise ErroGestaoWaha("gestao_waha_desativada")
        chave = os.getenv("WAHA_API_KEY", "").strip()
        if not chave:
            raise ErroGestaoWaha("gestao_waha_indisponivel")
        origem = os.getenv("WAHA_API_URL", "http://localhost:3000").rstrip("/")
        try:
            with requests.request(
                metodo, origem + caminho, json=corpo,
                headers={"X-Api-Key": chave, "Accept": "image/png" if imagem else "application/json"},
                timeout=(3, 8), allow_redirects=False, stream=imagem,
            ) as resposta:
                if resposta.status_code == 404:
                    raise ErroGestaoWaha("recurso_waha_indisponivel", 404)
                if resposta.status_code in (400, 403, 409, 422):
                    texto = resposta.text.lower()[:2048]
                    if any(f in texto for f in (
                        "only default session", "only 'default' session",
                        "session limit", "maximum number of sessions", "multiple sessions",
                        "only one session", "only supports one session",
                    )):
                        raise ErroGestaoWaha("limite_sessoes_provedor", 409)
                    raise ErroGestaoWaha("operacao_waha_recusada", 409)
                if not 200 <= resposta.status_code < 300:
                    raise ErroGestaoWaha("gestao_waha_indisponivel")
                if imagem:
                    dados = bytearray()
                    for bloco in resposta.iter_content(chunk_size=16384):
                        dados.extend(bloco)
                        if len(dados) > 256 * 1024:
                            raise ErroGestaoWaha("qr_waha_invalido")
                    if not dados.startswith(b"\x89PNG\r\n\x1a\n"):
                        raise ErroGestaoWaha("qr_waha_invalido")
                    return bytes(dados)
                return resposta.json() if metodo == "GET" else None
        except (requests.RequestException, ValueError):
            raise ErroGestaoWaha("gestao_waha_indisponivel") from None

    def consultar(self, sessao):
        dados = self._requisitar("GET", f"/api/sessions/{quote(sessao, safe='')}")
        if not isinstance(dados, dict) or dados.get("name") != sessao:
            raise ErroGestaoWaha("sessao_waha_divergente")
        estados = {"STOPPED", "STARTING", "SCAN_QR_CODE", "WORKING", "FAILED",
                   "PASSKEY_REQUIRED", "PASSKEY_CONFIRMATION_REQUIRED"}
        estado = dados.get("status")
        eu = dados.get("me")
        conta = eu.get("id") if isinstance(eu, dict) else None
        numero = re.fullmatch(r"([0-9]{5,20})(?::[0-9]+)?@(?:c\.us|s\.whatsapp\.net)", conta or "") \
            if isinstance(conta, str) else None
        return {"estado": estado if isinstance(estado, str) and estado in estados else "DESCONHECIDO",
                "numero": numero[1] if numero else None}

    def criar(self, sessao):
        webhook = os.getenv("ORION_WAHA_WEBHOOK_URL", "").strip()
        chave = os.getenv("WAHA_WEBHOOK_HMAC_KEY", "").strip()
        url = urlsplit(webhook)
        if url.scheme not in ("http", "https") or not url.hostname or url.username or not chave:
            raise ErroGestaoWaha("webhook_waha_nao_configurado")
        self._requisitar("POST", "/api/sessions", corpo={
            "name": sessao, "start": False,
            "config": {"webhooks": [{
                "url": webhook, "hmac": {"key": chave},
                "events": ["message", "message.any", "message.reaction", "message.ack"],
            }]},
        })

    def iniciar(self, sessao):
        self._requisitar("POST", f"/api/sessions/{quote(sessao, safe='')}/start")

    def reiniciar(self, sessao):
        self._requisitar("POST", f"/api/sessions/{quote(sessao, safe='')}/restart")

    def desconectar(self, sessao):
        self._requisitar("POST", f"/api/sessions/{quote(sessao, safe='')}/stop")

    def qr(self, sessao):
        return self._requisitar("GET", f"/api/{quote(sessao, safe='')}/auth/qr", imagem=True)
