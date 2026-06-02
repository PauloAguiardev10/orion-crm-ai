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
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pedidos (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            empresa_id INTEGER DEFAULT 1,

            cliente TEXT,

            produto TEXT,

            quantidade INTEGER DEFAULT 1,

            valor_total REAL DEFAULT 0,

            status TEXT DEFAULT 'Pendente',

            status_pagamento TEXT DEFAULT 'Pendente',

            forma_pagamento TEXT DEFAULT 'Pix',

            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("PRAGMA table_info(pedidos)")
    colunas = [col[1] for col in cursor.fetchall()]

    if "status_pagamento" not in colunas:
        cursor.execute("""
            ALTER TABLE pedidos
            ADD COLUMN status_pagamento TEXT DEFAULT 'Pendente'
        """)

    if "forma_pagamento" not in colunas:
        cursor.execute("""
            ALTER TABLE pedidos
            ADD COLUMN forma_pagamento TEXT DEFAULT 'Pix'
        """)

    if "status" not in colunas:
        cursor.execute("""
            ALTER TABLE pedidos
            ADD COLUMN status TEXT DEFAULT 'Pendente'
        """)

    conn.commit()
    conn.close()


def listar_pedidos(empresa_id=1):

    criar_tabela_pedidos()

    conn = conectar()

    pedidos = pd.read_sql_query("""
        SELECT *
        FROM pedidos
        WHERE empresa_id = ?
        ORDER BY id DESC
    """, conn, params=(empresa_id,))

    conn.close()

    return pedidos


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
    cursor = conn.cursor()

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
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE pedidos

        SET

            cliente = ?,
            produto = ?,
            quantidade = ?,
            valor_total = ?,
            status = ?,
            status_pagamento = ?,
            forma_pagamento = ?

        WHERE id = ?
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
    conn.close()


def excluir_pedido(pedido_id):

    criar_tabela_pedidos()

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM pedidos
        WHERE id = ?
    """, (
        int(pedido_id),
    ))

    conn.commit()
    conn.close()