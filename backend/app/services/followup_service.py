"""Regras de elegibilidade do Follow-up Automatico de primeiro contato."""

from sqlalchemy.orm import Session

from app.models.models import Conversa, Lead, Mensagem
from app.services.estados_mensagem import STATUS_ENVIO_CONFIRMADO_HTTP


ORIGENS_ANUNCIO = {
    "anuncio_instagram",
    "anuncio_facebook",
    "anuncio",
}


def verificar_elegibilidade_primeiro_followup(
    db: Session,
    *,
    empresa_id: int,
    lead_id: int,
) -> tuple[bool, str]:
    """Valida o primeiro contato sem modificar o banco."""

    lead = (
        db.query(Lead)
        .filter(Lead.id == lead_id, Lead.empresa_id == empresa_id)
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

    # Somente a proveniencia tecnica pode indicar anuncio.
    # A origem comercial informada pelo cliente nao e suficiente.
    if conversa.anuncio_referral_confirmado is not True:
        return False, "anuncio_sem_comprovacao_tecnica"

    if not conversa.anuncio_referral_id:
        return False, "anuncio_sem_identificador"

    if lead.resumo_vendedor:
        return False, "lead_ja_qualificada"

    if conversa.etapa in {"aguardando_humano", "encaminhar", "finalizado"}:
        return False, "conversa_ja_encaminhada"

    if conversa.status_atendimento in {
        "aguardando_humano",
        "aguardando_atendimento_humano",
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

    recebidas = [m for m in mensagens if m.from_me is False]
    enviadas = [m for m in mensagens if m.from_me is True]

    if not recebidas:
        return False, "cliente_nao_iniciou_contato"

    if not enviadas:
        return False, "empresa_ainda_nao_respondeu"

    primeira_recebida = recebidas[0]
    primeira_enviada = enviadas[0]

    if mensagens[0].id != primeira_recebida.id:
        return False, "empresa_iniciou_conversa"

    if primeira_enviada.status_envio != STATUS_ENVIO_CONFIRMADO_HTTP:
        return False, "primeira_resposta_sem_confirmacao_http"

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

    # A elegibilidade exige proveniencia tecnica previamente validada.
    # O disparo real permanece controlado por configuracao separada.
    return True, "elegivel_primeiro_followup"
