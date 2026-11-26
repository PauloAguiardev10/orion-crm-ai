from urllib.parse import quote
from dataclasses import dataclass

import requests

from app.services.waha_destino import ConfiguracaoWahaInvalida, resolver_waha


WAHA_TIMEOUT_SEGUNDOS = 10


@dataclass(frozen=True)
class WahaHealthResult:
    sessao: str
    status: str
    saudavel: bool
    requer_intervencao: bool
    engine_state: str | None = None
    detalhe: str | None = None


def normalizar_status_waha(status: object) -> str:
    valor = str(status or "UNKNOWN").strip().upper()
    return valor or "UNKNOWN"


def consultar_saude_sessao(
    sessao: str = "default",
) -> WahaHealthResult:
    sessao = str(sessao).strip() or "default"

    try:
        rota = resolver_waha(sessao, saude_legada=True)
        if not rota.chave_api:
            raise ConfiguracaoWahaInvalida("chave_waha_ausente")
        resposta = requests.get(
            f"{rota.origem}/api/sessions/{quote(rota.sessao, safe='')}",
            headers=rota.headers, allow_redirects=False,
            timeout=WAHA_TIMEOUT_SEGUNDOS,
        )
        resposta.raise_for_status()

        dados = resposta.json()

        if not isinstance(dados, dict):
            return WahaHealthResult(
                sessao=sessao,
                status="INVALID_RESPONSE",
                saudavel=False,
                requer_intervencao=False,
                detalhe="Resposta JSON nao e objeto",
            )

        status = normalizar_status_waha(
            dados.get("status")
        )

        engine = dados.get("engine") or {}

        engine_state = None
        if isinstance(engine, dict):
            estado = engine.get("state")
            if estado:
                engine_state = str(estado).strip().upper()

        return WahaHealthResult(
            sessao=sessao,
            status=status,
            saudavel=status == "WORKING",
            requer_intervencao=(
                status == "SCAN_QR_CODE"
            ),
            engine_state=engine_state,
        )

    except RuntimeError as erro:
        return WahaHealthResult(
            sessao=sessao,
            status="CONFIG_ERROR",
            saudavel=False,
            requer_intervencao=True,
            detalhe=str(erro),
        )

    except requests.RequestException as erro:
        return WahaHealthResult(
            sessao=sessao,
            status="UNREACHABLE",
            saudavel=False,
            requer_intervencao=False,
            detalhe=type(erro).__name__,
        )

    except (TypeError, ValueError) as erro:
        return WahaHealthResult(
            sessao=sessao,
            status="INVALID_RESPONSE",
            saudavel=False,
            requer_intervencao=False,
            detalhe=type(erro).__name__,
        )