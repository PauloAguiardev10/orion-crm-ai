import hashlib

import pandas as pd

from database.db import conectar


def hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode()).hexdigest()


def criar_tabela_usuarios() -> None:
    conn = conectar()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS usuarios (
                    id SERIAL PRIMARY KEY,
                    empresa_id INTEGER,
                    empresa VARCHAR(255) NOT NULL,
                    usuario VARCHAR(150) UNIQUE NOT NULL,
                    senha VARCHAR(255) NOT NULL,
                    nivel VARCHAR(50) DEFAULT 'usuario'
                )
                """
            )

        conn.commit()

    finally:
        conn.close()


def listar_usuarios():
    criar_tabela_usuarios()

    conn = conectar()

    try:
        usuarios = pd.read_sql_query(
            """
            SELECT
                id,
                empresa_id,
                empresa,
                usuario,
                nivel
            FROM usuarios
            ORDER BY id
            """,
            conn,
        )

        return usuarios

    finally:
        conn.close()


def criar_usuario(
    usuario,
    senha,
    empresa,
    nivel,
    empresa_id=None,
):
    usuario = usuario.strip()
    senha = senha.strip()
    empresa = empresa.strip()

    if not usuario or not senha or not empresa:
        return False

    criar_tabela_usuarios()

    conn = conectar()

    try:
        senha_hash = hash_senha(senha)

        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id
                FROM usuarios
                WHERE usuario = %s
                """,
                (usuario,),
            )

            existente = cursor.fetchone()

            if existente:
                cursor.execute(
                    """
                    UPDATE usuarios
                    SET
                        empresa_id = %s,
                        empresa = %s,
                        senha = %s,
                        nivel = %s
                    WHERE usuario = %s
                    """,
                    (
                        empresa_id,
                        empresa,
                        senha_hash,
                        nivel,
                        usuario,
                    ),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO usuarios (
                        empresa_id,
                        empresa,
                        usuario,
                        senha,
                        nivel
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        empresa_id,
                        empresa,
                        usuario,
                        senha_hash,
                        nivel,
                    ),
                )

        conn.commit()
        return True

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def criar_admin_empresa(
    empresa_id,
    empresa_nome,
    usuario,
    senha,
):
    return criar_usuario(
        usuario=usuario,
        senha=senha,
        empresa=empresa_nome,
        nivel="admin_empresa",
        empresa_id=empresa_id,
    )


def alterar_senha(usuario, nova_senha):
    nova_senha = nova_senha.strip()

    if not nova_senha:
        return False

    conn = conectar()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE usuarios
                SET senha = %s
                WHERE usuario = %s
                """,
                (
                    hash_senha(nova_senha),
                    usuario,
                ),
            )

            alterado = cursor.rowcount > 0

        conn.commit()
        return alterado

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()