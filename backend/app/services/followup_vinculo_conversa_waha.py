from sqlalchemy.orm import Session
from app.models.models import Conversa, ConexaoCanal
from app.services.waha_identificadores import aliases_chat


def localizar_conversa_entrada_waha(db, *, empresa_id, conexao_id, chat_id):
    conversas = db.query(Conversa).filter_by(
        empresa_id=empresa_id, canal="whatsapp",
    ).filter(Conversa.identificador.in_(aliases_chat(chat_id))).order_by(
        (Conversa.identificador == chat_id).desc(), Conversa.id.desc(),
    )
    vinculada = conversas.filter_by(conexao_canal_id=conexao_id).first()
    if vinculada is not None:
        return vinculada
    unicas = db.query(ConexaoCanal.id).filter_by(
        empresa_id=empresa_id, canal="whatsapp", provedor="waha", ativo=True,
    ).limit(2).all()
    if len(unicas) != 1 or unicas[0].id != conexao_id:
        return None
    legada = conversas.filter_by(conexao_canal_id=None).with_for_update().first()
    if legada is not None:
        legada.conexao_canal_id = conexao_id
    return legada


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
