"""Regras de elegibilidade do Follow-up Automatico."""

from sqlalchemy.orm import Session

from app.models.models import Conversa, Lead, Mensagem
from app.services.estados_mensagem import STATUS_ENVIO_CONFIRMADO_HTTP


def verificar_elegibilidade_primeiro_followup(
    db: Session,
    *,
    empresa_id: int,
    lead_id: int,
) -> tuple[bool, str]:
    """Consulta o historico sem modificar o banco."""

    lead = (
        db.query(Lead)
        .filter(
            Lead.id == lead_id,
            Lead.empresa_id == empresa_id,
        )
        .first()
    )

    if lead is None:
        return False, "lead_nao_encontrada"

    if lead.status != "Aguardando resposta":
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

    for mensagem in mensagens:
        if mensagem.criado_em is None or mensagem.id is None:
            return False, "historico_sem_data_confiavel"

        if mensagem.from_me is None:
            return False, "origem_mensagem_desconhecida"

    ultima_mensagem = mensagens[-1]

    if ultima_mensagem.from_me is False:
        if not any(mensagem.from_me is True for mensagem in mensagens):
            return False, "empresa_ainda_nao_respondeu"
        return False, "cliente_respondeu"

    if ultima_mensagem.status_envio != STATUS_ENVIO_CONFIRMADO_HTTP:
        return False, "ultima_resposta_sem_confirmacao_http"

    return True, "elegivel"
