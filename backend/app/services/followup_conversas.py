"""Localizacao segura de conversas para o Follow-up Automatico."""

from sqlalchemy.orm import Session

from app.models.models import Conversa


def localizar_conversa_followup(
    db: Session,
    *,
    empresa_id: int,
    identificador: str,
) -> tuple[Conversa | None, str]:
    """Localiza uma conversa WhatsApp existente sem modificar o banco."""

    if not isinstance(empresa_id, int) or empresa_id < 1:
        return None, "empresa_invalida"

    if not isinstance(identificador, str):
        return None, "identificador_invalido"

    identificador = identificador.strip()

    if not identificador or not identificador.endswith(("@c.us", "@lid")):
        return None, "identificador_invalido"

    conversas = (
        db.query(Conversa)
        .filter(
            Conversa.empresa_id == empresa_id,
            Conversa.canal == "whatsapp",
            Conversa.identificador == identificador,
        )
        .limit(2)
        .all()
    )

    if not conversas:
        return None, "conversa_nao_encontrada"

    if len(conversas) > 1:
        return None, "conversa_ambigua"

    conversa = conversas[0]

    if conversa.cliente_id is None:
        return None, "conversa_sem_cliente"

    return conversa, "conversa_identificada"
