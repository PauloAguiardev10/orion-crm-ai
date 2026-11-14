from sqlalchemy.orm import Session
from app.models.models import Conversa, ConexaoCanal


def vincular_conversa_conexao_waha(
    db: Session,
    empresa_id: int,
    conversa_id: int,
    conexao_canal_id: int,
) -> tuple[bool, str]:

    conexao = (
        db.query(ConexaoCanal)
        .filter(
            ConexaoCanal.id == conexao_canal_id,
            ConexaoCanal.empresa_id == empresa_id,
            ConexaoCanal.canal == "whatsapp",
            ConexaoCanal.provedor == "waha",
            ConexaoCanal.ativo.is_(True),
        )
        .first()
    )

    if conexao is None:
        return False, "conexao_invalida"

    conversa = (
        db.query(Conversa)
        .filter(
            Conversa.id == conversa_id,
            Conversa.empresa_id == empresa_id,
            Conversa.canal == "whatsapp",
        )
        .with_for_update()
        .first()
    )

    if conversa is None:
        return False, "conversa_nao_encontrada"

    if conversa.conexao_canal_id is not None:
        if conversa.conexao_canal_id != conexao_canal_id:
            return False, "conversa_vinculada_outra_conexao"

        return True, "vinculo_existente"

    conversa.conexao_canal_id = conexao_canal_id

    return True, "conversa_vinculada"
