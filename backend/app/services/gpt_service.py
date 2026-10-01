import os
import re
import unicodedata

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel


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



class CampoContextoLead(BaseModel):
    valor: str | None
    evidencia: str | None


class ContextoLeadExtraido(BaseModel):
    nome: CampoContextoLead
    empresa: CampoContextoLead
    segmento: CampoContextoLead
    objetivo: CampoContextoLead
    dor: CampoContextoLead


def extrair_contexto_lead_gpt(mensagem: str, debug: bool = False):
    """
    Extrai contexto comercial usando Structured Outputs.

    A funcao nao conduz a conversa e nao grava dados.
    Cada valor precisa estar apoiado por evidencia textual.
    """

    campos = (
        "nome",
        "empresa",
        "segmento",
        "objetivo",
        "dor",
    )

    def resultado_vazio():
        return {
            campo: {
                "valor": None,
                "evidencia": None,
            }
            for campo in campos
        }

    mensagem = (mensagem or "").strip()

    if not mensagem:
        return resultado_vazio()

    try:
        resposta = client.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Extraia somente informacoes explicitamente presentes "
                        "na mensagem do cliente. "

                        "Para cada campo, informe valor e evidencia. "
                        "Quando nao houver informacao suficiente, use null "
                        "em valor e null em evidencia. "

                        "A evidencia deve ser um trecho literal da mensagem "
                        "que sustente o valor extraido. "

                        "NOME: somente o nome da pessoa. "

                        "EMPRESA: somente nome proprio, marca ou nome comercial "
                        "explicitamente informado. "
                        "Uma descricao do tipo de negocio nao e nome de empresa. "
                        "'Tenho uma oficina mecanica' nao informa empresa. "
                        "'Tenho uma clinica de estetica' nao informa empresa. "

                        "SEGMENTO: atividade, mercado ou tipo de negocio. "
                        "'Tenho uma oficina mecanica' informa segmento "
                        "oficina mecanica. "
                        "'Tenho uma clinica de estetica' informa segmento "
                        "clinica de estetica ou estetica. "
                        "Esses sao apenas exemplos; identifique qualquer "
                        "segmento informado pelo cliente. "

                        "OBJETIVO: resultado comercial que o cliente deseja. "
                        "Se houver varios objetivos, coloque todos em uma unica "
                        "string curta, separados naturalmente. "
                        "Exemplo: 'vender mais e fortalecer minha marca'. "
                        "Conseguir clientes, gerar leads, aumentar vendas, "
                        "aumentar faturamento e fortalecer a marca sao exemplos "
                        "de objetivos. "
                        "Pedido generico de informacoes sobre servicos nao e "
                        "objetivo comercial. "

                        "DOR: problema ou dificuldade explicitamente relatado, "
                        "como vendas fracas, poucos contatos ou baixo retorno. "

                        "Nao invente informacoes. "
                        "Nao deduza nome de empresa a partir do segmento. "
                        "Nao use conhecimento externo."
                    ),
                },
                {
                    "role": "user",
                    "content": mensagem,
                },
            ],
            temperature=0,
            max_tokens=320,
            response_format=ContextoLeadExtraido,
        )

        mensagem_resposta = resposta.choices[0].message
        extraido = mensagem_resposta.parsed

        if debug:
            print(
                "GPT_PARSED:",
                extraido.model_dump()
                if extraido is not None
                else None,
            )

        if extraido is None:
            return resultado_vazio()

        dados = extraido.model_dump()
        resultado = resultado_vazio()

        def normalizar_evidencia(texto_evidencia: str) -> str:
            texto_evidencia = unicodedata.normalize(
                "NFKD",
                texto_evidencia,
            )

            texto_evidencia = "".join(
                caractere
                for caractere in texto_evidencia
                if not unicodedata.combining(caractere)
            )

            texto_evidencia = texto_evidencia.lower()

            texto_evidencia = re.sub(
                r"[^a-z0-9\s]",
                " ",
                texto_evidencia,
            )

            return re.sub(
                r"\s+",
                " ",
                texto_evidencia,
            ).strip()

        mensagem_normalizada = normalizar_evidencia(mensagem)

        palavras_mensagem = re.findall(
            r"[A-Za-z\u00c0-\u00ff0-9]+",
            mensagem,
        )

        mensagem_de_uma_palavra = (
            len(palavras_mensagem) == 1
        )

        segmento_extraido = dados.get("segmento") or {}

        valor_segmento = (
            segmento_extraido.get("valor")
            if isinstance(segmento_extraido, dict)
            else None
        )

        valor_segmento_normalizado = (
            normalizar_evidencia(valor_segmento)
            if isinstance(valor_segmento, str)
            else ""
        )

        for campo in campos:
            candidato = dados.get(campo)

            if not isinstance(candidato, dict):
                continue

            valor = candidato.get("valor")
            evidencia = candidato.get("evidencia")

            if not isinstance(valor, str):
                continue

            if not isinstance(evidencia, str):
                continue

            valor = valor.strip()
            evidencia = evidencia.strip()

            if not valor or not evidencia:
                continue

            # Alguns modelos podem representar ausencia como texto.
            if valor.lower() in {"null", "none"}:
                continue

            if evidencia.lower() in {"null", "none"}:
                continue

            valor_normalizado = normalizar_evidencia(valor)

            # Evita transformar uma palavra comercial isolada
            # em objetivo sem contexto suficiente.
            if (
                campo == "objetivo"
                and mensagem_de_uma_palavra
            ):
                continue

            # Se o mesmo valor foi extraido como empresa e
            # segmento, priorizamos segmento. Isso evita casos
            # como "Tenho um restaurante" -> empresa restaurante.
            if (
                campo == "empresa"
                and valor_segmento_normalizado
                and valor_normalizado
                == valor_segmento_normalizado
            ):
                continue

            evidencia_normalizada = normalizar_evidencia(
                evidencia
            )

            if not evidencia_normalizada:
                continue

            # Segunda barreira:
            # a evidencia precisa existir semanticamente no texto
            # original, tolerando apenas acentos e pontuacao.
            if evidencia_normalizada not in mensagem_normalizada:
                continue

            resultado[campo] = {
                "valor": valor,
                "evidencia": evidencia,
            }

        return resultado

    except Exception:
        return resultado_vazio()

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


def formatar_canal_atendimento(canal):
    mapa = {
        "whatsapp": "WhatsApp",
        "instagram": "Instagram",
        "facebook": "Facebook",
        "messenger": "Facebook Messenger",
    }

    valor = str(canal or "").strip()

    if not valor:
        return "Não informado"

    return mapa.get(
        valor.lower(),
        valor,
    )


def formatar_origem_aquisicao(origem):
    mapa = {
        "indicacao": "Indicação",
        "referencia_cliente": "Referência de cliente",
        "anuncio_instagram": "Anúncio no Instagram",
        "anuncio_facebook": "Anúncio no Facebook",
        "anuncio": "Anúncio",
        "organico_instagram": "Instagram orgânico",
        "organico_facebook": "Facebook orgânico",
    }

    valor = str(origem or "").strip()

    if not valor:
        return "Não informado"

    return mapa.get(
        valor,
        valor.replace("_", " ").capitalize(),
    )



def resumo_comercial_valido(texto: str) -> bool:
    """
    Valida se o resumo comercial possui uma proxima acao
    suficientemente completa para uso pela equipe comercial.
    """

    if not texto:
        return False

    padrao = re.compile(
        "Pr\u00f3xima a\u00e7\u00e3o recomendada:\\s*(.+)",
        flags=re.IGNORECASE | re.DOTALL,
    )

    resultado = padrao.search(
        texto.strip()
    )

    if not resultado:
        return False

    acao = resultado.group(1).strip()

    palavras = re.findall(
        r"\b[\w\u00c0-\u00ff]+\b",
        acao,
        flags=re.UNICODE,
    )

    return len(palavras) >= 6


def gerar_resumo_comercial_gpt(
    conversa,
    analise,
    contexto_empresa=None,
    nome_especialista=None,
):
    analise = analise or {}

    nome_empresa = (
        getattr(
            contexto_empresa,
            "nome_empresa",
            None,
        )
        or "Empresa"
    )

    especialista_responsavel = (
        nome_especialista
        or "Equipe comercial"
    )

    responsavel_acao = (
        nome_especialista
        or "A equipe comercial"
    )

    nome = conversa.nome or "Não informado"
    empresa = conversa.empresa or "Não informado"
    segmento = conversa.segmento or "Não informado"

    canal = formatar_canal_atendimento(
        conversa.canal
    )

    origem = formatar_origem_aquisicao(
        getattr(
            conversa,
            "origem_aquisicao",
            None,
        )
    )

    telefone = (
        conversa.telefone
        or "Não informado"
    )

    servico = (
        conversa.servico
        or analise.get("produto")
        or "Não informado"
    )

    temperatura = (
        analise.get("temperatura")
        or "Não informado"
    )

    prioridade = (
        analise.get("prioridade")
        or "Não informado"
    )

    score = analise.get(
        "score",
        0,
    )

    objetivo = (
        conversa.objetivo
        or "Não informado"
    )

    historico = (
        conversa.historico
        or "Não informado"
    )

    try:
        resposta = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"""
Você é responsável por gerar resumos comerciais para a equipe da {nome_empresa}.

Escreva exclusivamente em português do Brasil.

REGRAS OBRIGATÓRIAS:

- Use sempre a palavra "lead".
- Nunca traduza "lead" como "liderança", "pista" ou qualquer outro termo.
- Nunca use as palavras "derrotada", "derrotado" ou "jurídico".
- O título deve ser exatamente:
  Nova lead qualificada — {nome_empresa}
- Preserve exatamente o nome do serviço informado.
- Nunca renomeie, traduza ou substitua o serviço por outro.
- Não invente informações.
- Não copie o histórico bruto.
- Não altere nome, empresa da lead, telefone, canal de atendimento, origem da lead, serviço, temperatura, prioridade ou score.
- Não informe que a venda foi concluída.
- Não informe que a lead foi derrotada.
- O resumo deve ser objetivo, profissional e consultivo.
- Não use linguagem excessivamente promocional.
- Utilize marcadores com o caractere "-".
- Não inclua saudações, emojis ou mensagens direcionadas ao cliente.
- Na próxima ação recomendada, respeite o responsável comercial informado.
- Produza somente o resumo comercial no formato solicitado.
"""
                },
                {
                    "role": "user",
                    "content": f"""
Gere o resumo usando somente os dados abaixo.

Empresa responsável pelo atendimento: {nome_empresa}
Especialista responsável: {especialista_responsavel}

Nome: {nome}
Empresa: {empresa}
Segmento: {segmento}
Canal de atendimento: {canal}
Origem da lead: {origem}
WhatsApp: {telefone}
Serviço de interesse: {servico}
Temperatura: {temperatura}
Prioridade: {prioridade}
Score: {score}
Objetivo: {objetivo}

Histórico da conversa:
{historico}

Use obrigatoriamente este formato:

Nova lead qualificada — {nome_empresa}

Nome: {nome}
Empresa: {empresa}
Segmento: {segmento}
Canal de atendimento: {canal}
Origem da lead: {origem}
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
[use {responsavel_acao} como responsável pela continuidade comercial]
"""
                }
            ],
            temperature=0.2,
            max_tokens=600,
        )

        resumo = extrair_conteudo_resposta(
            resposta
        )

        if resumo:
            resumo_sanitizado = sanitizar_resumo_comercial(
                resumo
            )

            if resumo_comercial_valido(
                resumo_sanitizado
            ):
                return resumo_sanitizado

            raise ValueError(
                "A OpenAI retornou um resumo comercial incompleto."
            )

        raise ValueError(
            "A OpenAI retornou um resumo vazio."
        )

    except Exception as erro:
        print(
            "ERRO GPT RESUMO:",
            erro,
        )

        resumo_fallback = f"""
Nova lead qualificada — {nome_empresa}

Nome: {nome}
Empresa: {empresa}
Segmento: {segmento}
Canal de atendimento: {canal}
Origem da lead: {origem}
WhatsApp: {telefone}
Serviço de interesse: {servico}
Temperatura: {str(temperatura).capitalize()}
Prioridade: {str(prioridade).capitalize()}
Score: {score}

Resumo da conversa:
A lead atua no segmento de {segmento} e demonstrou interesse em {servico}. O objetivo informado foi: "{objetivo}".

Pontos importantes:
- Demonstrou interesse em {servico}
- Informou o objetivo principal do negócio
- Está disponível para contato comercial
- Deve receber uma abordagem consultiva

Próxima ação recomendada:
{responsavel_acao} deve entrar em contato apresentando uma solução alinhada ao objetivo informado, sem repetir perguntas já respondidas.
"""

        return sanitizar_resumo_comercial(
            resumo_fallback
        )

