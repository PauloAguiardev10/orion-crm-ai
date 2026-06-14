import re

from app.services.gpt_service import gerar_resumo_comercial_gpt


def limpar_nome_cliente(texto: str):
    nome = texto.strip()

    substituicoes = [
        "meu nome é",
        "meu nome e",
        "eu sou",
        "sou o",
        "sou a",
        "sou",
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


def limpar_nome_empresa(texto: str):
    empresa = texto.strip()

    substituicoes = [
        "minha empresa se chama",
        "minha empresa chama",
        "minha empresa é",
        "minha empresa e",
        "minha loja se chama",
        "minha loja chama",
        "minha loja é",
        "minha loja e",
        "a empresa se chama",
        "a empresa chama",
        "a empresa é",
        "a empresa e",
        "empresa se chama",
        "empresa chama",
        "empresa é",
        "empresa e",
        "a loja se chama",
        "a loja chama",
        "a loja é",
        "a loja e",
        "se chama",
    ]

    empresa_minusculo = empresa.lower()

    for frase in substituicoes:
        if empresa_minusculo.startswith(frase):
            empresa = empresa[len(frase):].strip()
            break

    return empresa.title()


def limpar_segmento(texto: str):
    segmento = texto.strip()

    substituicoes = [
        "atuamos com",
        "atuamos na área de",
        "atuamos na area de",
        "atuamos em",
        "trabalhamos com",
        "trabalhamos na área de",
        "trabalhamos na area de",
        "trabalhamos em",
        "somos do segmento de",
        "somos da área de",
        "somos da area de",
    ]

    segmento_minusculo = segmento.lower()

    for frase in substituicoes:
        if segmento_minusculo.startswith(frase):
            segmento = segmento[len(frase):].strip()
            break

    return segmento


def contem_termo(texto, termos):
    texto = f" {texto.lower()} "

    for termo in termos:
        termo = termo.lower()
        padrao = r"(?<!\w)" + re.escape(termo) + r"(?!\w)"

        if re.search(padrao, texto):
            return True

    return False


def detectar_intencao_cliente(mensagem: str):
    texto = mensagem.lower()

    if contem_termo(texto, [
        "o que é lead",
        "o que e lead",
        "o que significa lead",
        "não sei o que é lead",
        "nao sei o que e lead",
        "lead é o que",
        "lead e o que",
    ]):
        return "duvida_lead"

    if contem_termo(texto, [
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
        "medo de contratar",
        "não gostei",
        "nao gostei",
        "fui enganado",
        "fui enganada"
    ]):
        return "objecao_experiencia_ruim"

    if contem_termo(texto, [
        "estrutura completa",
        "marketing completo",
        "tudo completo",
        "tráfego, social media e atendimento",
        "trafego, social media e atendimento",
        "tráfego social media atendimento",
        "trafego social media atendimento",
        "tráfego e social media",
        "trafego e social media",
        "marketing, tráfego, social media e atendimento",
        "marketing, trafego, social media e atendimento",
    ]):
        return "estrutura_completa"

    if contem_termo(texto, [
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

    if contem_termo(texto, [
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

    if contem_termo(texto, [
        "reunião",
        "reuniao",
        "agenda",
        "agendar",
        "marcar horário",
        "marcar horario"
    ]):
        return "reuniao"

    if contem_termo(texto, [
        "tráfego",
        "trafego",
        "anúncio",
        "anuncio",
        "facebook ads",
        "instagram ads",
        "meta ads"
    ]):
        return "trafego"

    if contem_termo(texto, [
        "site",
        "landing page",
        "website",
        "página de vendas",
        "pagina de vendas"
    ]):
        return "web_design"

    if contem_termo(texto, [
        "social media",
        "instagram",
        "conteúdo",
        "conteudo",
        "rede social",
        "redes sociais",
        "postagem",
        "engajamento"
    ]):
        return "social_media"

    if contem_termo(texto, [
        "identidade visual",
        "design",
        "criativo",
        "arte",
        "logo",
        "marca mais profissional",
        "materiais melhores"
    ]):
        return "design"

    if contem_termo(texto, [
        "automação",
        "automacao",
        "ia",
        "chatbot",
        "sdr",
        "robô",
        "robo",
        "atendimento automático",
        "atendimento automatico"
    ]):
        return "automacao"

    if contem_termo(texto, [
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
        "marcar reuniao",
        "agendar",
        "tenho interesse",
        "quero saber mais",
        "gerar leads",
        "mais clientes",
        "automatizar atendimento",
        "presença digital",
        "atendimento comercial"
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
        "experiencia ruim",
        "não gostei",
        "nao gostei"
    ]

    produtos = {
        "Estrutura Completa": [
            "estrutura completa",
            "marketing completo",
            "tudo completo",
            "tráfego e social media",
            "trafego e social media",
            "marketing, tráfego, social media e atendimento",
            "marketing, trafego, social media e atendimento"
        ],
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
            "logo",
            "marca mais profissional",
            "materiais melhores"
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
    }

    for palavra in palavras_quentes:
        if contem_termo(texto, [palavra]):
            score += 3

    for palavra in palavras_objeção:
        if contem_termo(texto, [palavra]):
            score += 2

    for nome_produto, termos in produtos.items():
        for termo in termos:
            if contem_termo(texto, [termo]):
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
• Se houver objeção ou experiência ruim anterior, Luciano deve reforçar diagnóstico, confiança e clareza antes de falar de valores

Próxima ação recomendada:
Luciano deve entrar em contato para aprofundar o diagnóstico e conduzir a lead para uma reunião comercial.
""".strip()


def resposta_inicial_por_servico(intencao):
    if intencao == "estrutura_completa":
        return (
            "Oi, tudo bem? Eu sou a Sofia, da Forway 😊\n\n"
            "Legal você falar em estrutura completa. Normalmente, quando a empresa procura isso, é porque já percebeu que não adianta olhar só para anúncio ou só para conteúdo separado.\n\n"
            "A ideia é entender como está a geração de possíveis clientes, a presença digital e o atendimento, para o Luciano conseguir olhar o cenário com mais clareza.\n\n"
            "Me fala seu nome para eu registrar direitinho?"
        )

    if intencao == "trafego":
        return (
            "Oi, tudo bem? Eu sou a Sofia, da Forway 😊\n\n"
            "Sobre tráfego pago: a ideia não é só colocar anúncio no ar. O mais importante é atrair pessoas com real interesse no que a empresa oferece.\n\n"
            "Antes de te explicar melhor, vou entender rapidinho seu cenário para passar tudo organizado para o Luciano.\n\n"
            "Me fala seu nome?"
        )

    if intencao == "automacao":
        return (
            "Oi, tudo bem? Eu sou a Sofia, da Forway 😊\n\n"
            "Automação com IA costuma ajudar muito quando a empresa recebe contatos pelo WhatsApp ou Instagram e acaba perdendo oportunidade por demora ou falta de organização.\n\n"
            "Vou entender melhor como funciona hoje o atendimento por aí para o Luciano analisar com mais contexto.\n\n"
            "Qual é o seu nome?"
        )

    if intencao == "social_media":
        return (
            "Oi, tudo bem? Eu sou a Sofia, da Forway 😊\n\n"
            "Trabalhamos sim com social media estratégico. A ideia é ir além de postar por postar: é construir presença, posicionamento e conteúdo com intenção comercial.\n\n"
            "Para eu entender melhor o cenário da marca, me fala seu nome?"
        )

    if intencao == "web_design":
        return (
            "Oi, tudo bem? Eu sou a Sofia, da Forway 😊\n\n"
            "Um site bem feito ajuda muito na credibilidade da empresa e também pode apoiar a captação de novos clientes.\n\n"
            "Vou entender um pouco do seu cenário para o Luciano orientar melhor o caminho.\n\n"
            "Como você se chama?"
        )

    if intencao == "design":
        return (
            "Oi, tudo bem? Eu sou a Sofia, da Forway 😊\n\n"
            "Identidade visual faz muita diferença na forma como o cliente enxerga a empresa. Não é só estética, é percepção de profissionalismo e confiança.\n\n"
            "Vou entender melhor o que você quer melhorar para passar isso bem organizado para o Luciano.\n\n"
            "Qual é o seu nome?"
        )

    return (
        "Oi, tudo bem? Eu sou a Sofia, da Forway 😊\n\n"
        "Vou entender rapidinho seu cenário para deixar tudo organizado para o Luciano continuar com você.\n\n"
        "Como posso te chamar?"
    )


def resposta_base_por_servico(conversa, intencao):
    empresa = conversa.empresa or "sua empresa"

    if intencao == "duvida_lead":
        return (
            "Boa pergunta 😊\n\n"
            "Quando falamos em lead, estamos falando de um possível cliente: alguém que chamou no WhatsApp, pediu orçamento, preencheu um formulário ou demonstrou interesse no seu produto ou serviço.\n\n"
            "Ou seja, é uma oportunidade de venda que precisa ser bem atendida para virar cliente."
        )

    if intencao == "objecao_experiencia_ruim":
        return (
            "Entendo. E faz sentido você ter esse cuidado.\n\n"
            "Quando uma experiência anterior não dá certo, geralmente o problema não está em uma única coisa. Pode ser público errado, comunicação fraca, falta de acompanhamento ou até um processo comercial mal organizado.\n\n"
            "Por isso o Luciano costuma olhar primeiro o cenário antes de indicar qualquer caminho."
        )

    if conversa.servico == "Estrutura Completa":
        return (
            f"Entendi. Pelo que você contou, a {empresa} precisa olhar para o conjunto, não só para uma ação isolada.\n\n"
            "Faz sentido analisar geração de possíveis clientes, presença digital, conteúdo, anúncios e atendimento comercial trabalhando juntos.\n\n"
            "Vou deixar esse contexto organizado para o Luciano olhar com atenção."
        )

    if conversa.servico == "Gestão de Tráfego Pago":
        return (
            f"Entendi. No caso da {empresa}, o ponto principal parece ser atrair pessoas mais qualificadas, e não apenas aumentar visualizações.\n\n"
            "Esse é justamente o cuidado que o Luciano costuma ter antes de indicar uma estratégia de tráfego."
        )

    if conversa.servico == "Atendimento com IA":
        return (
            f"Entendi. Esse cenário da {empresa} é bem comum quando o volume de mensagens começa a crescer.\n\n"
            "A automação ajuda a organizar o primeiro contato, mas sem perder a ideia de atendimento humano e bem conduzido."
        )

    if conversa.servico == "Social Media Estratégico":
        return (
            f"Entendi. Para a {empresa}, o trabalho de social media precisa ir além de postagem bonita.\n\n"
            "O ideal é alinhar conteúdo, posicionamento e objetivo comercial, para a marca aparecer melhor e gerar mais confiança."
        )

    if conversa.servico == "Web Design":
        return (
            f"Entendi. Para a {empresa}, o site pode funcionar como uma vitrine mais profissional e também como apoio para gerar contatos interessados.\n\n"
            "O Luciano consegue avaliar melhor que tipo de estrutura faz sentido para esse momento."
        )

    if conversa.servico == "Design":
        return (
            f"Entendi. A identidade visual da {empresa} precisa transmitir profissionalismo e confiança logo no primeiro contato.\n\n"
            "Isso influencia muito na percepção que o cliente tem antes mesmo de conversar com a empresa."
        )

    return (
        f"Entendi. Pelo que você contou, existe uma oportunidade de organizar melhor a presença digital e o processo comercial da {empresa}.\n\n"
        "Vou deixar isso bem resumido para o Luciano analisar com mais contexto."
    )


def conduzir_conversa(conversa, mensagem: str):
    texto = mensagem.strip()
    canal = conversa.canal.lower()

    if conversa.etapa == "aguardando_humano":

        resposta = (
            f"{conversa.nome or 'Olá'}, suas informações já foram encaminhadas para o Luciano. "
            "Ele pode estar em atendimento ou reunião neste momento, mas assim que possível continuará com você por aqui 😊"
        )

        conversa.historico = (conversa.historico or "") + f"\nCliente: {texto}"
        conversa.historico += f"\nAgente: {resposta}"

        return resposta, analisar_mensagem(conversa.historico)

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

        if intencao == "duvida_lead":
            conversa.etapa = "coletar_nome"

            resposta = (
                "Boa pergunta 😊\n\n"
                "Lead é um possível cliente. Pode ser alguém que chamou no WhatsApp, pediu orçamento, entrou pelo Instagram ou demonstrou interesse no serviço da empresa.\n\n"
                "A Forway ajuda justamente a atrair e organizar melhor esses contatos para aumentar as chances de venda.\n\n"
                "Me fala seu nome para eu entender melhor seu cenário?"
            )

        elif intencao == "objecao_experiencia_ruim":
            conversa.etapa = "entender_objetivo_inicial"

            resposta = (
                "Oi, tudo bem? Eu sou a Sofia, da Forway 😊\n\n"
                "Entendo seu cuidado. Muita empresa chega até a Forway depois de uma experiência que não funcionou bem.\n\n"
                "Antes de falar em qualquer solução, o ideal é entender o que já foi feito e onde travou.\n\n"
                "Hoje, qual é o principal desafio da sua empresa?"
            )

        elif intencao == "conhecer_servicos":
            conversa.etapa = "entender_objetivo_inicial"

            resposta = (
                "Oi, tudo bem? Eu sou a Sofia, da Forway 😊\n\n"
                "A Forway trabalha com tráfego pago, social media estratégico, design, sites, automação com IA e estrutura comercial.\n\n"
                "Mas para não te passar algo genérico, prefiro entender primeiro o momento da empresa.\n\n"
                "Hoje o maior desafio é vender mais, melhorar a presença digital ou organizar melhor o atendimento?"
            )

        elif intencao == "orcamento":
            conversa.etapa = "coletar_nome"

            resposta = (
                "Oi, tudo bem? Eu sou a Sofia, da Forway 😊\n\n"
                "Sobre valores, o Luciano prefere entender primeiro o cenário da empresa antes de falar em proposta. Assim ele não te passa algo genérico.\n\n"
                "Me fala seu nome para eu organizar seu atendimento?"
            )

        elif intencao == "reuniao":
            conversa.etapa = "coletar_nome"

            resposta = (
                "Oi, tudo bem? Eu sou a Sofia, da Forway 😊\n\n"
                "Claro. Antes de encaminhar para o Luciano, vou pegar algumas informações rápidas para ele já entrar na conversa com contexto.\n\n"
                "Qual é o seu nome?"
            )

        elif intencao in [
            "estrutura_completa",
            "trafego",
            "automacao",
            "social_media",
            "web_design",
            "design",
        ]:
            conversa.etapa = "coletar_nome"
            resposta = resposta_inicial_por_servico(intencao)

        else:
            conversa.etapa = "coletar_nome"
            resposta = resposta_inicial_por_servico("geral")

    elif conversa.etapa == "entender_objetivo_inicial":

        conversa.objetivo = texto

        analise = analisar_mensagem(f"""
        {conversa.historico or ''}
        {texto}
        """)

        if conversa.servico is None and analise["produto"] != "não identificado":
            conversa.servico = analise["produto"]

        conversa.etapa = "coletar_nome"

        resposta = (
            "Entendi.\n\n"
            "Já deu para ter uma noção melhor do cenário. Agora vou registrar seus dados para o Luciano conseguir continuar com mais contexto.\n\n"
            "Como posso te chamar?"
        )

    elif conversa.etapa == "coletar_nome":

        conversa.nome = limpar_nome_cliente(texto)
        conversa.etapa = "coletar_segmento"

        resposta = (
            f"Prazer, {conversa.nome} 😊\n\n"
            "Antes de continuar, me conta uma coisa:\n\n"
            "Qual é o segmento da sua empresa?"
        )

    elif conversa.etapa == "coletar_segmento":

        conversa.segmento = limpar_segmento(texto)
        conversa.etapa = "coletar_empresa"

        resposta = (
            "Perfeito 😊\n\n"
            f"Então você atua no segmento de {conversa.segmento}.\n\n"
            "E qual é o nome da empresa?"
        )

    elif conversa.etapa == "coletar_empresa":

        conversa.empresa = limpar_nome_empresa(texto)

        if conversa.objetivo:

            if canal in ["instagram", "facebook", "messenger"]:

                conversa.etapa = "coletar_whatsapp"

                resposta = (
                    "Perfeito 😊\n\n"
                    f"Então estamos falando da {conversa.empresa}, que atua no segmento de {conversa.segmento}.\n\n"
                    "Para o Luciano continuar esse atendimento com mais contexto, me passa seu WhatsApp?"
                )

            else:

                conversa.etapa = "aguardando_humano"

                resposta = (
                    "Perfeito 😊\n\n"
                    f"Então estamos falando da {conversa.empresa}, que atua no segmento de {conversa.segmento}.\n\n"
                    "Já organizei tudo para o Luciano analisar com mais contexto e continuar essa conversa com você."
                )

        else:

            conversa.etapa = "entender_objetivo"

            resposta = (
                "Perfeito 😊\n\n"
                f"Então estamos falando da {conversa.empresa}, que atua no segmento de {conversa.segmento}.\n\n"
                "Agora me conta uma coisa:\n\n"
                "Hoje qual é o principal desafio da empresa?"
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

        resposta_base = resposta_base_por_servico(conversa, intencao)

        if canal in ["instagram", "facebook", "messenger"]:

            conversa.etapa = "coletar_whatsapp"

            resposta = (
                f"{resposta_base}\n\n"
                "Para o Luciano continuar com você de forma mais direta, me passa seu WhatsApp?"
            )

        else:

            conversa.etapa = "aguardando_humano"

            resposta = (
                f"{resposta_base}\n\n"
                f"Já deixei as principais informações organizadas, {conversa.nome}.\n\n"
                "Vou encaminhar para o Luciano analisar seu caso com mais calma e continuar essa conversa com você."
            )

    elif conversa.etapa == "coletar_whatsapp":

        conversa.telefone = texto
        conversa.etapa = "aguardando_humano"

        resposta = (
            f"Perfeito, {conversa.nome} 😊\n\n"
            f"Já organizei as informações da {conversa.empresa} para o Luciano entender melhor o cenário.\n\n"
            "Ele vai continuar seu atendimento assim que possível."
        )

    else:

        resposta = (
            "Já deixei suas informações organizadas para o time comercial da Forway. "
            "O Luciano continua com você assim que possível 😊"
        )

    conversa.historico += f"\nAgente: {resposta}"

    return resposta, analise