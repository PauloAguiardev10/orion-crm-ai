import os
from dataclasses import dataclass

import requests


WAHA_BASE_URL = os.getenv(
    "WAHA_BASE_URL",
    "http://localhost:3000",
).rstrip("/")

WAHA_TIMEOUT_SEGUNDOS = 10


@dataclass(frozen=True)
class WahaHealthResult:
    sessao: str
    status: str
    saudavel: bool
    requer_intervencao: bool
    engine_state: str | None = None
    detalhe: str | None = None


def _headers_waha() -> dict[str, str]:
    api_key = os.getenv("WAHA_API_KEY", "").strip()

    if not api_key:
        raise RuntimeError(
            "WAHA_API_KEY nao configurada"
        )

    return {
        "Accept": "application/json",
        "X-Api-Key": api_key,
    }


def normalizar_status_waha(status: object) -> str:
    valor = str(status or "UNKNOWN").strip().upper()
    return valor or "UNKNOWN"


def consultar_saude_sessao(
    sessao: str = "default",
) -> WahaHealthResult:
    sessao = str(sessao).strip() or "default"

    try:
        resposta = requests.get(
            f"{WAHA_BASE_URL}/api/sessions/{sessao}",
            headers=_headers_waha(),
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