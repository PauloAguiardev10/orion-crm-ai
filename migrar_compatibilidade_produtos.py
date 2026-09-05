from dashboard.database.db import conectar


COLUNAS_PRODUTO = {
    "categoria": {
        "tipo": "VARCHAR(100)",
        "default": None,
    },
    "preco": {
        "tipo": "NUMERIC(10, 2)",
        "default": "0",
    },
    "ativo": {
        "tipo": "BOOLEAN",
        "default": "TRUE",
    },
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


def validar_tabela_produtos(
    cursor,
) -> None:

    if not tabela_existe(
        cursor,
        "produtos",
    ):
        raise RuntimeError(
            "Tabela produtos nao encontrada."
        )

    print(
        "Tabela produtos encontrada."
    )


def adicionar_colunas_compatibilidade(
    cursor,
) -> None:

    for coluna, configuracao in (
        COLUNAS_PRODUTO.items()
    ):

        if coluna_existe(
            cursor,
            "produtos",
            coluna,
        ):
            print(
                f"produtos.{coluna}: ja existe."
            )
            continue

        tipo = configuracao[
            "tipo"
        ]

        default = configuracao[
            "default"
        ]

        sql = (
            f"ALTER TABLE produtos "
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
            f"produtos.{coluna}: criada."
        )


def migrar_preco_legado(
    cursor,
) -> None:

    if not coluna_existe(
        cursor,
        "produtos",
        "preco_base",
    ):
        print(
            "produtos.preco_base: ausente; "
            "nenhum backfill necessario."
        )
        return

    cursor.execute(
        """
        UPDATE produtos
        SET preco = preco_base
        WHERE preco_base IS NOT NULL
          AND (
              preco IS NULL
              OR preco = 0
          )
        """
    )

    print(
        "Backfill preco <- preco_base: "
        f"{cursor.rowcount} registro(s)."
    )


def migrar_status_legado(
    cursor,
) -> None:

    if not coluna_existe(
        cursor,
        "produtos",
        "status",
    ):
        print(
            "produtos.status: ausente; "
            "nenhum backfill necessario."
        )
        return

    cursor.execute(
        """
        UPDATE produtos
        SET ativo = CASE
            WHEN LOWER(
                COALESCE(
                    status,
                    ''
                )
            ) IN (
                'ativo',
                'active',
                'true',
                '1',
                'sim'
            )
            THEN TRUE
            ELSE FALSE
        END
        WHERE status IS NOT NULL
        """
    )

    print(
        "Backfill ativo <- status: "
        f"{cursor.rowcount} registro(s)."
    )


def validar_resultado(
    cursor,
) -> None:

    faltantes = []

    for coluna in (
        COLUNAS_PRODUTO
    ):

        if not coluna_existe(
            cursor,
            "produtos",
            coluna,
        ):
            faltantes.append(
                coluna
            )

    if faltantes:
        raise RuntimeError(
            "Colunas ainda ausentes em produtos: "
            + ", ".join(
                faltantes
            )
        )

    print(
        "Todas as colunas exigidas "
        "pelo ORM Produto existem."
    )


def exibir_resumo(
    cursor,
) -> None:

    cursor.execute(
        """
        SELECT
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'produtos'
        ORDER BY ordinal_position
        """
    )

    print("")
    print(
        "Estrutura final da tabela produtos:"
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

            validar_tabela_produtos(
                cursor
            )

            adicionar_colunas_compatibilidade(
                cursor
            )

            migrar_preco_legado(
                cursor
            )

            migrar_status_legado(
                cursor
            )

            validar_resultado(
                cursor
            )

            exibir_resumo(
                cursor
            )

        conn.commit()

        print("")
        print(
            "Migracao de compatibilidade "
            "de produtos concluida com sucesso."
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