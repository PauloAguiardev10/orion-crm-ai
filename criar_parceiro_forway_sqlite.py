import hashlib

from dashboard.database.db import conectar


def criptografar_senha(senha: str) -> str:
    """
    Gera o hash SHA-256 utilizado atualmente pelo sistema.
    """
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()


def garantir_colunas() -> None:
    """
    A estrutura do PostgreSQL já deve estar criada pelas migrations.

    Esta função foi mantida apenas para preservar compatibilidade com
    o fluxo original do script.
    """
    return


def criar_empresa(
    nome: str,
    tipo: str,
    parceiro_nome: str | None = None,
    valor_mensal: float = 0,
) -> int:
    """
    Cria uma empresa ou atualiza seus dados caso ela já exista.
    """
    conn = conectar()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id
                FROM empresas
                WHERE nome = %s
                LIMIT 1
                """,
                (nome,),
            )

            empresa = cursor.fetchone()

            if empresa:
                empresa_id = int(empresa[0])

                cursor.execute(
                    """
                    UPDATE empresas
                    SET tipo = %s,
                        parceiro_nome = %s,
                        status = 'ativa',
                        status_financeiro = 'em_dia',
                        valor_mensal = %s
                    WHERE id = %s
                    """,
                    (
                        tipo,
                        parceiro_nome,
                        valor_mensal,
                        empresa_id,
                    ),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO empresas (
                        nome,
                        tipo,
                        parceiro_nome,
                        status,
                        status_financeiro,
                        valor_mensal
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        'ativa',
                        'em_dia',
                        %s
                    )
                    RETURNING id
                    """,
                    (
                        nome,
                        tipo,
                        parceiro_nome,
                        valor_mensal,
                    ),
                )

                empresa_id = int(cursor.fetchone()[0])

        conn.commit()
        return empresa_id

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def criar_usuario(
    usuario: str,
    senha: str,
    empresa: str,
    nivel: str,
) -> None:
    """
    Cria um usuário ou atualiza seus dados caso ele já exista.
    """
    conn = conectar()

    try:
        senha_criptografada = criptografar_senha(senha)

        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id
                FROM empresas
                WHERE nome = %s
                LIMIT 1
                """,
                (empresa,),
            )

            empresa_row = cursor.fetchone()

            if not empresa_row:
                raise RuntimeError(
                    f"Empresa não encontrada: {empresa}"
                )

            empresa_id = int(empresa_row[0])

            cursor.execute(
                """
                SELECT id
                FROM usuarios
                WHERE usuario = %s
                LIMIT 1
                """,
                (usuario,),
            )

            existente = cursor.fetchone()

            if existente:
                cursor.execute(
                    """
                    UPDATE usuarios
                    SET senha = %s,
                        empresa = %s,
                        empresa_id = %s,
                        nivel = %s
                    WHERE usuario = %s
                    """,
                    (
                        senha_criptografada,
                        empresa,
                        empresa_id,
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
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    """,
                    (
                        empresa_id,
                        empresa,
                        usuario,
                        senha_criptografada,
                        nivel,
                    ),
                )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def main() -> None:
    garantir_colunas()

    criar_empresa(
        nome="Orion Systems",
        tipo="master",
        parceiro_nome=None,
        valor_mensal=0,
    )

    criar_empresa(
        nome="Forway",
        tipo="parceiro_cliente",
        parceiro_nome="Forway",
        valor_mensal=0,
    )

    criar_usuario(
        usuario="orion",
        senha="123456",
        empresa="Orion Systems",
        nivel="orion_admin",
    )

    criar_usuario(
        usuario="luciano",
        senha="123456",
        empresa="Forway",
        nivel="parceiro_admin",
    )

    print("Parceiro Forway criado/atualizado com sucesso.")
    print("Login Orion: orion / 123456")
    print("Login Forway: luciano / 123456")
    print("Atenção: altere as senhas padrão após o primeiro acesso.")


if __name__ == "__main__":
    main()
