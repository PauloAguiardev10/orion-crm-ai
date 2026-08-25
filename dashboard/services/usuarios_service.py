import hashlib
import re
import unicodedata

import pandas as pd

from database.db import conectar


def hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode()).hexdigest()


def gerar_email_interno(usuario: str) -> str:
    """
    Gera um e-mail técnico para compatibilidade com o schema atual
    da tabela usuarios, sem alterar a forma de login pelo campo usuario.
    """
    usuario = usuario.strip()

    if "@" in usuario and "." in usuario.split("@")[-1]:
        return usuario.lower()

    texto = unicodedata.normalize("NFKD", usuario)
    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )

    texto = texto.lower()
    texto = re.sub(r"[^a-z0-9]+", ".", texto)
    texto = texto.strip(".")

    if not texto:
        texto = "usuario"

    return f"{texto}@orionsystems.local"


def criar_tabela_usuarios() -> None:
    conn = conectar()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS usuarios (
                    id SERIAL PRIMARY KEY,
                    empresa_id INTEGER,
                    nome VARCHAR(150) NOT NULL,
                    email VARCHAR(150) UNIQUE NOT NULL,
                    senha_hash TEXT NOT NULL,
                    nivel VARCHAR(50) DEFAULT 'usuario',
                    status VARCHAR(30) DEFAULT 'ativo',
                    ultimo_login_em TIMESTAMP,
                    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    empresa VARCHAR(150),
                    usuario VARCHAR(150),
                    senha TEXT
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
        nome = usuario
        email = gerar_email_interno(usuario)

        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id
                FROM usuarios
                WHERE usuario = %s
                   OR email = %s
                LIMIT 1
                """,
                (
                    usuario,
                    email,
                ),
            )

            existente = cursor.fetchone()

            if existente:
                cursor.execute(
                    """
                    UPDATE usuarios
                    SET
                        empresa_id = %s,
                        empresa = %s,
                        nome = %s,
                        email = %s,
                        usuario = %s,
                        senha = %s,
                        senha_hash = %s,
                        nivel = %s,
                        status = 'ativo',
                        atualizado_em = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (
                        empresa_id,
                        empresa,
                        nome,
                        email,
                        usuario,
                        senha_hash,
                        senha_hash,
                        nivel,
                        existente[0],
                    ),
                )

            else:
                cursor.execute(
                    """
                    INSERT INTO usuarios (
                        empresa_id,
                        empresa,
                        nome,
                        email,
                        usuario,
                        senha,
                        senha_hash,
                        nivel,
                        status
                    )
                    VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, 'ativo'
                    )
                    """,
                    (
                        empresa_id,
                        empresa,
                        nome,
                        email,
                        usuario,
                        senha_hash,
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
        senha_hash = hash_senha(nova_senha)

        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE usuarios
                SET
                    senha = %s,
                    senha_hash = %s,
                    atualizado_em = CURRENT_TIMESTAMP
                WHERE usuario = %s
                """,
                (
                    senha_hash,
                    senha_hash,
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