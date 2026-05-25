from database.db import conectar

conn = conectar()

cursor = conn.cursor()

cursor.execute("""
UPDATE empresas
SET logo_path = 'assets/logo_forway.png'
WHERE nome = 'Forway'
""")

conn.commit()

conn.close()

print("Logo configurada.")