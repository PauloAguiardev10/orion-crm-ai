from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.models import Especialista, ConexaoCanal, Conversa


def autorizar_vendedor_conversa(
    db: Session,
    *,
    usuario_id: int,
    empresa_id: int,
    conversa_id: int,
    conexao_canal_id: int,
) -> tuple[bool, str]:

    if any(
        not isinstance(valor, int) or isinstance(valor, bool) or valor <= 0
        for valor in (usuario_id, empresa_id, conversa_id, conexao_canal_id)
    ):
        return False, "identificadores_invalidos"

    usuario = db.execute(
        text("""
            SELECT id
            FROM usuarios
            WHERE id = :usuario_id
              AND empresa_id = :empresa_id
              AND status = 'ativo'
            LIMIT 1
        """),
        {
            "usuario_id": usuario_id,
            "empresa_id": empresa_id,
        },
    ).first()

    if usuario is None:
        return False, "usuario_nao_autorizado"

    especialista = (
        db.query(Especialista)
        .filter(
            Especialista.usuario_id == usuario_id,
            Especialista.empresa_id == empresa_id,
        )
        .first()
    )

    if especialista is None:
        return False, "especialista_nao_vinculado"

    conexao = (
        db.query(ConexaoCanal)
        .filter(
            ConexaoCanal.id == conexao_canal_id,
            ConexaoCanal.empresa_id == empresa_id,
            ConexaoCanal.especialista_id == especialista.id,
            ConexaoCanal.canal == "whatsapp",
            ConexaoCanal.provedor == "waha",
            ConexaoCanal.ativo.is_(True),
        )
        .first()
    )

    if conexao is None:
        return False, "conexao_nao_autorizada"

    conversa = (
        db.query(Conversa)
        .filter(
            Conversa.id == conversa_id,
            Conversa.empresa_id == empresa_id,
            Conversa.conexao_canal_id == conexao_canal_id,
            Conversa.canal == "whatsapp",
        )
        .first()
    )

    if conversa is None:
        return False, "conversa_nao_autorizada"

    return True, "vendedor_autorizado"
