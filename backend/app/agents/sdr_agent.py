from app.services.gpt_service import (
    gerar_resposta_gpt,
    gerar_resumo_comercial_gpt,
    gerar_apresentacao_servicos_gpt
)


def detectar_intencao_cliente(mensagem: str):
    texto = mensagem.lower()

    if any(frase in texto for frase in [
        "quais serviços",
        "serviços vocês oferecem",
        "o que vocês fazem",
        "como vocês trabalham",
        "me fala dos serviços",
        "o que oferecem",
        "não sei o que preciso",
        "não sei qual serviço",
        "quero conhecer",
        "serviços da forway"
    ]):
        return "conhecer_servicos"

    if any(frase in texto for frase in [
        "orçamento",
        "preço",
        "valor",
        "quanto custa",
        "quanto fica"
    ]):
        return "orcamento"

    if any(frase in texto for frase in [
        "tráfego",
        "anúncio",
        "facebook ads",
        "instagram ads",
        "meta ads"
    ]):
        return "trafego"

    if any(frase in texto for frase in [
        "site",
        "landing page",
        "website",
        "página de vendas"
    ]):
        return "web_design"

    if any(frase in texto for frase in [
        "automação",
        "ia",
        "chatbot",
        "sdr",
        "robô"
    ]):
        return "automacao"

    if any(frase in texto for frase in [
        "oi",
        "olá",
        "bom dia",
        "boa tarde",
        "boa noite"
    ]):
        return "saudacao"

    return "geral"


def analisar_mensagem(mensagem: str):
    texto = mensagem.lower()

    score = 0
    produto = "não identificado"
    prioridade = "baixa"

    palavras_quentes = [
        "comprar",
        "orçamento",
        "preço",
        "valor",
        "contratar",
        "fechar",
        "proposta",
        "quanto custa",
        "quero contratar",
        "vender mais",
        "aumentar vendas"
    ]

    produtos = {
        "Gestão de Tráfego Pago": [
            "tráfego",
            "anúncio",
            "facebook ads",
            "instagram ads",
            "meta ads"
        ],

        "Social Media Estratégico": [
            "social media",
            "conteúdo",
            "instagram",
            "postagem",
            "redes sociais"
        ],

        "Design": [
            "design",
            "identidade visual",
            "criativo",
            "arte",
            "logo"
        ],

        "Atendimento com IA": [
            "automação",
            "ia",
            "chatbot",
            "sdr",
            "atendimento automático"
        ],

        "Web Design": [
            "site",
            "landing page",
            "website",
            "página de vendas"
        ],

        "Estrutura Completa": [
            "estrutura completa",
            "marketing completo",
            "tudo completo",
            "tráfego e social media"
        ]
    }

    for palavra in palavras_quentes:
        if palavra in texto:
            score += 3

    for nome_produto, termos in produtos.items():
        for termo in termos:
            if termo in texto:
                produto = nome_produto
                score += 2

    if score >= 5:
        temperatura = "quente"
        prioridade = "alta"
    elif score >= 2:
        temperatura = "morna"
        prioridade = "média"
    else:
        temperatura = "fria"
        prioridade = "baixa"

    return {
        "temperatura": temperatura,
        "score": score,
        "produto": produto,
        "prioridade": prioridade
    }


def gerar_resumo_vendedor(conversa, analise):
    try:
        return gerar_resumo_comercial_gpt(conversa, analise)

    except Exception:
        return f"""
Nova lead qualificada — Forway

Nome: {conversa.nome or "Não informado"}
Empresa: {conversa.empresa or "Não informado"}
Segmento: {conversa.segmento or "Não informado"}
Canal: {conversa.canal}
WhatsApp: {conversa.telefone or "Não informado"}
Serviço de interesse: {conversa.servico or analise["produto"]}
Temperatura: {analise["temperatura"].capitalize()}
Prioridade: {analise["prioridade"].capitalize()}
Score: {analise["score"]}

Resumo da conversa:
A lead informou que atua no segmento de {conversa.segmento or "não informado"} e demonstrou interesse em {conversa.servico or analise["produto"]}. O objetivo informado foi: "{conversa.objetivo or "não informado"}".

Pontos importantes:
• Demonstrou interesse nos serviços da Forway
• Informou o objetivo principal do negócio
• Está aberta ao contato comercial
• Deve ser abordada com foco consultivo

Próxima ação recomendada:
Entrar em contato apresentando uma solução alinhada ao objetivo informado, sem repetir perguntas já respondidas.
""".strip()


def conduzir_conversa(conversa, mensagem: str):
    texto = mensagem.strip()
    canal = conversa.canal.lower()
    intencao = detectar_intencao_cliente(texto)

    texto_para_analise = f"""
    {conversa.historico or ''}
    {texto}
    {conversa.objetivo or ''}
    {conversa.servico or ''}
    """

    analise = analisar_mensagem(texto_para_analise)

    if conversa.servico is None and analise["produto"] != "não identificado":
        conversa.servico = analise["produto"]

    conversa.historico = (conversa.historico or "") + f"\nCliente: {texto}"

    # INÍCIO

    if conversa.etapa == "inicio":

        if intencao == "conhecer_servicos":
            conversa.etapa = "entender_objetivo_inicial"

            contexto = f"""
            Cliente iniciou conversa no canal {conversa.canal} perguntando sobre os serviços.

            Mensagem:
            {texto}

            A Sofia deve:
            - apresentar os serviços da Forway
            - explicar de forma curta e profissional
            - destacar que a Forway oferece tudo em um só lugar
            - perguntar qual objetivo o cliente quer alcançar
            - não pedir nome ainda
            """

            resposta = gerar_apresentacao_servicos_gpt(contexto)

        else:
            conversa.etapa = "coletar_nome"

            contexto = f"""
            Cliente iniciou conversa no canal {conversa.canal}.

            Mensagem:
            {texto}

            Você é Sofia, assistente comercial da Forway.

            Seja humanizada, profissional, simpática, carismática e natural.

            Dê boas-vindas, agradeça o contato e pergunte o nome do cliente naturalmente.
            """

            resposta = gerar_resposta_gpt(contexto)

    # CLIENTE VIU SERVIÇOS E RESPONDEU OBJETIVO

    elif conversa.etapa == "entender_objetivo_inicial":

        conversa.objetivo = texto

        texto_para_analise = f"""
        {conversa.historico or ''}
        {texto}
        """

        analise = analisar_mensagem(texto_para_analise)

        if conversa.servico is None and analise["produto"] != "não identificado":
            conversa.servico = analise["produto"]

        conversa.etapa = "coletar_nome"

        contexto = f"""
        Você é Sofia, assistente comercial da Forway.

        O cliente explicou o objetivo:
        {texto}

        Responda de forma humanizada, mostrando que entendeu o objetivo.
        Depois pergunte naturalmente como pode chamar o cliente.
        """

        resposta = gerar_resposta_gpt(contexto)

    # COLETAR NOME

    elif conversa.etapa == "coletar_nome":

        conversa.nome = texto
        conversa.etapa = "coletar_empresa"

        resposta = (
            f"Prazer, {conversa.nome} 😊 "
            "Me conta uma coisa: qual é o nome da sua empresa ou negócio?"
        )

    # COLETAR EMPRESA

    elif conversa.etapa == "coletar_empresa":

        conversa.empresa = texto
        conversa.etapa = "coletar_segmento"

        resposta = (
            "Perfeito 😊 "
            "E sua empresa atua em qual segmento?"
        )

    # COLETAR SEGMENTO

    elif conversa.etapa == "coletar_segmento":

        conversa.segmento = texto

        if conversa.objetivo:
            if canal in ["instagram", "facebook", "messenger"]:
                conversa.etapa = "coletar_whatsapp"

                contexto = f"""
                Você é Sofia, assistente comercial da Forway.

                Dados:
                Nome: {conversa.nome}
                Empresa: {conversa.empresa}
                Segmento: {conversa.segmento}
                Objetivo: {conversa.objetivo}

                Mostre que já entendeu o contexto e peça o WhatsApp para nosso time especializado continuar o atendimento.
                """

                resposta = gerar_resposta_gpt(contexto)

            else:
                conversa.etapa = "encaminhar"

                resposta = (
                    f"Perfeito, {conversa.nome} 😊\n"
                    "Já organizei suas informações e encaminhei para nossa equipe comercial.\n"
                    "Nosso horário de atendimento do nosso time especializado é de segunda a sexta, "
                    "das 08h às 18h, mas sua solicitação já foi registrada e um especialista continuará "
                    "seu atendimento assim que possível."
                )

        else:
            conversa.etapa = "entender_objetivo"

            resposta = (
                "Entendi 😊 "
                "Agora me fala um pouco sobre o principal objetivo "
                "ou desafio da sua empresa hoje."
            )

    # ENTENDER OBJETIVO

    elif conversa.etapa == "entender_objetivo":

        conversa.objetivo = texto

        texto_para_analise = f"""
        {conversa.historico or ''}
        {texto}
        {conversa.objetivo or ''}
        """

        analise = analisar_mensagem(texto_para_analise)

        if conversa.servico is None and analise["produto"] != "não identificado":
            conversa.servico = analise["produto"]

        if canal in ["instagram", "facebook", "messenger"]:
            conversa.etapa = "coletar_whatsapp"

            contexto = f"""
            Você é Sofia, assistente comercial da Forway.

            Dados do cliente:
            Nome: {conversa.nome}
            Empresa: {conversa.empresa}
            Segmento: {conversa.segmento}

            Objetivo informado:
            {texto}

            Mostre que entendeu o objetivo do cliente de forma humanizada e consultiva.
            Depois peça o WhatsApp para nosso time especializado continuar o atendimento.
            """

            resposta = gerar_resposta_gpt(contexto)

        else:
            conversa.etapa = "encaminhar"

            contexto = f"""
            Você é Sofia, assistente comercial da Forway.

            Dados:
            Nome: {conversa.nome}
            Empresa: {conversa.empresa}
            Segmento: {conversa.segmento}
            Objetivo: {texto}

            Gere uma resposta humanizada dizendo que as informações foram organizadas
            e que o time especializado continuará o atendimento no horário comercial,
            de segunda a sexta das 08h às 18h.
            """

            resposta = gerar_resposta_gpt(contexto)

    # COLETAR WHATSAPP

    elif conversa.etapa == "coletar_whatsapp":

        conversa.telefone = texto
        conversa.etapa = "encaminhar"

        resposta = (
            f"Perfeito, {conversa.nome} 😊\n"
            "Já organizei suas informações e encaminhei para nossa equipe comercial.\n"
            "O horário de atendimento do nosso time especializado é de segunda a sexta, "
            "das 08h às 18h, mas sua solicitação já foi registrada e um especialista continuará "
            "seu atendimento assim que possível."
        )

    # FINALIZADO

    else:

        resposta = (
            "Suas informações já foram organizadas e encaminhadas para nossa equipe comercial. "
            "Um especialista continuará seu atendimento assim que possível 😊"
        )

    conversa.historico += f"\nAgente: {resposta}"

    return resposta, analise