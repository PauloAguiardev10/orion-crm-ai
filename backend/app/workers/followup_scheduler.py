"""Agendador independente de follow-up do Orion CRM AI.

Nesta etapa, executa exclusivamente ciclos sem envio real.
"""

import logging
import os
import time

from app.workers.followup_worker import (
    executar_ciclo_followup,
    recuperar_followups_expirados_transacional,
)


logger = logging.getLogger("orion.followup.scheduler")


def executar_agendador(
    *,
    empresa_ids: list[int],
    intervalo_segundos: int = 60,
    max_ciclos: int | None = None,
    session_factory=None,
    mapa_sessoes=None,
    simulador_envio=None,
) -> None:
    """Executa ciclos periodicos em modo seguro."""

    if type(intervalo_segundos) is not int or intervalo_segundos < 1:
        raise ValueError("intervalo_invalido")

    if max_ciclos is not None and (
        type(max_ciclos) is not int or max_ciclos < 1
    ):
        raise ValueError("max_ciclos_invalido")

    if not isinstance(empresa_ids, list) or not empresa_ids:
        raise ValueError("empresas_invalidas")

    if any(type(empresa_id) is not int or empresa_id < 1 for empresa_id in empresa_ids):
        raise ValueError("empresa_invalida")

    if len(set(empresa_ids)) != len(empresa_ids):
        raise ValueError("empresa_duplicada")

    if session_factory is None:
        from sqlalchemy.engine import make_url
        from app.database.database import DATABASE_URL, SessionLocal

        url = make_url(DATABASE_URL)

        ambiente_teste = (
            url.host == "127.0.0.1"
            and url.port == 55432
            and url.database == "orion_crm_followup_test"
            and url.username == "orion_test"
        )

        if not ambiente_teste:
            raise RuntimeError(
                "BLOQUEADO: agendador automatico fora do banco de testes"
            )

        session_factory = SessionLocal

    ciclos = 0

    while max_ciclos is None or ciclos < max_ciclos:
        for empresa_id in empresa_ids:
            try:
                try:
                    with session_factory() as db:
                        quantidade, motivo_recuperacao = (
                            recuperar_followups_expirados_transacional(
                                db,
                                empresa_id=empresa_id,
                            )
                        )

                    logger.info(
                        "recuperacao followup empresa=%s quantidade=%s resultado=%s",
                        empresa_id,
                        quantidade,
                        motivo_recuperacao,
                    )

                except Exception:
                    logger.exception(
                        "Erro na recuperacao de reservas da empresa %s",
                        empresa_id,
                    )
                    continue

                sucesso, resultado = executar_ciclo_followup(
                    empresa_id=empresa_id,
                    modo_simulacao=True,
                    session_factory=session_factory,
                    mapa_sessoes=mapa_sessoes,
                    simulador_envio=simulador_envio,
                )

                logger.info(
                    "followup empresa=%s sucesso=%s resultado=%s",
                    empresa_id,
                    sucesso,
                    resultado,
                )

            except Exception:
                logger.exception(
                    "Erro no ciclo de follow-up da empresa %s",
                    empresa_id,
                )

        ciclos += 1

        if max_ciclos is None or ciclos < max_ciclos:
            time.sleep(intervalo_segundos)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    empresas = os.getenv("FOLLOWUP_EMPRESA_IDS", "").strip()

    if not empresas:
        raise SystemExit(
            "Configure FOLLOWUP_EMPRESA_IDS para executar o agendador."
        )

    ids = [int(item.strip()) for item in empresas.split(",")]

    executar_agendador(
        empresa_ids=ids,
        intervalo_segundos=int(
            os.getenv("FOLLOWUP_INTERVALO_SEGUNDOS", "60")
        ),
    )
