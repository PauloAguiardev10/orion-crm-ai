"""Processamento seguro de follow-ups pendentes, sem envio."""

from datetime import datetime, timezone

from app.models.models import Conversa, FollowupAgendamento
from app.services.followup_service import (
    verificar_elegibilidade_primeiro_followup,
)


def processar_agendamento_pendente(
    db,
    *,
    agendamento_id: int,
    empresa_id: int,
    agora: datetime | None = None,
) -> tuple[str, str]:
    """
    Avalia um agendamento sem enviar mensagens.

    A transacao e controlada pelo chamador.
    """

    if agora is None:
        agora = datetime.now(timezone.utc)

    if agora.tzinfo is None or agora.utcoffset() is None:
        raise ValueError("A data atual precisa ter fuso horario.")

    agendamento = (
        db.query(FollowupAgendamento)
        .filter(
            FollowupAgendamento.id == agendamento_id,
            FollowupAgendamento.empresa_id == empresa_id,
        )
        .with_for_update()
        .first()
    )

    if agendamento is None:
        return "ignorado", "agendamento_nao_encontrado"

    if agendamento.status != "pendente":
        return "ignorado", "agendamento_nao_pendente"

    if agendamento.agendado_para > agora:
        return "ignorado", "agendamento_ainda_nao_venceu"

    elegivel, motivo = verificar_elegibilidade_primeiro_followup(
        db,
        empresa_id=empresa_id,
        lead_id=agendamento.lead_id,
    )

    if not elegivel:
        agendamento.status = "cancelado"
        agendamento.cancelado_em = agora
        agendamento.atualizado_em = agora
        return "cancelado", motivo

    return "elegivel", "aguardando_etapa_de_envio"


def cancelar_followups_pendentes_por_resposta(
    db,
    *,
    empresa_id: int,
    conversa_id: int,
    agora: datetime | None = None,
) -> int:
    """
    Cancela follow-ups pendentes quando o cliente responde.

    Nao altera Lead, Conversa ou Mensagem.
    Nao executa commit nem envia mensagens.
    """

    if empresa_id <= 0 or conversa_id <= 0:
        raise ValueError("Empresa e conversa devem possuir IDs validos.")

    if agora is None:
        agora = datetime.now(timezone.utc)

    if agora.tzinfo is None or agora.utcoffset() is None:
        raise ValueError("A data precisa conter fuso horario.")

    # Mantem a mesma ordem de bloqueios da autorizacao:
    # primeiro Conversa, depois FollowupAgendamento.
    conversa = (
        db.query(Conversa)
        .filter(
            Conversa.id == conversa_id,
            Conversa.empresa_id == empresa_id,
        )
        .with_for_update()
        .first()
    )

    if conversa is None:
        return 0

    agendamentos = (
        db.query(FollowupAgendamento)
        .filter(
            FollowupAgendamento.empresa_id == empresa_id,
            FollowupAgendamento.conversa_id == conversa_id,
            FollowupAgendamento.status.in_(("pendente", "processando")),
        )
        .with_for_update()
        .all()
    )

    cancelados = 0

    for agendamento in agendamentos:
        if (
            agendamento.status == "processando"
            and agendamento.envio_iniciado_em is not None
        ):
            continue

        agendamento.status = "cancelado"
        agendamento.cancelado_em = agora
        agendamento.atualizado_em = agora
        cancelados += 1

    return cancelados


def reservar_agendamento_pendente(
    db,
    *,
    empresa_id: int,
    agora: datetime | None = None,
    duracao_reserva_segundos: int = 120,
) -> tuple[int | None, str]:
    """
    Reserva um agendamento vencido de uma empresa.

    Ordem dos bloqueios: Conversa -> FollowupAgendamento.
    Nao envia mensagens e nao executa commit.
    """
    from datetime import timedelta
    from uuid import uuid4

    if empresa_id <= 0:
        raise ValueError("Empresa deve possuir ID valido.")

    if duracao_reserva_segundos <= 0:
        raise ValueError("Duracao da reserva deve ser positiva.")

    if agora is None:
        agora = datetime.now(timezone.utc)

    if agora.tzinfo is None or agora.utcoffset() is None:
        raise ValueError("A data precisa conter fuso horario.")

    candidatos = (
        db.query(
            FollowupAgendamento.id,
            FollowupAgendamento.conversa_id,
        )
        .filter(
            FollowupAgendamento.empresa_id == empresa_id,
            FollowupAgendamento.status == "pendente",
            FollowupAgendamento.agendado_para <= agora,
        )
        .order_by(
            FollowupAgendamento.agendado_para.asc(),
            FollowupAgendamento.id.asc(),
        )
        .all()
    )

    for candidato in candidatos:
        if candidato.conversa_id is None:
            continue

        conversa = (
            db.query(Conversa)
            .filter(
                Conversa.id == candidato.conversa_id,
                Conversa.empresa_id == empresa_id,
            )
            .with_for_update(skip_locked=True)
            .first()
        )

        if conversa is None:
            continue

        agendamento = (
            db.query(FollowupAgendamento)
            .filter(
                FollowupAgendamento.id == candidato.id,
                FollowupAgendamento.empresa_id == empresa_id,
                FollowupAgendamento.conversa_id == conversa.id,
                FollowupAgendamento.status == "pendente",
                FollowupAgendamento.agendado_para <= agora,
            )
            .with_for_update(skip_locked=True)
            .first()
        )

        if agendamento is None:
            continue

        elegivel, motivo = verificar_elegibilidade_primeiro_followup(
            db,
            empresa_id=empresa_id,
            lead_id=agendamento.lead_id,
        )

        if not elegivel:
            agendamento.status = "cancelado"
            agendamento.cancelado_em = agora
            agendamento.atualizado_em = agora
            db.flush()
            db.info["followup_cancelamento_atual"] = (
                empresa_id, agendamento.id
            )
            return None, motivo

        agendamento.status = "processando"
        agendamento.envio_iniciado_em = None
        agendamento.reservado_em = agora
        agendamento.reserva_token = str(uuid4())
        agendamento.reserva_expira_em = (
            agora + timedelta(seconds=duracao_reserva_segundos)
        )
        agendamento.atualizado_em = agora

        db.flush()
        return agendamento.id, "reservado"

    return None, "nenhum_agendamento_pendente"


def finalizar_agendamento_reservado(
    db,
    *,
    empresa_id: int,
    agendamento_id: int,
    reserva_token: str,
    status_envio: str,
    mensagem_id_externo: str | None = None,
    agora: datetime | None = None,
) -> tuple[bool, str]:
    """
    Finaliza uma reserva pertencente a empresa e ao token informado.

    Nao envia mensagens e nao executa commit.
    """
    if empresa_id <= 0 or agendamento_id <= 0:
        raise ValueError("IDs devem ser positivos.")

    if not reserva_token or not reserva_token.strip():
        raise ValueError("Token de reserva obrigatorio.")

    resultados = {
        "aceito_waha": "enviado",
        "falha_envio": "falha",
        "timeout_envio_inconclusivo": "inconclusivo",
    }

    if status_envio not in resultados:
        raise ValueError("Resultado de envio desconhecido.")

    if agora is None:
        agora = datetime.now(timezone.utc)

    if agora.tzinfo is None or agora.utcoffset() is None:
        raise ValueError("Data precisa conter fuso horario.")

    agendamento = (
        db.query(FollowupAgendamento)
        .filter(
            FollowupAgendamento.id == agendamento_id,
            FollowupAgendamento.empresa_id == empresa_id,
            FollowupAgendamento.status == "processando",
            FollowupAgendamento.reserva_token == reserva_token,
        )
        .with_for_update()
        .first()
    )

    if agendamento is None:
        return False, "reserva_nao_encontrada_ou_invalidada"

    if agendamento.envio_iniciado_em is None:
        return False, "envio_nao_autorizado"

    novo_status = resultados[status_envio]

    agendamento.status = novo_status
    agendamento.atualizado_em = agora
    agendamento.tentativas_envio = (
        (agendamento.tentativas_envio or 0) + 1
    )

    if novo_status == "enviado":
        agendamento.enviado_em = agora
        agendamento.erro_envio = None
        agendamento.mensagem_id_externo = mensagem_id_externo

    elif novo_status == "falha":
        agendamento.erro_envio = "falha_envio"

    else:
        agendamento.erro_envio = "timeout_envio_inconclusivo"

    db.flush()

    return True, novo_status


def recuperar_reservas_expiradas(
    db,
    *,
    empresa_id: int,
    agora: datetime | None = None,
    limite: int = 100,
) -> int:
    """
    Marca reservas expiradas como inconclusivas.

    Nao reenvia mensagens e nao executa commit.
    O chamador deve confirmar a transacao.
    """
    if empresa_id <= 0:
        raise ValueError("Empresa deve possuir ID valido.")

    if limite <= 0:
        raise ValueError("Limite deve ser positivo.")

    if agora is None:
        agora = datetime.now(timezone.utc)

    if agora.tzinfo is None or agora.utcoffset() is None:
        raise ValueError("Data precisa conter fuso horario.")

    agendamentos = (
        db.query(FollowupAgendamento)
        .filter(
            FollowupAgendamento.empresa_id == empresa_id,
            FollowupAgendamento.status == "processando",
            FollowupAgendamento.reserva_expira_em.isnot(None),
            FollowupAgendamento.reserva_expira_em <= agora,
        )
        .order_by(
            FollowupAgendamento.reserva_expira_em.asc(),
            FollowupAgendamento.id.asc(),
        )
        .with_for_update(skip_locked=True)
        .limit(limite)
        .all()
    )

    for agendamento in agendamentos:
        if agendamento.envio_iniciado_em is None:
            agendamento.status = "pendente"
            agendamento.erro_envio = None
            agendamento.reservado_em = None
            agendamento.reserva_token = None
            agendamento.reserva_expira_em = None
        else:
            agendamento.status = "inconclusivo"
            agendamento.erro_envio = (
                "reserva_expirada_resultado_envio_desconhecido"
            )
        agendamento.atualizado_em = agora

    if agendamentos:
        db.flush()

    return len(agendamentos)


def autorizar_envio_followup_reservado(
    db,
    *,
    empresa_id: int,
    agendamento_id: int,
    reserva_token: str,
    agora: datetime | None = None,
) -> tuple[bool, str]:
    """
    Autoriza o envio de uma reserva valida.

    O chamador deve executar COMMIT antes de chamar o WAHA.
    Nao envia mensagens e nao executa COMMIT.
    """
    if empresa_id <= 0 or agendamento_id <= 0:
        raise ValueError("IDs devem ser positivos.")

    if not reserva_token or not reserva_token.strip():
        raise ValueError("Token de reserva obrigatorio.")

    if agora is None:
        agora = datetime.now(timezone.utc)

    if agora.tzinfo is None or agora.utcoffset() is None:
        raise ValueError("Data precisa conter fuso horario.")

    referencia = (
        db.query(
            FollowupAgendamento.conversa_id,
        )
        .filter(
            FollowupAgendamento.id == agendamento_id,
            FollowupAgendamento.empresa_id == empresa_id,
        )
        .first()
    )

    if referencia is None:
        return False, "agendamento_nao_encontrado"

    conversa_id = referencia.conversa_id

    if conversa_id is None:
        return False, "agendamento_sem_conversa"

    conversa = (
        db.query(Conversa)
        .filter(
            Conversa.id == conversa_id,
            Conversa.empresa_id == empresa_id,
        )
        .with_for_update()
        .first()
    )

    if conversa is None:
        return False, "conversa_nao_encontrada"

    agendamento = (
        db.query(FollowupAgendamento)
        .filter(
            FollowupAgendamento.id == agendamento_id,
            FollowupAgendamento.empresa_id == empresa_id,
            FollowupAgendamento.conversa_id == conversa_id,
        )
        .with_for_update()
        .first()
    )

    if agendamento is None:
        return False, "reserva_invalidada"

    if agendamento.status != "processando":
        return False, "reserva_nao_processando"

    if agendamento.reserva_token != reserva_token:
        return False, "token_invalido"

    if agendamento.envio_iniciado_em is not None:
        return False, "envio_ja_autorizado"

    if (
        agendamento.reserva_expira_em is None
        or agendamento.reserva_expira_em <= agora
    ):
        return False, "reserva_expirada"

    elegivel, motivo = verificar_elegibilidade_primeiro_followup(
        db,
        empresa_id=empresa_id,
        lead_id=agendamento.lead_id,
    )

    if not elegivel:
        agendamento.status = "cancelado"
        agendamento.cancelado_em = agora
        agendamento.atualizado_em = agora
        db.flush()
        db.info["followup_cancelamento_atual"] = (
            empresa_id, agendamento.id
        )
        return False, motivo

    agendamento.envio_iniciado_em = agora
    agendamento.atualizado_em = agora

    db.flush()

    return True, "envio_autorizado"
