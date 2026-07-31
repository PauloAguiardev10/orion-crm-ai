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

    try:
        with conn.cursor() as cursor:

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS produtos (

                    id SERIAL PRIMARY KEY,

                    empresa_id INTEGER DEFAULT 1,

                    nome VARCHAR(255),

                    categoria VARCHAR(100),

                    descricao TEXT,

                    preco NUMERIC(10,2) DEFAULT 0,

                    ativo BOOLEAN DEFAULT TRUE,

                    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP

                )
            """)

        conn.commit()

    finally:
        conn.close()


def listar_produtos(empresa_id=1):

    criar_tabela_produtos()

    conn = conectar()

    try:
        produtos = pd.read_sql_query("""
            SELECT *
            FROM produtos
            WHERE empresa_id = %s
            ORDER BY id DESC
        """, conn, params=(empresa_id,))

        return produtos

    finally:
        conn.close()


def carregar_produtos(empresa_id=1):
    return listar_produtos(empresa_id)


def cadastrar_produto(
    empresa_id,
    nome,
    categoria,
    descricao,
    preco,
    ativo=True
):

    criar_tabela_produtos()

    conn = conectar()

    try:
        with conn.cursor() as cursor:

            cursor.execute("""
                INSERT INTO produtos (

                    empresa_id,
                    nome,
                    categoria,
                    descricao,
                    preco,
                    ativo

                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (

                empresa_id,
                nome,
                categoria,
                descricao,
                preco,
                ativo

            ))

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def atualizar_produto(
    produto_id,
    nome,
    categoria,
    descricao,
    preco,
    ativo=True
):

    criar_tabela_produtos()

    conn = conectar()

    try:
        with conn.cursor() as cursor:

            cursor.execute("""
                UPDATE produtos

                SET

                    nome = %s,
                    categoria = %s,
                    descricao = %s,
                    preco = %s,
                    ativo = %s

                WHERE id = %s
            """, (

                nome,
                categoria,
                descricao,
                preco,
                ativo,
                int(produto_id)

            ))

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def excluir_produto(produto_id):

    criar_tabela_produtos()

    conn = conectar()

    try:
        with conn.cursor() as cursor:

            cursor.execute("""
                DELETE FROM produtos
                WHERE id = %s
            """, (
                int(produto_id),
            ))

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()