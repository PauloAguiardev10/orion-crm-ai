import hashlib

from database.db import conectar
from psycopg2.extras import RealDictCursor

EMAIL_ADMIN_PADRAO = "admin@forway.local"
NOME_ADMIN_PADRAO = "admin"
SENHA_ADMIN_PADRAO = "123456"


def criptografar_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()


def garantir_tabelas_auth():
    """
    A estrutura das tabelas já existe no PostgreSQL.

    Esta função garante apenas:
    - que a empresa Forway exista;
    - que exista um administrador padrão para o primeiro acesso.
    """

    conn = conectar()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cursor.execute(
            """
            INSERT INTO empresas (
                nome,
                slug,
                plano,
                nicho,
                status
            )
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (slug) DO NOTHING
            """,
            (
                "Forway",
                "forway",
                "Premium",
                "Agência de marketing",
                "ativa",
            ),
        )

        cursor.execute(
            """
            SELECT id
            FROM empresas
            WHERE slug = %s
            LIMIT 1
            """,
            ("forway",),
        )

        empresa = cursor.fetchone()

        if not empresa:
            raise RuntimeError(
                "Não foi possível localizar a empresa Forway."
            )

        empresa_id = empresa["id"]

        cursor.execute(
            """
            INSERT INTO usuarios (
                empresa_id,
                nome,
                email,
                senha_hash,
                nivel,
                status
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (email) DO NOTHING
            """,
            (
                empresa_id,
                NOME_ADMIN_PADRAO,
                EMAIL_ADMIN_PADRAO,
                criptografar_senha(SENHA_ADMIN_PADRAO),
                "orion_admin",
                "ativo",
            ),
        )

        cursor.execute(
            """
            UPDATE usuarios
            SET
                empresa_id = %s,
                nivel = %s,
                status = %s,
                atualizado_em = CURRENT_TIMESTAMP
            WHERE email = %s
            """,
            (
                empresa_id,
                "orion_admin",
                "ativo",
                EMAIL_ADMIN_PADRAO,
            ),
        )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()


def validar_login(usuario: str, senha: str) -> bool:
    garantir_tabelas_auth()

    login = usuario.strip().lower()
    senha_hash = criptografar_senha(senha)

    conn = conectar()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cursor.execute(
            """
            SELECT usuarios.id
            FROM usuarios

            INNER JOIN empresas
                ON empresas.id = usuarios.empresa_id

            WHERE (
                LOWER(usuarios.email) = %s
                OR LOWER(usuarios.nome) = %s
            )
              AND usuarios.senha_hash = %s
              AND usuarios.status = 'ativo'
              AND empresas.status = 'ativa'

            LIMIT 1
            """,
            (
                login,
                login,
                senha_hash,
            ),
        )

        resultado = cursor.fetchone()

        if resultado:
            cursor.execute(
                """
                UPDATE usuarios
                SET ultimo_login_em = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (resultado["id"],),
            )

            conn.commit()
            return True

        return False

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()


def obter_empresa_usuario(usuario: str):
    garantir_tabelas_auth()

    login = usuario.strip().lower()

    conn = conectar()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cursor.execute(
            """
            SELECT empresas.nome
            FROM usuarios

            INNER JOIN empresas
                ON empresas.id = usuarios.empresa_id

            WHERE (
                LOWER(usuarios.email) = %s
                OR LOWER(usuarios.nome) = %s
            )
              AND usuarios.status = 'ativo'
              AND empresas.status = 'ativa'

            LIMIT 1
            """,
            (
                login,
                login,
            ),
        )

        resultado = cursor.fetchone()

        if resultado:
            return resultado["nome"]

        return None

    finally:
        cursor.close()
        conn.close()


def obter_empresa_id_usuario(usuario: str):
    garantir_tabelas_auth()

    login = usuario.strip().lower()

    conn = conectar()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cursor.execute(
            """
            SELECT empresas.id
            FROM usuarios

            INNER JOIN empresas
                ON empresas.id = usuarios.empresa_id

            WHERE (
                LOWER(usuarios.email) = %s
                OR LOWER(usuarios.nome) = %s
            )
              AND usuarios.status = 'ativo'
              AND empresas.status = 'ativa'

            LIMIT 1
            """,
            (
                login,
                login,
            ),
        )

        resultado = cursor.fetchone()

        if resultado:
            return resultado["id"]

        return None

    finally:
        cursor.close()
        conn.close()


def obter_nivel_usuario(usuario: str):
    garantir_tabelas_auth()

    login = usuario.strip().lower()

    conn = conectar()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cursor.execute(
            """
            SELECT usuarios.nivel
            FROM usuarios

            INNER JOIN empresas
                ON empresas.id = usuarios.empresa_id

            WHERE (
                LOWER(usuarios.email) = %s
                OR LOWER(usuarios.nome) = %s
            )
              AND usuarios.status = 'ativo'
              AND empresas.status = 'ativa'

            LIMIT 1
            """,
            (
                login,
                login,
            ),
        )

        resultado = cursor.fetchone()

        if resultado:
            return resultado["nivel"]

        return "usuario"

    finally:
        cursor.close()
        conn.close()