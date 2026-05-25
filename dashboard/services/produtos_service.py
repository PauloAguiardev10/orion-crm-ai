import pandas as pd

from database.db import conectar


def garantir_tabela_produtos():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER DEFAULT 1,
            nome TEXT NOT NULL,
            categoria TEXT,
            descricao TEXT,
            preco REAL DEFAULT 0,
            estoque INTEGER DEFAULT 0,
            imagem_url TEXT,
            status TEXT DEFAULT 'ativo',
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def listar_produtos(empresa_id):
    garantir_tabela_produtos()

    conn = conectar()

    produtos = pd.read_sql_query("""
        SELECT *
        FROM produtos
        WHERE empresa_id = ?
        ORDER BY id DESC
    """, conn, params=(empresa_id,))

    conn.close()

    return produtos


def cadastrar_produto(
    empresa_id,
    nome,
    categoria,
    descricao,
    preco,
    estoque,
    imagem_url,
    status
):
    if not nome.strip():
        return False

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO produtos (
            empresa_id,
            nome,
            categoria,
            descricao,
            preco,
            estoque,
            imagem_url,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        empresa_id,
        nome.strip(),
        categoria.strip(),
        descricao.strip(),
        float(preco),
        int(estoque),
        imagem_url.strip(),
        status
    ))

    conn.commit()
    conn.close()

    return True


def atualizar_produto(
    produto_id,
    nome,
    categoria,
    descricao,
    preco,
    estoque,
    imagem_url,
    status
):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE produtos
        SET nome = ?,
            categoria = ?,
            descricao = ?,
            preco = ?,
            estoque = ?,
            imagem_url = ?,
            status = ?
        WHERE id = ?
    """, (
        nome.strip(),
        categoria.strip(),
        descricao.strip(),
        float(preco),
        int(estoque),
        imagem_url.strip(),
        status,
        int(produto_id)
    ))

    conn.commit()
    conn.close()

    return True


def excluir_produto(produto_id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM produtos
        WHERE id = ?
    """, (int(produto_id),))

    conn.commit()
    conn.close()

    return True