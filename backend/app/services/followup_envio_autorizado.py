from collections.abc import Callable

from sqlalchemy.orm import Session

from app.models.models import Especialista
from app.services.followup_autorizacao_vendedor import (
    autorizar_vendedor_conversa,
)
from app.services.followup_envio_controlado import (
    executar_envio_controlado,
)


def executar_envio_autorizado(
    db: Session,
    *,
    usuario_id: int,
    empresa_id: int,
    conversa_id: int,
    mensagem_id: int,
    conexao_canal_id: int,
    transportador: Callable,
) -> tuple[bool, str]:
    """Valida o vendedor antes de executar envio previamente assumido."""

    autorizado, motivo = autorizar_vendedor_conversa(
        db,
        usuario_id=usuario_id,
        empresa_id=empresa_id,
        conversa_id=conversa_id,
        conexao_canal_id=conexao_canal_id,
    )

    if not autorizado:
        db.rollback()
        return False, motivo

    especialista = (
        db.query(Especialista)
        .filter(
            Especialista.empresa_id == empresa_id,
            Especialista.usuario_id == usuario_id,
        )
        .first()
    )

    if especialista is None:
        db.rollback()
        return False, "especialista_nao_vinculado"

    return executar_envio_controlado(
        db,
        empresa_id=empresa_id,
        conversa_id=conversa_id,
        mensagem_id=mensagem_id,
        conexao_canal_id=conexao_canal_id,
        especialista_id=especialista.id,
        transportador=transportador,
    )
