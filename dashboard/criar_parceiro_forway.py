from database.db import conectar
from services.usuarios_service import criar_usuario


conn = conectar()
cursor = conn.cursor()

cursor.execute("""
    SELECT id, nome
    FROM empresas
    WHERE nome = 'Forway'
""")

empresa = cursor.fetchone()

if not empresa:
    print("Empresa Forway não encontrada. Cadastre a Forway primeiro.")
else:
    empresa_id = empresa[0]
    empresa_nome = empresa[1]

    criar_usuario(
        usuario="forway_parceiro",
        senha="123456",
        empresa=empresa_nome,
        nivel="parceiro_admin",
        empresa_id=empresa_id
    )

    print("Parceiro admin criado com sucesso.")
    print("Usuário: forway_parceiro")
    print("Senha: 123456")

conn.close()