"""Preparacao do primeiro agendamento de follow-up."""

from datetime import datetime

from sqlalchemy import or_

from app.services.followup_horarios import calcular_primeiro_followup
from app.models.models import FollowupConfiguracao, FollowupModeloMensagem


def preparar_primeiro_agendamento(
    *,
    empresa_id: int,
    lead_id: int,
    entrada_lead_em: datetime,
    configuracao,
    modelo,
) -> dict:
    """Prepara os dados sem gravar no banco."""

    if empresa_id <= 0 or lead_id <= 0:
        raise ValueError("Empresa e lead devem possuir IDs validos.")

    if (
        entrada_lead_em.tzinfo is None
        or entrada_lead_em.utcoffset() is None
    ):
        raise ValueError("A entrada da lead precisa conter fuso horario.")

    agendado_para = calcular_primeiro_followup(
        entrada_lead_em,
        intervalo_minutos=modelo.intervalo_minutos,
        fuso_horario=configuracao.fuso_horario,
        segunda_sexta_inicio=configuracao.segunda_sexta_inicio,
        segunda_sexta_fim=configuracao.segunda_sexta_fim,
        sabado_ativo=configuracao.sabado_ativo,
        sabado_inicio=configuracao.sabado_inicio,
        sabado_fim=configuracao.sabado_fim,
        domingo_ativo=configuracao.domingo_ativo,
    )

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
            or_(
                FollowupAgendamento.lead_id == lead_id,
                FollowupAgendamento.conversa_id == lead.conversa_id,
            ),
            FollowupAgendamento.numero_tentativa == 1,
        )
        .first()
    )

    if existente is not None:
        if existente.lead_id != lead_id:
            return None, "primeiro_followup_ja_agendado_na_conversa"
        return existente, "agendamento_ja_existe"

    configuracao = (
        db.query(FollowupConfiguracao)
        .filter(FollowupConfiguracao.empresa_id == empresa_id)
        .first()
    )

    if configuracao is None or not configuracao.ativo:
        return None, "followup_empresa_desativado"

    if configuracao.quantidade_tentativas < 1:
        return None, "quantidade_tentativas_invalida"

    modelo = (
        db.query(FollowupModeloMensagem)
        .filter(
            FollowupModeloMensagem.empresa_id == empresa_id,
            FollowupModeloMensagem.numero_tentativa == 1,
        )
        .first()
    )

    if modelo is None or not modelo.ativo:
        return None, "primeira_tentativa_desabilitada"

    dados = preparar_primeiro_agendamento(
        empresa_id=empresa_id,
        lead_id=lead_id,
        entrada_lead_em=entrada_lead_em,
        configuracao=configuracao,
        modelo=modelo,
    )

    agendamento = FollowupAgendamento(
        **dados,
        conversa_id=lead.conversa_id,
    )

    db.add(agendamento)

    return agendamento, "agendamento_preparado"


def criar_proximo_agendamento(
    db,
    *,
    agendamento_anterior,
    enviado_em: datetime,
):
    """
    Cria a proxima tentativa na transacao atual, sem commit.

    Deve ser chamada apenas apos confirmacao do envio anterior,
    com a conversa bloqueada pelo chamador.
    """
    from app.models.models import FollowupAgendamento
    from app.services.followup_service import (
        agendamento_followup_ativo,
        verificar_elegibilidade_primeiro_followup,
    )

    if not agendamento_followup_ativo():
        return None, "agendamento_desativado"

    if agendamento_anterior.status != "enviado":
        return None, "tentativa_anterior_nao_enviada"

    if enviado_em.tzinfo is None or enviado_em.utcoffset() is None:
        raise ValueError("Data de envio precisa conter fuso horario.")

    empresa_id = agendamento_anterior.empresa_id
    lead_id = agendamento_anterior.lead_id
    proxima_tentativa = agendamento_anterior.numero_tentativa + 1

    configuracao = (
        db.query(FollowupConfiguracao)
        .filter(FollowupConfiguracao.empresa_id == empresa_id)
        .first()
    )

    if configuracao is None or not configuracao.ativo:
        return None, "followup_empresa_desativado"

    if proxima_tentativa > configuracao.quantidade_tentativas:
        return None, "limite_tentativas_atingido"

    elegivel, motivo = verificar_elegibilidade_primeiro_followup(
        db,
        empresa_id=empresa_id,
        lead_id=lead_id,
    )

    if not elegivel:
        return None, motivo

    modelo = (
        db.query(FollowupModeloMensagem)
        .filter(
            FollowupModeloMensagem.empresa_id == empresa_id,
            FollowupModeloMensagem.numero_tentativa == proxima_tentativa,
            FollowupModeloMensagem.ativo.is_(True),
        )
        .first()
    )

    if modelo is None:
        return None, "modelo_proxima_tentativa_desativado"

    existente = (
        db.query(FollowupAgendamento)
        .filter(
            FollowupAgendamento.empresa_id == empresa_id,
            FollowupAgendamento.lead_id == lead_id,
            FollowupAgendamento.numero_tentativa == proxima_tentativa,
        )
        .first()
    )

    if existente is not None:
        return existente, "agendamento_ja_existe"

    agendado_para = calcular_primeiro_followup(
        enviado_em,
        intervalo_minutos=modelo.intervalo_minutos,
        fuso_horario=configuracao.fuso_horario,
        segunda_sexta_inicio=configuracao.segunda_sexta_inicio,
        segunda_sexta_fim=configuracao.segunda_sexta_fim,
        sabado_ativo=configuracao.sabado_ativo,
        sabado_inicio=configuracao.sabado_inicio,
        sabado_fim=configuracao.sabado_fim,
        domingo_ativo=configuracao.domingo_ativo,
    )

    novo_agendamento = FollowupAgendamento(
        empresa_id=empresa_id,
        lead_id=lead_id,
        conversa_id=agendamento_anterior.conversa_id,
        numero_tentativa=proxima_tentativa,
        entrada_lead_em=agendamento_anterior.entrada_lead_em,
        agendado_para=agendado_para,
        status="pendente",
    )

    db.add(novo_agendamento)
    db.flush()

    return novo_agendamento, "proximo_agendamento_criado"
