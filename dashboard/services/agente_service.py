import pandas as pd

from database.db import conectar


def criar_tabela_agente():

    conn = conectar()

    try:

        with conn.cursor() as cursor:

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agente_config (

                    id SERIAL PRIMARY KEY,

                    empresa_id INTEGER UNIQUE,

                    nome_agente VARCHAR(100) DEFAULT 'Sofia',

                    tom VARCHAR(100) DEFAULT 'Humanizado',

                    nicho TEXT,

                    objetivo TEXT,

                    ia_pode_vender BOOLEAN DEFAULT FALSE,

                    ia_envia_pix BOOLEAN DEFAULT FALSE,

                    ia_envia_link BOOLEAN DEFAULT FALSE,

                    whatsapp BOOLEAN DEFAULT TRUE,

                    instagram BOOLEAN DEFAULT FALSE,

                    facebook BOOLEAN DEFAULT FALSE

                )
            """)

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def carregar_config_agente(
    empresa_id
):

    criar_tabela_agente()

    conn = conectar()

    try:

        config = pd.read_sql_query("""
            SELECT *
            FROM agente_config
            WHERE empresa_id = %s
        """, conn, params=(empresa_id,))

    finally:
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

    try:

        with conn.cursor() as cursor:

            cursor.execute("""
                INSERT INTO agente_config (

                    empresa_id

                )
                VALUES (%s)
            """, (
                empresa_id,
            ))

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
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

    try:

        with conn.cursor() as cursor:

            cursor.execute("""
                UPDATE agente_config

                SET

                    nome_agente = %s,

                    tom = %s,

                    nicho = %s,

                    objetivo = %s,

                    ia_pode_vender = %s,

                    ia_envia_pix = %s,

                    ia_envia_link = %s,

                    whatsapp = %s,

                    instagram = %s,

                    facebook = %s

                WHERE empresa_id = %s
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

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()