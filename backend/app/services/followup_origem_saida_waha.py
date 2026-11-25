from sqlalchemy.orm import Session
from app.models.models import Mensagem


def proteger_followup_de_saida_manual(
    db: Session, *, conexao, destinatario: str, mensagem_id: str,
) -> bool:
    """Persiste a evidência de contato e cancela tentativas antes do envio."""
    from app.models.models import Conversa, Lead
    from app.services.followup_processamento_service import (
        cancelar_followups_pendentes_por_resposta,
    )
    from app.services.followup_service import REMETENTE_SAIDA_APLICATIVO
    from app.services.mensagem_service import registrar_mensagem

    conversas = (
        db.query(Conversa)
        .filter(
            Conversa.empresa_id == conexao.empresa_id,
            Conversa.conexao_canal_id == conexao.id,
            Conversa.canal == "whatsapp",
            Conversa.identificador == destinatario,
        )
        .with_for_update()
        .limit(2)
        .all()
    )
    if len(conversas) != 1:
        return False

    conversa = conversas[0]
    lead_ativo = (
        db.query(Lead.id)
        .filter(
            Lead.empresa_id == conexao.empresa_id,
            Lead.conversa_id == conversa.id,
            Lead.status.in_(("Em atendimento", "Aguardando resposta")),
        )
        .first()
    )
    if lead_ativo is None:
        return False

    registro, criado = registrar_mensagem(
        db, empresa_id=conexao.empresa_id, conversa_id=conversa.id,
        cliente_id=conversa.cliente_id, remetente=REMETENTE_SAIDA_APLICATIVO,
        texto="", from_me=True, mensagem_id_externo=mensagem_id,
    )
    if not criado and registro.remetente != REMETENTE_SAIDA_APLICATIVO:
        return False
    cancelar_followups_pendentes_por_resposta(
        db, empresa_id=conexao.empresa_id, conversa_id=conversa.id,
    )
    return True


def verificar_saida_automatica_registrada(
    db: Session,
    empresa_id: int,
    sessao_waha: str,
    mensagem_id_waha: str | None,
) -> tuple[bool, str]:

    if not mensagem_id_waha:
        return False, "id_waha_ausente"

    if not sessao_waha or not sessao_waha.strip():
        return False, "sessao_invalida"

    mensagem = (
        db.query(Mensagem)
        .filter(
            Mensagem.empresa_id == empresa_id,
            Mensagem.sessao_waha == sessao_waha.strip(),
            Mensagem.mensagem_id_waha == mensagem_id_waha,
            Mensagem.from_me.is_(True),
        )
        .first()
    )

    if mensagem is None:
        return False, "origem_ainda_nao_comprovada"

    return True, "saida_automatica_registrada"
