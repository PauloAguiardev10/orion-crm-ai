PALAVRAS_QUENTE = [
    "orçamento",
    "orcamento",
    "valor",
    "preço",
    "preco",
    "contratar",
    "fechar",
    "reunião",
    "reuniao",
    "automatizar",
    "ia",
    "atendimento",
    "marketing",
    "vendas",
]

PALAVRAS_MORNO = [
    "como funciona",
    "explica",
    "informação",
    "informacao",
    "site",
    "instagram",
    "whatsapp",
]

PALAVRAS_FRIO = [
    "não quero",
    "nao quero",
    "sem interesse",
]

def detectar_intencao(mensagem):

    msg = mensagem.lower()

    if any(p in msg for p in [
        "reunião",
        "reuniao",
        "agenda",
        "marcar",
    ]):
        return "REUNIAO"

    if any(p in msg for p in [
        "valor",
        "preço",
        "preco",
        "orçamento",
        "orcamento",
    ]):
        return "ORCAMENTO"

    if any(p in msg for p in [
        "ia",
        "automação",
        "automacao",
        "atendimento",
    ]):
        return "IA_ATENDIMENTO"

    return "GERAL"


def calcular_score(mensagem):

    score = 0

    msg = mensagem.lower()

    for palavra in PALAVRAS_QUENTE:
        if palavra in msg:
            score += 15

    for palavra in PALAVRAS_MORNO:
        if palavra in msg:
            score += 5

    for palavra in PALAVRAS_FRIO:
        if palavra in msg:
            score -= 20

    return score


def definir_temperatura(score):

    if score >= 40:
        return "QUENTE"

    if score >= 15:
        return "MORNO"

    return "FRIO"


def gerar_resumo(nome, mensagem, intencao, temperatura):

    resumo = f"""
Lead: {nome}

Intenção identificada:
{intencao}

Temperatura:
{temperatura}

Resumo:
Cliente demonstrou interesse em soluções da Forway.
A Sofia iniciou o atendimento, apresentou benefícios
e recomendou continuidade comercial com Luciano.
"""

    return resumo.strip()