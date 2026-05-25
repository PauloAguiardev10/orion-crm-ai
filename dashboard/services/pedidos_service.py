import pandas as pd

from database.db import conectar


STATUS_PAGAMENTO = [
    "Aguardando pagamento",
    "Aguardando confirmação",
    "Pagamento confirmado",
    "Pagamento recusado",
]


STATUS_PEDIDO = [
    "Novo pedido",
    "Em separação",
    "Enviado",
    "Entregue",
    "Cancelado",
]


FORMAS_PAGAMENTO = [
    "PIX",
    "Cartão",
    "Dinheiro",
    "Outro",
]


def garantir_tabela_pedidos():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER DEFAULT 1,
            cliente_nome TEXT,
            cliente_telefone TEXT,
            produto_id INTEGER,
            produto_nome TEXT,
            quantidade INTEGER DEFAULT 1,
            valor_total REAL DEFAULT 0,
            forma_pagamento TEXT,
            status_pagamento TEXT DEFAULT 'Aguardando pagamento',
            status_pedido TEXT DEFAULT 'Novo pedido',
            origem TEXT,
            vendido_por TEXT DEFAULT 'IA',
            observacoes TEXT,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def listar_pedidos(empresa_id):
    garantir_tabela_pedidos()

    conn = conectar()

    pedidos = pd.read_sql_query("""
        SELECT *
        FROM pedidos
        WHERE empresa_id = ?
        ORDER BY id DESC
    """, conn, params=(empresa_id,))

    conn.close()

    return pedidos


def cadastrar_pedido(
    empresa_id,
    cliente_nome,
    cliente_telefone,
    produto_id,
    produto_nome,
    quantidade,
    valor_total,
    forma_pagamento,
    status_pagamento,
    status_pedido,
    origem,
    vendido_por,
    observacoes
):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO pedidos (
            empresa_id,
            cliente_nome,
            cliente_telefone,
            produto_id,
            produto_nome,
            quantidade,
            valor_total,
            forma_pagamento,
            status_pagamento,
            status_pedido,
            origem,
            vendido_por,
            observacoes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        empresa_id,
        cliente_nome.strip(),
        cliente_telefone.strip(),
        int(produto_id) if produto_id else None,
        produto_nome.strip(),
        int(quantidade),
        float(valor_total),
        forma_pagamento,
        status_pagamento,
        status_pedido,
        origem,
        vendido_por,
        observacoes.strip()
    ))

    conn.commit()
    conn.close()

    return True


def atualizar_pedido(
    pedido_id,
    status_pagamento,
    status_pedido,
    observacoes
):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE pedidos
        SET status_pagamento = ?,
            status_pedido = ?,
            observacoes = ?
        WHERE id = ?
    """, (
        status_pagamento,
        status_pedido,
        observacoes.strip(),
        int(pedido_id)
    ))

    conn.commit()
    conn.close()

    return True


def excluir_pedido(pedido_id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM pedidos
        WHERE id = ?
    """, (int(pedido_id),))

    conn.commit()
    conn.close()

    return True