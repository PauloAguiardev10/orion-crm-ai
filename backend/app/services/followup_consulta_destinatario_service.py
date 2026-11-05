"""Consulta segura do destinatario de follow-up."""

from sqlalchemy.orm import Session

from app.models.models import (
    FollowupAgendamento,
    Lead,
    Conversa,
)
from app.services.followup_destinatario_service import (
    validar_destinatario_followup,
)


def consultar_destinatario_followup(
    db: Session,
    *,
    empresa_id: int,
    agendamento_id: int,
) -> tuple[str | None, str]:
    """Consulta e valida o destinatario sem modificar registros."""

    if (
        type(empresa_id) is not int
        or empresa_id < 1
        or type(agendamento_id) is not int
        or agendamento_id < 1
    ):
        return None, "identificadores_invalidos"

    agendamento = (
        db.query(FollowupAgendamento)
        .filter(
            FollowupAgendamento.id == agendamento_id,
            FollowupAgendamento.empresa_id == empresa_id,
        )
        .first()
    )

    if agendamento is None:
        return None, "agendamento_nao_encontrado"

    lead = (
        db.query(Lead)
        .filter(
            Lead.id == agendamento.lead_id,
            Lead.empresa_id == empresa_id,
        )
        .first()
    )

    if lead is None:
        return None, "lead_nao_encontrada"

    conversa = (
        db.query(Conversa)
        .filter(
            Conversa.id == agendamento.conversa_id,
            Conversa.empresa_id == empresa_id,
        )
        .first()
    )

    if conversa is None:
        return None, "conversa_nao_encontrada"

    return validar_destinatario_followup(
        empresa_id=empresa_id,
        empresa_agendamento_id=agendamento.empresa_id,
        empresa_lead_id=lead.empresa_id,
        empresa_conversa_id=conversa.empresa_id,
        conversa_id_agendamento=agendamento.conversa_id,
        conversa_id_lead=lead.conversa_id,
        conversa_id=conversa.id,
        canal=conversa.canal,
        chat_id=conversa.identificador,
    )
