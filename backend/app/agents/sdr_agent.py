import re
import random
import unicodedata

from app.services.gpt_service import gerar_resumo_comercial_gpt


ABREVIACOES_WHATSAPP = {
    "vc": "voce",
    "vcs": "voces",
    "ce": "voce",
    "pq": "porque",
    "q": "que",
    "qto": "quanto",
    "qnt": "quanto",
    "tb": "tambem",
    "tbm": "tambem",
    "td": "tudo",
    "agr": "agora",
    "qro": "quero",
    "to": "estou",
    "ta": "esta",
    "pra": "para",
    "pro": "para o",
    "pros": "para os",
    "pras": "para as",
    "qnd": "quando",
    "dps": "depois",
    "hj": "hoje",
    "msg": "mensagem",
    "insta": "instagram",
    "face": "facebook",
    "zap": "whatsapp",
    "whats": "whatsapp",
    "blz": "beleza",
}


PADRAO_ABREVIACOES_WHATSAPP = re.compile(
    r"\b("
    + "|".join(
        re.escape(chave)
        for chave in sorted(ABREVIACOES_WHATSAPP, key=len, reverse=True)
    )
    + r")\b"
)


def normalizar_linguagem_cliente(texto: str) -> str:
    """
    Normaliza a linguagem somente para interpretação comercial.

    A mensagem original do cliente permanece intacta no histórico.
    """
    texto = str(texto or "").strip().lower()

    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )

    texto = PADRAO_ABREVIACOES_WHATSAPP.sub(
        lambda correspondencia: ABREVIACOES_WHATSAPP[correspondencia.group(0)],
        texto,
    )

    return re.sub(r"\s+", " ", texto).strip()


def contem_termo(texto, termos):
    texto_normalizado = normalizar_linguagem_cliente(texto)

    for termo in termos:
        termo_normalizado = normalizar_linguagem_cliente(termo)
        padrao = r"(?<!\w)" + re.escape(termo_normalizado) + r"(?!\w)"
        if re.search(padrao, texto_normalizado):
            return True

    return False


def resposta_aleatoria(lista):
    return random.choice(lista)


def parece_nome(texto: str):
    texto = texto.strip()

    if not texto:
        return False

    texto_lower = texto.lower()

    frases_bloqueadas = [
        "quero", "queria", "gostaria", "serviço", "serviços",
        "servico", "servicos", "informação", "informações",
        "informacao", "informacoes", "tráfego", "trafego",
        "instagram", "facebook", "whatsapp", "como funciona",
        "orçamento", "orcamento", "valor", "preço", "preco",
        "empresa", "anúncio", "anuncio", "forway", "oferece",
        "trabalham", "atendimento", "marketing",
        "bom dia", "boa tarde", "boa noite", "olá", "ola", "oi",
        "tudo bem", "sim", "não", "nao", "ok", "certo",
        "beleza", "show", "perfeito", "entendi", "obrigado",
        "obrigada", "valeu", "não sei", "nao sei",
        "tudo isso", "todos", "as três", "as tres",
    ]

    for frase in frases_bloqueadas:
        if contem_termo(texto_lower, [frase]):
            return False

    # Evita respostas grandes sendo interpretadas como nome.
    palavras = texto.split()

    if len(palavras) > 4:
        return False

    # Nome precisa ter letras de verdade.
    quantidade_letras = sum(
        1
        for caractere in texto
        if caractere.isalpha()
    )

    if quantidade_letras < 2:
        return False

    # Não aceita números.
    if any(
        caractere.isdigit()
        for caractere in texto
    ):
        return False

    # Aceita letras Unicode, espaços, hífen e apóstrofos.
    caracteres_permitidos = {
        " ",
        "-",
        "'",
        "’",
    }

    if not all(
        caractere.isalpha()
        or caractere in caracteres_permitidos
        for caractere in texto
    ):
        return False

    return True


def resposta_nome_nao_identificado():
    return resposta_aleatoria([
        (
            "Acho que não peguei seu nome direitinho 😅\n\n"
            "Como você prefere que eu te chame?"
        ),
        (
            "Desculpa, acho que entendi outra coisa 😊\n\n"
            "Me fala só seu nome para eu continuar?"
        ),
        (
            "Só para eu não registrar errado 😊\n\n"
            "Qual é o seu nome?"
        ),
    ])


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


def objetivo_multiplo_para_estrutura(texto: str) -> bool:
    return contem_termo(
        texto,
        [
            "tudo isso",
            "quero tudo isso",
            "busco tudo isso",
            "estou buscando tudo isso",
            "estou precisando de tudo",
            "preciso de tudo isso",
            "tudo que você está falando",
            "tudo que voce esta falando",
            "tudo o que você está falando",
            "tudo o que voce esta falando",
            "todos esses objetivos",
            "todos esses pontos",
            "tudo que você falou",
            "tudo que voce falou",
            "tudo o que você falou",
            "tudo o que voce falou",
            "tudo que você citou",
            "tudo que voce citou",
            "as três opções",
            "as tres opcoes",
            "as três",
            "as tres",
            "todos eles",
        ],
    )


def objetivo_vendas_para_estrutura(texto: str) -> bool:
    return contem_termo(
        texto,
        [
            "vender mais",
            "aumentar vendas",
            "aumentar minhas vendas",
            "aumentar as vendas",
            "gerar mais vendas",
            "gerar vendas",
            "mais clientes",
            "conseguir mais clientes",
            "captar clientes",
            "gerar leads",
            "mais leads",
            "mais contatos",
            "receber mais contatos",
            "gerar contatos",
        ],
    )


def objetivo_marca_para_social_media(texto: str) -> bool:
    return contem_termo(
        texto,
        [
            "fortalecer minha marca",
            "fortalecer a marca",
            "fortalecer presença",
            "fortalecer a presença",
            "presença da marca",
            "presenca da marca",
            "fortalecer presença da marca",
            "fortalecer a presença da marca",
            "melhorar minha presença digital",
            "presença digital",
            "presenca digital",
        ],
    )


def normalizar_texto_comparacao(texto: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        (texto or "").strip().lower(),
    )


def eh_resposta_cadastral(texto: str, conversa) -> bool:
    valor = normalizar_texto_comparacao(texto)

    if not valor:
        return True

    campos = [
        conversa.nome,
        conversa.empresa,
        conversa.segmento,
        conversa.telefone,
    ]

    for campo in campos:
        campo_normalizado = normalizar_texto_comparacao(
            str(campo or "")
        )

        if campo_normalizado and valor == campo_normalizado:
            return True

    prefixos_cadastrais = [
        "meu nome é ", "meu nome e ", "eu sou ", "sou o ", "sou a ",
        "me chamo ", "minha empresa é ", "minha empresa e ",
        "minha empresa se chama ", "minha loja é ", "minha loja e ",
        "atuamos com ", "atuamos na área de ", "atuamos na area de ",
        "atuamos em ", "trabalhamos com ", "trabalhamos na área de ",
        "trabalhamos na area de ", "trabalhamos em ",
        "somos do segmento de ", "somos da área de ", "somos da area de ",
    ]

    for prefixo in prefixos_cadastrais:
        if valor.startswith(prefixo):
            restante = valor[len(prefixo):].strip()

            for campo in campos:
                campo_normalizado = normalizar_texto_comparacao(
                    str(campo or "")
                )

                if campo_normalizado and restante == campo_normalizado:
                    return True

    return False


def extrair_falas_cliente_comerciais(
    historico: str,
    conversa,
) -> str:
    if not historico:
        return ""

    falas = []

    for linha in historico.splitlines():
        linha = linha.strip()

        if not linha.lower().startswith("cliente:"):
            continue

        fala = linha.split(":", 1)[1].strip()

        if not fala:
            continue

        if eh_resposta_cadastral(fala, conversa):
            continue

        falas.append(fala)

    return "\n".join(falas)


def montar_texto_comercial_cliente(
    conversa,
    mensagem_atual="",
):
    partes = [
        extrair_falas_cliente_comerciais(
            conversa.historico or "",
            conversa,
        ),
        mensagem_atual.strip(),
        conversa.objetivo or "",
    ]

    return "\n".join(
        parte
        for parte in partes
        if parte
    )



def detectar_contexto_aquisicao(mensagem: str):
    """Detecta como o cliente conheceu a Forway sem substituir a intenção comercial."""
    texto = normalizar_linguagem_cliente(mensagem)

    if contem_termo(texto, [
        "vim por indicacao",
        "foi indicacao",
        "por indicacao",
        "me indicou",
        "me recomendaram",
        "me recomendou",
        "me passou o contato",
        "me passaram o contato",
        "peguei o contato com",
        "falou de voces",
        "falou da forway",
        "me falou de voces",
        "me falou da forway",
        "recomendou voces",
        "recomendou a forway",
    ]):
        return {"tipo": "indicacao", "canal": None}

    if contem_termo(texto, [
        "vi o trabalho que voces estao fazendo",
        "vi o trabalho de voces",
        "vi o trabalho da forway",
        "acompanho o trabalho que voces fazem",
        "acompanho o trabalho da forway",
        "vi o resultado que voces tiveram",
        "vi os resultados que voces tiveram",
        "vi um trabalho de voces",
        "conheci o trabalho de voces",
    ]):
        return {"tipo": "referencia_cliente", "canal": None}

    origem_anuncio = contem_termo(texto, [
        "vi um anuncio",
        "vi uma propaganda",
        "vi uma campanha",
        "vi uma publicidade",
        "vi um patrocinado",
        "vi uma patrocinada",
        "vim por um anuncio",
        "vim pelo anuncio",
        "vim por uma propaganda",
        "vim pela campanha",
        "cheguei por um anuncio",
        "cheguei pelo anuncio",
        "cheguei por uma propaganda",
        "cheguei pela campanha",
        "achei voces por um anuncio",
        "achei voces pelo anuncio",
        "conheci voces por um anuncio",
        "conheci voces pelo anuncio",
    ])

    if origem_anuncio:
        canal = None

        if contem_termo(texto, ["instagram"]):
            canal = "instagram"
        elif contem_termo(texto, ["facebook"]):
            canal = "facebook"

        return {"tipo": "anuncio", "canal": canal}

    origem_organica = contem_termo(texto, [
        "vi voces no instagram",
        "conheci voces pelo instagram",
        "achei voces no instagram",
        "vim pelo instagram",
        "vi uma postagem de voces",
        "vi um post de voces",
        "vi uma publicacao de voces",
        "vi um conteudo de voces",
    ])

    if origem_organica and contem_termo(texto, ["instagram"]):
        return {"tipo": "organico", "canal": "instagram"}

    origem_organica = contem_termo(texto, [
        "vi voces no facebook",
        "conheci voces pelo facebook",
        "achei voces no facebook",
        "vim pelo facebook",
        "vi uma postagem de voces",
        "vi um post de voces",
        "vi uma publicacao de voces",
        "vi um conteudo de voces",
    ])

    if origem_organica and contem_termo(texto, ["facebook"]):
        return {"tipo": "organico", "canal": "facebook"}

    return None

def obter_origem_aquisicao(contexto):
    """
    Converte o contexto de aquisição detectado em um valor
    padronizado para persistência no CRM.
    """
    if not contexto:
        return None

    tipo = contexto.get("tipo")
    canal = contexto.get("canal")

    if tipo in ("anuncio", "organico") and canal:
        return f"{tipo}_{canal}"

    return tipo

def resposta_contexto_aquisicao(contexto):
    if not contexto:
        return None

    tipo = contexto.get("tipo")
    canal = contexto.get("canal")

    if tipo == "indicacao":
        return "Que legal saber que você chegou até a Forway por indicação 😊"
    if tipo == "referencia_cliente":
        return "Que legal saber que você conheceu a Forway através de um trabalho que estamos realizando 😊"
    if tipo == "anuncio" and canal == "instagram":
        return "Que legal que você chegou até a Forway pelo nosso anúncio no Instagram 😊"
    if tipo == "anuncio" and canal == "facebook":
        return "Que legal que você chegou até a Forway pelo nosso anúncio no Facebook 😊"
    if tipo == "anuncio":
        return "Que legal que você chegou até a Forway através de uma campanha nossa 😊"
    if tipo == "organico" and canal == "instagram":
        return "Que legal que você conheceu a Forway pelo nosso Instagram 😊"
    if tipo == "organico" and canal == "facebook":
        return "Que legal que você conheceu a Forway pelo nosso Facebook 😊"

    return None


def combinar_contexto_com_resposta(contexto, resposta):
    abertura = resposta_contexto_aquisicao(contexto)
    if not abertura:
        return resposta
    return f"{abertura}\n\n{resposta}"


def detectar_intencao_cliente(mensagem: str):
    texto = mensagem.lower().strip()

    grupos = [
        ("duvida_lead", ["o que é lead","o que e lead","o que significa lead","não sei o que é lead","nao sei o que e lead","lead é o que","lead e o que","o que são leads","o que sao leads"]),
        ("objecao_experiencia_ruim", ["já tentei","ja tentei","não deu certo","nao deu certo","não funcionou","nao funcionou","experiência ruim","experiencia ruim","outra agência","outra agencia","outras agências","outras agencias","tenho medo","medo de contratar","não gostei","nao gostei","fui enganado","fui enganada","já perdi dinheiro","ja perdi dinheiro","joguei dinheiro fora","não confio","nao confio"]),
        # Intenções comerciais fortes vêm antes de consultas genéricas.
        ("contratacao", ["quero contratar","quero fechar","vamos fechar","fechar negócio","fechar negocio","quero começar","quero comecar","podemos começar","podemos comecar","quero comprar","tenho interesse em contratar","quero contratar vocês","quero contratar voces"]),
        ("reuniao", ["reunião","reuniao","agenda","agendar","agendamento","marcar horário","marcar horario","marcar uma reunião","marcar uma reuniao","falar com o luciano","quero falar com o luciano","falar com especialista","falar com um especialista"]),
        ("orcamento", ["orçamento","orcamento","preço","preco","valor","quanto custa","quanto fica","qual o valor","qual valor","quanto vocês cobram","quanto voces cobram","investimento","mensalidade","pacote","pacotes","proposta"]),
        ("estrutura_completa", ["estrutura completa","marketing completo","tudo completo","quero tudo","pacote completo","serviço completo","servico completo","solução completa","solucao completa","quero todos os serviços","quero todos os servicos","quero todos os seus serviços","quero todos os seus servicos","quero todos os serviços oferecidos","quero todos os servicos oferecidos","quero todos os serviços oferecido","quero todos os servicos oferecido","quero tudo que vocês oferecem","quero tudo que voces oferecem","quero tudo que a forway oferece","tenho interesse em todos os serviços","tenho interesse em todos os servicos","preciso de tudo","estou precisando de tudo","preciso de tudo isso","tudo que você está falando","tudo que voce esta falando","tudo o que você está falando","tudo o que voce esta falando","preciso de todos os serviços","preciso de todos os servicos","tráfego e social media","trafego e social media","tráfego, social media e atendimento","trafego, social media e atendimento"]),
        ("conhecer_servicos", ["como funciona o trabalho de vocês","como funciona o trabalho de voces","como funciona o trabalho da forway","como funciona o trabalho","quais serviços","quais servicos","quais são os serviços","quais sao os servicos","que serviços vocês oferecem","que servicos voces oferecem","serviços vocês oferecem","servicos voces oferecem","serviços que a forway oferece","servicos que a forway oferece","informações sobre os serviços","informacoes sobre os servicos","o que vocês fazem","o que voces fazem","como vocês trabalham","como voces trabalham","me fala dos serviços","me fala dos servicos","me explica os serviços","me explica os servicos","o que oferecem","não sei o que preciso","nao sei o que preciso","não sei qual serviço","nao sei qual servico","quero conhecer","serviços da forway","servicos da forway","gostaria de saber os serviços","gostaria de saber os servicos","gostaria de saber sobre os serviços","gostaria de saber sobre os servicos","gostaria de saber mais sobre seus serviços","gostaria de saber mais sobre seus servicos","gostaria de saber sobre seus serviços","gostaria de saber sobre seus servicos","quero saber sobre seus serviços","quero saber sobre seus servicos","quero saber mais sobre seus serviços","quero saber mais sobre seus servicos","seus serviços","seus servicos","serviços de vocês","servicos de voces","saber sobre os serviços","saber sobre os servicos","saber mais sobre os serviços","saber mais sobre os servicos","saber mais sobre seus serviços","saber mais sobre seus servicos"]),
        ("trafego", ["tráfego","trafego","tráfego pago","trafego pago","gestão de tráfego","gestao de trafego","quero anunciar","quero fazer anúncios","quero fazer anuncios","fazer anúncios","fazer anuncios","criar anúncios","criar anuncios","rodar anúncios","rodar anuncios","facebook ads","instagram ads","meta ads","google ads","campanha paga","campanhas pagas","mídia paga","midia paga"]),
        ("web_design", ["site","landing page","website","web site","página de vendas","pagina de vendas","criar um site","fazer um site","site profissional","loja virtual"]),
        ("social_media", ["social media","social mídia","social midia","gestão de redes sociais","gestao de redes sociais","cuidar do instagram","gerenciar instagram","gestão do instagram","gestao do instagram","cuidar das redes sociais","gerenciar redes sociais","quero conteúdo","quero conteudo","preciso de conteúdo","preciso de conteudo","criar conteúdo","criar conteudo","quero postagens","preciso de postagens","melhorar engajamento","aumentar engajamento"]),
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
    """
    Classificação comercial determinística e explicável.

    A temperatura representa o estágio comercial demonstrado pelo cliente:
    - fria: descoberta, sem interesse específico ou necessidade concreta;
    - morna: interesse em serviço específico ou necessidade comercial;
    - quente: intenção clara de avançar (orçamento, proposta, reunião,
      especialista ou contratação).

    O score, limitado de 0 a 10, complementa a temperatura e mede a força
    acumulada dos sinais comerciais. Cada categoria pontua no máximo uma vez.
    """
    texto = mensagem.lower()
    score = 0
    produto = "não identificado"

    produtos = {
        "Estrutura Completa": [
            "estrutura completa", "marketing completo", "tudo completo",
            "pacote completo", "serviço completo", "servico completo",
            "solução completa", "solucao completa", "quero tudo",
            "quero todos os serviços", "quero todos os servicos",
            "quero todos os seus serviços", "quero todos os seus servicos",
            "quero todos os serviços oferecidos",
            "quero todos os servicos oferecidos",
            "quero todos os serviços oferecido",
            "quero todos os servicos oferecido",
            "quero tudo que vocês oferecem", "quero tudo que voces oferecem",
            "quero tudo que a forway oferece",
            "tenho interesse em todos os serviços",
            "tenho interesse em todos os servicos",
            "preciso de tudo", "estou precisando de tudo",
            "preciso de tudo isso",
            "tudo que você está falando", "tudo que voce esta falando",
            "tudo o que você está falando", "tudo o que voce esta falando",
            "preciso de todos os serviços", "preciso de todos os servicos",
            "tráfego e social media", "trafego e social media",
        ],
        "Gestão de Tráfego Pago": [
            "tráfego", "trafego", "tráfego pago", "trafego pago",
            "gestão de tráfego", "gestao de trafego",
            "quero anunciar", "quero fazer anúncios", "quero fazer anuncios",
            "fazer anúncios", "fazer anuncios", "criar anúncios", "criar anuncios",
            "rodar anúncios", "rodar anuncios",
            "facebook ads", "instagram ads", "meta ads", "google ads",
            "campanha paga", "campanhas pagas", "mídia paga", "midia paga",
        ],
        "Social Media Estratégico": [
            "social media", "social mídia", "social midia",
            "gestão de redes sociais", "gestao de redes sociais",
            "cuidar do instagram", "gerenciar instagram",
            "gestão do instagram", "gestao do instagram",
            "cuidar das redes sociais", "gerenciar redes sociais",
            "quero conteúdo", "quero conteudo",
            "preciso de conteúdo", "preciso de conteudo",
            "criar conteúdo", "criar conteudo",
            "quero postagens", "preciso de postagens",
            "melhorar engajamento", "aumentar engajamento",
        ],
        "Design": [
            "design", "identidade visual", "criativo", "criativos",
            "arte gráfica", "arte grafica", "artes gráficas", "artes graficas",
            "criação de arte", "criacao de arte",
            "criação de artes", "criacao de artes",
            "quero um logo", "quero criar um logo", "preciso de um logo",
            "criar um logo", "fazer um logo", "criar logo", "fazer logo",
            "criação de logo", "criacao de logo", "logotipo",
            "marca mais profissional", "materiais melhores",
            "material gráfico", "material grafico",
        ],
        "Atendimento com IA": [
            "automação", "automacao", "ia",
            "inteligência artificial", "inteligencia artificial",
            "chatbot", "sdr", "agente de ia", "agente ia",
            "atendimento automático", "atendimento automatico",
            "atendimento automatizado", "automatizar atendimento",
            "automatizar whatsapp", "automatizar meu whatsapp",
            "automatizar o whatsapp", "automatizar nosso whatsapp",
            "automatizar as mensagens", "automatizar mensagens",
        ],
        "Web Design": [
            "site", "landing page", "website", "web site",
            "página de vendas", "pagina de vendas",
            "loja virtual", "site profissional",
        ],
    }

    for nome_produto, termos in produtos.items():
        if contem_termo(texto, termos):
            produto = nome_produto
            break

    sinal_contratacao = contem_termo(texto, [
        "quero contratar", "vamos fechar", "quero fechar",
        "fechar negócio", "fechar negocio",
        "quero começar", "quero comecar",
        "podemos começar", "podemos comecar",
        "quero comprar", "tenho interesse em contratar",
        "quero contratar vocês", "quero contratar voces",
    ])

    sinal_reuniao = contem_termo(texto, [
        "reunião", "reuniao",
        "agenda", "agendar", "agendamento",
        "marcar horário", "marcar horario",
        "marcar reunião", "marcar reuniao",
        "marcar uma reunião", "marcar uma reuniao",
        "falar com o luciano", "quero falar com o luciano",
        "falar com especialista", "falar com um especialista",
    ])

    sinal_orcamento = contem_termo(texto, [
        "orçamento", "orcamento",
        "preço", "preco", "valor",
        "quanto custa", "quanto fica",
        "qual o valor", "qual valor",
        "quanto vocês cobram", "quanto voces cobram",
        "proposta", "investimento", "mensalidade",
    ])

    sinal_objetivo = contem_termo(texto, [
        "vender mais", "aumentar vendas", "aumentar minhas vendas",
        "aumentar as vendas", "melhorar minhas vendas",
        "gerar mais vendas", "gerar vendas",
        "mais clientes", "conseguir mais clientes", "captar clientes",
        "conseguir clientes", "gerar leads", "mais leads",
        "mais contatos", "receber mais contatos", "gerar contatos",
        "fortalecer a marca", "fortalecer minha marca",
        "fortalecer a presença", "fortalecer presença",
        "presença digital", "presenca digital",
        "melhorar minha presença digital", "melhorar o instagram",
        "automatizar atendimento", "automatizar whatsapp",
        "melhorar atendimento",
    ])

    sinal_urgencia = contem_termo(texto, [
        "urgente", "urgência", "urgencia", "o quanto antes",
        "ainda hoje", "essa semana", "esta semana",
        "preciso começar logo", "preciso comecar logo",
        "quero começar logo", "quero comecar logo",
        "imediatamente",
    ])

    sinal_dor = contem_termo(texto, [
        "já tentei", "ja tentei",
        "não deu certo", "nao deu certo",
        "não funcionou", "nao funcionou",
        "outra agência", "outra agencia",
        "experiência ruim", "experiencia ruim",
        "já perdi dinheiro", "ja perdi dinheiro",
        "fui enganado", "fui enganada",
    ])

    # Score complementar: mede intensidade, mas não decide sozinho a temperatura.
    if sinal_contratacao:
        score += 6

    if sinal_reuniao:
        score += 3

    if sinal_orcamento:
        score += 3

    if sinal_objetivo:
        score += 3

    # Interesse em um serviço específico já é um sinal comercial real.
    if produto != "não identificado":
        score += 2

    # Estrutura completa amplia a necessidade, mas não torna a lead quente sozinha.
    if produto == "Estrutura Completa":
        score += 1

    if sinal_urgencia:
        score += 2

    if sinal_dor:
        score += 1

    score = min(score, 10)

    # Temperatura por estágio comercial:
    # intenção de avançar => quente;
    # interesse/necessidade concreta => morna;
    # descoberta sem sinal comercial concreto => fria.
    if sinal_contratacao or sinal_reuniao or sinal_orcamento:
        temperatura, prioridade = "quente", "alta"
    elif produto != "não identificado" or sinal_objetivo:
        temperatura, prioridade = "morna", "média"
    else:
        temperatura, prioridade = "fria", "baixa"

    return {
        "temperatura": temperatura,
        "score": score,
        "produto": produto,
        "prioridade": prioridade,
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
Luciano deve entrar em contato com a lead de forma consultiva e aprofundar o entendimento do cenário.
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



def sofia_ja_se_apresentou(conversa):
    historico = conversa.historico or ""
    return (
        "Sou a Sofia, da Forway." in historico
        or "Agente:" in historico
        or "Sofia:" in historico
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
            "Antes de encaminhar seu atendimento para o Luciano, responsável pela Forway, vou entender rapidamente seu cenário para ele receber seu caso com o contexto certo.\n\n"
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
            "Para eu organizar seu atendimento e encaminhar tudo certinho para o Luciano, responsável pela Forway, como posso te chamar?"
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
            "Moda é um segmento onde uma boa presença digital e um posicionamento bem trabalhado podem ajudar bastante a atrair clientes e fortalecer a marca."
        )

    return (
        "Entendi 😊\n\n"
        "Agora já consigo ter uma visão melhor do seu cenário."
    )


def resposta_apos_encaminhamento(texto, nome=None):
    interacao = detectar_interacao_social(texto)

    if interacao == "agradecimento":
        return resposta_aleatoria([
            (
                f"Eu que agradeço pelo contato{', ' + nome if nome else ''} 😊\n\n"
                "Já deixei tudo organizado e encaminhei seu atendimento diretamente "
                "para o Luciano, responsável pela Forway. Ele vai entrar em contato "
                "com você assim que possível."
            ),
            (
                "Obrigado você pela confiança 😊\n\n"
                "Suas informações já estão organizadas e seu atendimento foi encaminhado "
                "diretamente para o Luciano. Ele vai entrar em contato com você assim que possível."
            ),
            (
                "Foi um prazer falar com você 😊\n\n"
                "Seu atendimento já está encaminhado para o Luciano. "
                "Ele vai entrar em contato com você assim que estiver disponível."
            ),
        ])

    if interacao == "confirmacao":
        return resposta_aleatoria([
            (
                "Perfeito 😊\n\n"
                "Já deixei tudo certo e seu atendimento está encaminhado."
            ),
            (
                "Combinado 😊\n\n"
                "Seu atendimento já está encaminhado para o Luciano. "
                "Ele vai entrar em contato com você assim que possível."
            ),
            (
                "Tudo certo 😊\n\n"
                "Agora é só aguardar o contato do Luciano."
            ),
        ])

    if interacao == "despedida":
        return resposta_aleatoria([
            (
                "Combinado 😊\n\n"
                "Obrigado pelo contato. O Luciano vai entrar em contato "
                "com você assim que estiver disponível."
            ),
            (
                "Tudo certo 😊\n\n"
                "Foi um prazer te atender."
            ),
            (
                "Perfeito 😊\n\n"
                "Seu atendimento já está encaminhado. "
                "Agora é só aguardar o contato do Luciano."
            ),
        ])

    return resposta_aleatoria([
        (
            "Seu atendimento já foi encaminhado diretamente para o Luciano, "
            "responsável pela Forway 😊\n\n"
            "Ele vai entrar em contato com você assim que estiver disponível."
        ),
        (
            "Já deixei suas informações organizadas e encaminhadas "
            "para o Luciano analisar com atenção 😊"
        ),
        (
            "Tudo certo por aqui 😊\n\n"
            "Seu atendimento já está com o Luciano. "
            "Ele vai entrar em contato com você assim que possível."
        ),
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
            "Assim o Luciano consegue analisar seu cenário e orientar você com mais segurança."
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
            "Nesse cenário, faz sentido trabalhar posicionamento, conteúdo e presença digital para fortalecer a marca de forma estratégica."
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

    return (
        "Entendi.\n\n"
        "Já deu para ter uma boa noção do que você busca."
    )



def sincronizar_status_atendimento(conversa):
    if conversa.humano_assumiu:
        conversa.status_atendimento = "em_atendimento_humano"
    elif conversa.etapa == "aguardando_humano":
        conversa.status_atendimento = "aguardando_humano"
    else:
        conversa.status_atendimento = "em_atendimento_ia"

def conduzir_conversa(conversa, mensagem: str):
    sincronizar_status_atendimento(conversa)

    texto = mensagem.strip()
    canal = conversa.canal.lower()

    if conversa.etapa == "aguardando_humano":
        resposta = resposta_apos_encaminhamento(texto, conversa.nome)
        conversa.historico = (conversa.historico or "") + f"\nCliente: {texto}"
        conversa.historico += f"\nAgente: {resposta}"
        return resposta, analisar_mensagem(
            montar_texto_comercial_cliente(conversa)
        )

    intencao = detectar_intencao_cliente(texto)
    contexto_aquisicao = detectar_contexto_aquisicao(texto)
    # Persiste a primeira origem de aquisição identificada.
    if contexto_aquisicao and not conversa.origem_aquisicao:
        conversa.origem_aquisicao = obter_origem_aquisicao(
            contexto_aquisicao
        )

    # Considera somente sinais comerciais vindos do cliente.
    # As respostas da Sofia não podem influenciar a escolha do serviço.
    texto_para_analise = montar_texto_comercial_cliente(
        conversa,
        texto,
    )

    analise = analisar_mensagem(
        texto_para_analise
    )

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

        elif intencao == "saudacao":
            conversa.etapa = "inicio"

            if sofia_ja_se_apresentou(conversa):
                resposta = "Como posso ajudar você hoje? 😊"
            else:
                resposta = resposta_inicial_por_servico(
                    "saudacao",
                    texto,
                )

        elif contexto_aquisicao and intencao == "geral":
            conversa.etapa = "inicio"
            resposta = combinar_contexto_com_resposta(
                contexto_aquisicao,
                "Me conta, o que você está buscando para sua empresa hoje?",
            )

        elif intencao in [
            "orcamento", "reuniao", "estrutura_completa", "trafego",
            "automacao", "social_media", "web_design", "design",
            "contratacao", "objetivo_comercial"
        ]:
            conversa.etapa = "coletar_nome"

            # Se a Sofia já respondeu uma saudação nesta conversa,
            # não cumprimenta novamente ao identificar o serviço.
            if sofia_ja_se_apresentou(conversa):
                if intencao == "trafego":
                    resposta = (
                        "Posso te ajudar com tráfego pago sim.\n\n"
                        "Antes de te encaminhar para o especialista, me fala seu nome?"
                    )
                elif intencao == "orcamento":
                    resposta = (
                        "Para falar de valores sem te passar algo genérico, o ideal é entender primeiro seu cenário.\n\n"
                        "Me fala seu nome?"
                    )
                elif intencao == "reuniao":
                    resposta = (
                        "Antes de encaminhar seu atendimento para o Luciano, responsável pela Forway, vou entender rapidamente seu cenário para ele receber seu caso com o contexto certo.\n\n"
                        "Qual é o seu nome?"
                    )
                elif intencao == "automacao":
                    resposta = (
                        "Automação com IA pode ajudar bastante quando a empresa recebe contatos e precisa organizar melhor o primeiro atendimento.\n\n"
                        "Me fala seu nome para eu entender seu cenário?"
                    )
                elif intencao == "social_media":
                    resposta = (
                        "A Forway trabalha social media de forma estratégica, pensando em posicionamento e resultado, não só postagem.\n\n"
                        "Como posso te chamar?"
                    )
                elif intencao == "web_design":
                    resposta = (
                        "Um site bem estruturado ajuda muito na credibilidade e também na geração de contatos.\n\n"
                        "Me fala seu nome?"
                    )
                elif intencao == "design":
                    resposta = (
                        "Design e identidade visual fazem muita diferença na forma como o cliente percebe a empresa.\n\n"
                        "Como posso te chamar?"
                    )
                elif intencao == "estrutura_completa":
                    resposta = (
                        "Quando a empresa busca uma estrutura mais completa, o ideal é olhar tráfego, conteúdo, atendimento e presença digital juntos.\n\n"
                        "Me fala seu nome para eu organizar melhor seu atendimento?"
                    )
                elif intencao == "contratacao":
                    resposta = (
                        "Perfeito 😊\n\n"
                        "Para eu organizar seu atendimento e encaminhar tudo certinho para o Luciano, responsável pela Forway, como posso te chamar?"
                    )
                else:
                    resposta = (
                        "Entendi 😊\n\n"
                        "Esse é exatamente o tipo de objetivo que vale analisar com mais contexto.\n\n"
                        "Para eu organizar melhor seu atendimento, como posso te chamar?"
                    )
            else:
                resposta = resposta_inicial_por_servico(intencao, texto)

        else:
            conversa.etapa = "coletar_nome"

            if sofia_ja_se_apresentou(conversa):
                resposta = (
                    "Claro 😊\n\n"
                    "Para eu entender melhor seu cenário, "
                    "como posso te chamar?"
                )
            else:
                resposta = resposta_inicial_por_servico(
                    "geral",
                    texto,
                )

        if contexto_aquisicao and intencao != "geral":
            resposta = combinar_contexto_com_resposta(
                contexto_aquisicao,
                resposta,
            )

    elif conversa.etapa == "entender_objetivo_inicial":

        conversa.objetivo = texto
        analise = analisar_mensagem(
            montar_texto_comercial_cliente(
                conversa,
                texto,
            )
        )

        if conversa.servico is None:
            if objetivo_multiplo_para_estrutura(
                conversa.objetivo or ""
            ):
                conversa.servico = "Estrutura Completa"

            elif objetivo_marca_para_social_media(
                conversa.objetivo or ""
            ):
                conversa.servico = "Social Media Estratégico"

            elif objetivo_vendas_para_estrutura(
                conversa.objetivo or ""
            ):
                conversa.servico = "Estrutura Completa"

            elif (
                analise["produto"]
                != "não identificado"
            ):
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
                montar_texto_comercial_cliente(
                    conversa,
                    texto,
                )
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
            resposta = resposta_nome_nao_identificado()
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
                    "Para eu encaminhar seu atendimento ao Luciano e ele falar com você diretamente, me passa seu WhatsApp?"
                )
            else:
                conversa.etapa = "aguardando_humano"
                resposta = (
                    f"{comentario_segmento(conversa.segmento)}\n\n"
                    "Já deixei as informações principais organizadas para o Luciano analisar seu cenário.\n\n"
                    "Ele vai entrar em contato com você assim que estiver disponível."
                )
        else:
            conversa.etapa = "entender_objetivo"
            resposta = (
                f"{comentario_segmento(conversa.segmento)}\n\n"
                "Hoje o que você mais busca: gerar mais vendas, receber mais contatos ou fortalecer a presença da marca?"
            )

    elif conversa.etapa == "entender_objetivo":

        conversa.objetivo = texto

        analise = analisar_mensagem(
            montar_texto_comercial_cliente(
                conversa,
                texto,
            )
        )

        if conversa.servico is None:
            if objetivo_multiplo_para_estrutura(
                conversa.objetivo or ""
            ):
                conversa.servico = "Estrutura Completa"

            elif objetivo_marca_para_social_media(
                conversa.objetivo or ""
            ):
                conversa.servico = "Social Media Estratégico"

            elif objetivo_vendas_para_estrutura(
                conversa.objetivo or ""
            ):
                conversa.servico = "Estrutura Completa"

            elif (
                analise["produto"]
                != "não identificado"
            ):
                conversa.servico = analise["produto"]

        resposta_base = resposta_base_por_servico(conversa, intencao)

        if canal in ["instagram", "facebook", "messenger"]:
            conversa.etapa = "coletar_whatsapp"
            resposta = (
                f"{resposta_base}\n\n"
                "Para eu encaminhar seu atendimento ao Luciano e ele falar com você diretamente, me passa seu WhatsApp?"
            )
        else:
            conversa.etapa = "aguardando_humano"
            resposta = (
                f"{resposta_base}\n\n"
                "Já organizei as informações principais para o Luciano analisar seu caso com mais calma.\n\n"
                "Seu atendimento já foi encaminhado para o Luciano. Ele vai entrar em contato com você assim que estiver disponível 😊"
            )

    elif conversa.etapa == "coletar_whatsapp":

        conversa.telefone = texto
        conversa.etapa = "aguardando_humano"

        resposta = (
            "Perfeito 😊\n\n"
            "Já deixei tudo organizado e encaminhei seu atendimento diretamente para o Luciano, responsável pela Forway. Ele vai entrar em contato com você assim que possível."
        )

    else:
        resposta = resposta_apos_encaminhamento(texto, conversa.nome)

    conversa.historico += f"\nAgente: {resposta}"

    # Recalcula a qualificação final sem usar respostas da Sofia.
    analise = analisar_mensagem(
        montar_texto_comercial_cliente(
            conversa
        )
    )

    sincronizar_status_atendimento(conversa)

    return resposta, analise