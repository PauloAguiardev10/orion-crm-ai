from sqlalchemy.orm import Session

from app.services.followup_reserva_envio_humano import (
    reservar_envio_humano,
)


def confirmar_reserva_envio_humano(
    db: Session,
    *,
    usuario_id: int,
    empresa_id: int,
    conversa_id: int,
    conexao_canal_id: int,
    texto: str,
    chave_solicitacao: str,
) -> tuple[int | None, str]:
    """
    Confirma uma reserva no banco antes do envio ao WAHA.

    Nao realiza chamadas externas.
    """

    try:
        mensagem_id, resultado = reservar_envio_humano(
            db,
            usuario_id=usuario_id,
            empresa_id=empresa_id,
            conversa_id=conversa_id,
            conexao_canal_id=conexao_canal_id,
            texto=texto,
            chave_solicitacao=chave_solicitacao,
        )

        if resultado != "envio_reservado":
            db.rollback()
            return mensagem_id, resultado

        db.commit()

        return mensagem_id, "reserva_confirmada"

    except Exception:
        db.rollback()
        raise
