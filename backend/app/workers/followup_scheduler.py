"""Agendador independente de follow-up do Orion CRM AI."""

import logging
import os
import time

from app.services.followup_service import agendamento_followup_ativo
from app.workers.followup_worker import (
    executar_ciclo_followup,
    recuperar_followups_expirados_transacional,
)


logger = logging.getLogger("orion.followup.scheduler")



def processar_leads_apos_cinco_minutos(db, *, empresa_id: int) -> int:
    """Agenda leads sem resposta apos cinco minutos. Nao envia mensagens."""
    from datetime import datetime, timedelta, timezone
    from app.models.models import Conversa, Lead
    from app.services.followup_service import (
        verificar_elegibilidade_primeiro_followup,
    )
    from app.services.followup_agendamento_service import (
        criar_primeiro_agendamento,
    )

    limite = datetime.now(timezone.utc) - timedelta(minutes=5)
    quantidade = 0

    candidatos = (
        db.query(Lead.id, Lead.conversa_id)
        .filter(
            Lead.empresa_id == empresa_id,
            Lead.status == "Em atendimento",
            Lead.entrada_followup_em.isnot(None),
            Lead.entrada_followup_em <= limite,
        )
        .all()
    )

    for lead_id, conversa_id in candidatos:
        try:
            # Usa a mesma ordem de bloqueios da recepção de mensagens.
            conversa = (
                db.query(Conversa.id)
                .filter(
                    Conversa.id == conversa_id,
                    Conversa.empresa_id == empresa_id,
                )
                .with_for_update(skip_locked=True)
                .one_or_none()
            )
            if conversa is None:
                db.rollback()
                continue

            lead = (
                db.query(Lead)
                .filter(
                    Lead.id == lead_id,
                    Lead.empresa_id == empresa_id,
                    Lead.conversa_id == conversa_id,
                    Lead.status == "Em atendimento",
                    Lead.entrada_followup_em <= limite,
                )
                .with_for_update()
                .one_or_none()
            )

            if lead is None:
                db.rollback()
                continue

            elegivel, motivo = verificar_elegibilidade_primeiro_followup(
                db,
                empresa_id=empresa_id,
                lead_id=lead.id,
                permitir_em_atendimento=True,
            )

            if not elegivel:
                db.rollback()
                continue

            lead.status = "Aguardando resposta"
            db.flush()

            agendamento, motivo = criar_primeiro_agendamento(
                db,
                empresa_id=empresa_id,
                lead_id=lead.id,
                entrada_lead_em=lead.entrada_followup_em,
            )

            if agendamento is None:
                db.rollback()
                logger.info(
                    "Follow-up nao agendado: lead=%s motivo=%s",
                    lead_id, motivo,
                )
                continue

            db.commit()
            if motivo == "agendamento_preparado":
                quantidade += 1

        except Exception:
            db.rollback()
            logger.exception(
                "Erro ao processar lead %s para follow-up", lead_id,
            )

    return quantidade


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
                    if agendamento_followup_ativo():
                        with session_factory() as db:
                            quantidade_novos = processar_leads_apos_cinco_minutos(
                                db,
                                empresa_id=empresa_id,
                            )
                            logger.info(
                                "Follow-up: %s novos agendamentos; empresa=%s",
                                quantidade_novos,
                                empresa_id,
                            )

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

                if (
                    not modo_simulacao
                    and os.getenv("FOLLOWUP_ENVIO_REAL_ATIVO") != "1"
                ):
                    logger.info(
                        "Envio real desativado; agendamentos preservados."
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


    executar_agendador(
        empresa_ids=ids,
        modo_simulacao=False,
    )
