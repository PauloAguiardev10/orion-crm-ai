from sqlalchemy.orm import Session
from app.models.models import Conversa


def localizar_conversa_saida_waha(
    db: Session,
    empresa_id: int,
    chat_id: str,
    conexao_canal_id: int,
) -> tuple[Conversa | None, str]:

    if not isinstance(chat_id, str) or not chat_id.strip():
        return None, "chat_id_invalido"

    if not isinstance(conexao_canal_id, int) or conexao_canal_id <= 0:
        return None, "conexao_invalida"

    conversas = (
        db.query(Conversa)
        .filter(
            Conversa.empresa_id == empresa_id,
            Conversa.identificador == chat_id.strip(),
        )
        .limit(2)
        .all()
    )

    if not conversas:
        return None, "conversa_nao_encontrada"

    if len(conversas) != 1:
        return None, "conversa_ambigua"

    conversa = conversas[0]

    if conversa.conexao_canal_id is None:
        return None, "conversa_sem_conexao_vinculada"

    if conversa.conexao_canal_id != conexao_canal_id:
        return None, "conexao_diferente_da_conversa"

    return conversa, "conversa_identificada"
