from sqlalchemy.orm import Session

from app.services.followup_resultado_envio_humano import (
    registrar_resultado_envio_humano,
)


def confirmar_resultado_envio_humano(
    db: Session,
    *,
    empresa_id: int,
    conversa_id: int,
    mensagem_id: int,
    conexao_canal_id: int,
    especialista_id: int,
    status_envio: str,
    mensagem_id_waha: str | None = None,
    sessao_waha: str | None = None,
) -> tuple[bool, str]:
    """Confirma o resultado em transacao propria."""

    try:
        registrado = registrar_resultado_envio_humano(
            db,
            empresa_id=empresa_id,
            conversa_id=conversa_id,
            mensagem_id=mensagem_id,
            conexao_canal_id=conexao_canal_id,
            especialista_id=especialista_id,
            status_envio=status_envio,
            mensagem_id_waha=mensagem_id_waha,
            sessao_waha=sessao_waha,
        )

        if not registrado:
            db.rollback()
            return False, "resultado_ja_registrado_ou_invalido"

        db.commit()
        return True, "resultado_confirmado"

    except Exception:
        db.rollback()
        raise
