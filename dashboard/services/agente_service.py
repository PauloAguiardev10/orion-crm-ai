from database.db import conectar

import pandas as pd


def criar_tabela_agente():

    conn = conectar()

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agente_config (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            empresa_id INTEGER UNIQUE,

            nome_agente TEXT DEFAULT 'Sofia',

            tom TEXT DEFAULT 'Humanizado',

            nicho TEXT,

            objetivo TEXT,

            ia_pode_vender BOOLEAN DEFAULT 0,

            ia_envia_pix BOOLEAN DEFAULT 0,

            ia_envia_link BOOLEAN DEFAULT 0,

            whatsapp BOOLEAN DEFAULT 1,

            instagram BOOLEAN DEFAULT 0,

            facebook BOOLEAN DEFAULT 0

        )
    """)

    conn.commit()

    conn.close()


def carregar_config_agente(
    empresa_id
):

    criar_tabela_agente()

    conn = conectar()

    config = pd.read_sql_query("""
        SELECT *
        FROM agente_config
        WHERE empresa_id = ?
    """, conn, params=(empresa_id,))

    conn.close()

    if config.empty:

        criar_config_padrao(
            empresa_id
        )

        return carregar_config_agente(
            empresa_id
        )

    return config.iloc[0]


def criar_config_padrao(
    empresa_id
):

    conn = conectar()

    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO agente_config (

            empresa_id

        )
        VALUES (?)
    """, (
        empresa_id,
    ))

    conn.commit()

    conn.close()


def salvar_config_agente(

    empresa_id,

    nome_agente,

    tom,

    nicho,

    objetivo,

    ia_pode_vender,

    ia_envia_pix,

    ia_envia_link,

    whatsapp,

    instagram,

    facebook
):

    conn = conectar()

    cursor = conn.cursor()

    cursor.execute("""
        UPDATE agente_config

        SET

            nome_agente = ?,

            tom = ?,

            nicho = ?,

            objetivo = ?,

            ia_pode_vender = ?,

            ia_envia_pix = ?,

            ia_envia_link = ?,

            whatsapp = ?,

            instagram = ?,

            facebook = ?

        WHERE empresa_id = ?
    """, (

        nome_agente,

        tom,

        nicho,

        objetivo,

        ia_pode_vender,

        ia_envia_pix,

        ia_envia_link,

        whatsapp,

        instagram,

        facebook,

        empresa_id
    ))

    conn.commit()

    conn.close()