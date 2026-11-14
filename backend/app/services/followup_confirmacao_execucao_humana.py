from sqlalchemy.orm import Session

from app.models.models import Especialista

from app.services.followup_autorizacao_vendedor import (
    autorizar_vendedor_conversa,
)
from app.services.followup_execucao_envio_humano import (
    assumir_envio_humano,
)


def confirmar_execucao_envio_humano(
    db: Session,
    *,
    usuario_id: int,
    empresa_id: int,
    conversa_id: int,
    conexao_canal_id: int,
    mensagem_id: int,
) -> tuple[bool, str]:
    """
    Autoriza o vendedor e assume a reserva.

    Confirma a transacao antes de qualquer envio externo.
    Nao chama o WAHA.
    """

    try:
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

        assumido = assumir_envio_humano(
            db,
            empresa_id=empresa_id,
            conversa_id=conversa_id,
            mensagem_id=mensagem_id,
            conexao_canal_id=conexao_canal_id,
            especialista_id=especialista.id,
        )

        if not assumido:
            db.rollback()
            return False, "envio_ja_assumido_ou_invalido"

        db.commit()

        return True, "execucao_confirmada"

    except Exception:
        db.rollback()
        raise
