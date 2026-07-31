import hashlib

from dashboard.database.db import conectar


def criptografar_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()


def criar_ou_atualizar_empresa(
    nome: str,
    slug: str,
    tipo: str,
    parceiro_nome: str,
    plano: str,
    nicho: str,
) -> int:
    conn = conectar()

    try:
        with conn.cursor() as cursor:
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
                    %s, %s, %s, %s, %s, %s,
                    'ativa', 'em_dia', 0, TRUE
                )
                ON CONFLICT (slug)
                DO UPDATE SET
                    nome = EXCLUDED.nome,
                    tipo = EXCLUDED.tipo,
                    parceiro_nome = EXCLUDED.parceiro_nome,
                    plano = EXCLUDED.plano,
                    nicho = EXCLUDED.nicho,
                    status = 'ativa',
                    status_financeiro = 'em_dia'
                RETURNING id
                """,
                (nome, slug, tipo, parceiro_nome, plano, nicho),
            )

            empresa_id = int(cursor.fetchone()[0])

        conn.commit()
        return empresa_id

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def criar_ou_atualizar_usuario(
    empresa_id: int,
    empresa_nome: str,
    usuario: str,
    email: str,
    senha: str,
    nivel: str,
) -> None:
    senha_hash = criptografar_senha(senha)
    conn = conectar()

    try:
        with conn.cursor() as cursor:
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
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, 'ativo'
                )
                ON CONFLICT (LOWER(usuario))
                WHERE usuario IS NOT NULL
                DO UPDATE SET
                    empresa_id = EXCLUDED.empresa_id,
                    empresa = EXCLUDED.empresa,
                    nome = EXCLUDED.nome,
                    email = EXCLUDED.email,
                    senha = EXCLUDED.senha,
                    senha_hash = EXCLUDED.senha_hash,
                    nivel = EXCLUDED.nivel,
                    status = 'ativo',
                    atualizado_em = CURRENT_TIMESTAMP
                """,
                (
                    empresa_id,
                    empresa_nome,
                    usuario,
                    usuario,
                    email,
                    senha_hash,
                    senha_hash,
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
    orion_id = criar_ou_atualizar_empresa(
        nome="Orion Systems",
        slug="orion-systems",
        tipo="master",
        parceiro_nome="Orion",
        plano="Premium",
        nicho="Tecnologia e automação",
    )

    forway_id = criar_ou_atualizar_empresa(
        nome="Forway",
        slug="forway",
        tipo="parceiro",
        parceiro_nome="Forway",
        plano="Premium",
        nicho="Agência de marketing",
    )

    criar_ou_atualizar_usuario(
        empresa_id=orion_id,
        empresa_nome="Orion Systems",
        usuario="orion",
        email="orion@orion.local",
        senha="123456",
        nivel="orion_admin",
    )

    criar_ou_atualizar_usuario(
        empresa_id=forway_id,
        empresa_nome="Forway",
        usuario="luciano",
        email="luciano@forway.local",
        senha="123456",
        nivel="parceiro_admin",
    )

    print("Orion Systems e Forway criadas/atualizadas com sucesso.")
    print("Login Orion: orion / 123456")
    print("Login Forway: luciano / 123456")
    print("Altere as senhas padrão após o primeiro acesso.")


if __name__ == "__main__":
    main()