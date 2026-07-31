import pandas as pd

from database.db import conectar


def criar_tabelas_modulos():
    conn = conectar()

    try:
        with conn.cursor() as cursor:

            # =========================================
            # MÓDULOS DISPONÍVEIS
            # =========================================

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS modulos (

                    id SERIAL PRIMARY KEY,

                    nome VARCHAR(150) UNIQUE,

                    valor NUMERIC(10,2) DEFAULT 0

                )
            """)

            # =========================================
            # MÓDULOS DA EMPRESA
            # =========================================

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS empresa_modulos (

                    id SERIAL PRIMARY KEY,

                    empresa_id INTEGER NOT NULL,

                    modulo_id INTEGER NOT NULL

                )
            """)

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
                    INSERT INTO modulos (
                        nome,
                        valor
                    )
                    VALUES (%s, %s)
                    ON CONFLICT (nome) DO NOTHING
                """, (
                    nome,
                    valor
                ))

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def listar_modulos():

    criar_tabelas_modulos()

    conn = conectar()

    try:
        modulos = pd.read_sql_query("""
            SELECT *
            FROM modulos
            ORDER BY nome
        """, conn)

        return modulos

    finally:
        conn.close()


def listar_modulos_empresa(
    empresa_id
):

    criar_tabelas_modulos()

    conn = conectar()

    try:
        modulos = pd.read_sql_query("""
            SELECT
                modulos.id,
                modulos.nome,
                modulos.valor

            FROM empresa_modulos

            LEFT JOIN modulos
                ON modulos.id = empresa_modulos.modulo_id

            WHERE empresa_modulos.empresa_id = %s
        """, conn, params=(empresa_id,))

        return modulos

    finally:
        conn.close()


def salvar_modulos_empresa(
    empresa_id,
    modulos_ids
):

    conn = conectar()

    try:
        with conn.cursor() as cursor:

            cursor.execute("""
                DELETE FROM empresa_modulos
                WHERE empresa_id = %s
            """, (
                empresa_id,
            ))

            for modulo_id in modulos_ids:

                cursor.execute("""
                    INSERT INTO empresa_modulos (

                        empresa_id,
                        modulo_id

                    )
                    VALUES (%s, %s)
                """, (
                    empresa_id,
                    modulo_id
                ))

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()