from app.services.gpt_service import (
    gerar_resposta_gpt,
    gerar_resumo_comercial_gpt,
    gerar_apresentacao_servicos_gpt
)


def limpar_nome_cliente(texto: str):
    nome = texto.strip()

    substituicoes = [
        "meu nome é",
        "meu nome e",
        "eu sou",
        "sou o",
        "sou a",
        "me chamo",
        "me chama de",
        "pode me chamar de",
        "aqui é",
        "aqui e",
    ]

    nome_minusculo = nome.lower()

    for frase in substituicoes:
        if nome_minusculo.startswith(frase):
            nome = nome[len(frase):].strip()
            break

    return nome.title()


def detectar_intencao_cliente(mensagem: str):
    texto = mensagem.lower()

    if any(frase in texto for frase in [
        "já tentei",
        "ja tentei",
        "não deu certo",
        "nao deu certo",
        "não funcionou",
        "nao funcionou",
        "experiência ruim",
        "experiencia ruim",
        "outra agência",
        "outra agencia",
        "tenho medo",
        "medo de contratar"
    ]):
        return "objecao_experiencia_ruim"

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
        "orcamento",
        "preço",
        "preco",
        "valor",
        "quanto custa",
        "quanto fica",
        "pacote",
        "pacotes"
    ]):
        return "orcamento"

    if any(frase in texto for frase in [
        "reunião",
        "reuniao",
        "agenda",
        "agendar",
        "marcar horário",
        "marcar horario"
    ]):
        return "reuniao"

    if any(frase in texto for frase in [
        "tráfego",
        "trafego",
        "anúncio",
        "anuncio",
        "facebook ads",
        "instagram ads",
        "meta ads"
    ]):
        return "trafego"

    if any(frase in texto for frase in [
        "site",
        "landing page",
        "website",
        "página de vendas",
        "pagina de vendas"
    ]):
        return "web_design"

    if any(frase in texto for frase in [
        "automação",
        "automacao",
        "ia",
        "chatbot",
        "sdr",
        "robô",
        "robo"
    ]):
        return "automacao"

    if any(frase in texto for frase in [
        "oi",
        "olá",
        "ola",
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
        "orcamento",
        "preço",
        "preco",
        "valor",
        "contratar",
        "fechar",
        "proposta",
        "quanto custa",
        "quero contratar",
        "vender mais",
        "aumentar vendas",
        "marcar reunião",
        "agendar",
        "tenho interesse",
        "quero saber mais"
    ]

    palavras_objeção = [
        "já tentei",
        "ja tentei",
        "não deu certo",
        "nao deu certo",
        "não funcionou",
        "nao funcionou",
        "outra agência",
        "outra agencia",
        "experiência ruim",
        "experiencia ruim"
    ]

    produtos = {
        "Gestão de Tráfego Pago": [
            "tráfego",
            "trafego",
            "anúncio",
            "anuncio",
            "facebook ads",
            "instagram ads",
            "meta ads"
        ],
        "Social Media Estratégico": [
            "social media",
            "conteúdo",
            "conteudo",
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
            "automacao",
            "ia",
            "chatbot",
            "sdr",
            "atendimento automático",
            "atendimento automatico"
        ],
        "Web Design": [
            "site",
            "landing page",
            "website",
            "página de vendas",
            "pagina de vendas"
        ],
        "Estrutura Completa": [
            "estrutura completa",
            "marketing completo",
            "tudo completo",
            "tráfego e social media",
            "trafego e social media"
        ]
    }

    for palavra in palavras_quentes:
        if palavra in texto:
            score += 3

    for palavra in palavras_objeção:
        if palavra in texto:
            score += 2

    for nome_produto, termos in produtos.items():
        for termo in termos:
            if termo in texto:
                produto = nome_produto
                score += 2

    if score >= 7:
        temperatura = "quente"
        prioridade = "alta"
    elif score >= 3:
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
A lead demonstrou interesse nos serviços da Forway e informou como principal objetivo: "{conversa.objetivo or "não informado"}".

Pontos importantes:
• Lead foi atendida inicialmente pela Sofia
• Demonstrou abertura para entender melhor a solução
• Deve ser conduzida de forma consultiva
• Se houver objeção ou experiência ruim anterior, Luciano deve reforçar o diagnóstico antes de falar de valores

Próxima ação recomendada:
Luciano deve entrar em contato para aprofundar o diagnóstico e conduzir a lead para uma reunião comercial.
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

    if conversa.etapa == "inicio":

        if intencao == "conhecer_servicos":
            conversa.etapa = "entender_objetivo_inicial"

            resposta = (
                "Olá! Tudo bem? 😊\n\n"
                "A Forway trabalha com soluções para ajudar empresas a venderem mais e organizarem melhor sua presença digital.\n\n"
                "Atuamos com tráfego pago, social media, criação de sites, landing pages, identidade visual, automações e estratégias comerciais.\n\n"
                "Mas antes de falar de pacote ou valor, gosto de entender melhor o momento da empresa, porque cada negócio precisa de uma estratégia diferente.\n\n"
                "Hoje, qual é o principal objetivo da sua empresa: vender mais, divulgar melhor a marca, gerar mais leads ou organizar o atendimento?"
            )

        else:
            conversa.etapa = "coletar_nome"

            resposta = (
                "Olá! Tudo bem? 😊\n\n"
                "Que bom receber seu contato. Eu sou a Sofia, assistente comercial da Forway.\n\n"
                "Vou entender um pouco do seu cenário para encaminhar tudo bem organizado para nosso time comercial.\n\n"
                "Como posso te chamar?"
            )

    elif conversa.etapa == "entender_objetivo_inicial":

        conversa.objetivo = texto
        analise = analisar_mensagem(f"{conversa.historico or ''}\n{texto}")

        if conversa.servico is None and analise["produto"] != "não identificado":
            conversa.servico = analise["produto"]

        conversa.etapa = "coletar_nome"

        if intencao == "objecao_experiencia_ruim":
            resposta = (
                "Entendo perfeitamente 😊\n\n"
                "Isso é mais comum do que parece. Muitas empresas chegam até a Forway depois de experiências que não deram certo, normalmente por falta de acompanhamento, estratégia ou clareza no processo.\n\n"
                "Por isso nosso atendimento começa entendendo o cenário antes de indicar qualquer solução.\n\n"
                "Pra eu registrar certinho aqui, como posso te chamar?"
            )
        else:
            resposta = (
                "Entendi perfeitamente 😊\n\n"
                "Esse é exatamente o tipo de cenário em que a Forway costuma atuar: entendendo o momento da empresa, identificando os pontos de melhoria e montando uma estratégia mais alinhada para gerar resultado.\n\n"
                "Pra eu registrar certinho aqui, como posso te chamar?"
            )

    elif conversa.etapa == "coletar_nome":

        conversa.nome = limpar_nome_cliente(texto)
        conversa.etapa = "coletar_empresa"

        resposta = (
            f"Prazer, {conversa.nome} 😊\n\n"
            "Me conta uma coisa: qual é o nome da sua empresa ou marca?"
        )

    elif conversa.etapa == "coletar_empresa":

        conversa.empresa = texto
        conversa.etapa = "coletar_segmento"

        resposta = (
            "Perfeito 😊\n\n"
            "E sua empresa atua em qual segmento?"
        )

    elif conversa.etapa == "coletar_segmento":

        conversa.segmento = texto

        if conversa.objetivo:
            if canal in ["instagram", "facebook", "messenger"]:
                conversa.etapa = "coletar_whatsapp"

                resposta = (
                    f"Entendi, {conversa.nome} 😊\n\n"
                    f"Pelo que você me passou, a {conversa.empresa} atua no segmento de {conversa.segmento} e tem um objetivo que precisa ser analisado com cuidado.\n\n"
                    "A Forway trabalha justamente com esse olhar mais estratégico, entendendo o cenário antes de apresentar uma solução.\n\n"
                    "Para nosso time comercial continuar o atendimento com mais precisão, me passa seu WhatsApp?"
                )

            else:
                conversa.etapa = "encaminhar"

                resposta = (
                    f"Perfeito, {conversa.nome} 😊\n\n"
                    "Já organizei suas informações e vou encaminhar para o Luciano, responsável comercial da Forway.\n\n"
                    "Pelo que você me passou, faz mais sentido ele analisar seu cenário com calma e te orientar sobre a melhor estratégia.\n\n"
                    "Nosso time comercial atende de segunda a sexta, das 08h às 18h. Sua solicitação já ficou registrada e será continuada assim que possível."
                )

        else:
            conversa.etapa = "entender_objetivo"

            resposta = (
                "Entendi 😊\n\n"
                "Agora me conta um pouco sobre o principal objetivo ou desafio da sua empresa hoje.\n\n"
                "Por exemplo: vender mais, atrair clientes melhores, melhorar o Instagram, gerar leads, estruturar campanhas ou organizar o atendimento."
            )

    elif conversa.etapa == "entender_objetivo":

        conversa.objetivo = texto

        analise = analisar_mensagem(f"""
        {conversa.historico or ''}
        {texto}
        {conversa.objetivo or ''}
        """)

        if conversa.servico is None and analise["produto"] != "não identificado":
            conversa.servico = analise["produto"]

        if intencao == "objecao_experiencia_ruim":
            resposta_base = (
                "Entendo perfeitamente 😊\n\n"
                "Isso acontece bastante. Muitas empresas procuram a Forway justamente depois de uma experiência ruim com marketing ou tráfego, porque perceberam que não basta só anunciar: precisa ter estratégia, acompanhamento e clareza sobre o objetivo.\n\n"
                "Por isso, antes de falar em pacote ou valor, o ideal é o Luciano entender melhor o que já foi feito e onde o processo travou."
            )
        else:
            resposta_base = (
                "Esse ponto que você trouxe é muito importante 😊\n\n"
                "Muitas empresas têm um bom produto ou serviço, mas acabam perdendo oportunidade por falta de estratégia, posicionamento ou processo comercial bem organizado.\n\n"
                "A Forway costuma analisar exatamente isso: o momento da empresa, o que já foi feito e qual caminho pode gerar mais resultado."
            )

        if canal in ["instagram", "facebook", "messenger"]:
            conversa.etapa = "coletar_whatsapp"

            resposta = (
                f"{resposta_base}\n\n"
                "Para nosso time especializado continuar esse atendimento, me passa seu WhatsApp?"
            )

        else:
            conversa.etapa = "encaminhar"

            resposta = (
                f"{resposta_base}\n\n"
                f"Já organizei suas informações, {conversa.nome}, e vou encaminhar para o Luciano, responsável comercial da Forway.\n\n"
                "Ele vai conseguir analisar melhor seu cenário e te orientar com uma visão mais consultiva sobre a melhor estratégia.\n\n"
                "Nosso time comercial atende de segunda a sexta, das 08h às 18h. Sua solicitação já ficou registrada e será continuada assim que possível."
            )

    elif conversa.etapa == "coletar_whatsapp":

        conversa.telefone = texto
        conversa.etapa = "encaminhar"

        resposta = (
            f"Perfeito, {conversa.nome} 😊\n\n"
            "Já organizei suas informações e vou encaminhar para o Luciano, responsável comercial da Forway.\n\n"
            "Ele vai conseguir analisar melhor seu cenário e te orientar sobre qual solução faz mais sentido para sua empresa.\n\n"
            "Nosso time comercial atende de segunda a sexta, das 08h às 18h. Sua solicitação já ficou registrada e será continuada assim que possível."
        )

    else:

        resposta = (
            "Suas informações já foram organizadas e encaminhadas para nossa equipe comercial. "
            "Um especialista continuará seu atendimento assim que possível 😊"
        )

    conversa.historico += f"\nAgente: {resposta}"

    return resposta, analise