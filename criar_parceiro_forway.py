import sqlite3
import hashlib
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database" / "agente_sdr.db"


def conectar():
    return sqlite3.connect(DB_PATH)


def criptografar_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()


def garantir_colunas():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS empresas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            tipo TEXT DEFAULT 'cliente',
            parceiro_nome TEXT,
            status TEXT DEFAULT 'ativa',
            status_financeiro TEXT DEFAULT 'em_dia',
            valor_mensal REAL DEFAULT 0,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER,
            empresa TEXT,
            usuario TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL,
            nivel TEXT DEFAULT 'usuario'
        )
    """)

    cursor.execute("PRAGMA table_info(empresas)")
    colunas_empresas = [col[1] for col in cursor.fetchall()]

    if "tipo" not in colunas_empresas:
        cursor.execute("ALTER TABLE empresas ADD COLUMN tipo TEXT DEFAULT 'cliente'")

    if "parceiro_nome" not in colunas_empresas:
        cursor.execute("ALTER TABLE empresas ADD COLUMN parceiro_nome TEXT")

    if "status" not in colunas_empresas:
        cursor.execute("ALTER TABLE empresas ADD COLUMN status TEXT DEFAULT 'ativa'")

    if "status_financeiro" not in colunas_empresas:
        cursor.execute("ALTER TABLE empresas ADD COLUMN status_financeiro TEXT DEFAULT 'em_dia'")

    if "valor_mensal" not in colunas_empresas:
        cursor.execute("ALTER TABLE empresas ADD COLUMN valor_mensal REAL DEFAULT 0")

    cursor.execute("PRAGMA table_info(usuarios)")
    colunas_usuarios = [col[1] for col in cursor.fetchall()]

    if "empresa_id" not in colunas_usuarios:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN empresa_id INTEGER")

    if "empresa" not in colunas_usuarios:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN empresa TEXT")

    if "nivel" not in colunas_usuarios:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN nivel TEXT DEFAULT 'usuario'")

    conn.commit()
    conn.close()


def criar_empresa(nome, tipo, parceiro_nome=None, valor_mensal=0):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id
        FROM empresas
        WHERE nome = ?
    """, (nome,))

    empresa = cursor.fetchone()

    if empresa:
        empresa_id = empresa[0]

        cursor.execute("""
            UPDATE empresas
            SET tipo = ?,
                parceiro_nome = ?,
                status = 'ativa',
                status_financeiro = 'em_dia',
                valor_mensal = ?
            WHERE id = ?
        """, (
            tipo,
            parceiro_nome,
            valor_mensal,
            empresa_id
        ))

        conn.commit()
        conn.close()
        return empresa_id

    cursor.execute("""
        INSERT INTO empresas (
            nome,
            tipo,
            parceiro_nome,
            status,
            status_financeiro,
            valor_mensal
        )
        VALUES (?, ?, ?, 'ativa', 'em_dia', ?)
    """, (
        nome,
        tipo,
        parceiro_nome,
        valor_mensal
    ))

    conn.commit()
    empresa_id = cursor.lastrowid
    conn.close()

    return empresa_id


def criar_usuario(usuario, senha, empresa, nivel):
    conn = conectar()
    cursor = conn.cursor()

    senha_criptografada = criptografar_senha(senha)

    cursor.execute("""
        SELECT id
        FROM empresas
        WHERE nome = ?
    """, (empresa,))

    empresa_row = cursor.fetchone()

    if not empresa_row:
        conn.close()
        raise Exception(f"Empresa não encontrada: {empresa}")

    empresa_id = empresa_row[0]

    cursor.execute("""
        SELECT id
        FROM usuarios
        WHERE usuario = ?
    """, (usuario,))

    existente = cursor.fetchone()

    if existente:
        cursor.execute("""
            UPDATE usuarios
            SET senha = ?,
                empresa = ?,
                empresa_id = ?,
                nivel = ?
            WHERE usuario = ?
        """, (
            senha_criptografada,
            empresa,
            empresa_id,
            nivel,
            usuario
        ))

    else:
        cursor.execute("""
            INSERT INTO usuarios (
                empresa_id,
                empresa,
                usuario,
                senha,
                nivel
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            empresa_id,
            empresa,
            usuario,
            senha_criptografada,
            nivel
        ))

    conn.commit()
    conn.close()


def main():
    garantir_colunas()

    criar_empresa(
        nome="Orion Systems",
        tipo="master",
        parceiro_nome=None,
        valor_mensal=0
    )

    criar_empresa(
        nome="Forway",
        tipo="parceiro_cliente",
        parceiro_nome="Forway",
        valor_mensal=0
    )

    criar_usuario(
        usuario="orion",
        senha="123456",
        empresa="Orion Systems",
        nivel="orion_admin"
    )

    criar_usuario(
        usuario="luciano",
        senha="123456",
        empresa="Forway",
        nivel="parceiro_admin"
    )

    print("Parceiro Forway criado/atualizado com sucesso.")
    print("Login Orion: orion / 123456")
    print("Login Forway: luciano / 123456")


if __name__ == "__main__":
    main()