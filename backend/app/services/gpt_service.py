import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


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

A Forway oferece:
- Gestão de tráfego pago
- Social media estratégico
- Design
- Atendimento automatizado com IA
- Web design
- Treinamento e suporte comercial

Contexto:
{contexto_cliente}
"""
                }
            ],
            temperature=0.7,
            max_tokens=300
        )

        return resposta.choices[0].message.content

    except Exception as erro:
        print("ERRO GPT:", erro)

        return (
            "Perfeito 😊 entendi melhor o que você procura. "
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

Serviços:
- Gestão de tráfego pago
- Social media estratégico
- Design
- Atendimento automatizado com IA
- Web design
- Treinamento e suporte comercial

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

        return resposta.choices[0].message.content

    except Exception as erro:
        print("ERRO GPT SERVIÇOS:", erro)

        return (
            "Claro 😊 A Forway trabalha com tráfego pago, social media estratégico, design, "
            "atendimento automatizado com IA, web design e suporte comercial. "
            "Nosso diferencial é oferecer tudo em um só lugar, de forma integrada. "
            "Qual objetivo você deseja alcançar hoje?"
        )


def gerar_resumo_comercial_gpt(conversa, analise):
    try:
        resposta = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"""
Gere um resumo comercial profissional para o vendedor da Forway.

Dados:
Nome: {conversa.nome or "Não informado"}
Empresa: {conversa.empresa or "Não informado"}
Segmento: {conversa.segmento or "Não informado"}
Canal: {conversa.canal}
WhatsApp: {conversa.telefone or "Não informado"}
Serviço: {conversa.servico or analise["produto"]}
Temperatura: {analise["temperatura"]}
Prioridade: {analise["prioridade"]}
Score: {analise["score"]}
Objetivo: {conversa.objetivo or "Não informado"}

Histórico:
{conversa.historico}

Formato obrigatório:

Nova lead qualificada — Forway

Nome:
Empresa:
Segmento:
Canal:
WhatsApp:
Serviço de interesse:
Temperatura:
Prioridade:
Score:

Resumo da conversa:

Pontos importantes:
•

Próxima ação recomendada:

Não copie o histórico bruto. Faça uma análise comercial limpa.
"""
                }
            ],
            temperature=0.4,
            max_tokens=600
        )

        return resposta.choices[0].message.content

    except Exception as erro:
        print("ERRO GPT RESUMO:", erro)

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