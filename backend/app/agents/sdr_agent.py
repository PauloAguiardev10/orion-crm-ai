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


def parece_nome(texto: str):
    texto = texto.lower().strip()

    palavras_bloqueadas = [
        "quero", "queria", "gostaria", "serviço", "serviços",
        "servico", "servicos", "informação", "informações",
        "informacao", "informacoes", "tráfego", "trafego",
        "instagram", "facebook", "whatsapp", "como funciona",
        "orçamento", "orcamento", "valor", "preço", "preco",
        "empresa", "anúncio", "anuncio", "forway", "oferece",
        "trabalham", "atendimento", "marketing"
    ]

    for palavra in palavras_bloqueadas:
        if palavra in texto:
            return False

    if len(texto.split()) > 4:
        return False

    if len(texto) < 2:
        return False

    return True


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


def saudacao_personalizada(texto: str):
    texto = texto.lower()

    if "bom dia" in texto:
        return "Bom dia 😊"

    if "boa tarde" in texto:
        return "Boa tarde 😊"

    if "boa noite" in texto:
        return "Boa noite 😊"

    if "olá" in texto or "ola" in texto or "oi" in texto:
        return "Olá 😊"

    return "Olá 😊"


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
    texto = mensagem.lower().strip()

    grupos = [
        ("duvida_lead", ["o que é lead","o que e lead","o que significa lead","não sei o que é lead","nao sei o que e lead","lead é o que","lead e o que","o que são leads","o que sao leads"]),
        ("objecao_experiencia_ruim", ["já tentei","ja tentei","não deu certo","nao deu certo","não funcionou","nao funcionou","experiência ruim","experiencia ruim","outra agência","outra agencia","outras agências","outras agencias","tenho medo","medo de contratar","não gostei","nao gostei","fui enganado","fui enganada","já perdi dinheiro","ja perdi dinheiro","joguei dinheiro fora","não confio","nao confio"]),
        ("estrutura_completa", ["estrutura completa","marketing completo","tudo completo","quero tudo","pacote completo","serviço completo","servico completo","solução completa","solucao completa","quero todos os serviços","quero todos os servicos","quero todos os seus serviços","quero todos os seus servicos","quero todos os serviços oferecidos","quero todos os servicos oferecidos","quero todos os serviços oferecido","quero todos os servicos oferecido","quero tudo que vocês oferecem","quero tudo que voces oferecem","quero tudo que a forway oferece","tenho interesse em todos os serviços","tenho interesse em todos os servicos","preciso de tudo","preciso de todos os serviços","preciso de todos os servicos","tráfego e social media","trafego e social media","tráfego, social media e atendimento","trafego, social media e atendimento"]),
        ("conhecer_servicos", ["quais serviços","quais servicos","quais são os serviços","quais sao os servicos","que serviços vocês oferecem","que servicos voces oferecem","serviços vocês oferecem","servicos voces oferecem","serviços que a forway oferece","servicos que a forway oferece","informações sobre os serviços","informacoes sobre os servicos","o que vocês fazem","o que voces fazem","como vocês trabalham","como voces trabalham","me fala dos serviços","me fala dos servicos","me explica os serviços","me explica os servicos","o que oferecem","não sei o que preciso","nao sei o que preciso","não sei qual serviço","nao sei qual servico","quero conhecer","serviços da forway","servicos da forway","gostaria de saber os serviços","gostaria de saber os servicos","gostaria de saber sobre os serviços","gostaria de saber sobre os servicos","gostaria de saber mais sobre seus serviços","gostaria de saber mais sobre seus servicos","gostaria de saber sobre seus serviços","gostaria de saber sobre seus servicos","quero saber sobre seus serviços","quero saber sobre seus servicos","quero saber mais sobre seus serviços","quero saber mais sobre seus servicos","seus serviços","seus servicos","serviços de vocês","servicos de voces","saber sobre os serviços","saber sobre os servicos","saber mais sobre os serviços","saber mais sobre os servicos","saber mais sobre seus serviços","saber mais sobre seus servicos"]),
        ("anuncio_instagram", ["vi um anúncio","vi um anuncio","vi vocês no instagram","vi voces no instagram","vim pelo instagram","vim do instagram","achei vocês no instagram","achei voces no instagram","anúncio de vocês","anuncio de voces","vi no facebook","vim pelo facebook","vi uma propaganda"]),
        ("orcamento", ["orçamento","orcamento","preço","preco","valor","quanto custa","quanto fica","qual o valor","qual valor","quanto vocês cobram","quanto voces cobram","investimento","mensalidade","pacote","pacotes","proposta"]),
        ("reuniao", ["reunião","reuniao","agenda","agendar","agendamento","marcar horário","marcar horario","marcar uma reunião","marcar uma reuniao","falar com o luciano","quero falar com o luciano","falar com especialista","falar com um especialista"]),
        ("contratacao", ["quero contratar","quero fechar","vamos fechar","fechar negócio","fechar negocio","quero começar","quero comecar","podemos começar","podemos comecar","quero comprar","tenho interesse em contratar","quero contratar vocês","quero contratar voces"]),
        ("trafego", ["tráfego","trafego","tráfego pago","trafego pago","gestão de tráfego","gestao de trafego","anúncio","anuncio","anúncios","anuncios","facebook ads","instagram ads","meta ads","google ads","campanha paga","campanhas pagas","mídia paga","midia paga"]),
        ("web_design", ["site","landing page","website","web site","página de vendas","pagina de vendas","criar um site","fazer um site","site profissional","loja virtual"]),
        ("social_media", ["social media","social mídia","social midia","gestão de redes sociais","gestao de redes sociais","instagram","conteúdo","conteudo","rede social","redes sociais","postagem","postagens","engajamento","feed","reels","stories","cuidar do instagram","gerenciar instagram"]),
        ("design", ["identidade visual","design","criativo","criativos","arte gráfica","arte grafica","artes gráficas","artes graficas","criação de arte","criacao de arte","criação de artes","criacao de artes","quero um logo","quero criar um logo","preciso de um logo","criar um logo","fazer um logo","criar logo","fazer logo","criação de logo","criacao de logo","logotipo","marca mais profissional","materiais melhores","material gráfico","material grafico","identidade da marca"]),
        ("automacao", ["automação","automacao","automação de atendimento","automacao de atendimento","ia","inteligência artificial","inteligencia artificial","chatbot","sdr","agente de ia","agente ia","robô","robo","atendimento automático","atendimento automatico","atendimento automatizado","automatizar atendimento","automatizar whatsapp","automatizar meu whatsapp","automatizar o whatsapp","automatizar nosso whatsapp","automatizar as mensagens","automatizar mensagens","primeiro atendimento"]),
        ("objetivo_comercial", ["vender mais","aumentar vendas","aumentar minhas vendas","aumentar as vendas","gerar mais vendas","gerar vendas","mais clientes","conseguir mais clientes","captar clientes","gerar leads","mais leads","mais contatos","receber mais contatos","gerar contatos","fortalecer minha marca","fortalecer a marca","fortalecer presença","fortalecer a presença","melhorar minha presença digital","presença digital","presenca digital"]),
        ("saudacao", ["oi","olá","ola","bom dia","boa tarde","boa noite","e aí","e ai","opa"]),
    ]

    for intencao, termos in grupos:
        if contem_termo(texto, termos):
            return intencao
    return "geral"


def analisar_mensagem(mensagem: str):
    """Classificação comercial determinística com score limitado de 0 a 10."""
    texto = mensagem.lower()
    score = 0
    produto = "não identificado"

    produtos = {
        "Estrutura Completa": ["estrutura completa","marketing completo","tudo completo","pacote completo","serviço completo","servico completo","solução completa","solucao completa","quero tudo","quero todos os serviços","quero todos os servicos","quero todos os seus serviços","quero todos os seus servicos","quero todos os serviços oferecidos","quero todos os servicos oferecidos","quero todos os serviços oferecido","quero todos os servicos oferecido","quero tudo que vocês oferecem","quero tudo que voces oferecem","quero tudo que a forway oferece","tenho interesse em todos os serviços","tenho interesse em todos os servicos","preciso de todos os serviços","preciso de todos os servicos","tráfego e social media","trafego e social media"],
        "Gestão de Tráfego Pago": ["tráfego","trafego","tráfego pago","trafego pago","gestão de tráfego","gestao de trafego","anúncio","anuncio","anúncios","anuncios","facebook ads","instagram ads","meta ads","google ads","campanha paga","campanhas pagas","mídia paga","midia paga"],
        "Social Media Estratégico": ["social media","social mídia","social midia","conteúdo","conteudo","instagram","postagem","postagens","redes sociais","rede social","engajamento","feed","reels","stories","gestão de redes sociais","gestao de redes sociais"],
        "Design": ["design","identidade visual","criativo","criativos","arte gráfica","arte grafica","artes gráficas","artes graficas","criação de arte","criacao de arte","criação de artes","criacao de artes","quero um logo","quero criar um logo","preciso de um logo","criar um logo","fazer um logo","criar logo","fazer logo","criação de logo","criacao de logo","logotipo","marca mais profissional","materiais melhores","material gráfico","material grafico"],
        "Atendimento com IA": ["automação","automacao","ia","inteligência artificial","inteligencia artificial","chatbot","sdr","agente de ia","agente ia","atendimento automático","atendimento automatico","atendimento automatizado","automatizar atendimento","automatizar whatsapp","automatizar meu whatsapp","automatizar o whatsapp","automatizar nosso whatsapp","automatizar as mensagens","automatizar mensagens"],
        "Web Design": ["site","landing page","website","web site","página de vendas","pagina de vendas","loja virtual","site profissional"],
    }

    for nome_produto, termos in produtos.items():
        if contem_termo(texto, termos):
            produto = nome_produto
            if nome_produto == "Estrutura Completa":
                break

    # Sinais independentes: cada categoria pontua uma vez.
    if contem_termo(texto, ["quero contratar","vamos fechar","quero fechar","fechar negócio","fechar negocio","quero começar","quero comecar","podemos começar","podemos comecar","quero comprar","tenho interesse em contratar"]):
        score += 6

    if contem_termo(texto, ["orçamento","orcamento","preço","preco","valor","quanto custa","quanto fica","qual o valor","quanto vocês cobram","quanto voces cobram","proposta","investimento","mensalidade","reunião","reuniao","agendar","marcar reunião","marcar reuniao","marcar uma reunião","marcar uma reuniao","falar com o luciano","falar com especialista"]):
        score += 4

    if contem_termo(texto, ["vender mais","aumentar vendas","aumentar minhas vendas","aumentar as vendas","melhorar minhas vendas","gerar mais vendas","gerar vendas","mais clientes","conseguir mais clientes","captar clientes","conseguir clientes","gerar leads","mais leads","mais contatos","receber mais contatos","gerar contatos","fortalecer a marca","fortalecer minha marca","fortalecer a presença","fortalecer presença","presença digital","presenca digital","melhorar minha presença digital","melhorar o instagram","automatizar atendimento","automatizar whatsapp","melhorar atendimento"]):
        score += 3

    if produto != "não identificado":
        score += 1

    if produto == "Estrutura Completa":
        score += 3

    if contem_termo(texto, ["urgente","urgência","urgencia","o quanto antes","ainda hoje","essa semana","esta semana","preciso começar logo","preciso comecar logo","quero começar logo","quero comecar logo","imediatamente"]):
        score += 2

    if contem_termo(texto, ["já tentei","ja tentei","não deu certo","nao deu certo","não funcionou","nao funcionou","outra agência","outra agencia","experiência ruim","experiencia ruim","já perdi dinheiro","ja perdi dinheiro","fui enganado","fui enganada"]):
        score += 1

    score = min(score, 10)

    if score >= 9:
        temperatura, prioridade = "quentíssima", "alta"
    elif score >= 6:
        temperatura, prioridade = "quente", "alta"
    elif score >= 3:
        temperatura, prioridade = "morna", "média"
    else:
        temperatura, prioridade = "fria", "baixa"

    return {"temperatura": temperatura, "score": score, "produto": produto, "prioridade": prioridade}

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


def resposta_servicos_forway(saudacao=None):
    inicio = f"{saudacao}\n\n" if saudacao else "Claro 😊\n\n"

    return (
        f"{inicio}"
        "Hoje a Forway trabalha com:\n\n"
        "• Gestão de tráfego pago\n"
        "• Social media estratégico\n"
        "• Design\n"
        "• Atendimento automatizado com IA\n"
        "• Web design\n"
        "• Treinamento e suporte comercial\n\n"
        "Para eu organizar melhor seu atendimento, como posso te chamar?"
    )


def resposta_inicial_por_servico(intencao, mensagem=""):
    saudacao = saudacao_personalizada(mensagem)

    if intencao == "saudacao":
        return (
            f"{saudacao}\n\n"
            "Tudo bem?\n\n"
            "Sou a Sofia, da Forway.\n\n"
            "Como posso ajudar você hoje?"
        )

    if intencao == "conhecer_servicos":
        return resposta_servicos_forway()

    if intencao == "anuncio_instagram":
        return (
            f"{saudacao}\n\n"
            "Que bom que nosso anúncio chegou até você 😊\n\n"
            "A Forway trabalha entendendo primeiro o objetivo da empresa para indicar uma estratégia mais adequada.\n\n"
            "Hoje você busca mais vendas, mais contatos ou fortalecer a presença da marca?"
        )

    if intencao == "trafego":
        return (
            f"{saudacao}\n\n"
            "Posso te ajudar com tráfego pago sim.\n\n"
            "Antes de te encaminhar para o especialista, me fala seu nome?"
        )

    if intencao == "orcamento":
        return (
            f"{saudacao}\n\n"
            "Para falar de valores sem te passar algo genérico, o ideal é entender primeiro seu cenário.\n\n"
            "Me fala seu nome?"
        )

    if intencao == "reuniao":
        return (
            f"{saudacao}\n\n"
            "Antes de te passar para o Luciano, vou pegar um contexto rápido para ele já continuar com mais clareza.\n\n"
            "Qual é o seu nome?"
        )

    if intencao == "automacao":
        return (
            f"{saudacao}\n\n"
            "Automação com IA pode ajudar bastante quando a empresa recebe contatos e precisa organizar melhor o primeiro atendimento.\n\n"
            "Me fala seu nome para eu entender seu cenário?"
        )

    if intencao == "social_media":
        return (
            f"{saudacao}\n\n"
            "A Forway trabalha social media de forma estratégica, pensando em posicionamento e resultado, não só postagem.\n\n"
            "Como posso te chamar?"
        )

    if intencao == "web_design":
        return (
            f"{saudacao}\n\n"
            "Um site bem estruturado ajuda muito na credibilidade e também na geração de contatos.\n\n"
            "Me fala seu nome?"
        )

    if intencao == "design":
        return (
            f"{saudacao}\n\n"
            "Design e identidade visual fazem muita diferença na forma como o cliente percebe a empresa.\n\n"
            "Como posso te chamar?"
        )

    if intencao == "estrutura_completa":
        return (
            f"{saudacao}\n\n"
            "Quando a empresa busca uma estrutura mais completa, o ideal é olhar tráfego, conteúdo, atendimento e presença digital juntos.\n\n"
            "Me fala seu nome para eu organizar melhor seu atendimento?"
        )

    if intencao == "contratacao":
        return (
            f"{saudacao}\n\n"
            "Perfeito 😊\n\n"
            "Para eu organizar seu atendimento e o Luciano já continuar com o contexto certo, como posso te chamar?"
        )

    if intencao == "objetivo_comercial":
        return (
            f"{saudacao}\n\n"
            "Entendi 😊\n\n"
            "Esse é exatamente o tipo de objetivo que vale analisar com mais contexto.\n\n"
            "Para eu organizar melhor seu atendimento, como posso te chamar?"
        )

    return (
        f"{saudacao}\n\n"
        "Sou a Sofia, da Forway.\n\n"
        "Como posso ajudar você hoje?"
    )


def comentario_segmento(segmento: str):
    texto = segmento.lower()

    if "moda" in texto or "roupa" in texto:
        return (
            "Que legal 😊\n\n"
            "Moda feminina é um segmento onde tráfego, presença digital e fortalecimento de marca costumam fazer bastante diferença."
        )

    return (
        "Entendi 😊\n\n"
        "Agora já consigo ter uma visão melhor do seu cenário."
    )


def resposta_apos_encaminhamento(texto, nome=None):
    interacao = detectar_interacao_social(texto)

    if interacao == "agradecimento":
        return resposta_aleatoria([
            f"Eu que agradeço pelo contato{', ' + nome if nome else ''} 😊\n\nJá deixei tudo organizado para o Luciano continuar com você.",
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
    if conversa.servico == "Estrutura Completa":
        return (
        "Entendi.\n\n"
        "Nesse cenário, faz sentido trabalhar geração de vendas, fortalecimento da marca e presença digital de forma integrada."
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
    {texto}
    {conversa.objetivo or ''}
    {conversa.servico or ''}
    """

    analise = analisar_mensagem(texto_para_analise)

    etapas_que_podem_identificar_servico = [
        "inicio",
        "entender_objetivo_inicial",
        "entender_objetivo",
    ]

    if (
        conversa.etapa in etapas_que_podem_identificar_servico
        and conversa.servico is None
        and analise["produto"] != "não identificado"
    ):
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
            conversa.etapa = "coletar_nome"
            resposta = resposta_inicial_por_servico("conhecer_servicos", texto)

        elif intencao == "anuncio_instagram":
            conversa.etapa = "entender_objetivo_inicial"
            resposta = resposta_inicial_por_servico("anuncio_instagram", texto)

        elif intencao == "saudacao":
            conversa.etapa = "inicio"
            resposta = resposta_inicial_por_servico("saudacao", texto)

        elif intencao in [
            "orcamento", "reuniao", "estrutura_completa", "trafego",
            "automacao", "social_media", "web_design", "design",
            "contratacao", "objetivo_comercial"
        ]:
            conversa.etapa = "coletar_nome"
            resposta = resposta_inicial_por_servico(intencao, texto)

        else:
            conversa.etapa = "coletar_nome"
            resposta = resposta_inicial_por_servico("geral", texto)

    elif conversa.etapa == "entender_objetivo_inicial":

        conversa.objetivo = texto
        analise = analisar_mensagem(f"{conversa.objetivo or ''}\n{conversa.segmento or ''}")

        if conversa.servico is None and analise["produto"] != "não identificado":
            conversa.servico = analise["produto"]

        conversa.etapa = "coletar_nome"

        resposta = (
            "Entendi 😊\n\n"
            "Para eu organizar melhor esse atendimento, como posso te chamar?"
        )

    elif conversa.etapa == "coletar_nome":

        nova_intencao = detectar_intencao_cliente(texto)

        if nova_intencao == "conhecer_servicos":
            conversa.etapa = "coletar_nome"
            resposta = resposta_servicos_forway()
            conversa.historico += f"\nAgente: {resposta}"
            return resposta, analise

        if nova_intencao in [
            "orcamento", "reuniao", "estrutura_completa", "trafego",
            "automacao", "social_media", "web_design", "design",
            "contratacao", "objetivo_comercial"
        ]:
            analise = analisar_mensagem(
                f"{texto}\n{conversa.objetivo or ''}\n{conversa.servico or ''}"
            )
            if analise["produto"] != "não identificado":
                conversa.servico = analise["produto"]
            resposta = (
                f"{resposta_base_por_servico(conversa, nova_intencao)}\n\n"
                "Para eu organizar melhor seu atendimento, como posso te chamar?"
            )
            conversa.historico += f"\nAgente: {resposta}"
            return resposta, analise

        if not parece_nome(texto):
            resposta = (
                "Desculpa 😊\n\n"
                "Não consegui identificar seu nome.\n\n"
                "Como posso te chamar?"
            )
            conversa.historico += f"\nAgente: {resposta}"
            return resposta, analise

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
                    f"{comentario_segmento(conversa.segmento)}\n\n"
                    "Para o Luciano continuar com você de forma mais direta, me passa seu WhatsApp?"
                )
            else:
                conversa.etapa = "aguardando_humano"
                resposta = (
                    f"{comentario_segmento(conversa.segmento)}\n\n"
                    "Já deixei as informações principais organizadas para o Luciano analisar seu cenário.\n\n"
                    "Ele continua com você por aqui assim que estiver disponível."
                )
        else:
            conversa.etapa = "entender_objetivo"
            resposta = (
                f"{comentario_segmento(conversa.segmento)}\n\n"
                "Hoje o que você mais busca: gerar mais vendas, receber mais contatos ou fortalecer a presença da marca?"
            )

    elif conversa.etapa == "entender_objetivo":

        conversa.objetivo = texto

        analise = analisar_mensagem(f"{conversa.objetivo or ''}\n{conversa.segmento or ''}")

        if (
            analise["produto"] == "Estrutura Completa"
            or (
                conversa.servico is None
                and analise["produto"] != "não identificado"
            )
        ):
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