from sqlalchemy import inspect, text

from backend.app.database.database import engine


def coluna_existe(inspector, tabela, coluna):
    return any(
        item["name"] == coluna
        for item in inspector.get_columns(tabela)
    )


def migrar():
    inspector = inspect(engine)

    if "servicos" not in inspector.get_table_names():
        raise RuntimeError(
            "Tabela servicos nao encontrada."
        )

    alteracoes = []

    if not coluna_existe(
        inspector,
        "servicos",
        "descricao",
    ):
        alteracoes.append(
            """
            ALTER TABLE servicos
            ADD COLUMN descricao TEXT
            """
        )

    if not coluna_existe(
        inspector,
        "servicos",
        "palavras_chave",
    ):
        alteracoes.append(
            """
            ALTER TABLE servicos
            ADD COLUMN palavras_chave TEXT
            """
        )

    if not coluna_existe(
        inspector,
        "servicos",
        "ativo",
    ):
        alteracoes.append(
            """
            ALTER TABLE servicos
            ADD COLUMN ativo BOOLEAN
            NOT NULL
            DEFAULT TRUE
            """
        )

    if not alteracoes:
        print(
            "OK - estrutura de servicos "
            "ja esta atualizada."
        )
        return

    with engine.begin() as conexao:
        for comando in alteracoes:
            conexao.execute(
                text(comando)
            )

    print(
        "OK - catalogo de servicos "
        "atualizado."
    )


if __name__ == "__main__":
    migrar()
