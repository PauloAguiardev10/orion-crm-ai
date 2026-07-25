import os
import re

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def extrair_conteudo_resposta(resposta) -> str:
    """
    Extrai com segurança o conteúdo textual retornado pela OpenAI.
    """
    try:
        conteudo = resposta.choices[0].message.content

        if conteudo:
            return conteudo.strip()

    except (AttributeError, IndexError, TypeError):
        pass

    return ""


def gerar_resposta_gpt(contexto_cliente: str):
    try:
        resposta = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"""
Você é Sofia, assistente comercial da Forway.

Regras importantes:
- Seja humanizada, profissional, simpática e consultiva.
- Responda de forma curta, natural e objetiva.
- Não pareça robô.
- Não use "Olá" ou "Oi" se o cliente já estiver no meio da conversa.
- Só cumprimente no início do atendimento.
- Se o cliente já respondeu uma pergunta, apenas demonstre entendimento e continue o fluxo.
- Escreva exclusivamente em português do Brasil.
- Utilize sempre a palavra "lead".
- Nunca traduza "lead" como "liderança", "pista" ou outro termo.
- Preserve exatamente os nomes oficiais dos serviços da Forway.

A Forway oferece:
- Gestão de Tráfego Pago
- Social Media Estratégico
- Design
- Atendimento Automatizado com IA
- Web Design
- Treinamento e Suporte Comercial

Contexto:
{contexto_cliente}
"""
                }
            ],
            temperature=0.7,
            max_tokens=300
        )

        conteudo = extrair_conteudo_resposta(resposta)

        if conteudo:
            return conteudo

        return (
            "Perfeito 😊 Entendi melhor o que você procura. "
            "Vou continuar seu atendimento da melhor forma."
        )

    except Exception as erro:
        print("ERRO GPT:", erro)

        return (
            "Perfeito 😊 Entendi melhor o que você procura. "
            "Vou continuar seu atendimento da melhor forma."
        )


def gerar_apresentacao_servicos_gpt(contexto_cliente: str):
    try:
        resposta = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"""
Você é Sofia, assistente comercial da Forway.

Apresente os serviços de forma elegante, curta e consultiva.

Regras importantes:
- Escreva exclusivamente em português do Brasil.
- Preserve exatamente os nomes oficiais dos serviços.
- Não substitua "Social Media Estratégico" por "Estratégia de mídia social".
- Utilize sempre a palavra "lead".
- Nunca traduza "lead" como "liderança", "pista" ou outro termo.
- Não invente serviços que não estejam listados abaixo.

Serviços:
- Gestão de Tráfego Pago
- Social Media Estratégico
- Design
- Atendimento Automatizado com IA
- Web Design
- Treinamento e Suporte Comercial

Diferencial:
A Forway oferece tudo em um só lugar, de forma integrada e estratégica.

Contexto:
{contexto_cliente}

No final, pergunte qual objetivo o cliente deseja alcançar.
"""
                }
            ],
            temperature=0.7,
            max_tokens=450
        )

        conteudo = extrair_conteudo_resposta(resposta)

        if conteudo:
            return conteudo

        return (
            "Claro 😊 A Forway trabalha com Gestão de Tráfego Pago, "
            "Social Media Estratégico, Design, Atendimento Automatizado com IA, "
            "Web Design e Treinamento e Suporte Comercial. "
            "Nosso diferencial é oferecer tudo em um só lugar, de forma integrada. "
            "Qual objetivo você deseja alcançar hoje?"
        )

    except Exception as erro:
        print("ERRO GPT SERVIÇOS:", erro)

        return (
            "Claro 😊 A Forway trabalha com Gestão de Tráfego Pago, "
            "Social Media Estratégico, Design, Atendimento Automatizado com IA, "
            "Web Design e Treinamento e Suporte Comercial. "
            "Nosso diferencial é oferecer tudo em um só lugar, de forma integrada. "
            "Qual objetivo você deseja alcançar hoje?"
        )


def sanitizar_resumo_comercial(texto: str) -> str:
    """
    Corrige termos inadequados ou traduções indesejadas
    antes de salvar o resumo comercial no banco de dados.
    """
    if not texto:
        return ""

    substituicoes = [
        (r"\bliderança qualificada\b", "lead qualificada"),
        (r"\bliderança derrotada\b", "lead qualificada"),
        (r"\blead derrotada\b", "lead qualificada"),
        (r"\blead derrotado\b", "lead qualificada"),
        (r"\bpista qualificada\b", "lead qualificada"),
        (r"\bpistas qualificadas\b", "leads qualificadas"),
        (
            r"\bestratégia de mídia social\b",
            "Social Media Estratégico"
        ),
        (r"\bjurídico\b", "Legal"),
        (r"\bdiminuindo que\b", "indicando que"),
    ]

    texto_corrigido = texto

    for termo_errado, termo_correto in substituicoes:
        texto_corrigido = re.sub(
            termo_errado,
            termo_correto,
            texto_corrigido,
            flags=re.IGNORECASE
        )

    return texto_corrigido.strip()


def gerar_resumo_comercial_gpt(conversa, analise):
    analise = analise or {}

    nome = conversa.nome or "Não informado"
    empresa = conversa.empresa or "Não informado"
    segmento = conversa.segmento or "Não informado"
    canal = conversa.canal or "Não informado"
    telefone = conversa.telefone or "Não informado"

    servico = (
        conversa.servico
        or analise.get("produto")
        or "Não informado"
    )

    temperatura = analise.get("temperatura") or "Não informado"
    prioridade = analise.get("prioridade") or "Não informado"
    score = analise.get("score", 0)

    objetivo = conversa.objetivo or "Não informado"
    historico = conversa.historico or "Não informado"

    try:
        resposta = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """
Você é responsável por gerar resumos comerciais para vendedores da Forway.

Escreva exclusivamente em português do Brasil.

REGRAS OBRIGATÓRIAS:

- Use sempre a palavra "lead".
- Nunca traduza "lead" como "liderança", "pista" ou qualquer outro termo.
- Nunca use as palavras "derrotada", "derrotado" ou "jurídico".
- O título deve ser exatamente:
  Nova lead qualificada — Forway
- Preserve exatamente os nomes dos serviços informados.
- Quando o serviço for "Social Media Estratégico", escreva exatamente:
  Social Media Estratégico
- Não escreva "Estratégia de mídia social".
- Não invente informações.
- Não copie o histórico bruto.
- Não altere nome, empresa, telefone, canal, serviço, temperatura,
  prioridade ou score.
- Não informe que a venda foi concluída.
- Não informe que a lead foi derrotada.
- O resumo deve ser objetivo, profissional e consultivo.
- Não use linguagem excessivamente promocional.
- Utilize marcadores com o caractere "-".
- Não inclua saudações, emojis ou mensagens direcionadas ao cliente.
- Produza somente o resumo comercial no formato solicitado.
"""
                },
                {
                    "role": "user",
                    "content": f"""
Gere o resumo usando somente os dados abaixo.

Nome: {nome}
Empresa: {empresa}
Segmento: {segmento}
Canal: {canal}
WhatsApp: {telefone}
Serviço de interesse: {servico}
Temperatura: {temperatura}
Prioridade: {prioridade}
Score: {score}
Objetivo: {objetivo}

Histórico da conversa:
{historico}

Use obrigatoriamente este formato:

Nova lead qualificada — Forway

Nome: {nome}
Empresa: {empresa}
Segmento: {segmento}
Canal: {canal}
WhatsApp: {telefone}
Serviço de interesse: {servico}
Temperatura: {temperatura}
Prioridade: {prioridade}
Score: {score}

Resumo da conversa:
[resumo comercial objetivo]

Pontos importantes:
- [ponto importante]
- [ponto importante]
- [ponto importante]

Próxima ação recomendada:
[ação comercial consultiva]
"""
                }
            ],
            temperature=0.2,
            max_tokens=600
        )

        resumo = extrair_conteudo_resposta(resposta)

        if resumo:
            return sanitizar_resumo_comercial(resumo)

        raise ValueError("A OpenAI retornou um resumo vazio.")

    except Exception as erro:
        print("ERRO GPT RESUMO:", erro)

        resumo_fallback = f"""
Nova lead qualificada — Forway

Nome: {nome}
Empresa: {empresa}
Segmento: {segmento}
Canal: {canal}
WhatsApp: {telefone}
Serviço de interesse: {servico}
Temperatura: {str(temperatura).capitalize()}
Prioridade: {str(prioridade).capitalize()}
Score: {score}

Resumo da conversa:
A lead atua no segmento de {segmento} e demonstrou interesse em {servico}. O objetivo informado foi: "{objetivo}".

Pontos importantes:
- Demonstrou interesse nos serviços da Forway
- Informou o objetivo principal do negócio
- Está disponível para contato comercial
- Deve receber uma abordagem consultiva

Próxima ação recomendada:
Entrar em contato apresentando uma solução alinhada ao objetivo informado, sem repetir perguntas já respondidas.
"""

        return sanitizar_resumo_comercial(resumo_fallback)