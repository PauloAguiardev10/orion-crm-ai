from dashboard.database.db import conectar


TABELAS_EMPRESA = (
    "agente_config",
    "produtos",
    "servicos",
    "especialistas",
    "especialista_servicos",
)


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


def constraint_existe(cursor, tabela: str, constraint: str) -> bool:
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
        (tabela, constraint),
    )
    return bool(cursor.fetchone()[0])


def validar_tabelas(cursor) -> None:
    faltando = [
        tabela
        for tabela in ("empresas", *TABELAS_EMPRESA)
        if not tabela_existe(cursor, tabela)
    ]

    if faltando:
        raise RuntimeError(
            "Tabelas obrigatorias nao encontradas: "
            + ", ".join(faltando)
        )


def validar_empresa_ids(cursor) -> None:
    for tabela in TABELAS_EMPRESA:
        cursor.execute(
            f"""
            SELECT COUNT(*)
            FROM {tabela}
            WHERE empresa_id IS NULL
            """
        )

        sem_empresa = cursor.fetchone()[0]

        if sem_empresa:
            raise RuntimeError(
                f"{tabela}: existem {sem_empresa} registro(s) "
                "com empresa_id NULL."
            )

        cursor.execute(
            f"""
            SELECT COUNT(*)
            FROM {tabela} t
            WHERE NOT EXISTS (
                SELECT 1
                FROM empresas e
                WHERE e.id = t.empresa_id
            )
            """
        )

        orfaos = cursor.fetchone()[0]

        if orfaos:
            raise RuntimeError(
                f"{tabela}: existem {orfaos} registro(s) "
                "referenciando empresa inexistente."
            )

    print("Integridade de empresa_id validada.")


def remover_defaults_empresa_id(cursor) -> None:
    for tabela in TABELAS_EMPRESA:
        cursor.execute(
            f"""
            ALTER TABLE {tabela}
            ALTER COLUMN empresa_id DROP DEFAULT
            """
        )

    print("Defaults de empresa_id removidos.")


def tornar_empresa_id_obrigatorio(cursor) -> None:
    for tabela in TABELAS_EMPRESA:
        cursor.execute(
            f"""
            ALTER TABLE {tabela}
            ALTER COLUMN empresa_id SET NOT NULL
            """
        )

    print("empresa_id definido como NOT NULL.")


def criar_fk_empresa(
    cursor,
    tabela: str,
    constraint: str,
) -> None:
    if constraint_existe(cursor, tabela, constraint):
        return

    cursor.execute(
        f"""
        ALTER TABLE {tabela}
        ADD CONSTRAINT {constraint}
        FOREIGN KEY (empresa_id)
        REFERENCES empresas(id)
        ON DELETE RESTRICT
        """
    )


def criar_fks_empresa(cursor) -> None:
    configuracao = {
        "agente_config": "fk_agente_config_empresa",
        "produtos": "fk_produtos_empresa",
        "servicos": "fk_servicos_empresa",
        "especialistas": "fk_especialistas_empresa",
        "especialista_servicos": "fk_especialista_servicos_empresa",
    }

    for tabela, constraint in configuracao.items():
        criar_fk_empresa(
            cursor,
            tabela,
            constraint,
        )

    print("Foreign keys para empresas verificadas/criadas.")


def criar_indices_empresa(cursor) -> None:
    for tabela in TABELAS_EMPRESA:
        cursor.execute(
            f"""
            CREATE INDEX IF NOT EXISTS
                ix_{tabela}_empresa_id
            ON {tabela} (empresa_id)
            """
        )

    print("Indices de empresa_id verificados/criados.")


def criar_protecao_especialistas(cursor) -> None:
    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS
            uq_especialistas_empresa_id_id
        ON especialistas (empresa_id, id)
        """
    )

    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS
            uq_servicos_empresa_id_id
        ON servicos (empresa_id, id)
        """
    )

    if not constraint_existe(
        cursor,
        "especialista_servicos",
        "fk_especialista_servicos_especialista_empresa",
    ):
        cursor.execute(
            """
            ALTER TABLE especialista_servicos
            ADD CONSTRAINT
                fk_especialista_servicos_especialista_empresa
            FOREIGN KEY (empresa_id, especialista_id)
            REFERENCES especialistas (empresa_id, id)
            ON DELETE RESTRICT
            """
        )

    if not constraint_existe(
        cursor,
        "especialista_servicos",
        "fk_especialista_servicos_servico_empresa",
    ):
        cursor.execute(
            """
            ALTER TABLE especialista_servicos
            ADD CONSTRAINT
                fk_especialista_servicos_servico_empresa
            FOREIGN KEY (empresa_id, servico_id)
            REFERENCES servicos (empresa_id, id)
            ON DELETE RESTRICT
            """
        )

    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS
            uq_especialista_servicos_empresa_especialista_servico
        ON especialista_servicos (
            empresa_id,
            especialista_id,
            servico_id
        )
        """
    )

    print(
        "Protecao contra relacionamentos entre empresas "
        "diferentes verificada/criada."
    )


def exibir_resumo(cursor) -> None:
    print("")
    print("Resumo da integridade multiempresa:")

    for tabela in TABELAS_EMPRESA:
        cursor.execute(
            """
            SELECT
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = %s
              AND column_name = 'empresa_id'
            """,
            (tabela,),
        )

        nullable, default = cursor.fetchone()

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM pg_indexes
            WHERE schemaname = 'public'
              AND tablename = %s
              AND indexdef ILIKE '%%empresa_id%%'
            """,
            (tabela,),
        )

        indices = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.table_constraints
            WHERE table_schema = 'public'
              AND table_name = %s
              AND constraint_type = 'FOREIGN KEY'
            """,
            (tabela,),
        )

        fks = cursor.fetchone()[0]

        print(
            f"- {tabela}: "
            f"nullable={nullable}, "
            f"default={default}, "
            f"indices_empresa={indices}, "
            f"foreign_keys={fks}"
        )


def main() -> None:
    conn = conectar()

    try:
        with conn.cursor() as cursor:
            validar_tabelas(cursor)
            validar_empresa_ids(cursor)

            remover_defaults_empresa_id(cursor)
            tornar_empresa_id_obrigatorio(cursor)

            criar_fks_empresa(cursor)
            criar_indices_empresa(cursor)

            criar_protecao_especialistas(cursor)

            exibir_resumo(cursor)

        conn.commit()

        print("")
        print(
            "Migracao de integridade multiempresa "
            "concluida com sucesso."
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