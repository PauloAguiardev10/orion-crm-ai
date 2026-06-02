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


def limpar_especialistas_duplicados(empresa_id=1):
    garantir_tabelas_config()

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT nome
        FROM especialistas
        WHERE empresa_id = ?
        GROUP BY LOWER(TRIM(nome))
        HAVING COUNT(*) > 1
    """, (empresa_id,))

    nomes_duplicados = cursor.fetchall()

    for item in nomes_duplicados:
        nome = item["nome"] if hasattr(item, "keys") else item[0]

        cursor.execute("""
            SELECT id
            FROM especialistas
            WHERE empresa_id = ?
            AND LOWER(TRIM(nome)) = LOWER(TRIM(?))
            ORDER BY id ASC
        """, (empresa_id, nome))

        ids = [
            linha["id"] if hasattr(linha, "keys") else linha[0]
            for linha in cursor.fetchall()
        ]

        if not ids:
            continue

        id_principal = ids[0]
        ids_duplicados = ids[1:]

        for id_dup in ids_duplicados:
            cursor.execute("""
                UPDATE especialista_servicos
                SET especialista_id = ?
                WHERE especialista_id = ?
                AND empresa_id = ?
            """, (
                id_principal,
                id_dup,
                empresa_id
            ))

            cursor.execute("""
                DELETE FROM especialistas
                WHERE id = ?
                AND empresa_id = ?
            """, (
                id_dup,
                empresa_id
            ))

    cursor.execute("""
        DELETE FROM especialista_servicos
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM especialista_servicos
            WHERE empresa_id = ?
            GROUP BY empresa_id, especialista_id, servico_id
        )
        AND empresa_id = ?
    """, (
        empresa_id,
        empresa_id
    ))

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
    limpar_especialistas_duplicados(empresa_id)

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


def carregar_ids_servicos_especialista(nome, empresa_id=1):
    garantir_tabelas_config()

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id
        FROM especialistas
        WHERE empresa_id = ?
        AND LOWER(TRIM(nome)) = LOWER(TRIM(?))
        ORDER BY id ASC
        LIMIT 1
    """, (
        empresa_id,
        nome.strip()
    ))

    especialista = cursor.fetchone()

    if not especialista:
        conn.close()
        return []

    especialista_id = (
        especialista["id"]
        if hasattr(especialista, "keys")
        else especialista[0]
    )

    cursor.execute("""
        SELECT servico_id
        FROM especialista_servicos
        WHERE empresa_id = ?
        AND especialista_id = ?
    """, (
        empresa_id,
        especialista_id
    ))

    ids = [
        linha["servico_id"] if hasattr(linha, "keys") else linha[0]
        for linha in cursor.fetchall()
    ]

    conn.close()
    return ids


def cadastrar_servico(nome, empresa_id=1):
    if not nome.strip():
        return False

    garantir_tabelas_config()

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id
        FROM servicos
        WHERE empresa_id = ?
        AND LOWER(TRIM(nome)) = LOWER(TRIM(?))
    """, (
        empresa_id,
        nome.strip()
    ))

    existente = cursor.fetchone()

    if existente:
        conn.close()
        return True

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

    garantir_tabelas_config()

    nome = nome.strip()

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id
        FROM especialistas
        WHERE empresa_id = ?
        AND LOWER(TRIM(nome)) = LOWER(TRIM(?))
        ORDER BY id ASC
        LIMIT 1
    """, (
        empresa_id,
        nome
    ))

    especialista = cursor.fetchone()

    if especialista:
        especialista_id = (
            especialista["id"]
            if hasattr(especialista, "keys")
            else especialista[0]
        )

        cursor.execute("""
            UPDATE especialistas
            SET nome = ?
            WHERE id = ?
            AND empresa_id = ?
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
            VALUES (?, ?)
        """, (
            empresa_id,
            nome
        ))

        conn.commit()
        especialista_id = cursor.lastrowid

    cursor.execute("""
        DELETE FROM especialista_servicos
        WHERE empresa_id = ?
        AND especialista_id = ?
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
            VALUES (?, ?, ?)
        """, (
            empresa_id,
            especialista_id,
            int(servico_id)
        ))

    conn.commit()
    conn.close()

    limpar_especialistas_duplicados(empresa_id)

    return True


def excluir_especialista_por_nome(nome, empresa_id=1):
    garantir_tabelas_config()

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id
        FROM especialistas
        WHERE empresa_id = ?
        AND LOWER(TRIM(nome)) = LOWER(TRIM(?))
    """, (
        empresa_id,
        nome.strip()
    ))

    especialistas = cursor.fetchall()

    ids = [
        linha["id"] if hasattr(linha, "keys") else linha[0]
        for linha in especialistas
    ]

    for especialista_id in ids:
        cursor.execute("""
            DELETE FROM especialista_servicos
            WHERE empresa_id = ?
            AND especialista_id = ?
        """, (
            empresa_id,
            especialista_id
        ))

        cursor.execute("""
            DELETE FROM especialistas
            WHERE empresa_id = ?
            AND id = ?
        """, (
            empresa_id,
            especialista_id
        ))

    conn.commit()
    conn.close()

    return True
def excluir_servico(servico_id, empresa_id=1):

    garantir_tabelas_config()

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM especialista_servicos
        WHERE servico_id = ?
        AND empresa_id = ?
    """, (
        int(servico_id),
        empresa_id
    ))

    cursor.execute("""
        DELETE FROM servicos
        WHERE id = ?
        AND empresa_id = ?
    """, (
        int(servico_id),
        empresa_id
    ))

    conn.commit()
    conn.close()

    return True