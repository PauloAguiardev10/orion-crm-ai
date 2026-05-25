from database.db import conectar

import pandas as pd


PLANOS = [
    "Lite",
    "Pro",
    "Premium"
]


def criar_tabela_empresas():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS empresas (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            nome TEXT UNIQUE NOT NULL,

            plano TEXT DEFAULT 'Lite',

            nicho TEXT,

            nome_agente TEXT DEFAULT 'Sofia',

            status TEXT DEFAULT 'ativa',

            whatsapp BOOLEAN DEFAULT 1,

            instagram BOOLEAN DEFAULT 0,

            facebook BOOLEAN DEFAULT 0,

            crm BOOLEAN DEFAULT 0,

            funil BOOLEAN DEFAULT 0,

            analytics BOOLEAN DEFAULT 0,

            vendas_ia BOOLEAN DEFAULT 0,

            criado_em TEXT DEFAULT CURRENT_TIMESTAMP

        )
    """)

    conn.commit()
    conn.close()


def listar_empresas():

    criar_tabela_empresas()

    conn = conectar()

    empresas = pd.read_sql_query("""
        SELECT *
        FROM empresas
        ORDER BY id DESC
    """, conn)

    conn.close()

    return empresas


def criar_empresa(
    nome,
    plano,
    nicho,
    nome_agente
):

    conn = conectar()
    cursor = conn.cursor()

    # =========================
    # MÓDULOS AUTOMÁTICOS
    # =========================

    whatsapp = True

    instagram = False
    facebook = False

    crm = False
    funil = False
    analytics = False

    vendas_ia = False

    # =========================
    # PRO
    # =========================

    if plano in ["Pro", "Premium"]:

        crm = True
        funil = True
        analytics = True

    # =========================
    # PREMIUM
    # =========================

    if plano == "Premium":

        instagram = True
        facebook = True

        vendas_ia = True

    cursor.execute("""
        INSERT INTO empresas (

            nome,
            plano,
            nicho,
            nome_agente,

            whatsapp,
            instagram,
            facebook,

            crm,
            funil,
            analytics,

            vendas_ia

        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (

        nome,
        plano,
        nicho,
        nome_agente,

        whatsapp,
        instagram,
        facebook,

        crm,
        funil,
        analytics,

        vendas_ia

    ))

    conn.commit()
    conn.close()