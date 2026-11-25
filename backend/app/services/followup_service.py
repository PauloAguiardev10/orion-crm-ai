"""Regras de elegibilidade do Follow-up Automatico de primeiro contato."""

import os
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.models import Conversa, Lead, Mensagem
from app.services.estados_mensagem import ESTADOS_ENVIO_COM_ACEITE_HTTP


REMETENTES_PRIMEIRA_RESPOSTA = ("agente", "humano")
REMETENTE_SAIDA_APLICATIVO = "humano_whatsapp"


def agendamento_followup_ativo() -> bool:
    return os.getenv("FOLLOWUP_AGENDAMENTO_ATIVO", "").strip().lower() in (
        "1", "true", "yes", "on",
    )


def consultar_primeira_resposta_confirmada(db: Session, *, empresa_id: int, conversa_id: int):
    return (
        db.query(Mensagem.id, Mensagem.criado_em)
        .filter(
            Mensagem.empresa_id == empresa_id,
            Mensagem.conversa_id == conversa_id,
            Mensagem.from_me.is_(True),
            Mensagem.remetente.in_(REMETENTES_PRIMEIRA_RESPOSTA),
            Mensagem.status_envio.in_(ESTADOS_ENVIO_COM_ACEITE_HTTP),
        )
        .order_by(Mensagem.criado_em.asc(), Mensagem.id.asc())
        .first()
    )


def registrar_entrada_followup(
    db: Session, *, empresa_id: int, conversa_id: int, mensagem_id: int,
) -> None:
    """Registra a primeira confirmação no mesmo commit do envio."""
    if not agendamento_followup_ativo():
        return

    confirmada = consultar_primeira_resposta_confirmada(
        db, empresa_id=empresa_id, conversa_id=conversa_id,
    )
    if confirmada is None or confirmada.id != mensagem_id:
        return

    lead_atual = (
        db.query(Lead.id)
        .filter(Lead.empresa_id == empresa_id, Lead.conversa_id == conversa_id)
        .order_by(Lead.id.desc())
        .limit(1)
        .scalar_subquery()
    )
    (
        db.query(Lead)
        .filter(
            Lead.id == lead_atual,
            Lead.empresa_id == empresa_id,
            Lead.conversa_id == conversa_id,
            Lead.status.in_(("Em atendimento", "Aguardando resposta")),
            Lead.entrada_followup_em.is_(None),
        )
        .update(
            {Lead.entrada_followup_em: datetime.now(timezone.utc)},
            synchronize_session=False,
        )
    )


def verificar_elegibilidade_primeiro_followup(
    db: Session,
    *,
    empresa_id: int,
    lead_id: int,
    permitir_em_atendimento: bool = False,
) -> tuple[bool, str]:
    """Valida o primeiro contato sem modificar o banco."""

    lead = (
        db.query(Lead)
        .filter(Lead.id == lead_id, Lead.empresa_id == empresa_id)
        .first()
    )

    if lead is None:
        return False, "lead_nao_encontrada"

    status_permitidos = (
        ("Aguardando resposta", "Em atendimento")
        if permitir_em_atendimento
        else ("Aguardando resposta",)
    )

    if lead.status not in status_permitidos:
        return False, "lead_nao_aguardando_resposta"

    if lead.conversa_id is None:
        return False, "sem_conversa_vinculada"

    conversa = (
        db.query(Conversa)
        .filter(
            Conversa.id == lead.conversa_id,
            Conversa.empresa_id == empresa_id,
            Conversa.cliente_id == lead.cliente_id,
        )
        .first()
    )

    if conversa is None:
        return False, "vinculo_conversa_invalido"

    if lead.resumo_vendedor:
        return False, "lead_ja_qualificada"

    if conversa.humano_assumiu is True:
        return False, "atendimento_humano_assumiu"

    if conversa.etapa in {"aguardando_humano", "encaminhar", "finalizado"}:
        return False, "conversa_ja_encaminhada"

    if conversa.status_atendimento in {
        "aguardando_humano",
        "aguardando_atendimento_humano",
        "em_atendimento_humano",
        "finalizado",
    }:
        return False, "atendimento_ja_encaminhado"

    mensagens = (
        db.query(Mensagem)
        .filter(
            Mensagem.empresa_id == empresa_id,
            Mensagem.conversa_id == lead.conversa_id,
        )
        .order_by(Mensagem.criado_em.asc(), Mensagem.id.asc())
        .all()
    )

    if not mensagens:
        return False, "historico_vazio"

    if any(
        m.criado_em is None or m.id is None or m.from_me is None
        for m in mensagens
    ):
        return False, "historico_incompleto"

    if any(m.from_me is True and m.remetente == REMETENTE_SAIDA_APLICATIVO for m in mensagens):
        return False, "contato_manual_whatsapp"

    recebidas = [m for m in mensagens if m.from_me is False]
    respostas_confirmadas = [
        m for m in mensagens
        if m.from_me is True
        and m.remetente in REMETENTES_PRIMEIRA_RESPOSTA
        and m.status_envio in ESTADOS_ENVIO_COM_ACEITE_HTTP
    ]

    if not recebidas:
        return False, "cliente_nao_iniciou_contato"

    primeira_recebida = recebidas[0]

    if mensagens[0].id != primeira_recebida.id:
        return False, "empresa_iniciou_conversa"

    if not respostas_confirmadas:
        return False, "primeira_resposta_sem_confirmacao_http"

    primeira_enviada = respostas_confirmadas[0]
    # Nenhuma mensagem do cliente pode ocorrer depois da primeira
    # resposta da empresa. Isso impede reentrada apos interacao.
    indice_primeira_enviada = next(
        i for i, m in enumerate(mensagens)
        if m.id == primeira_enviada.id
    )

    if any(
        m.from_me is False
        for m in mensagens[indice_primeira_enviada + 1:]
    ):
        return False, "cliente_ja_respondeu_primeiro_contato"

    if mensagens[-1].from_me is not True:
        return False, "ultima_mensagem_nao_e_da_empresa"

    return True, "elegivel_primeiro_followup"
