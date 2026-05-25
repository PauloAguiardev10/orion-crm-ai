import hashlib
import pandas as pd

from database.db import conectar


def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()


def criar_tabela_usuarios():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER,
            empresa TEXT NOT NULL,
            usuario TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            nivel TEXT DEFAULT 'usuario'
        )
    """)

    conn.commit()
    conn.close()


def listar_usuarios():
    criar_tabela_usuarios()

    conn = conectar()

    usuarios = pd.read_sql_query("""
        SELECT
            id,
            empresa_id,
            empresa,
            usuario,
            nivel
        FROM usuarios
        ORDER BY id
    """, conn)

    conn.close()

    return usuarios


def criar_usuario(
    usuario,
    senha,
    empresa,
    nivel,
    empresa_id=None
):
    if not usuario.strip() or not senha.strip() or not empresa.strip():
        return False

    criar_tabela_usuarios()

    conn = conectar()
    cursor = conn.cursor()

    senha_hash = hash_senha(senha)

    cursor.execute("""
        SELECT id
        FROM usuarios
        WHERE usuario = ?
    """, (usuario.strip(),))

    existente = cursor.fetchone()

    if existente:
        cursor.execute("""
            UPDATE usuarios
            SET empresa_id = ?,
                empresa = ?,
                senha = ?,
                nivel = ?
            WHERE usuario = ?
        """, (
            empresa_id,
            empresa.strip(),
            senha_hash,
            nivel,
            usuario.strip()
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
            empresa.strip(),
            usuario.strip(),
            senha_hash,
            nivel
        ))

    conn.commit()
    conn.close()

    return True


def criar_admin_empresa(
    empresa_id,
    empresa_nome,
    usuario,
    senha
):
    return criar_usuario(
        usuario=usuario,
        senha=senha,
        empresa=empresa_nome,
        nivel="admin_empresa",
        empresa_id=empresa_id
    )


def alterar_senha(usuario, nova_senha):
    if not nova_senha.strip():
        return False

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE usuarios
        SET senha = ?
        WHERE usuario = ?
    """, (
        hash_senha(nova_senha),
        usuario
    ))

    conn.commit()
    alterado = cursor.rowcount > 0
    conn.close()

    return alterado