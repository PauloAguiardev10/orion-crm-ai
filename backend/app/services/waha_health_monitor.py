import logging
import os
import time

from app.services.waha_health_service import (
    WahaHealthResult,
    consultar_saude_sessao,
)


INTERVALO_SEGUNDOS = int(
    os.getenv(
        "WAHA_MONITOR_INTERVAL_SECONDS",
        "60",
    )
)

logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s "
        "%(levelname)s "
        "%(message)s"
    ),
)

logger = logging.getLogger("orion-waha-monitor")


def estado_mudou(
    anterior: WahaHealthResult | None,
    atual: WahaHealthResult,
) -> bool:
    if anterior is None:
        return True

    return (
        anterior.status != atual.status
        or anterior.engine_state != atual.engine_state
        or anterior.detalhe != atual.detalhe
    )


def registrar_estado(
    anterior: WahaHealthResult | None,
    atual: WahaHealthResult,
) -> None:
    if not estado_mudou(anterior, atual):
        return

    if anterior is None:
        logger.info(
            "WAHA_ESTADO_INICIAL "
            "sessao=%s status=%s "
            "engine_state=%s saudavel=%s",
            atual.sessao,
            atual.status,
            atual.engine_state,
            atual.saudavel,
        )

    else:
        logger.warning(
            "WAHA_TRANSICAO sessao=%s "
            "status_anterior=%s "
            "status_atual=%s "
            "engine_anterior=%s "
            "engine_atual=%s",
            atual.sessao,
            anterior.status,
            atual.status,
            anterior.engine_state,
            atual.engine_state,
        )

    if atual.requer_intervencao:
        logger.error(
            "WAHA_INTERVENCAO_NECESSARIA "
            "sessao=%s status=%s "
            "engine_state=%s detalhe=%s",
            atual.sessao,
            atual.status,
            atual.engine_state,
            atual.detalhe,
        )

    elif not atual.saudavel:
        logger.error(
            "WAHA_INDISPONIVEL "
            "sessao=%s status=%s "
            "engine_state=%s detalhe=%s",
            atual.sessao,
            atual.status,
            atual.engine_state,
            atual.detalhe,
        )

    elif anterior is not None:
        logger.info(
            "WAHA_RECUPERADO "
            "sessao=%s status=%s "
            "engine_state=%s",
            atual.sessao,
            atual.status,
            atual.engine_state,
        )


def executar_monitor() -> None:
    logger.info(
        "WAHA_MONITOR_INICIADO intervalo=%ss",
        INTERVALO_SEGUNDOS,
    )

    estado_anterior: WahaHealthResult | None = None

    while True:
        atual = consultar_saude_sessao("default")

        registrar_estado(
            estado_anterior,
            atual,
        )

        estado_anterior = atual

        time.sleep(INTERVALO_SEGUNDOS)


if __name__ == "__main__":
    executar_monitor()