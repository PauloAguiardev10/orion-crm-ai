import hashlib

from database.db import conectar
from psycopg2.extras import RealDictCursor


EMAIL_ADMIN_PADRAO = "admin@forway.local"
USUARIO_ADMIN_PADRAO = "admin"
NOME_ADMIN_PADRAO = "admin"
SENHA_ADMIN_PADRAO = "123456"


def criptografar_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()


def garantir_tabelas_auth() -> None:
    """
    Garante que a empresa Forway e o administrador padrão existam.

    Esta função não cria tabelas. A estrutura do PostgreSQL deve ser
    criada pelos scripts de migração do projeto.
    """
    conn = conectar()

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT id
                FROM empresas
                WHERE slug = %s
                   OR LOWER(nome) = LOWER(%s)
                ORDER BY id
                LIMIT 1
                """,
                (
                    "forway",
                    "Forway",
                ),
            )

            empresa = cursor.fetchone()

            if empresa:
                empresa_id = int(empresa["id"])

                cursor.execute(
                    """
                    UPDATE empresas
                    SET
                        nome = %s,
                        slug = %s,
                        tipo = %s,
                        parceiro_nome = %s,
                        plano = %s,
                        nicho = %s,
                        status = %s,
                        status_financeiro = %s
                    WHERE id = %s
                    """,
                    (
                        "Forway",
                        "forway",
                        "parceiro",
                        "Forway",
                        "Premium",
                        "Agência de marketing",
                        "ativa",
                        "em_dia",
                        empresa_id,
                    ),
                )

            else:
                cursor.execute(
                    """
                    INSERT INTO empresas (
                        nome,
                        slug,
                        tipo,
                        parceiro_nome,
                        plano,
                        nicho,
                        status,
                        status_financeiro,
                        valor_mensal,
                        bloqueio_automatico
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    RETURNING id
                    """,
                    (
                        "Forway",
                        "forway",
                        "parceiro",
                        "Forway",
                        "Premium",
                        "Agência de marketing",
                        "ativa",
                        "em_dia",
                        0,
                        True,
                    ),
                )

                empresa_id = int(cursor.fetchone()["id"])

            senha_hash = criptografar_senha(SENHA_ADMIN_PADRAO)

            cursor.execute(
                """
                SELECT id
                FROM usuarios
                WHERE LOWER(COALESCE(email, '')) = %s
                   OR LOWER(COALESCE(usuario, '')) = %s
                ORDER BY id
                LIMIT 1
                """,
                (
                    EMAIL_ADMIN_PADRAO.lower(),
                    USUARIO_ADMIN_PADRAO.lower(),
                ),
            )

            usuario_existente = cursor.fetchone()

            if usuario_existente:
                cursor.execute(
                    """
                    UPDATE usuarios
                    SET
                        empresa_id = %s,
                        empresa = %s,
                        usuario = %s,
                        nome = %s,
                        email = %s,
                        senha = %s,
                        senha_hash = %s,
                        nivel = %s,
                        status = %s,
                        atualizado_em = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (
                        empresa_id,
                        "Forway",
                        USUARIO_ADMIN_PADRAO,
                        NOME_ADMIN_PADRAO,
                        EMAIL_ADMIN_PADRAO,
                        senha_hash,
                        senha_hash,
                        "parceiro_admin",
                        "ativo",
                        int(usuario_existente["id"]),
                    ),
                )

            else:
                cursor.execute(
                    """
                    INSERT INTO usuarios (
                        empresa_id,
                        empresa,
                        usuario,
                        nome,
                        email,
                        senha,
                        senha_hash,
                        nivel,
                        status
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    """,
                    (
                        empresa_id,
                        "Forway",
                        USUARIO_ADMIN_PADRAO,
                        NOME_ADMIN_PADRAO,
                        EMAIL_ADMIN_PADRAO,
                        senha_hash,
                        senha_hash,
                        "parceiro_admin",
                        "ativo",
                    ),
                )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def _buscar_usuario_por_login(
    cursor,
    login: str,
    senha_hash: str | None = None,
):
    filtros_senha = ""
    parametros = [
        login,
        login,
        login,
    ]

    if senha_hash is not None:
        filtros_senha = "AND usuarios.senha_hash = %s"
        parametros.append(senha_hash)

    cursor.execute(
        f"""
        SELECT
            usuarios.id,
            usuarios.empresa_id,
            usuarios.nivel,
            empresas.nome AS empresa_nome
        FROM usuarios

        INNER JOIN empresas
            ON empresas.id = usuarios.empresa_id

        WHERE (
            LOWER(COALESCE(usuarios.email, '')) = %s
            OR LOWER(COALESCE(usuarios.nome, '')) = %s
            OR LOWER(COALESCE(usuarios.usuario, '')) = %s
        )
          {filtros_senha}
          AND usuarios.status = 'ativo'
          AND empresas.status = 'ativa'

        LIMIT 1
        """,
        tuple(parametros),
    )

    return cursor.fetchone()


def validar_login(usuario: str, senha: str) -> bool:
    garantir_tabelas_auth()

    login = usuario.strip().lower()
    senha_hash = criptografar_senha(senha)

    conn = conectar()

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            resultado = _buscar_usuario_por_login(
                cursor,
                login,
                senha_hash,
            )

            if not resultado:
                return False

            cursor.execute(
                """
                UPDATE usuarios
                SET
                    ultimo_login_em = CURRENT_TIMESTAMP,
                    atualizado_em = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (int(resultado["id"]),),
            )

        conn.commit()
        return True

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def obter_empresa_usuario(usuario: str):
    garantir_tabelas_auth()

    login = usuario.strip().lower()
    conn = conectar()

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            resultado = _buscar_usuario_por_login(
                cursor,
                login,
            )

            if resultado:
                return resultado["empresa_nome"]

            return None

    finally:
        conn.close()


def obter_empresa_id_usuario(usuario: str):
    garantir_tabelas_auth()

    login = usuario.strip().lower()
    conn = conectar()

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            resultado = _buscar_usuario_por_login(
                cursor,
                login,
            )

            if resultado:
                return int(resultado["empresa_id"])

            return None

    finally:
        conn.close()


def obter_nivel_usuario(usuario: str):
    garantir_tabelas_auth()

    login = usuario.strip().lower()
    conn = conectar()

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            resultado = _buscar_usuario_por_login(
                cursor,
                login,
            )

            if resultado:
                return resultado["nivel"]

            return "usuario"

    finally:
        conn.close()