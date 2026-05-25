import hashlib

from database.db import conectar


def criptografar_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()


def garantir_tabelas_auth():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS empresas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            plano TEXT DEFAULT 'Lite',
            status TEXT DEFAULT 'ativa',
            valor_mensal REAL DEFAULT 350,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        INSERT OR IGNORE INTO empresas (nome, plano, status, valor_mensal)
        VALUES (?, ?, ?, ?)
    """, ("Orion Systems", "Premium", "ativa", 1000))

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER,
            empresa TEXT,
            usuario TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            nivel TEXT DEFAULT 'usuario'
        )
    """)

    cursor.execute("SELECT id FROM empresas WHERE nome = ?", ("Orion Systems",))
    empresa_orion_id = cursor.fetchone()[0]

    senha_padrao = criptografar_senha("123456")

    cursor.execute("""
        INSERT OR IGNORE INTO usuarios (
            empresa_id,
            empresa,
            usuario,
            senha,
            nivel
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        empresa_orion_id,
        "Orion Systems",
        "admin",
        senha_padrao,
        "orion_admin"
    ))

    cursor.execute("""
        UPDATE usuarios
        SET empresa_id = ?,
            empresa = 'Orion Systems',
            nivel = 'orion_admin'
        WHERE usuario = 'admin'
    """, (empresa_orion_id,))

    conn.commit()
    conn.close()


def validar_login(usuario, senha):
    garantir_tabelas_auth()

    conn = conectar()
    cursor = conn.cursor()

    senha_hash = criptografar_senha(senha)

    cursor.execute("""
        SELECT usuarios.id
        FROM usuarios
        INNER JOIN empresas
            ON empresas.id = usuarios.empresa_id
        WHERE usuarios.usuario = ?
        AND usuarios.senha = ?
        AND empresas.status = 'ativa'
    """, (
        usuario,
        senha_hash
    ))

    resultado = cursor.fetchone()

    conn.close()

    return resultado is not None


def obter_empresa_usuario(usuario):
    garantir_tabelas_auth()

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT empresas.nome
        FROM usuarios
        INNER JOIN empresas
            ON empresas.id = usuarios.empresa_id
        WHERE usuarios.usuario = ?
        AND empresas.status = 'ativa'
    """, (usuario,))

    resultado = cursor.fetchone()

    conn.close()

    if resultado and resultado[0]:
        return resultado[0]

    return None


def obter_empresa_id_usuario(usuario):
    garantir_tabelas_auth()

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT empresas.id
        FROM usuarios
        INNER JOIN empresas
            ON empresas.id = usuarios.empresa_id
        WHERE usuarios.usuario = ?
        AND empresas.status = 'ativa'
    """, (usuario,))

    resultado = cursor.fetchone()

    conn.close()

    if resultado:
        return resultado[0]

    return None


def obter_nivel_usuario(usuario):
    garantir_tabelas_auth()

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT usuarios.nivel
        FROM usuarios
        INNER JOIN empresas
            ON empresas.id = usuarios.empresa_id
        WHERE usuarios.usuario = ?
        AND empresas.status = 'ativa'
    """, (usuario,))

    resultado = cursor.fetchone()

    conn.close()

    if resultado and resultado[0]:
        return resultado[0]

    return "usuario"