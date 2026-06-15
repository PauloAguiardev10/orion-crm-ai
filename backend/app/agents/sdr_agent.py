import re
import random

from app.services.gpt_service import gerar_resumo_comercial_gpt


def contem_termo(texto, termos):
    texto = f" {texto.lower()} "
    for termo in termos:
        termo = termo.lower()
        padrao = r"(?<!\w)" + re.escape(termo) + r"(?!\w)"
        if re.search(padrao, texto):
            return True
    return False


def resposta_aleatoria(lista):
    return random.choice(lista)


def limpar_nome_cliente(texto: str):
    nome = texto.strip()
    substituicoes = [
        "meu nome é", "meu nome e", "eu sou", "sou o", "sou a",
        "sou", "me chamo", "me chama de", "pode me chamar de",
        "aqui é", "aqui e",
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
        "minha empresa se chama", "minha empresa chama",
        "minha empresa é", "minha empresa e",
        "minha loja se chama", "minha loja chama",
        "minha loja é", "minha loja e",
        "a empresa se chama", "a empresa chama",
        "a empresa é", "a empresa e",
        "empresa se chama", "empresa chama",
        "empresa é", "empresa e",
        "a loja se chama", "a loja chama",
        "a loja é", "a loja e",
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
        "atuamos com", "atuamos na área de", "atuamos na area de",
        "atuamos em", "trabalhamos com", "trabalhamos na área de",
        "trabalhamos na area de", "trabalhamos em",
        "somos do segmento de", "somos da área de", "somos da area de",
    ]
    segmento_minusculo = segmento.lower()
    for frase in substituicoes:
        if segmento_minusculo.startswith(frase):
            segmento = segmento[len(frase):].strip()
            break
    return segmento


def detectar_interacao_social(mensagem: str):
    texto = mensagem.lower().strip()

    if contem_termo(texto, [
        "obrigado", "obrigada", "valeu", "agradeço", "agradeco",
        "muito obrigado", "muito obrigada", "ok obrigado", "ok obrigada"
    ]):
        return "agradecimento"

    if contem_termo(texto, [
        "ok", "certo", "beleza", "show", "perfeito", "entendi",
        "tranquilo", "combinado", "ta certo", "tá certo"
    ]):
        return "confirmacao"

    if contem_termo(texto, [
        "tchau", "até mais", "ate mais", "até logo", "ate logo"
    ]):
        return "despedida"

    return None


def detectar_intencao_cliente(mensagem: str):
    texto = mensagem.lower()

    if contem_termo(texto, [
        "o que é lead", "o que e lead", "o que significa lead",
        "não sei o que é lead", "nao sei o que e lead",
        "lead é o que", "lead e o que",
    ]):
        return "duvida_lead"

    if contem_termo(texto, [
        "já tentei", "ja tentei", "não deu certo", "nao deu certo",
        "não funcionou", "nao funcionou", "experiência ruim",
        "experiencia ruim", "outra agência", "outra agencia",
        "tenho medo", "medo de contratar", "não gostei", "nao gostei",
        "fui enganado", "fui enganada"
    ]):
        return "objecao_experiencia_ruim"

    if contem_termo(texto, [
        "estrutura completa", "marketing completo", "tudo completo",
        "tráfego e social media", "trafego e social media",
        "tráfego, social media e atendimento",
        "trafego, social media e atendimento",
    ]):
        return "estrutura_completa"

    if contem_termo(texto, [
        "quais serviços", "quais servicos",
        "serviços vocês oferecem", "servicos voces oferecem",
        "o que vocês fazem", "o que voces fazem",
        "como vocês trabalham", "como voces trabalham",
        "me fala dos serviços", "me fala dos servicos",
        "o que oferecem", "não sei o que preciso",
        "nao sei o que preciso", "não sei qual serviço",
        "nao sei qual servico", "quero conhecer",
        "serviços da forway", "servicos da forway",
        "vi um anúncio", "vi um anuncio",
        "vi vocês no instagram", "vi voces no instagram",
        "vim pelo instagram", "gostaria de saber como trabalham",
        "gostaria de saber como vocês trabalham",
        "gostaria de saber como voces trabalham",
    ]):
        return "conhecer_servicos"

    if contem_termo(texto, [
        "orçamento", "orcamento", "preço", "preco", "valor",
        "quanto custa", "quanto fica", "pacote", "pacotes"
    ]):
        return "orcamento"

    if contem_termo(texto, [
        "reunião", "reuniao", "agenda", "agendar",
        "marcar horário", "marcar horario"
    ]):
        return "reuniao"

    if contem_termo(texto, [
        "tráfego", "trafego", "anúncio", "anuncio",
        "facebook ads", "instagram ads", "meta ads"
    ]):
        return "trafego"

    if contem_termo(texto, [
        "site", "landing page", "website",
        "página de vendas", "pagina de vendas"
    ]):
        return "web_design"

    if contem_termo(texto, [
        "social media", "instagram", "conteúdo", "conteudo",
        "rede social", "redes sociais", "postagem", "engajamento"
    ]):
        return "social_media"

    if contem_termo(texto, [
        "identidade visual", "design", "criativo", "arte",
        "logo", "marca mais profissional", "materiais melhores"
    ]):
        return "design"

    if contem_termo(texto, [
        "automação", "automacao", "ia", "chatbot", "sdr",
        "robô", "robo", "atendimento automático", "atendimento automatico"
    ]):
        return "automacao"

    if contem_termo(texto, [
        "oi", "olá", "ola", "bom dia", "boa tarde", "boa noite"
    ]):
        return "saudacao"

    return "geral"


def analisar_mensagem(mensagem: str):
    texto = mensagem.lower()
    score = 0
    produto = "não identificado"
    prioridade = "baixa"

    palavras_quentes = [
        "comprar", "orçamento", "orcamento", "preço", "preco",
        "valor", "contratar", "fechar", "proposta", "quanto custa",
        "quero contratar", "vender mais", "aumentar vendas",
        "marcar reunião", "marcar reuniao", "agendar",
        "tenho interesse", "quero saber mais", "gerar leads",
        "mais clientes", "captar clientes", "automatizar atendimento",
        "presença digital", "presenca digital", "atendimento comercial"
    ]

    palavras_objecao = [
        "já tentei", "ja tentei", "não deu certo", "nao deu certo",
        "não funcionou", "nao funcionou", "outra agência",
        "outra agencia", "experiência ruim", "experiencia ruim",
        "não gostei", "nao gostei"
    ]

    produtos = {
        "Estrutura Completa": [
            "estrutura completa", "marketing completo", "tudo completo",
            "tráfego e social media", "trafego e social media",
        ],
        "Gestão de Tráfego Pago": [
            "tráfego", "trafego", "anúncio", "anuncio",
            "facebook ads", "instagram ads", "meta ads"
        ],
        "Social Media Estratégico": [
            "social media", "conteúdo", "conteudo",
            "instagram", "postagem", "redes sociais"
        ],
        "Design": [
            "design", "identidade visual", "criativo",
            "arte", "logo", "marca mais profissional",
            "materiais melhores"
        ],
        "Atendimento com IA": [
            "automação", "automacao", "ia", "chatbot",
            "sdr", "atendimento automático", "atendimento automatico"
        ],
        "Web Design": [
            "site", "landing page", "website",
            "página de vendas", "pagina de vendas"
        ],
    }

    for palavra in palavras_quentes:
        if contem_termo(texto, [palavra]):
            score += 3

    for palavra in palavras_objecao:
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

Próxima ação recomendada:
Luciano deve continuar o atendimento de forma consultiva e entender melhor o cenário da lead.
""".strip()


def resposta_inicial_por_servico(intencao):
    if intencao == "trafego":
        return (
            "Que bom que entrou em contato 😊\n\n"
            "Posso te ajudar com tráfego pago sim.\n\n"
            "Antes de te encaminhar para o especialista, me fala seu nome?"
        )

    if intencao == "conhecer_servicos":
        return (
            "Bom falar com você 😊\n\n"
            "A Forway trabalha entendendo primeiro o momento da empresa para depois indicar o melhor caminho.\n\n"
            "Hoje você busca mais vendas, mais contatos ou fortalecer a presença da marca?"
        )

    if intencao == "orcamento":
        return (
            "Claro 😊\n\n"
            "Para falar de valores sem te passar algo genérico, o ideal é entender primeiro seu cenário.\n\n"
            "Me fala seu nome?"
        )

    if intencao == "reuniao":
        return (
            "Claro 😊\n\n"
            "Antes de te passar para o Luciano, vou pegar um contexto rápido para ele já continuar com mais clareza.\n\n"
            "Qual é o seu nome?"
        )

    if intencao == "automacao":
        return (
            "Legal 😊\n\n"
            "Automação com IA pode ajudar bastante quando a empresa recebe contatos e precisa organizar melhor o primeiro atendimento.\n\n"
            "Me fala seu nome para eu entender seu cenário?"
        )

    if intencao == "social_media":
        return (
            "Claro 😊\n\n"
            "A Forway trabalha social media de forma estratégica, pensando em posicionamento e resultado, não só postagem.\n\n"
            "Como posso te chamar?"
        )

    if intencao == "web_design":
        return (
            "Claro 😊\n\n"
            "Um site bem estruturado ajuda muito na credibilidade e também na geração de contatos.\n\n"
            "Me fala seu nome?"
        )

    if intencao == "design":
        return (
            "Claro 😊\n\n"
            "Design e identidade visual fazem muita diferença na forma como o cliente percebe a empresa.\n\n"
            "Como posso te chamar?"
        )

    if intencao == "estrutura_completa":
        return (
            "Perfeito 😊\n\n"
            "Quando a empresa busca uma estrutura mais completa, o ideal é olhar tráfego, conteúdo, atendimento e presença digital juntos.\n\n"
            "Me fala seu nome para eu organizar melhor seu atendimento?"
        )

    return (
        "Oi, tudo bem? 😊\n\n"
        "Sou a Sofia, da Forway.\n\n"
        "Me conta rapidinho: você quer entender algum serviço específico ou precisa de ajuda para saber o melhor caminho?"
    )


def resposta_apos_encaminhamento(texto, nome=None):
    interacao = detectar_interacao_social(texto)

    if interacao == "agradecimento":
        return resposta_aleatoria([
            "Eu que agradeço pelo contato 😊\n\nJá deixei tudo organizado para o Luciano continuar com você.",
            "Obrigado você pela confiança 😊\n\nO Luciano já recebeu as informações e continua por aqui assim que possível.",
            "Foi um prazer falar com você 😊\n\nAssim que o Luciano estiver disponível, ele segue o atendimento por aqui."
        ])

    if interacao == "confirmacao":
        return resposta_aleatoria([
            "Perfeito 😊\n\nJá deixei tudo certo por aqui.",
            "Combinado 😊\n\nO Luciano continua com você assim que possível.",
            "Tudo certo 😊\n\nSeu atendimento já está encaminhado."
        ])

    if interacao == "despedida":
        return resposta_aleatoria([
            "Combinado 😊\n\nObrigado pelo contato. O Luciano segue com você assim que estiver disponível.",
            "Tudo certo 😊\n\nFoi um prazer te atender.",
            "Perfeito 😊\n\nQualquer novidade o Luciano continua por aqui."
        ])

    return resposta_aleatoria([
        "Seu atendimento já está com o Luciano 😊\n\nAssim que ele estiver disponível, continua com você por aqui.",
        "Já deixei as informações organizadas para o Luciano analisar com calma 😊",
        "Tudo certo por aqui 😊\n\nO Luciano segue com você assim que possível."
    ])


def resposta_base_por_servico(conversa, intencao):
    if intencao == "duvida_lead":
        return (
            "Lead é um possível cliente 😊\n\n"
            "Pode ser alguém que chamou no WhatsApp, pediu orçamento, veio pelo Instagram ou demonstrou interesse em algum serviço."
        )

    if intencao == "objecao_experiencia_ruim":
        return (
            "Entendo seu cuidado.\n\n"
            "Quando uma experiência anterior não foi boa, o ideal é olhar o que foi feito, o público, a comunicação e o acompanhamento.\n\n"
            "Assim o Luciano consegue orientar com mais segurança."
        )

    if conversa.servico == "Gestão de Tráfego Pago":
        return (
            "Entendi.\n\n"
            "Nesse caso, o foco não é só colocar anúncio no ar, mas atrair pessoas com perfil real de compra."
        )

    if conversa.servico == "Atendimento com IA":
        return (
            "Entendi.\n\n"
            "Nesse cenário, a automação pode ajudar a organizar o primeiro contato sem perder o tom humano do atendimento."
        )

    if conversa.servico == "Social Media Estratégico":
        return (
            "Entendi.\n\n"
            "Para social media, o ideal é alinhar conteúdo, posicionamento e objetivo comercial."
        )

    if conversa.servico == "Web Design":
        return (
            "Entendi.\n\n"
            "Um site pode funcionar como uma vitrine mais profissional e também apoiar a geração de contatos."
        )

    if conversa.servico == "Design":
        return (
            "Entendi.\n\n"
            "A identidade visual influencia muito na percepção de profissionalismo e confiança da empresa."
        )

    if conversa.servico == "Estrutura Completa":
        return (
            "Entendi.\n\n"
            "Nesse caso faz sentido olhar presença digital, anúncios, conteúdo e atendimento de forma integrada."
        )

    return (
        "Entendi.\n\n"
        "Já deu para ter uma boa noção do que você busca."
    )


def conduzir_conversa(conversa, mensagem: str):
    texto = mensagem.strip()
    canal = conversa.canal.lower()

    if conversa.etapa == "aguardando_humano":
        resposta = resposta_apos_encaminhamento(texto, conversa.nome)
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
                "Lead é um possível cliente, como alguém que chama no WhatsApp, pede orçamento ou vem pelo Instagram.\n\n"
                "Me fala seu nome para eu entender melhor seu cenário?"
            )

        elif intencao == "objecao_experiencia_ruim":
            conversa.etapa = "entender_objetivo_inicial"
            resposta = (
                "Entendo seu cuidado.\n\n"
                "Muita empresa chega até a Forway depois de uma experiência que não funcionou bem.\n\n"
                "Antes de indicar qualquer caminho, o ideal é entender o que aconteceu e qual é seu objetivo agora."
            )

        elif intencao == "conhecer_servicos":
            conversa.etapa = "entender_objetivo_inicial"
            resposta = resposta_inicial_por_servico("conhecer_servicos")

        elif intencao in [
            "orcamento", "reuniao", "estrutura_completa", "trafego",
            "automacao", "social_media", "web_design", "design"
        ]:
            conversa.etapa = "coletar_nome"
            resposta = resposta_inicial_por_servico(intencao)

        else:
            conversa.etapa = "coletar_nome"
            resposta = resposta_inicial_por_servico("geral")

    elif conversa.etapa == "entender_objetivo_inicial":

        conversa.objetivo = texto
        analise = analisar_mensagem(f"{conversa.historico or ''}\n{texto}")

        if conversa.servico is None and analise["produto"] != "não identificado":
            conversa.servico = analise["produto"]

        conversa.etapa = "coletar_nome"

        resposta = (
            "Entendi 😊\n\n"
            "Para eu organizar melhor esse atendimento, como posso te chamar?"
        )

    elif conversa.etapa == "coletar_nome":

        conversa.nome = limpar_nome_cliente(texto)
        conversa.etapa = "coletar_empresa"

        resposta = (
            f"Prazer, {conversa.nome} 😊\n\n"
            "Qual é o nome da sua empresa?"
        )

    elif conversa.etapa == "coletar_empresa":

        conversa.empresa = limpar_nome_empresa(texto)
        conversa.etapa = "coletar_segmento"

        resposta = (
            "Legal 😊\n\n"
            "E qual é a área de atuação da empresa?"
        )

    elif conversa.etapa == "coletar_segmento":

        conversa.segmento = limpar_segmento(texto)

        if conversa.objetivo:
            if canal in ["instagram", "facebook", "messenger"]:
                conversa.etapa = "coletar_whatsapp"
                resposta = (
                    "Perfeito.\n\n"
                    "Para o Luciano continuar com você de forma mais direta, me passa seu WhatsApp?"
                )
            else:
                conversa.etapa = "aguardando_humano"
                resposta = (
                    "Perfeito 😊\n\n"
                    "Já deixei as informações principais organizadas para o Luciano analisar seu cenário.\n\n"
                    "Ele continua com você por aqui assim que estiver disponível."
                )
        else:
            conversa.etapa = "entender_objetivo"
            resposta = (
                "Entendi.\n\n"
                "Hoje o que você mais busca: gerar mais vendas, receber mais contatos ou fortalecer a presença da marca?"
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
                "Para o Luciano continuar de forma mais direta, me passa seu WhatsApp?"
            )
        else:
            conversa.etapa = "aguardando_humano"
            resposta = (
                f"{resposta_base}\n\n"
                "Já organizei as informações principais para o Luciano analisar seu caso com mais calma.\n\n"
                "Ele continua essa conversa com você por aqui assim que estiver disponível 😊"
            )

    elif conversa.etapa == "coletar_whatsapp":

        conversa.telefone = texto
        conversa.etapa = "aguardando_humano"

        resposta = (
            "Perfeito 😊\n\n"
            "Já deixei tudo organizado para o Luciano continuar com você."
        )

    else:
        resposta = resposta_apos_encaminhamento(texto, conversa.nome)

    conversa.historico += f"\nAgente: {resposta}"

    return resposta, analise
