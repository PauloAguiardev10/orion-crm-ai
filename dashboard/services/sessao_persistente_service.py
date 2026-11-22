
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from database.db import conectar
from psycopg2.extras import RealDictCursor


DURACAO_SESSAO_HORAS = 12


def _hash_token(token: str) -> str:
    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


def criar_sessao(usuario_id: int) -> str:
    """
    Cria uma sessao persistente para um usuario autenticado.

    Retorna o token original para armazenamento no cookie.
    Apenas o hash e armazenado no PostgreSQL.
    """

    if not usuario_id or int(usuario_id) <= 0:
        raise ValueError("Usuario invalido.")

    token = secrets.token_urlsafe(32)
    token_hash = _hash_token(token)

    agora = datetime.now(timezone.utc)
    expira_em = agora + timedelta(
        hours=DURACAO_SESSAO_HORAS
    )

    conn = conectar()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO sessoes_usuarios (
                    usuario_id,
                    token_hash,
                    criado_em,
                    expira_em
                )
                SELECT
                    u.id,
                    %s,
                    %s,
                    %s
                FROM usuarios u
                INNER JOIN empresas e
                    ON e.id = u.empresa_id
                WHERE u.id = %s
                  AND u.status = 'ativo'
                  AND e.status = 'ativa'
                RETURNING id
                """,
                (
                    token_hash,
                    agora,
                    expira_em,
                    int(usuario_id),
                ),
            )

            if cursor.fetchone() is None:
                raise ValueError(
                    "Usuario ou empresa inativos."
                )

        conn.commit()
        return token

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def validar_sessao(token: str):
    """
    Valida uma sessao persistente no PostgreSQL.

    Retorna os dados atuais do usuario e da empresa
    somente quando a sessao estiver valida.
    """

    if not isinstance(token, str) or not token:
        return None

    token_hash = _hash_token(token)

    conn = conectar()

    try:
        with conn.cursor(
            cursor_factory=RealDictCursor
        ) as cursor:
            cursor.execute(
                """
                SELECT
                    u.id AS usuario_id,
                    u.usuario,
                    u.nome,
                    u.empresa_id,
                    u.nivel,
                    e.nome AS empresa_nome
                FROM sessoes_usuarios s

                INNER JOIN usuarios u
                    ON u.id = s.usuario_id

                INNER JOIN empresas e
                    ON e.id = u.empresa_id

                WHERE s.token_hash = %s
                  AND s.revogado_em IS NULL
                  AND s.expira_em > NOW()
                  AND u.status = 'ativo'
                  AND e.status = 'ativa'

                LIMIT 1
                """,
                (token_hash,),
            )

            return cursor.fetchone()

    finally:
        conn.close()


def revogar_sessao(token: str) -> bool:
    """
    Revoga a sessao no servidor.
    O token deixa de funcionar imediatamente.
    """

    if not isinstance(token, str) or not token:
        return False

    token_hash = _hash_token(token)

    conn = conectar()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE sessoes_usuarios
                SET revogado_em = NOW()
                WHERE token_hash = %s
                  AND revogado_em IS NULL
                """,
                (token_hash,),
            )

            revogada = cursor.rowcount > 0

        conn.commit()
        return revogada

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()
