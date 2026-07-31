from dashboard.database.db import conectar

EMPRESAS_COLUNAS = [
    ("slug", "VARCHAR(255)"),
    ("tipo", "VARCHAR(50) DEFAULT 'cliente'"),
    ("logo_path", "TEXT"),
    ("parceiro_nome", "VARCHAR(255)"),
    ("data_adesao", "DATE"),
    ("data_vencimento", "DATE"),
    ("status_financeiro", "VARCHAR(30) DEFAULT 'em_dia'"),
    ("bloqueio_automatico", "BOOLEAN DEFAULT TRUE"),
    ("valor_mensal", "NUMERIC(12,2) DEFAULT 0"),
    ("servicos", "TEXT DEFAULT ''"),
]

USUARIOS_COLUNAS = [
    ("nome", "VARCHAR(150)"),
    ("email", "VARCHAR(255)"),
    ("senha_hash", "VARCHAR(255)"),
    ("status", "VARCHAR(30) DEFAULT 'ativo'"),
    ("criado_em", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
    ("atualizado_em", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
    ("ultimo_login_em", "TIMESTAMP"),
]


def coluna_existe(cursor, tabela: str, coluna: str) -> bool:
    cursor.execute(
        """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = %s
              AND column_name = %s
        )
        """,
        (tabela, coluna),
    )
    return bool(cursor.fetchone()[0])


def adicionar_colunas(cursor, tabela: str, colunas) -> None:
    for coluna, definicao in colunas:
        if not coluna_existe(cursor, tabela, coluna):
            cursor.execute(
                f'ALTER TABLE "{tabela}" ADD COLUMN "{coluna}" {definicao}'
            )
            print(f"Coluna criada: {tabela}.{coluna}")


def migrar_dados_legados(cursor) -> None:
    cursor.execute(
        """
        UPDATE empresas
        SET slug = LOWER(
            REGEXP_REPLACE(
                REGEXP_REPLACE(TRIM(nome), '[^a-zA-Z0-9]+', '-', 'g'),
                '(^-|-$)',
                '',
                'g'
            )
        )
        WHERE slug IS NULL OR TRIM(slug) = ''
        """
    )

    cursor.execute(
        """
        UPDATE empresas
        SET parceiro_nome = CASE
            WHEN LOWER(nome) = 'forway' THEN 'Forway'
            WHEN parceiro_nome IS NULL OR TRIM(parceiro_nome) = '' THEN 'Orion'
            ELSE parceiro_nome
        END
        """
    )

    cursor.execute(
        """
        UPDATE empresas
        SET tipo = CASE
            WHEN LOWER(nome) = 'orion systems' THEN 'master'
            WHEN LOWER(nome) = 'forway' THEN 'parceiro'
            ELSE COALESCE(NULLIF(TRIM(tipo), ''), 'cliente')
        END
        """
    )

    cursor.execute(
        """
        UPDATE usuarios
        SET nome = usuario
        WHERE (nome IS NULL OR TRIM(nome) = '')
          AND usuario IS NOT NULL
        """
    )

    cursor.execute(
        """
        UPDATE usuarios
        SET email = LOWER(usuario) || '@orion.local'
        WHERE (email IS NULL OR TRIM(email) = '')
          AND usuario IS NOT NULL
        """
    )

    cursor.execute(
        """
        UPDATE usuarios
        SET senha_hash = senha
        WHERE (senha_hash IS NULL OR TRIM(senha_hash) = '')
          AND senha IS NOT NULL
        """
    )

    cursor.execute(
        """
        UPDATE usuarios
        SET status = 'ativo'
        WHERE status IS NULL OR TRIM(status) = ''
        """
    )


def criar_indices(cursor) -> None:
    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ux_empresas_slug
        ON empresas (slug)
        WHERE slug IS NOT NULL
        """
    )
    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ux_usuarios_email
        ON usuarios (LOWER(email))
        WHERE email IS NOT NULL
        """
    )
    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ux_usuarios_usuario
        ON usuarios (LOWER(usuario))
        WHERE usuario IS NOT NULL
        """
    )


def main() -> None:
    conn = conectar()

    try:
        with conn.cursor() as cursor:
            adicionar_colunas(cursor, "empresas", EMPRESAS_COLUNAS)
            adicionar_colunas(cursor, "usuarios", USUARIOS_COLUNAS)
            migrar_dados_legados(cursor)
            criar_indices(cursor)

        conn.commit()
        print("Migração de compatibilidade concluída com sucesso.")

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    main()