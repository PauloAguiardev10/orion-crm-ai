from dashboard.database.db import conectar


def tabela_existe(cursor, tabela: str) -> bool:
    cursor.execute(
        """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name = %s
        )
        """,
        (tabela,),
    )
    return bool(cursor.fetchone()[0])


def criar_tabela_conexoes_canais(cursor) -> None:
    tabela = "conexoes_canais"

    if tabela_existe(cursor, tabela):
        print(f"Tabela ja existe: {tabela}")
        return

    cursor.execute(
        """
        CREATE TABLE conexoes_canais (
            id SERIAL PRIMARY KEY,

            empresa_id INTEGER NOT NULL,

            provedor VARCHAR(50) NOT NULL DEFAULT 'meta',
            canal VARCHAR(50) NOT NULL,

            account_id VARCHAR(150),
            page_id VARCHAR(150),
            phone_number_id VARCHAR(150),

            access_token TEXT,

            ativo BOOLEAN NOT NULL DEFAULT TRUE,

            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            CONSTRAINT fk_conexoes_canais_empresa
                FOREIGN KEY (empresa_id)
                REFERENCES empresas(id)
                ON DELETE CASCADE
        )
        """
    )

    print(f"Tabela criada: {tabela}")


def criar_indices(cursor) -> None:
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
            ix_conexoes_canais_empresa_id
        ON conexoes_canais (empresa_id)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
            ix_conexoes_canais_canal
        ON conexoes_canais (canal)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
            ix_conexoes_canais_account_id
        ON conexoes_canais (account_id)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
            ix_conexoes_canais_page_id
        ON conexoes_canais (page_id)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
            ix_conexoes_canais_phone_number_id
        ON conexoes_canais (phone_number_id)
        """
    )

    print("Indices verificados/criados.")


def criar_restricoes_unicas(cursor) -> None:
    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS
            uq_conexoes_canais_meta_account
        ON conexoes_canais (provedor, canal, account_id)
        WHERE account_id IS NOT NULL
        """
    )

    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS
            uq_conexoes_canais_meta_phone
        ON conexoes_canais (provedor, canal, phone_number_id)
        WHERE phone_number_id IS NOT NULL
        """
    )

    print("Restricoes de unicidade verificadas/criadas.")


def exibir_resumo(cursor) -> None:
    cursor.execute(
        """
        SELECT
            column_name,
            data_type,
            is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'conexoes_canais'
        ORDER BY ordinal_position
        """
    )

    colunas = cursor.fetchall()

    print("")
    print("Resumo da migracao:")

    for coluna, tipo, nullable in colunas:
        print(
            f"- {coluna}: {tipo}, "
            f"nullable={nullable}"
        )


def main() -> None:
    conn = conectar()

    try:
        with conn.cursor() as cursor:
            criar_tabela_conexoes_canais(cursor)
            criar_indices(cursor)
            criar_restricoes_unicas(cursor)
            exibir_resumo(cursor)

        conn.commit()

        print("")
        print("Migracao de conexoes de canais concluida com sucesso.")

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    main()