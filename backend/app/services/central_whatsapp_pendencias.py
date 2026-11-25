from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.models import Mensagem


def listar_pendencias_envio_central(
    db: Session,
    *,
    empresa_id: int,
    conversa_id: int,
    especialista_id: int,
) -> list[dict]:
    """Consulta mensagens humanas sem confirmacao de envio."""

    if any(
        not isinstance(valor, int)
        or isinstance(valor, bool)
        or valor <= 0
        for valor in (empresa_id, conversa_id, especialista_id)
    ):
        return []

    mensagens = (
        db.query(Mensagem)
        .filter(
            Mensagem.empresa_id == empresa_id,
            Mensagem.conversa_id == conversa_id,
            Mensagem.remetente == "humano",
            Mensagem.from_me.is_(True),
            or_(
                Mensagem.status_envio.is_(None),
                Mensagem.status_envio == "timeout_envio_inconclusivo",
            ),
        )
        .order_by(Mensagem.id.asc())
        .all()
    )

    return [
        {
            "mensagem_id": mensagem.id,
            "status_processamento": mensagem.status_processamento,
            "status_envio": mensagem.status_envio,
            "criado_em": (
                mensagem.criado_em.isoformat()
                if mensagem.criado_em is not None
                else None
            ),
        }
        for mensagem in mensagens
    ]
