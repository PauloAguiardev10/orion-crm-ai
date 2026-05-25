import pandas as pd

from database.db import conectar


def garantir_tabelas_config():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS especialistas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER DEFAULT 1,
            nome TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS servicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER DEFAULT 1,
            nome TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS especialista_servicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER DEFAULT 1,
            especialista_id INTEGER NOT NULL,
            servico_id INTEGER NOT NULL
        )
    """)

    for tabela in ["especialistas", "servicos", "especialista_servicos"]:
        cursor.execute(f"PRAGMA table_info({tabela})")
        colunas = [col[1] for col in cursor.fetchall()]

        if "empresa_id" not in colunas:
            cursor.execute(f"""
                ALTER TABLE {tabela}
                ADD COLUMN empresa_id INTEGER DEFAULT 1
            """)

    conn.commit()
    conn.close()


def carregar_servicos(empresa_id=1):
    garantir_tabelas_config()

    conn = conectar()

    servicos = pd.read_sql_query("""
        SELECT *
        FROM servicos
        WHERE empresa_id = ?
        ORDER BY id
    """, conn, params=(empresa_id,))

    conn.close()
    return servicos


def carregar_especialistas(empresa_id=1):
    garantir_tabelas_config()

    conn = conectar()

    especialistas = pd.read_sql_query("""
        SELECT
            especialistas.id,
            especialistas.empresa_id,
            especialistas.nome,
            GROUP_CONCAT(servicos.nome, ', ') AS especialidades
        FROM especialistas
        LEFT JOIN especialista_servicos
            ON especialista_servicos.especialista_id = especialistas.id
            AND especialista_servicos.empresa_id = especialistas.empresa_id
        LEFT JOIN servicos
            ON servicos.id = especialista_servicos.servico_id
            AND servicos.empresa_id = especialistas.empresa_id
        WHERE especialistas.empresa_id = ?
        GROUP BY especialistas.id, especialistas.empresa_id, especialistas.nome
        ORDER BY especialistas.id
    """, conn, params=(empresa_id,))

    conn.close()
    return especialistas


def cadastrar_servico(nome, empresa_id=1):
    if not nome.strip():
        return False

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO servicos (
            empresa_id,
            nome
        )
        VALUES (?, ?)
    """, (
        empresa_id,
        nome.strip()
    ))

    conn.commit()
    conn.close()

    return True


def cadastrar_especialista(nome, servicos_ids, empresa_id=1):
    if not nome.strip():
        return False

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO especialistas (
            empresa_id,
            nome
        )
        VALUES (?, ?)
    """, (
        empresa_id,
        nome.strip()
    ))

    conn.commit()

    especialista_id = cursor.lastrowid

    for servico_id in servicos_ids:
        cursor.execute("""
            INSERT INTO especialista_servicos (
                empresa_id,
                especialista_id,
                servico_id
            )
            VALUES (?, ?, ?)
        """, (
            empresa_id,
            especialista_id,
            int(servico_id)
        ))

    conn.commit()
    conn.close()

    return True