import sqlite3

DB_PATH = "../database/agente_sdr.db"


def conectar():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn