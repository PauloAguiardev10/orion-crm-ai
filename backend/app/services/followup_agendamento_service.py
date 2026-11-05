"""Preparacao do primeiro agendamento de follow-up."""

from datetime import datetime

from app.services.followup_horarios import calcular_primeiro_followup


def preparar_primeiro_agendamento(
    *,
    empresa_id: int,
    lead_id: int,
    entrada_lead_em: datetime,
) -> dict:
    """Prepara os dados sem gravar no banco."""

    if empresa_id <= 0 or lead_id <= 0:
        raise ValueError("Empresa e lead devem possuir IDs validos.")

    if (
        entrada_lead_em.tzinfo is None
        or entrada_lead_em.utcoffset() is None
    ):
        raise ValueError("A entrada da lead precisa conter fuso horario.")

    agendado_para = calcular_primeiro_followup(entrada_lead_em)

    return {
        "empresa_id": empresa_id,
        "lead_id": lead_id,
        "numero_tentativa": 1,
        "entrada_lead_em": entrada_lead_em,
        "agendado_para": agendado_para,
        "status": "pendente",
    }

def criar_primeiro_agendamento(
    db,
    *,
    empresa_id: int,
    lead_id: int,
    entrada_lead_em: datetime,
):
    """
    Prepara e adiciona o primeiro agendamento na transacao atual.

    Nao executa commit. O chamador controla a transacao.
    """

    from app.models.models import Conversa, FollowupAgendamento, Lead
    from app.services.followup_service import (
        verificar_elegibilidade_primeiro_followup,
    )

    # Bloqueia a conversa antes da verificacao de elegibilidade.
    # O chamador mantem o bloqueio ate commit ou rollback.
    lead_vinculo = (
        db.query(Lead.conversa_id, Lead.cliente_id)
        .filter(
            Lead.id == lead_id,
            Lead.empresa_id == empresa_id,
        )
        .first()
    )

    if lead_vinculo is None:
        return None, "lead_nao_encontrada"

    if lead_vinculo.conversa_id is None:
        return None, "sem_conversa_vinculada"

    conversa_bloqueada = (
        db.query(Conversa)
        .filter(
            Conversa.id == lead_vinculo.conversa_id,
            Conversa.empresa_id == empresa_id,
            Conversa.cliente_id == lead_vinculo.cliente_id,
        )
        .with_for_update()
        .one_or_none()
    )

    if conversa_bloqueada is None:
        return None, "vinculo_conversa_invalido"

    elegivel, motivo = verificar_elegibilidade_primeiro_followup(
        db,
        empresa_id=empresa_id,
        lead_id=lead_id,
    )

    if not elegivel:
        return None, motivo

    lead = (
        db.query(Lead)
        .filter(
            Lead.id == lead_id,
            Lead.empresa_id == empresa_id,
        )
        .first()
    )

    if lead is None or lead.conversa_id is None:
        return None, "lead_sem_conversa_valida"

    if lead.entrada_followup_em is None:
        return None, "lead_sem_data_entrada_followup"

    entrada_lead_em = lead.entrada_followup_em

    existente = (
        db.query(FollowupAgendamento)
        .filter(
            FollowupAgendamento.empresa_id == empresa_id,
            FollowupAgendamento.lead_id == lead_id,
            FollowupAgendamento.numero_tentativa == 1,
        )
        .first()
    )

    if existente is not None:
        return existente, "agendamento_ja_existe"

    dados = preparar_primeiro_agendamento(
        empresa_id=empresa_id,
        lead_id=lead_id,
        entrada_lead_em=entrada_lead_em,
    )

    agendamento = FollowupAgendamento(
        **dados,
        conversa_id=lead.conversa_id,
    )

    db.add(agendamento)

    return agendamento, "agendamento_preparado"
