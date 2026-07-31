import pandas as pd

from database.db import conectar


STATUS_PAGAMENTO = [
    "Pendente",
    "Pago",
    "Atrasado",
    "Cancelado"
]


STATUS_PEDIDO = [
    "Pendente",
    "Em andamento",
    "Concluído",
    "Cancelado"
]


FORMAS_PAGAMENTO = [
    "Pix",
    "Cartão",
    "Boleto",
    "Dinheiro",
    "Transferência"
]


def criar_tabela_pedidos():

    conn = conectar()

    try:

        with conn.cursor() as cursor:

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pedidos (

                    id SERIAL PRIMARY KEY,

                    empresa_id INTEGER DEFAULT 1,

                    cliente VARCHAR(255),

                    produto VARCHAR(255),

                    quantidade INTEGER DEFAULT 1,

                    valor_total NUMERIC(10,2) DEFAULT 0,

                    status VARCHAR(50) DEFAULT 'Pendente',

                    status_pagamento VARCHAR(50) DEFAULT 'Pendente',

                    forma_pagamento VARCHAR(50) DEFAULT 'Pix',

                    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP

                )
            """)

        conn.commit()

    finally:
        conn.close()


def listar_pedidos(empresa_id=1):

    criar_tabela_pedidos()

    conn = conectar()

    try:

        pedidos = pd.read_sql_query("""
            SELECT *
            FROM pedidos
            WHERE empresa_id = %s
            ORDER BY id DESC
        """, conn, params=(empresa_id,))

        return pedidos

    finally:
        conn.close()


def carregar_pedidos(empresa_id=1):
    return listar_pedidos(empresa_id)


def cadastrar_pedido(
    empresa_id,
    cliente,
    produto,
    quantidade,
    valor_total,
    status="Pendente",
    status_pagamento="Pendente",
    forma_pagamento="Pix"
):

    criar_tabela_pedidos()

    conn = conectar()

    try:

        with conn.cursor() as cursor:

            cursor.execute("""
                INSERT INTO pedidos (

                    empresa_id,
                    cliente,
                    produto,
                    quantidade,
                    valor_total,
                    status,
                    status_pagamento,
                    forma_pagamento

                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (

                empresa_id,
                cliente,
                produto,
                quantidade,
                valor_total,
                status,
                status_pagamento,
                forma_pagamento

            ))

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def salvar_pedido(
    empresa_id,
    cliente,
    produto,
    quantidade,
    valor_total,
    status="Pendente",
    status_pagamento="Pendente",
    forma_pagamento="Pix"
):

    cadastrar_pedido(
        empresa_id,
        cliente,
        produto,
        quantidade,
        valor_total,
        status,
        status_pagamento,
        forma_pagamento
    )


def atualizar_pedido(
    pedido_id,
    cliente,
    produto,
    quantidade,
    valor_total,
    status,
    status_pagamento="Pendente",
    forma_pagamento="Pix"
):

    criar_tabela_pedidos()

    conn = conectar()

    try:

        with conn.cursor() as cursor:

            cursor.execute("""
                UPDATE pedidos

                SET

                    cliente = %s,
                    produto = %s,
                    quantidade = %s,
                    valor_total = %s,
                    status = %s,
                    status_pagamento = %s,
                    forma_pagamento = %s

                WHERE id = %s
            """, (

                cliente,
                produto,
                quantidade,
                valor_total,
                status,
                status_pagamento,
                forma_pagamento,
                int(pedido_id)

            ))

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def excluir_pedido(pedido_id):

    criar_tabela_pedidos()

    conn = conectar()

    try:

        with conn.cursor() as cursor:

            cursor.execute("""
                DELETE FROM pedidos
                WHERE id = %s
            """, (
                int(pedido_id),
            ))

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()