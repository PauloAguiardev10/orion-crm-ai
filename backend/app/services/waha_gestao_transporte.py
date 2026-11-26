import os
import re
from urllib.parse import quote, urlsplit

import requests

from app.services.waha_destino import PREFIXO, ConfiguracaoWahaInvalida, resolver_waha


class ErroGestaoWaha(Exception):
    def __init__(self, motivo, status=503):
        super().__init__(motivo)
        self.motivo = motivo
        self.status = status


class TransporteGestaoWaha:
    def __init__(self, sessao=None):
        self.sessao = sessao

    def _destino(self):
        try:
            return resolver_waha(self.sessao or "default")
        except ConfiguracaoWahaInvalida:
            raise ErroGestaoWaha("gestao_waha_indisponivel") from None

    def _sessao_fisica(self, sessao):
        if self.sessao is None:
            return sessao
        if self.sessao != sessao:
            raise ErroGestaoWaha("sessao_waha_divergente")
        return self._destino().sessao

    def _requisitar(self, metodo, caminho, *, corpo=None, imagem=False):
        if os.getenv("ORION_WAHA_GESTAO_ATIVA") != "1":
            raise ErroGestaoWaha("gestao_waha_desativada")
        rota = self._destino()
        if not rota.chave_api:
            raise ErroGestaoWaha("gestao_waha_indisponivel")
        origem = rota.origem
        try:
            with requests.request(
                metodo, origem + caminho, json=corpo,
                headers={**rota.headers, "Accept": "image/png" if imagem else "application/json"},
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
        sessao = self._sessao_fisica(sessao)
        dados = self._requisitar("GET", f"/api/sessions/{quote(sessao, safe='')}")
        if not isinstance(dados, dict) or dados.get("name") != sessao:
            raise ErroGestaoWaha("sessao_waha_divergente")
        if self.sessao and self.sessao.startswith(PREFIXO):
            config = dados.get("config")
            metadata = config.get("metadata") if isinstance(config, dict) else None
            if not isinstance(metadata, dict) or metadata.get("orionSessao") != self.sessao:
                raise ErroGestaoWaha("sessao_waha_divergente", 409)
        estados = {"STOPPED", "STARTING", "SCAN_QR_CODE", "WORKING", "FAILED",
                   "PASSKEY_REQUIRED", "PASSKEY_CONFIRMATION_REQUIRED"}
        estado = dados.get("status")
        eu = dados.get("me")
        if estado == "WORKING" and (not isinstance(eu, dict) or not eu.get("id")):
            try:
                eu = self._requisitar("GET", f"/api/sessions/{quote(sessao, safe='')}/me")
            except ErroGestaoWaha:
                eu = None
        conta = eu.get("id") if isinstance(eu, dict) else None
        numero = re.fullmatch(r"([0-9]{5,20})(?::[0-9]+)?@(?:c\.us|s\.whatsapp\.net)", conta or "") \
            if isinstance(conta, str) else None
        return {"estado": estado if isinstance(estado, str) and estado in estados else "DESCONHECIDO",
                "numero": numero[1] if numero else None}

    def criar(self, sessao):
        sessao = self._sessao_fisica(sessao)
        webhook = os.getenv("ORION_WAHA_WEBHOOK_URL", "").strip()
        rota = self._destino()
        chave = rota.chave_hmac
        if self.sessao and self.sessao.startswith(PREFIXO):
            instancia = self.sessao[len(PREFIXO):].split(":", 1)[0]
            webhook = rota.webhook or (f"{webhook.rstrip('/')}/{instancia}" if webhook else "")
        url = urlsplit(webhook)
        if url.scheme not in ("http", "https") or not url.hostname or url.username or url.password or url.query or url.fragment or not chave:
            raise ErroGestaoWaha("webhook_waha_nao_configurado")
        self._requisitar("POST", "/api/sessions", corpo={
            "name": sessao, "start": False,
            "config": {"metadata": {"orionSessao": self.sessao or sessao}, "webhooks": [{
                "url": webhook, "hmac": {"key": chave},
                "events": ["message", "message.any", "message.reaction", "message.ack", "message.edited", "message.revoked",
                           *(["presence.update"] if os.getenv("ORION_WAHA_PRESENCA_ATIVA") == "1" else [])],
            }]},
        })

    def iniciar(self, sessao):
        sessao = self._sessao_fisica(sessao)
        self._requisitar("POST", f"/api/sessions/{quote(sessao, safe='')}/start")

    def reiniciar(self, sessao):
        sessao = self._sessao_fisica(sessao)
        self._requisitar("POST", f"/api/sessions/{quote(sessao, safe='')}/restart")

    def desconectar(self, sessao):
        sessao = self._sessao_fisica(sessao)
        self._requisitar("POST", f"/api/sessions/{quote(sessao, safe='')}/stop")

    def esquecer_pareamento(self, sessao):
        sessao = self._sessao_fisica(sessao)
        self._requisitar("POST", f"/api/sessions/{quote(sessao, safe='')}/logout")

    def qr(self, sessao):
        sessao = self._sessao_fisica(sessao)
        return self._requisitar("GET", f"/api/{quote(sessao, safe='')}/auth/qr", imagem=True)
