from sqlalchemy.orm import Session

from app.models.models import Mensagem


def consultar_status_envio_central(
    db: Session,
    *,
    empresa_id: int,
    conversa_id: int,
    mensagem_id: int,
    especialista_id: int,
) -> dict | None:
    """Consulta o status de uma mensagem humana sem alterar o banco."""

    if any(
        not isinstance(valor, int)
        or isinstance(valor, bool)
        or valor <= 0
        for valor in (
            empresa_id,
            conversa_id,
            mensagem_id,
            especialista_id,
        )
    ):
        return None

    mensagem = (
        db.query(Mensagem)
        .filter(
            Mensagem.id == mensagem_id,
            Mensagem.empresa_id == empresa_id,
            Mensagem.conversa_id == conversa_id,
            Mensagem.especialista_id == especialista_id,
            Mensagem.remetente == "humano",
            Mensagem.from_me.is_(True),
        )
        .first()
    )

    if mensagem is None:
        return None

    return {
        "mensagem_id": mensagem.id,
        "status_processamento": mensagem.status_processamento,
        "status_envio": mensagem.status_envio,
        "mensagem_id_waha": mensagem.mensagem_id_waha,
    }
