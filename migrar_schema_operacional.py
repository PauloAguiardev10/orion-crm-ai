from dashboard.database.db import conectar


COLUNAS_POR_TABELA = {
    "clientes": [
        ("empresa_id", "INTEGER"),
    ],
    "conversas": [
        ("empresa_id", "INTEGER"),
    ],
    "leads": [
        ("empresa_id", "INTEGER"),
        ("responsavel", "VARCHAR(150) DEFAULT 'Não atribuído'"),
        ("valor_negocio", "NUMERIC(12,2) DEFAULT 0"),
        ("mensalidade", "NUMERIC(12,2) DEFAULT 0"),
        ("motivo_perda", "TEXT DEFAULT ''"),
        ("observacao_comercial", "TEXT DEFAULT ''"),
        ("atualizado_em", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
    ],
}


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


def constraint_existe(cursor, nome: str) -> bool:
    cursor.execute(
        """
        SELECT EXISTS (
            SELECT 1
            FROM pg_constraint
            WHERE conname = %s
        )
        """,
        (nome,),
    )
    return bool(cursor.fetchone()[0])


def adicionar_colunas(cursor) -> None:
    for tabela, colunas in COLUNAS_POR_TABELA.items():
        for coluna, definicao in colunas:
            if coluna_existe(cursor, tabela, coluna):
                continue

            cursor.execute(
                f'ALTER TABLE "{tabela}" '
                f'ADD COLUMN "{coluna}" {definicao}'
            )

            print(f"Coluna criada: {tabela}.{coluna}")


def criar_foreign_keys(cursor) -> None:
    for tabela in ("clientes", "conversas", "leads"):
        nome_constraint = f"{tabela}_empresa_id_fkey"

        if constraint_existe(cursor, nome_constraint):
            continue

        cursor.execute(
            f"""
            ALTER TABLE "{tabela}"
            ADD CONSTRAINT "{nome_constraint}"
            FOREIGN KEY (empresa_id)
            REFERENCES empresas(id)
            ON DELETE SET NULL
            """
        )

        print(f"Foreign key criada: {nome_constraint}")


def criar_indices(cursor) -> None:
    for tabela in ("clientes", "conversas", "leads"):
        cursor.execute(
            f"""
            CREATE INDEX IF NOT EXISTS "ix_{tabela}_empresa_id"
            ON "{tabela}" (empresa_id)
            """
        )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_leads_status
        ON leads (status)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_leads_criado_em
        ON leads (criado_em)
        """
    )


def normalizar_dados(cursor) -> None:
    cursor.execute(
        """
        UPDATE leads
        SET responsavel = 'Não atribuído'
        WHERE responsavel IS NULL
           OR TRIM(responsavel) = ''
        """
    )

    cursor.execute(
        """
        UPDATE leads
        SET valor_negocio = 0
        WHERE valor_negocio IS NULL
        """
    )

    cursor.execute(
        """
        UPDATE leads
        SET mensalidade = 0
        WHERE mensalidade IS NULL
        """
    )

    cursor.execute(
        """
        UPDATE leads
        SET motivo_perda = ''
        WHERE motivo_perda IS NULL
        """
    )

    cursor.execute(
        """
        UPDATE leads
        SET observacao_comercial = ''
        WHERE observacao_comercial IS NULL
        """
    )

    cursor.execute(
        """
        UPDATE leads
        SET atualizado_em = COALESCE(criado_em, CURRENT_TIMESTAMP)
        WHERE atualizado_em IS NULL
        """
    )


def exibir_resumo(cursor) -> None:
    print("")
    print("Resumo da estrutura operacional:")

    for tabela in ("clientes", "conversas", "leads"):
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = %s
            """,
            (tabela,),
        )

        total_colunas = int(cursor.fetchone()[0])

        cursor.execute(
            f"""
            SELECT COUNT(*)
            FROM "{tabela}"
            WHERE empresa_id IS NULL
            """
        )

        registros_sem_empresa = int(cursor.fetchone()[0])

        print(
            f"- {tabela}: {total_colunas} colunas; "
            f"{registros_sem_empresa} registro(s) sem empresa_id"
        )


def main() -> None:
    conn = conectar()

    try:
        with conn.cursor() as cursor:
            adicionar_colunas(cursor)
            criar_foreign_keys(cursor)
            criar_indices(cursor)
            normalizar_dados(cursor)
            exibir_resumo(cursor)

        conn.commit()

        print("")
        print("Migração operacional concluída com sucesso.")

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    main()