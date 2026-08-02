import pandas as pd

from database.db import conectar


def garantir_tabelas_config():

    conn = conectar()

    try:

        with conn.cursor() as cursor:

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS especialistas (

                    id SERIAL PRIMARY KEY,

                    empresa_id INTEGER DEFAULT 1,

                    nome VARCHAR(255) NOT NULL

                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS servicos (

                    id SERIAL PRIMARY KEY,

                    empresa_id INTEGER DEFAULT 1,

                    nome VARCHAR(255) NOT NULL

                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS especialista_servicos (

                    id SERIAL PRIMARY KEY,

                    empresa_id INTEGER DEFAULT 1,

                    especialista_id INTEGER NOT NULL,

                    servico_id INTEGER NOT NULL

                )
            """)

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def limpar_especialistas_duplicados(empresa_id=1):

    garantir_tabelas_config()

    conn = conectar()

    try:

        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT MIN(nome) AS nome
                FROM especialistas
                WHERE empresa_id = %s
                GROUP BY LOWER(TRIM(nome))
                HAVING COUNT(*) > 1
            """, (
                empresa_id,
            ))

            nomes_duplicados = cursor.fetchall()

            for item in nomes_duplicados:

                nome = item[0]

                cursor.execute("""
                    SELECT id
                    FROM especialistas
                    WHERE empresa_id = %s
                    AND LOWER(TRIM(nome)) = LOWER(TRIM(%s))
                    ORDER BY id ASC
                """, (
                    empresa_id,
                    nome
                ))

                ids = [
                    linha[0]
                    for linha in cursor.fetchall()
                ]

                if not ids:
                    continue

                id_principal = ids[0]
                ids_duplicados = ids[1:]

                for id_duplicado in ids_duplicados:

                    cursor.execute("""
                        UPDATE especialista_servicos

                        SET especialista_id = %s

                        WHERE especialista_id = %s
                        AND empresa_id = %s
                    """, (
                        id_principal,
                        id_duplicado,
                        empresa_id
                    ))

                    cursor.execute("""
                        DELETE FROM especialistas

                        WHERE id = %s
                        AND empresa_id = %s
                    """, (
                        id_duplicado,
                        empresa_id
                    ))

            cursor.execute("""
                DELETE FROM especialista_servicos

                WHERE id NOT IN (

                    SELECT MIN(id)

                    FROM especialista_servicos

                    WHERE empresa_id = %s

                    GROUP BY
                        empresa_id,
                        especialista_id,
                        servico_id

                )

                AND empresa_id = %s
            """, (
                empresa_id,
                empresa_id
            ))

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def carregar_servicos(empresa_id=1):

    garantir_tabelas_config()

    conn = conectar()

    try:

        servicos = pd.read_sql_query("""
            SELECT *
            FROM servicos
            WHERE empresa_id = %s
            ORDER BY id
        """, conn, params=(empresa_id,))

        return servicos

    finally:
        conn.close()


def carregar_especialistas(empresa_id=1):

    garantir_tabelas_config()
    limpar_especialistas_duplicados(empresa_id)

    conn = conectar()

    try:

        especialistas = pd.read_sql_query("""
            SELECT

                especialistas.id,

                especialistas.empresa_id,

                especialistas.nome,

                STRING_AGG(
                    DISTINCT servicos.nome,
                    ', '
                    ORDER BY servicos.nome
                ) AS especialidades

            FROM especialistas

            LEFT JOIN especialista_servicos

                ON especialista_servicos.especialista_id =
                   especialistas.id

                AND especialista_servicos.empresa_id =
                    especialistas.empresa_id

            LEFT JOIN servicos

                ON servicos.id =
                   especialista_servicos.servico_id

                AND servicos.empresa_id =
                    especialistas.empresa_id

            WHERE especialistas.empresa_id = %s

            GROUP BY

                especialistas.id,

                especialistas.empresa_id,

                especialistas.nome

            ORDER BY especialistas.id
        """, conn, params=(empresa_id,))

        return especialistas

    finally:
        conn.close()


def carregar_ids_servicos_especialista(
    nome,
    empresa_id=1
):

    garantir_tabelas_config()

    conn = conectar()

    try:

        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT id
                FROM especialistas

                WHERE empresa_id = %s

                AND LOWER(TRIM(nome)) =
                    LOWER(TRIM(%s))

                ORDER BY id ASC

                LIMIT 1
            """, (
                empresa_id,
                nome.strip()
            ))

            especialista = cursor.fetchone()

            if not especialista:
                return []

            especialista_id = especialista[0]

            cursor.execute("""
                SELECT servico_id
                FROM especialista_servicos

                WHERE empresa_id = %s

                AND especialista_id = %s
            """, (
                empresa_id,
                especialista_id
            ))

            ids = [
                linha[0]
                for linha in cursor.fetchall()
            ]

            return ids

    finally:
        conn.close()
        def cadastrar_servico(nome, empresa_id=1):

            if not nome.strip():
                return False

    garantir_tabelas_config()

    conn = conectar()

    try:

        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT id
                FROM servicos

                WHERE empresa_id = %s

                AND LOWER(TRIM(nome)) =
                    LOWER(TRIM(%s))
            """, (
                empresa_id,
                nome.strip()
            ))

            existente = cursor.fetchone()

            if existente:
                return True

            cursor.execute("""
                INSERT INTO servicos (

                    empresa_id,
                    nome

                )
                VALUES (%s, %s)
            """, (
                empresa_id,
                nome.strip()
            ))

        conn.commit()

        return True

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

def cadastrar_servico(nome, empresa_id=1):

    if not nome or not nome.strip():
        return False

    garantir_tabelas_config()

    conn = conectar()

    try:

        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT id
                FROM servicos

                WHERE empresa_id = %s

                AND LOWER(TRIM(nome)) =
                    LOWER(TRIM(%s))
            """, (
                empresa_id,
                nome.strip()
            ))

            existente = cursor.fetchone()

            if existente:
                return True

            cursor.execute("""
                INSERT INTO servicos (
                    empresa_id,
                    nome
                )
                VALUES (%s, %s)
            """, (
                empresa_id,
                nome.strip()
            ))

        conn.commit()

        return True

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

def cadastrar_especialista(
    nome,
    servicos_ids,
    empresa_id=1
):

    if not nome.strip():
        return False

    garantir_tabelas_config()

    nome = nome.strip()

    conn = conectar()

    try:

        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT id
                FROM especialistas

                WHERE empresa_id = %s

                AND LOWER(TRIM(nome)) =
                    LOWER(TRIM(%s))

                ORDER BY id ASC

                LIMIT 1
            """, (
                empresa_id,
                nome
            ))

            especialista = cursor.fetchone()

            if especialista:

                especialista_id = especialista[0]

                cursor.execute("""
                    UPDATE especialistas

                    SET nome = %s

                    WHERE id = %s

                    AND empresa_id = %s
                """, (
                    nome,
                    especialista_id,
                    empresa_id
                ))

            else:

                cursor.execute("""
                    INSERT INTO especialistas (

                        empresa_id,
                        nome

                    )
                    VALUES (%s, %s)

                    RETURNING id
                """, (
                    empresa_id,
                    nome
                ))

                especialista_id = cursor.fetchone()[0]

            cursor.execute("""
                DELETE FROM especialista_servicos

                WHERE empresa_id = %s

                AND especialista_id = %s
            """, (
                empresa_id,
                especialista_id
            ))

            for servico_id in servicos_ids:

                cursor.execute("""
                    INSERT INTO especialista_servicos (

                        empresa_id,
                        especialista_id,
                        servico_id

                    )
                    VALUES (%s, %s, %s)
                """, (
                    empresa_id,
                    especialista_id,
                    int(servico_id)
                ))

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

    limpar_especialistas_duplicados(empresa_id)

    return True


def excluir_especialista_por_nome(
    nome,
    empresa_id=1
):

    garantir_tabelas_config()

    conn = conectar()

    try:

        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT id
                FROM especialistas

                WHERE empresa_id = %s

                AND LOWER(TRIM(nome)) =
                    LOWER(TRIM(%s))
            """, (
                empresa_id,
                nome.strip()
            ))

            especialistas = cursor.fetchall()

            ids = [
                linha[0]
                for linha in especialistas
            ]

            for especialista_id in ids:

                cursor.execute("""
                    DELETE FROM especialista_servicos

                    WHERE empresa_id = %s

                    AND especialista_id = %s
                """, (
                    empresa_id,
                    especialista_id
                ))

                cursor.execute("""
                    DELETE FROM especialistas

                    WHERE empresa_id = %s

                    AND id = %s
                """, (
                    empresa_id,
                    especialista_id
                ))

        conn.commit()

        return True

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def excluir_servico(
    servico_id,
    empresa_id=1
):

    garantir_tabelas_config()

    conn = conectar()

    try:

        with conn.cursor() as cursor:

            cursor.execute("""
                DELETE FROM especialista_servicos

                WHERE servico_id = %s

                AND empresa_id = %s
            """, (
                int(servico_id),
                empresa_id
            ))

            cursor.execute("""
                DELETE FROM servicos

                WHERE id = %s

                AND empresa_id = %s
            """, (
                int(servico_id),
                empresa_id
            ))

        conn.commit()

        return True

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()