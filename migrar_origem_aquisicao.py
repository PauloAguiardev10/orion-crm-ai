from dashboard.database.db import conectar


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


def adicionar_coluna_origem_aquisicao(cursor) -> None:
    tabela = "conversas"
    coluna = "origem_aquisicao"

    if coluna_existe(cursor, tabela, coluna):
        print(f"Coluna já existe: {tabela}.{coluna}")
        return

    cursor.execute(
        """
        ALTER TABLE conversas
        ADD COLUMN origem_aquisicao VARCHAR(80)
        """
    )

    print(f"Coluna criada: {tabela}.{coluna}")


def exibir_resumo(cursor) -> None:
    cursor.execute(
        """
        SELECT data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'conversas'
          AND column_name = 'origem_aquisicao'
        """
    )

    resultado = cursor.fetchone()

    print("")
    print("Resumo da migração:")

    if resultado:
        tipo, tamanho = resultado
        print(
            "- conversas.origem_aquisicao: "
            f"{tipo}, tamanho máximo {tamanho}"
        )
    else:
        print("- conversas.origem_aquisicao: NÃO ENCONTRADA")


def main() -> None:
    conn = conectar()

    try:
        with conn.cursor() as cursor:
            adicionar_coluna_origem_aquisicao(cursor)
            exibir_resumo(cursor)

        conn.commit()

        print("")
        print("Migração de origem de aquisição concluída com sucesso.")

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    main()
