from sqlalchemy.orm import Session

from app.services.followup_conexoes_waha import localizar_conexao_waha


def validar_conexao_entrada_waha(
    db: Session,
    sessao: str,
    empresa_id: int,
) -> tuple[int | None, str]:

    conexao, motivo = localizar_conexao_waha(db, sessao)

    if conexao is None:
        return None, motivo

    if conexao.empresa_id != empresa_id:
        return None, "empresa_divergente"

    return conexao.id, "conexao_validada"
