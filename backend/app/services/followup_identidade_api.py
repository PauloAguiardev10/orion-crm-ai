from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.autenticacao_api import validar_token_api


def identificar_usuario_api(
    db: Session,
    *,
    token: str,
) -> tuple[dict | None, str]:
    """Valida token e consulta usuario e empresa ativos."""

    identidade = validar_token_api(token)

    if identidade is None:
        return None, "token_invalido_ou_expirado"

    usuario = db.execute(
        text("""
            SELECT
                u.id AS usuario_id,
                u.empresa_id,
                u.nivel
            FROM usuarios AS u
            INNER JOIN empresas AS e
                ON e.id = u.empresa_id
            WHERE u.id = :usuario_id
              AND u.empresa_id = :empresa_id
              AND u.status = 'ativo'
              AND e.status = 'ativa'
            LIMIT 1
        """),
        identidade,
    ).mappings().first()

    if usuario is None:
        return None, "usuario_ou_empresa_inativo"

    return {
        "usuario_id": int(usuario["usuario_id"]),
        "empresa_id": int(usuario["empresa_id"]),
        "nivel": usuario["nivel"],
    }, "usuario_autenticado"
