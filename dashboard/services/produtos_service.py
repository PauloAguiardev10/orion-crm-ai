import pandas as pd

from database.db import conectar


CATEGORIAS_PRODUTOS = [
    "Serviço",
    "Produto",
    "Plano",
    "Marketing",
    "Automação",
    "Website"
]


def criar_tabela_produtos():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            empresa_id INTEGER DEFAULT 1,

            nome TEXT,

            categoria TEXT,

            descricao TEXT,

            preco REAL DEFAULT 0,

            ativo INTEGER DEFAULT 1,

            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def listar_produtos(empresa_id=1):

    criar_tabela_produtos()

    conn = conectar()

    produtos = pd.read_sql_query("""
        SELECT *
        FROM produtos
        WHERE empresa_id = ?
        ORDER BY id DESC
    """, conn, params=(empresa_id,))

    conn.close()

    return produtos


def carregar_produtos(empresa_id=1):
    return listar_produtos(empresa_id)


def cadastrar_produto(
    empresa_id,
    nome,
    categoria,
    descricao,
    preco,
    ativo=1
):

    criar_tabela_produtos()

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO produtos (

            empresa_id,
            nome,
            categoria,
            descricao,
            preco,
            ativo

        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (

        empresa_id,
        nome,
        categoria,
        descricao,
        preco,
        ativo
    ))

    conn.commit()
    conn.close()


def atualizar_produto(
    produto_id,
    nome,
    categoria,
    descricao,
    preco,
    ativo=1
):

    criar_tabela_produtos()

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE produtos

        SET

            nome = ?,
            categoria = ?,
            descricao = ?,
            preco = ?,
            ativo = ?

        WHERE id = ?
    """, (

        nome,
        categoria,
        descricao,
        preco,
        ativo,
        int(produto_id)
    ))

    conn.commit()
    conn.close()


def excluir_produto(produto_id):

    criar_tabela_produtos()

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM produtos
        WHERE id = ?
    """, (
        int(produto_id),
    ))

    conn.commit()
    conn.close()