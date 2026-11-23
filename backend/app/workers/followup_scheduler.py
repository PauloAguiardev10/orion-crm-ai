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
    modo_simulacao: bool = True,
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

    if type(modo_simulacao) is not bool:
        raise ValueError("modo_simulacao_invalido")

    if modo_simulacao:
        if not callable(session_factory):
            raise ValueError("simulacao_exige_sessao_de_teste")
        if mapa_sessoes is None or not callable(simulador_envio):
            raise ValueError("simulacao_exige_transporte_simulado")
    else:
        if os.getenv("FOLLOWUP_WORKER_ATIVO") != "1":
            raise ValueError("worker_desabilitado")
        if os.getenv("FOLLOWUP_ENVIO_REAL_ATIVO") != "1":
            raise ValueError("envio_real_desabilitado")
        if simulador_envio is not None:
            raise ValueError("transporte_injetado_no_modo_real")
        if session_factory is None:
            from app.database.database import SessionLocal
            session_factory = SessionLocal
        if not callable(session_factory):
            raise ValueError("session_factory_invalida")

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
                    modo_simulacao=modo_simulacao,
                    session_factory=session_factory,
                    mapa_sessoes=mapa_sessoes,
                    simulador_envio=(
                        simulador_envio if modo_simulacao else None
                    ),
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

    if os.getenv("FOLLOWUP_WORKER_ATIVO") != "1":
        raise SystemExit("Follow-up desabilitado: FOLLOWUP_WORKER_ATIVO != 1")

    if os.getenv("FOLLOWUP_ENVIO_REAL_ATIVO") != "1":
        raise SystemExit("Envio real desabilitado: FOLLOWUP_ENVIO_REAL_ATIVO != 1")

    executar_agendador(
        empresa_ids=ids,
        modo_simulacao=False,
    )
