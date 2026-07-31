import pandas as pd

from database.db import conectar


PLANOS = [
    "Lite",
    "Pro",
    "Premium"
]


def criar_tabela_empresas():
    conn = conectar()

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS empresas (

                    id SERIAL PRIMARY KEY,

                    nome VARCHAR(255) UNIQUE NOT NULL,

                    plano VARCHAR(50) DEFAULT 'Lite',

                    nicho VARCHAR(255),

                    nome_agente VARCHAR(100) DEFAULT 'Sofia',

                    status VARCHAR(30) DEFAULT 'ativa',

                    whatsapp BOOLEAN DEFAULT TRUE,

                    instagram BOOLEAN DEFAULT FALSE,

                    facebook BOOLEAN DEFAULT FALSE,

                    crm BOOLEAN DEFAULT FALSE,

                    funil BOOLEAN DEFAULT FALSE,

                    analytics BOOLEAN DEFAULT FALSE,

                    vendas_ia BOOLEAN DEFAULT FALSE,

                    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP

                )
            """)

        conn.commit()

    finally:
        conn.close()


def listar_empresas():

    criar_tabela_empresas()

    conn = conectar()

    try:
        empresas = pd.read_sql_query("""
            SELECT *
            FROM empresas
            ORDER BY id DESC
        """, conn)

        return empresas

    finally:
        conn.close()


def criar_empresa(
    nome,
    plano,
    nicho,
    nome_agente
):

    criar_tabela_empresas()

    whatsapp = True

    instagram = False
    facebook = False

    crm = False
    funil = False
    analytics = False

    vendas_ia = False

    if plano in ["Pro", "Premium"]:
        crm = True
        funil = True
        analytics = True

    if plano == "Premium":
        instagram = True
        facebook = True
        vendas_ia = True

    conn = conectar()

    try:
        with conn.cursor() as cursor:

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
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()