from database.db import conectar

import pandas as pd


def criar_tabelas_modulos():

    conn = conectar()

    cursor = conn.cursor()

    # =========================================
    # MODULOS DISPONIVEIS
    # =========================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS modulos (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            nome TEXT UNIQUE,

            valor REAL DEFAULT 0

        )
    """)

    # =========================================
    # MODULOS EMPRESA
    # =========================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS empresa_modulos (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            empresa_id INTEGER,

            modulo_id INTEGER

        )
    """)

    conn.commit()

    # =========================================
    # MODULOS PADROES
    # =========================================

    modulos_padrao = [

        ("Instagram Direct", 80),
        ("Facebook Messenger", 80),
        ("IA Vendas", 200),
        ("PIX Automático", 100),
        ("Link de Pagamento", 100),
        ("Relatórios Avançados", 150),
        ("Multi IA", 200)

    ]

    for nome, valor in modulos_padrao:

        cursor.execute("""
            INSERT OR IGNORE INTO modulos (
                nome,
                valor
            )
            VALUES (?, ?)
        """, (
            nome,
            valor
        ))

    conn.commit()

    conn.close()


def listar_modulos():

    criar_tabelas_modulos()

    conn = conectar()

    modulos = pd.read_sql_query("""
        SELECT *
        FROM modulos
        ORDER BY nome
    """, conn)

    conn.close()

    return modulos


def listar_modulos_empresa(
    empresa_id
):

    criar_tabelas_modulos()

    conn = conectar()

    modulos = pd.read_sql_query("""
        SELECT
            modulos.id,
            modulos.nome,
            modulos.valor

        FROM empresa_modulos

        LEFT JOIN modulos
            ON modulos.id = empresa_modulos.modulo_id

        WHERE empresa_modulos.empresa_id = ?
    """, conn, params=(empresa_id,))

    conn.close()

    return modulos


def salvar_modulos_empresa(
    empresa_id,
    modulos_ids
):

    conn = conectar()

    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM empresa_modulos
        WHERE empresa_id = ?
    """, (
        empresa_id,
    ))

    for modulo_id in modulos_ids:

        cursor.execute("""
            INSERT INTO empresa_modulos (

                empresa_id,
                modulo_id

            )
            VALUES (?, ?)
        """, (
            empresa_id,
            modulo_id
        ))

    conn.commit()

    conn.close()