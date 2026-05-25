from database.db import conectar


EMPRESAS_DEMO = {
    150: "NIKE",
    307: "FILA",
    242: "PENA",
    209: "Forway",
}


conn = conectar()
cursor = conn.cursor()


for empresa_id, nome_empresa in EMPRESAS_DEMO.items():

    cursor.execute(
        "SELECT id FROM empresas WHERE id = ?",
        (empresa_id,)
    )

    existe = cursor.fetchone()

    if not existe:
        print(f"{nome_empresa} não encontrada.")
        continue

    # =========================================
    # PRODUTOS DEMO
    # =========================================

    produtos = [

        (
            "Plano IA Atendimento",
            "Serviço",
            "Atendimento automático via WhatsApp",
            350,
            10,
            "ativo"
        ),

        (
            "Plano IA Vendas",
            "Serviço",
            "IA realizando vendas automáticas",
            1000,
            10,
            "ativo"
        ),

        (
            "Consultoria Comercial",
            "Serviço",
            "Diagnóstico comercial",
            700,
            5,
            "ativo"
        ),
    ]

    for produto in produtos:

        cursor.execute("""
            INSERT INTO produtos (

                empresa_id,
                nome,
                categoria,
                descricao,
                preco,
                estoque,
                status

            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (

            empresa_id,

            produto[0],
            produto[1],
            produto[2],
            produto[3],
            produto[4],
            produto[5],
        ))

    # =========================================
    # LEADS DEMO
    # =========================================

    leads = [

        (
            1,
            "Plano IA Vendas",
            "Quente",
            "Alta",
            95,
            "WhatsApp",
            "Cliente quer fechar ainda hoje",
            "Lead extremamente quente",
            "Aguardando atendimento humano",
            "Carlos"
        ),

        (
            2,
            "Plano Premium",
            "Quente",
            "Alta",
            92,
            "Instagram",
            "Solicitou proposta completa",
            "Cliente quer automação total",
            "Em atendimento",
            "Fernanda"
        ),

        (
            3,
            "Plano Pro",
            "Morna",
            "Média",
            65,
            "Facebook",
            "Interessado mas ainda comparando",
            "Necessita follow-up",
            "Novo Lead",
            "Não atribuído"
        ),

        (
            4,
            "Plano Lite",
            "Fria",
            "Baixa",
            30,
            "WhatsApp",
            "Apenas consultando preços",
            "Baixa intenção de compra",
            "Não fechado",
            "Não atribuído"
        ),

        (
            5,
            "Plano IA Atendimento",
            "Quente",
            "Alta",
            98,
            "Instagram",
            "Cliente aprovou orçamento",
            "Venda praticamente fechada",
            "Fechado",
            "Roberto"
        ),
    ]

    for lead in leads:

        cursor.execute("""
            INSERT INTO leads (

                cliente_id,
                produto,
                temperatura,
                prioridade,
                score,
                origem,
                observacoes,
                resumo_vendedor,
                status,
                responsavel,
                empresa_id

            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (

            lead[0],
            lead[1],
            lead[2],
            lead[3],
            lead[4],
            lead[5],
            lead[6],
            lead[7],
            lead[8],
            lead[9],
            empresa_id,
        ))

    print(f"Dados demo criados para {nome_empresa}")


conn.commit()
conn.close()

print("Processo finalizado.")