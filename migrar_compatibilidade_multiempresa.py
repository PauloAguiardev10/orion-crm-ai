from dashboard.database.db import conectar


COLUNAS_EMPRESA = {
    "nome_agente": (
        "VARCHAR(100)",
        "'Sofia'",
    ),
    "whatsapp": (
        "BOOLEAN",
        "TRUE",
    ),
    "instagram": (
        "BOOLEAN",
        "FALSE",
    ),
    "facebook": (
        "BOOLEAN",
        "FALSE",
    ),
    "crm": (
        "BOOLEAN",
        "FALSE",
    ),
    "funil": (
        "BOOLEAN",
        "FALSE",
    ),
    "analytics": (
        "BOOLEAN",
        "FALSE",
    ),
    "vendas_ia": (
        "BOOLEAN",
        "FALSE",
    ),
}


COLUNAS_AGENTE_CONFIG = {
    "nome_agente": (
        "VARCHAR(100)",
        "'Sofia'",
    ),
    "tom": (
        "VARCHAR(100)",
        "'Humanizado'",
    ),
    "nicho": (
        "TEXT",
        None,
    ),
    "objetivo": (
        "TEXT",
        None,
    ),
    "ia_pode_vender": (
        "BOOLEAN",
        "FALSE",
    ),
    "ia_envia_pix": (
        "BOOLEAN",
        "FALSE",
    ),
    "ia_envia_link": (
        "BOOLEAN",
        "FALSE",
    ),
    "whatsapp": (
        "BOOLEAN",
        "TRUE",
    ),
    "instagram": (
        "BOOLEAN",
        "FALSE",
    ),
    "facebook": (
        "BOOLEAN",
        "FALSE",
    ),
}


def tabela_existe(
    cursor,
    tabela: str,
) -> bool:

    cursor.execute(
        """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name = %s
        )
        """,
        (
            tabela,
        ),
    )

    return bool(
        cursor.fetchone()[0]
    )


def coluna_existe(
    cursor,
    tabela: str,
    coluna: str,
) -> bool:

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
        (
            tabela,
            coluna,
        ),
    )

    return bool(
        cursor.fetchone()[0]
    )


def constraint_existe(
    cursor,
    tabela: str,
    constraint: str,
) -> bool:

    cursor.execute(
        """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.table_constraints
            WHERE table_schema = 'public'
              AND table_name = %s
              AND constraint_name = %s
        )
        """,
        (
            tabela,
            constraint,
        ),
    )

    return bool(
        cursor.fetchone()[0]
    )


def validar_empresas(
    cursor,
) -> None:

    if not tabela_existe(
        cursor,
        "empresas",
    ):
        raise RuntimeError(
            "Tabela empresas nao encontrada."
        )

    print(
        "Tabela empresas encontrada."
    )


def atualizar_tabela_empresas(
    cursor,
) -> None:

    for (
        coluna,
        (
            tipo,
            default,
        ),
    ) in COLUNAS_EMPRESA.items():

        if coluna_existe(
            cursor,
            "empresas",
            coluna,
        ):
            print(
                f"empresas.{coluna}: ja existe."
            )
            continue

        sql = (
            f"ALTER TABLE empresas "
            f"ADD COLUMN {coluna} {tipo}"
        )

        if default is not None:
            sql += (
                f" DEFAULT {default}"
            )

        cursor.execute(
            sql
        )

        print(
            f"empresas.{coluna}: criada."
        )


def criar_agente_config(
    cursor,
) -> None:

    if tabela_existe(
        cursor,
        "agente_config",
    ):
        print(
            "Tabela agente_config ja existe."
        )

        return

    cursor.execute(
        """
        CREATE TABLE agente_config (
            id SERIAL PRIMARY KEY,

            empresa_id INTEGER NOT NULL,

            nome_agente VARCHAR(100)
                DEFAULT 'Sofia',

            tom VARCHAR(100)
                DEFAULT 'Humanizado',

            nicho TEXT,

            objetivo TEXT,

            ia_pode_vender BOOLEAN
                DEFAULT FALSE,

            ia_envia_pix BOOLEAN
                DEFAULT FALSE,

            ia_envia_link BOOLEAN
                DEFAULT FALSE,

            whatsapp BOOLEAN
                DEFAULT TRUE,

            instagram BOOLEAN
                DEFAULT FALSE,

            facebook BOOLEAN
                DEFAULT FALSE,

            CONSTRAINT fk_agente_config_empresa
                FOREIGN KEY (empresa_id)
                REFERENCES empresas(id)
                ON DELETE RESTRICT
        )
        """
    )

    print(
        "Tabela agente_config criada."
    )


def garantir_colunas_agente_config(
    cursor,
) -> None:

    for (
        coluna,
        (
            tipo,
            default,
        ),
    ) in COLUNAS_AGENTE_CONFIG.items():

        if coluna_existe(
            cursor,
            "agente_config",
            coluna,
        ):
            continue

        sql = (
            f"ALTER TABLE agente_config "
            f"ADD COLUMN {coluna} {tipo}"
        )

        if default is not None:
            sql += (
                f" DEFAULT {default}"
            )

        cursor.execute(
            sql
        )

        print(
            f"agente_config.{coluna}: criada."
        )


def validar_empresa_id_agente(
    cursor,
) -> None:

    if not coluna_existe(
        cursor,
        "agente_config",
        "empresa_id",
    ):
        cursor.execute(
            """
            ALTER TABLE agente_config
            ADD COLUMN empresa_id INTEGER
            """
        )

        print(
            "agente_config.empresa_id criado."
        )

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM agente_config
        WHERE empresa_id IS NULL
        """
    )

    nulos = cursor.fetchone()[0]

    if nulos:
        raise RuntimeError(
            "agente_config possui "
            f"{nulos} registro(s) "
            "com empresa_id NULL."
        )

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM agente_config a
        WHERE NOT EXISTS (
            SELECT 1
            FROM empresas e
            WHERE e.id = a.empresa_id
        )
        """
    )

    orfaos = cursor.fetchone()[0]

    if orfaos:
        raise RuntimeError(
            "agente_config possui "
            f"{orfaos} registro(s) "
            "referenciando empresa inexistente."
        )

    cursor.execute(
        """
        ALTER TABLE agente_config
        ALTER COLUMN empresa_id
        SET NOT NULL
        """
    )

    print(
        "agente_config.empresa_id: NOT NULL."
    )


def garantir_fk_agente_config(
    cursor,
) -> None:

    constraint = (
        "fk_agente_config_empresa"
    )

    if constraint_existe(
        cursor,
        "agente_config",
        constraint,
    ):
        print(
            "FK agente_config -> empresas "
            "ja existe."
        )

        return

    cursor.execute(
        """
        ALTER TABLE agente_config
        ADD CONSTRAINT fk_agente_config_empresa
        FOREIGN KEY (empresa_id)
        REFERENCES empresas(id)
        ON DELETE RESTRICT
        """
    )

    print(
        "FK agente_config -> empresas criada."
    )


def garantir_unicidade_agente(
    cursor,
) -> None:

    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS
            uq_agente_config_empresa_id
        ON agente_config (empresa_id)
        """
    )

    print(
        "Unicidade de agente_config "
        "por empresa verificada."
    )


def exibir_resumo(
    cursor,
) -> None:

    print("")
    print(
        "Resumo da compatibilidade multiempresa:"
    )

    cursor.execute(
        """
        SELECT
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'empresas'
          AND column_name IN (
              'nome_agente',
              'whatsapp',
              'instagram',
              'facebook',
              'crm',
              'funil',
              'analytics',
              'vendas_ia'
          )
        ORDER BY column_name
        """
    )

    print("")
    print(
        "Campos adicionados/validados em empresas:"
    )

    for (
        coluna,
        tipo,
        nullable,
        default,
    ) in cursor.fetchall():

        print(
            f"- {coluna}: "
            f"{tipo}, "
            f"nullable={nullable}, "
            f"default={default}"
        )

    cursor.execute(
        """
        SELECT
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'agente_config'
        ORDER BY ordinal_position
        """
    )

    print("")
    print(
        "Estrutura agente_config:"
    )

    for (
        coluna,
        tipo,
        nullable,
        default,
    ) in cursor.fetchall():

        print(
            f"- {coluna}: "
            f"{tipo}, "
            f"nullable={nullable}, "
            f"default={default}"
        )


def main() -> None:

    conn = conectar()

    try:

        with conn.cursor() as cursor:

            validar_empresas(
                cursor
            )

            atualizar_tabela_empresas(
                cursor
            )

            criar_agente_config(
                cursor
            )

            garantir_colunas_agente_config(
                cursor
            )

            validar_empresa_id_agente(
                cursor
            )

            garantir_fk_agente_config(
                cursor
            )

            garantir_unicidade_agente(
                cursor
            )

            exibir_resumo(
                cursor
            )

        conn.commit()

        print("")
        print(
            "Migracao de compatibilidade "
            "multiempresa concluida com sucesso."
        )

    except Exception:

        conn.rollback()

        print("")
        print(
            "ERRO: migracao revertida. "
            "Nenhuma alteracao parcial foi mantida."
        )

        raise

    finally:

        conn.close()


if __name__ == "__main__":
    main()