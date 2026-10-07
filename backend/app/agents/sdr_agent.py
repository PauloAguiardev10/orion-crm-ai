import re
import random
import unicodedata

from app.services.gpt_service import (
    extrair_contexto_lead_gpt,
    formatar_canal_atendimento,
    formatar_origem_aquisicao,
    gerar_resumo_comercial_gpt,
)


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


def obter_nome_empresa(contexto_empresa) -> str:
    if contexto_empresa and contexto_empresa.nome_empresa:
        return contexto_empresa.nome_empresa
    return 'Forway'


def obter_nome_agente(contexto_empresa) -> str:
    if contexto_empresa and contexto_empresa.agente and contexto_empresa.agente.nome_agente:
        return contexto_empresa.agente.nome_agente
    return 'Sofia'


def _termo_servico_corresponde(mensagem: str, termo: str) -> bool:
    """
    Verifica se um termo configurado para um servico
    aparece na mensagem do cliente.

    Alem da frase exata, aceita pequenas palavras
    intermediarias mantendo a ordem dos termos.
    """
    mensagem_normalizada = normalizar_linguagem_cliente(mensagem)
    termo_normalizado = normalizar_linguagem_cliente(termo)
    if not termo_normalizado:
        return False
    if contem_termo(mensagem_normalizada, [termo_normalizado]):
        return True
    palavras_termo = [palavra for palavra in termo_normalizado.split() if palavra]
    if len(palavras_termo) < 2:
        return False
    palavras_mensagem = [palavra for palavra in mensagem_normalizada.split() if palavra]
    indice = 0
    for palavra in palavras_mensagem:
        if palavra == palavras_termo[indice]:
            indice += 1
            if indice == len(palavras_termo):
                return True
    return False


def identificar_servico_empresa(mensagem: str, contexto_empresa=None):
    """
    Identifica um servico usando exclusivamente
    o catalogo do tenant atual.

    Retorna o nome exato do servico cadastrado
    ou None quando nao houver correspondencia.
    """
    if contexto_empresa is None:
        return None
    servicos = contexto_empresa.servicos or ()
    candidatos = []
    for servico in servicos:
        if not getattr(servico, 'ativo', True):
            continue
        termos = []
        nome = (getattr(servico, 'nome', '') or '').strip()
        if nome:
            termos.append(nome)
        palavras_chave = getattr(servico, 'palavras_chave', '') or ''
        termos.extend((termo.strip() for termo in palavras_chave.splitlines() if termo.strip()))
        for termo in termos:
            if not _termo_servico_corresponde(mensagem, termo):
                continue
            quantidade_palavras = len(normalizar_linguagem_cliente(termo).split())
            candidatos.append((quantidade_palavras, len(termo), servico.nome))
    if not candidatos:
        return None
    candidatos.sort(reverse=True)
    return candidatos[0][2]


def resposta_servicos_empresa(contexto_empresa, saudacao=None):
    inicio = f'{saudacao}\n\n' if saudacao else 'Claro 😊\n\n'
    nome_empresa = obter_nome_empresa(contexto_empresa)
    servicos = contexto_empresa.servicos if contexto_empresa is not None else ()
    if not servicos:
        return f'{inicio}No momento, os serviços desta empresa ainda não estão configurados no sistema.\n\nComo posso te chamar?'

    nomes_servicos = [
        servico.nome.strip()
        for servico in servicos
        if servico.nome and servico.nome.strip()
    ]

    estrutura_completa = next(
        (
            nome
            for nome in nomes_servicos
            if nome.casefold() == 'estrutura completa'
        ),
        None,
    )

    servicos_individuais = sorted(
        (
            nome
            for nome in nomes_servicos
            if nome.casefold() != 'estrutura completa'
        ),
        key=str.casefold,
    )

    lista_servicos = '\n'.join(
        f'\u2022 {nome}' for nome in servicos_individuais
    )

    if not lista_servicos and not estrutura_completa:
        return f'{inicio}No momento, os serviços desta empresa ainda não estão configurados no sistema.\n\nComo posso te chamar?'

    resposta = (
        f'{inicio}Hoje a {nome_empresa} trabalha com:\n\n'
        f'{lista_servicos}'
    )

    if estrutura_completa:
        resposta += (
            '\n\nE, para empresas que precisam de uma solu\u00e7\u00e3o mais completa, '
            f'tamb\u00e9m oferecemos a {estrutura_completa}, que re\u00fane diferentes '
            f'frentes da {nome_empresa} em uma estrat\u00e9gia integrada.'
        )

    resposta += (
        '\n\nPara eu entender melhor o que faz sentido para voc\u00ea, '
        'como posso te chamar?'
    )

    return resposta


def obter_especialista_responsavel(
    contexto_empresa,
    nome_servico=None,
):
    """
    Resolve o especialista responsável dentro do próprio tenant.

    Quando um serviço ? informado, retorna somente um especialista
    explicitamente vinculado àquele serviço.

    Se existem especialistas na empresa, mas nenhum atende ao serviço
    informado, retorna None para impedir encaminhamento nominal incorreto.

    Quando nenhum serviço ? informado, pode usar o primeiro especialista
    configurado da própria empresa como referência geral.

    Nunca busca especialista em outra empresa.
    """
    if contexto_empresa is None:
        return None

    especialistas = (
        contexto_empresa.especialistas
        or ()
    )

    if not especialistas:
        return None

    if nome_servico:
        nome_normalizado = (
            normalizar_texto_comparacao(
                nome_servico
            )
        )

        servico_encontrado = None

        for servico in (
            contexto_empresa.servicos
            or ()
        ):
            if (
                normalizar_texto_comparacao(
                    servico.nome
                )
                == nome_normalizado
            ):
                servico_encontrado = servico
                break

        if servico_encontrado is not None:
            for especialista in especialistas:
                if (
                    servico_encontrado.id
                    in especialista.servicos_ids
                ):
                    return especialista

        # Existe um serviço definido, mas nenhum
        # especialista está vinculado a ele.
        # Não usar outro especialista como fallback.
        return None

    # Sem serviço definido, o primeiro especialista
    # da própria empresa pode servir como referência geral.
    return especialistas[0]


def obter_nome_especialista(contexto_empresa, nome_servico=None):
    """
    Retorna o nome do especialista responsável ou None quando
    a empresa ainda não possui especialista configurado.
    """
    especialista = obter_especialista_responsavel(contexto_empresa, nome_servico=nome_servico)
    if especialista is None:
        return None
    nome = (especialista.nome or '').strip()

    if nome and nome == nome.lower():
        particulas = {
            'da',
            'das',
            'de',
            'do',
            'dos',
            'e',
        }

        palavras = nome.split()

        nome = ' '.join(
            (
                palavra.capitalize()
                if indice == 0 or palavra not in particulas
                else palavra
            )
            for indice, palavra in enumerate(palavras)
        )

    return nome or None


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


def resposta_sem_conteudo_util(texto: str) -> bool:
    """
    Identifica respostas que nao carregam informacao suficiente
    para preencher campos de qualificacao.
    """
    valor = normalizar_linguagem_cliente(texto or "").strip()

    if not valor:
        return True

    quantidade_letras = sum(
        1
        for caractere in valor
        if caractere.isalpha()
    )

    if quantidade_letras == 0:
        return True

    respostas_genericas = {
        "sim",
        "nao",
        "ok",
        "okay",
        "certo",
        "beleza",
        "show",
        "perfeito",
        "entendi",
        "isso",
        "isso mesmo",
        "aham",
        "uhum",
        "blz",
        "ta",
        "esta bem",
        "tudo bem",
    }

    return valor in respostas_genericas


def cliente_informa_nao_ter_empresa(texto: str) -> bool:
    """
    Identifica quando a pessoa informa que nao possui empresa ou negocio formal.
    """
    valor = normalizar_linguagem_cliente(texto or "").strip()

    expressoes = [
        "nao tenho empresa",
        "nao tenho uma empresa",
        "nao tenho negocio",
        "nao tenho um negocio",
        "nao tenho cnpj",
        "sem empresa",
        "nao tei empresa",
    ]

    return any(
        expressao in valor
        for expressao in expressoes
    )


def parece_segmento_valido(texto: str) -> bool:
    """
    Evita registrar confirmacoes, emojis e cargos isolados
    como segmento de uma empresa.
    """
    valor = normalizar_linguagem_cliente(texto or "").strip()

    if resposta_sem_conteudo_util(valor):
        return False

    cargos_isolados = {
        "vendedor",
        "vendedora",
        "gerente",
        "diretor",
        "diretora",
        "dono",
        "dona",
        "proprietario",
        "proprietaria",
        "socio",
        "socia",
        "ceo",
    }

    if valor in cargos_isolados:
        return False

    return True


def parece_objetivo_valido(texto: str) -> bool:
    """
    Exige informacao comercial minimamente util antes de
    considerar o objetivo respondido.
    """
    valor = normalizar_linguagem_cliente(texto or "").strip()

    if resposta_sem_conteudo_util(valor):
        return False

    return True

def parece_nome(texto: str):
    texto = texto.strip()

    if not texto:
        return False

    texto_lower = texto.lower()

    # Evita interpretar contexto do negocio como nome da pessoa.
    prefixos_contexto_negocio = [
        "trabalho com ",
        "trabalhamos com ",
        "atuo com ",
        "atuamos com ",
        "vendo ",
        "vendemos ",
        "minha empresa ",
        "minha loja ",
        "meu negócio ",
        "meu negocio ",
        "somos do segmento ",
        "sou do segmento ",
    ]

    if any(
        texto_lower.startswith(prefixo)
        for prefixo in prefixos_contexto_negocio
    ):
        return False

    # Respostas comerciais curtas nao devem virar nome.
    respostas_comerciais_curtas = {
        "venda",
        "vendas",
        "cliente",
        "clientes",
        "lead",
        "leads",
        "contato",
        "contatos",
        "marca",
        "entrar",
        "vendedor",
        "vendedora",
    }

    if texto_lower in respostas_comerciais_curtas:
        return False

    # Evita interpretar perguntas ou frases conversacionais como nome.
    # Ex.: "Vose trabalha com oq", "Quanto custa", "Como funciona".
    palavras_conversacionais = {
        "trabalha",
        "trabalham",
        "faz",
        "fazem",
        "oferece",
        "oferecem",
        "quanto",
        "qual",
        "quais",
        "como",
    }

    palavras_normalizadas = set(
        normalizar_linguagem_cliente(texto).split()
    )

    if palavras_normalizadas & palavras_conversacionais:
        return False

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
        "Como posso te chamar? \U0001f60a",
        "Me fala seu nome? \U0001f60a",
        "E qual \u00e9 o seu nome? \U0001f60a",
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


def parece_contexto_segmento(texto: str) -> bool:
    valor = (texto or '').strip().lower()

    if not valor:
        return False

    prefixos = [
        "trabalho com ",
        "trabalhamos com ",
        "trabalho em ",
        "trabalhamos em ",
        "atuo com ",
        "atuamos com ",
        "atuo em ",
        "atuamos em ",
        "sou do segmento de ",
        "somos do segmento de ",
    ]

    return any(
        valor.startswith(prefixo)
        for prefixo in prefixos
    )


def limpar_segmento(texto: str):
    segmento = texto.strip()
    substituicoes = [
        "atuamos com", "atuamos na área de", "atuamos na area de",
        "atuamos em", "trabalhamos com", "trabalhamos na área de",
        "trabalhamos na area de", "trabalhamos em",
        "trabalho com", "trabalho na área de", "trabalho na area de",
        "trabalho em", "atuo com", "atuo na área de", "atuo na area de",
        "atuo em",
        "somos do segmento de", "sou do segmento de", "somos da área de", "somos da area de",
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



def classificar_servico_por_objetivo_contextual(
    conversa,
    analise=None,
    contexto_empresa=None,
):
    """
    Classifica o servico a partir do objetivo ja consolidado.

    Nunca sobrescreve um servico previamente identificado.
    Quando existe contexto de empresa, somente aceita servicos
    presentes e ativos no catalogo do tenant atual.
    """
    if conversa.servico:
        return conversa.servico

    objetivo = (conversa.objetivo or "").strip()
    referencia_servico = None

    if objetivo:
        if objetivo_multiplo_para_estrutura(objetivo):
            referencia_servico = "estrutura completa"

        elif objetivo_marca_para_social_media(objetivo):
            referencia_servico = "social media"


    if referencia_servico:
        if contexto_empresa is not None:
            conversa.servico = identificar_servico_empresa(
                referencia_servico,
                contexto_empresa,
            )
        else:
            if referencia_servico == "estrutura completa":
                conversa.servico = "Estrutura Completa"

            elif referencia_servico == "social media":
                conversa.servico = "Social Media Estrat\u00e9gico"

    if (
        conversa.servico is None
        and isinstance(analise, dict)
    ):
        produto = analise.get("produto")

        if produto and produto != "n\u00e3o identificado":
            if contexto_empresa is not None:
                conversa.servico = identificar_servico_empresa(
                    produto,
                    contexto_empresa,
                )
            else:
                conversa.servico = produto

    return conversa.servico


def objetivo_multiplo_para_estrutura(texto: str) -> bool:
    if (
        objetivo_vendas_para_estrutura(texto)
        and objetivo_marca_para_social_media(texto)
    ):
        return True

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
            "tudo que você mencionou",
            "tudo que voce mencionou",
            "tudo o que você mencionou",
            "tudo o que voce mencionou",
            "tenho interesse em tudo",
            "quero todos",
            "quero todos eles",
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
            "venda",
            "vendas",
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
            "presença de marca",
            "presenca de marca",
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



def obter_ultima_fala_cliente(historico: str):
    """
    Retorna a ultima fala do cliente registrada no historico.
    """
    if not historico:
        return None

    for linha in reversed(historico.splitlines()):
        linha = linha.strip()

        if not linha.lower().startswith("cliente:"):
            continue

        fala = linha.split(":", 1)[1].strip()

        if fala:
            return fala

    return None


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

def detectar_origem_aquisicao_resposta(mensagem):
    """
    Interpreta a resposta do cliente quando a Sofia perguntou
    especificamente como ele conheceu a Forway.

    Aqui podemos aceitar respostas curtas como "Instagram" ou
    "Facebook", pois já sabemos que o contexto da pergunta é a origem.
    """
    contexto = detectar_contexto_aquisicao(mensagem)

    if contexto:
        return obter_origem_aquisicao(contexto)

    texto_normalizado = normalizar_texto_comparacao(mensagem)

    if contem_termo(
        texto_normalizado,
        [
            "trabalho de um cliente",
            "trabalho para um cliente",
            "trabalho de voces para um cliente",
            "trabalho de vocês para um cliente",
            "trabalho de cliente",
            "cliente de voces",
            "cliente de vocês",
        ],
    ) and not contem_termo(
        texto_normalizado,
        [
            "me indicaram",
            "me indicou",
            "indicaram",
            "indicou",
            "indicacao",
            "indicação",
        ],
    ):
        return "referencia_cliente"

    if contem_termo(
        texto_normalizado,
        [
            "indicacao",
            "indicação",
            "me indicaram",
            "me indicou",
            "indicaram",
            "indicou",
            "amigo",
        ],
    ):
        return "indicacao"

    # Como esta funcao roda especificamente apos a pergunta de origem,
    # mencoes curtas a anuncio/campanha podem ser interpretadas como
    # aquisicao paga sem afetar a deteccao comercial geral.
    sinal_anuncio = contem_termo(
        texto_normalizado,
        [
            "anuncio",
            "an\u00fancio",
            "campanha",
            "patrocinado",
            "patrocinada",
            "publicidade",
            "propaganda",
        ],
    )

    if sinal_anuncio:
        if contem_termo(
            texto_normalizado,
            ["instagram", "insta"],
        ):
            return "anuncio_instagram"

        if contem_termo(
            texto_normalizado,
            ["facebook", "face", "facebok"],
        ):
            return "anuncio_facebook"

        return "anuncio"

    if contem_termo(
        texto_normalizado,
        ["instagram", "insta"],
    ):
        return "organico_instagram"

    if contem_termo(
        texto_normalizado,
        ["facebook", "face", "facebok"],
    ):
        return "organico_facebook"

    return None

def resposta_contexto_aquisicao(contexto, contexto_empresa=None):
    if not contexto:
        return None
    tipo = contexto.get('tipo')
    canal = contexto.get('canal')
    nome_empresa = obter_nome_empresa(contexto_empresa)
    if tipo == 'indicacao':
        return f'Que legal saber que você chegou até a {nome_empresa} por indicação 😊'
    if tipo == 'referencia_cliente':
        return f'Que legal saber que você conheceu a {nome_empresa} através de um trabalho que estamos realizando 😊'
    if tipo == 'anuncio' and canal == 'instagram':
        return f'Que legal que você chegou até a {nome_empresa} pelo nosso anúncio no Instagram 😊'
    if tipo == 'anuncio' and canal == 'facebook':
        return f'Que legal que você chegou até a {nome_empresa} pelo nosso anúncio no Facebook 😊'
    if tipo == 'anuncio':
        return f'Que legal que você chegou até a {nome_empresa} através de uma campanha nossa 😊'
    if tipo == 'organico' and canal == 'instagram':
        return f'Que legal que você conheceu a {nome_empresa} pelo nosso Instagram 😊'
    if tipo == 'organico' and canal == 'facebook':
        return f'Que legal que você conheceu a {nome_empresa} pelo nosso Facebook 😊'
    return None


def combinar_contexto_com_resposta(
    contexto,
    resposta,
    contexto_empresa=None,
    saudacao=None,
):
    abertura = resposta_contexto_aquisicao(
        contexto,
        contexto_empresa=contexto_empresa,
    )

    if not abertura:
        return resposta

    resposta_limpa = resposta.strip()

    saudacoes = (
        "Olá 😊",
        "Ola 😊",
        "Bom dia 😊",
        "Boa tarde 😊",
        "Boa noite 😊",
    )

    for saudacao_existente in saudacoes:
        if resposta_limpa.startswith(saudacao_existente):
            resposta_limpa = resposta_limpa[len(saudacao_existente):].lstrip()
            break

    if saudacao:
        return (
            f"{saudacao}\n\n"
            f"{abertura}\n\n"
            f"{resposta_limpa}"
        )

    return f"{abertura}\n\n{resposta_limpa}"


def servico_por_intencao(intencao: str):
    """
    Retorna o nome canonico do servico quando a intencao
    representa explicitamente um servico.
    """

    servicos = {
        'estrutura_completa': 'Estrutura Completa',
        'trafego': 'Gestão de Tráfego Pago',
        'automacao': 'Atendimento com IA',
        'social_media': 'Social Media Estratégico',
        'web_design': 'Web Design',
        'design': 'Design',
    }

    return servicos.get(intencao)


def identificar_servico_explicito_na_mensagem(
    mensagem: str,
    contexto_empresa=None,
):
    """
    Identifica apenas um servico explicitamente citado.

    Mantem separadas a intencao conversacional
    e a identificacao do servico.
    """
    servico_catalogo = identificar_servico_empresa(
        mensagem,
        contexto_empresa=contexto_empresa,
    )

    if servico_catalogo:
        return servico_catalogo

    # Em ambiente multiempresa, o catalogo da empresa
    # e a unica fonte valida para identificar servicos.
    if contexto_empresa is not None:
        return None

    texto = normalizar_linguagem_cliente(
        mensagem
    )

    grupos_servico = (
        (
            "estrutura_completa",
            (
                "estrutura completa",
                "estrutura de marketing",
                "toda a estrutura",
                "nossa estrutura",
                "marketing completo",
                "pacote completo",
                "servico completo",
                "solucao completa",
            ),
        ),
        (
            "trafego",
            (
                "trafego",
                "trafego pago",
                "gestao de trafego",
                "facebook ads",
                "instagram ads",
                "meta ads",
                "google ads",
                "midia paga",
            ),
        ),
        (
            "social_media",
            (
                "social media",
                "social midia",
                "gestao de redes sociais",
                "gestao do instagram",
            ),
        ),
        (
            "web_design",
            (
                "web design",
                "landing page",
                "website",
                "site profissional",
                "loja virtual",
            ),
        ),
        (
            "design",
            (
                "identidade visual",
                "design",
                "logotipo",
            ),
        ),
        (
            "automacao",
            (
                "automacao",
                "automacao de atendimento",
                "inteligencia artificial",
                "chatbot",
                "agente de ia",
                "atendimento automatizado",
            ),
        ),
    )

    for intencao_servico, termos in grupos_servico:
        if contem_termo(texto, termos):
            return servico_por_intencao(
                intencao_servico
            )

    return None


def detectar_intencao_cliente(mensagem: str):
    texto = mensagem.lower().strip()
    grupos = [('duvida_lead', ['o que é lead', 'o que e lead', 'o que significa lead', 'não sei o que é lead', 'nao sei o que e lead', 'lead é o que', 'lead e o que', 'o que são leads', 'o que sao leads']), ('objecao_experiencia_ruim', ['já tentei', 'ja tentei', 'não deu certo', 'nao deu certo', 'não funcionou', 'nao funcionou', 'experiência ruim', 'experiencia ruim', 'outra agência', 'outra agencia', 'outras agências', 'outras agencias', 'tenho medo', 'medo de contratar', 'não gostei', 'nao gostei', 'fui enganado', 'fui enganada', 'já perdi dinheiro', 'ja perdi dinheiro', 'joguei dinheiro fora', 'não confio', 'nao confio', 'experiência muito ruim', 'experiencia muito ruim', 'experiência péssima', 'experiencia pessima', 'não tive resultado', 'nao tive resultado', 'não deu resultado', 'nao deu resultado', 'sem resultado']), ('contratacao', ['quero contratar', 'quero fechar', 'vamos fechar', 'fechar negócio', 'fechar negocio', 'quero começar', 'quero comecar', 'podemos começar', 'podemos comecar', 'quero comprar', 'tenho interesse em contratar', 'quero contratar vocês', 'quero contratar voces']), ('reuniao', ['reunião', 'reuniao', 'agenda', 'agendar', 'agendamento', 'marcar horário', 'marcar horario', 'marcar uma reunião', 'marcar uma reuniao', 'falar com o luciano', 'quero falar com o luciano', 'falar com especialista', 'falar com um especialista']), ('orcamento', ['orçamento', 'orcamento', 'preço', 'preco', 'valor', 'quanto custa', 'quanto fica', 'qual o valor', 'qual valor', 'quanto vocês cobram', 'quanto voces cobram', 'investimento', 'mensalidade', 'pacote', 'pacotes', 'proposta']), ('estrutura_completa', ['estrutura completa', 'estrutura de marketing', 'toda a estrutura', 'nossa estrutura', 'marketing completo', 'tudo completo', 'quero tudo', 'pacote completo', 'serviço completo', 'servico completo', 'solução completa', 'solucao completa', 'quero todos os serviços', 'quero todos os servicos', 'quero todos os seus serviços', 'quero todos os seus servicos', 'quero todos os serviços oferecidos', 'quero todos os servicos oferecidos', 'quero todos os serviços oferecido', 'quero todos os servicos oferecido', 'quero tudo que vocês oferecem', 'quero tudo que voces oferecem', 'quero tudo que a forway oferece', 'tenho interesse em todos os serviços', 'tenho interesse em todos os servicos', 'preciso de tudo', 'estou precisando de tudo', 'preciso de tudo isso', 'tudo que você está falando', 'tudo que voce esta falando', 'tudo o que você está falando', 'tudo o que voce esta falando', 'preciso de todos os serviços', 'preciso de todos os servicos', 'tráfego e social media', 'trafego e social media', 'tráfego, social media e atendimento', 'trafego, social media e atendimento']), ('conhecer_servicos', ['como funciona o trabalho de vocês', 'como funciona o trabalho de voces', 'como funciona o trabalho da forway', 'como funciona o trabalho', 'quais serviços', 'quais servicos', 'quais são os serviços', 'quais sao os servicos', 'que serviços vocês oferecem', 'que servicos voces oferecem', 'serviços vocês oferecem', 'servicos voces oferecem', 'serviços que a forway oferece', 'servicos que a forway oferece', 'informações sobre os serviços', 'informacoes sobre os servicos', 'o que vocês fazem', 'o que voces fazem', 'como vocês trabalham', 'como voces trabalham', 'me fala dos serviços', 'me fala dos servicos', 'me explica os serviços', 'me explica os servicos', 'o que oferecem', 'não sei o que preciso', 'nao sei o que preciso', 'não sei qual serviço', 'nao sei qual servico', 'quero conhecer', 'serviços da forway', 'servicos da forway', 'gostaria de saber os serviços', 'gostaria de saber os servicos', 'gostaria de saber sobre os serviços', 'gostaria de saber sobre os servicos', 'gostaria de saber mais sobre seus serviços', 'gostaria de saber mais sobre seus servicos', 'gostaria de saber sobre seus serviços', 'gostaria de saber sobre seus servicos', 'quero saber sobre seus serviços', 'quero saber sobre seus servicos', 'quero saber mais sobre seus serviços', 'quero saber mais sobre seus servicos', 'seus serviços', 'seus servicos', 'serviços de vocês', 'servicos de voces', 'saber sobre os serviços', 'saber sobre os servicos', 'saber mais sobre os serviços', 'saber mais sobre os servicos', 'saber mais sobre seus serviços', 'saber mais sobre seus servicos']), ('trafego', ['tráfego', 'trafego', 'tráfego pago', 'trafego pago', 'gestão de tráfego', 'gestao de trafego', 'quero anunciar', 'quero fazer anúncios', 'quero fazer anuncios', 'fazer anúncios', 'fazer anuncios', 'criar anúncios', 'criar anuncios', 'rodar anúncios', 'rodar anuncios', 'facebook ads', 'instagram ads', 'meta ads', 'google ads', 'campanha paga', 'campanhas pagas', 'mídia paga', 'midia paga']), ('web_design', ['site', 'landing page', 'website', 'web site', 'página de vendas', 'pagina de vendas', 'criar um site', 'fazer um site', 'site profissional', 'loja virtual']), ('social_media', ['social media', 'social mídia', 'social midia', 'gestão de redes sociais', 'gestao de redes sociais', 'cuidar do instagram', 'gerenciar instagram', 'gestão do instagram', 'gestao do instagram', 'cuidar das redes sociais', 'gerenciar redes sociais', 'quero conteúdo', 'quero conteudo', 'preciso de conteúdo', 'preciso de conteudo', 'criar conteúdo', 'criar conteudo', 'quero postagens', 'preciso de postagens', 'melhorar engajamento', 'aumentar engajamento']), ('design', ['identidade visual', 'design', 'criativo', 'criativos', 'arte gráfica', 'arte grafica', 'artes gráficas', 'artes graficas', 'criação de arte', 'criacao de arte', 'criação de artes', 'criacao de artes', 'quero um logo', 'quero criar um logo', 'preciso de um logo', 'criar um logo', 'fazer um logo', 'criar logo', 'fazer logo', 'criação de logo', 'criacao de logo', 'logotipo', 'marca mais profissional', 'materiais melhores', 'material gráfico', 'material grafico', 'identidade da marca']), ('automacao', ['automação', 'automacao', 'automação de atendimento', 'automacao de atendimento', 'ia', 'inteligência artificial', 'inteligencia artificial', 'chatbot', 'sdr', 'agente de ia', 'agente ia', 'robô', 'robo', 'atendimento automático', 'atendimento automatico', 'atendimento automatizado', 'automatizar atendimento', 'automatizar whatsapp', 'automatizar meu whatsapp', 'automatizar o whatsapp', 'automatizar nosso whatsapp', 'automatizar as mensagens', 'automatizar mensagens', 'primeiro atendimento']), ('objetivo_comercial', ['vender mais', 'aumentar vendas', 'aumentar minhas vendas', 'aumentar as vendas', 'gerar mais vendas', 'gerar vendas', 'mais clientes', 'conseguir mais clientes', 'captar clientes', 'gerar leads', 'mais leads', 'mais contatos', 'receber mais contatos', 'gerar contatos', 'fortalecer minha marca', 'fortalecer a marca', 'fortalecer presença', 'fortalecer a presença', 'melhorar minha presença digital', 'presença digital', 'presenca digital']), ('saudacao', ['oi', 'olá', 'ola', 'bom dia', 'boa tarde', 'boa noite', 'e aí', 'e ai', 'opa'])]
    for intencao, termos in grupos:
        if contem_termo(texto, termos):
            return intencao
    return 'geral'


def analisar_mensagem(
    mensagem: str,
    contexto_empresa=None,
):
    """
    Classificacao comercial deterministica e explicavel.

    A temperatura representa o estagio comercial demonstrado pelo cliente:

    - fria: descoberta, sem interesse especifico ou necessidade concreta;
    - morna: interesse em servico especifico ou necessidade comercial;
    - quente: intencao clara de avancar para orcamento, proposta, reuniao,
      especialista ou contratacao.

    O servico e identificado exclusivamente pelo catalogo do tenant atual.

    O score, limitado de 0 a 10, complementa a temperatura e mede a forca
    acumulada dos sinais comerciais. Cada categoria pontua no maximo uma vez.
    """
    texto = mensagem.lower()
    score = 0

    servico_identificado = identificar_servico_empresa(
        mensagem,
        contexto_empresa=contexto_empresa,
    )

    produto = (
        servico_identificado
        if servico_identificado
        else "n\u00e3o identificado"
    )

    sinal_contratacao = contem_termo(
        texto,
        [
            "quero contratar",
            "vamos fechar",
            "quero fechar",
            "fechar neg\u00f3cio",
            "quero come\u00e7ar",
            "podemos come\u00e7ar",
            "quero comprar",
            "tenho interesse em contratar",
            "quero contratar voc\u00eas",
        ],
    )

    sinal_reuniao = contem_termo(
        texto,
        [
            "reuni\u00e3o",
            "agenda",
            "agendar",
            "agendamento",
            "marcar hor\u00e1rio",
            "marcar reuni\u00e3o",
            "marcar uma reuni\u00e3o",
            "falar com especialista",
            "falar com um especialista",
        ],
    )

    sinal_orcamento = contem_termo(
        texto,
        [
            "or\u00e7amento",
            "pre\u00e7o",
            "valor",
            "quanto custa",
            "quanto fica",
            "qual o valor",
            "qual valor",
            "quanto voc\u00eas cobram",
            "proposta",
            "investimento",
            "mensalidade",
        ],
    )

    sinal_objetivo = contem_termo(
        texto,
        [
            "vender",
            "vendas",
            "venda",
            "vender mais",
            "aumentar vendas",
            "aumentar minhas vendas",
            "aumentar as vendas",
            "melhorar minhas vendas",
            "gerar mais vendas",
            "gerar vendas",
            "mais clientes",
            "conseguir mais clientes",
            "captar clientes",
            "conseguir clientes",
            "gerar leads",
            "mais leads",
            "contatos",
            "clientes",
            "mais contatos",
            "receber mais contatos",
            "gerar contatos",
            "fortalecer a marca",
            "fortalecer minha marca",
            "fortalecer a presen\u00e7a",
            "presen\u00e7a digital",
            "melhorar minha presen\u00e7a digital",
            "melhorar o instagram",
            "automatizar atendimento",
            "automatizar whatsapp",
            "melhorar atendimento",
        ],
    )

    sinal_objetivo = (
        sinal_objetivo
        or objetivo_marca_para_social_media(texto)
        or objetivo_multiplo_para_estrutura(mensagem)
    )

    sinal_urgencia = contem_termo(
        texto,
        [
            "urgente",
            "urg\u00eancia",
            "o quanto antes",
            "ainda hoje",
            "essa semana",
            "esta semana",
            "preciso come\u00e7ar logo",
            "quero come\u00e7ar logo",
            "imediatamente",
        ],
    )

    sinal_dor = contem_termo(
        texto,
        [
            "j\u00e1 tentei",
            "n\u00e3o deu certo",
            "n\u00e3o funcionou",
            "outra ag\u00eancia",
            "experi\u00eancia ruim",
            "j\u00e1 perdi dinheiro",
            "fui enganado",
            "fui enganada",
        ],
    )

    if sinal_contratacao:
        score += 6

    if sinal_reuniao:
        score += 3

    if sinal_orcamento:
        score += 3

    if sinal_objetivo:
        score += 3

    if produto != "n\u00e3o identificado":
        score += 2

    if sinal_urgencia:
        score += 2

    if sinal_dor:
        score += 1

    score = min(score, 10)

    if (
        sinal_contratacao
        or sinal_reuniao
        or sinal_orcamento
    ):
        temperatura = "quente"
        prioridade = "alta"

    elif (
        produto != "n\u00e3o identificado"
        or sinal_objetivo
    ):
        temperatura = "morna"
        prioridade = "m\u00e9dia"

    else:
        temperatura = "fria"
        prioridade = "baixa"

    return {
        "temperatura": temperatura,
        "score": score,
        "produto": produto,
        "prioridade": prioridade,
    }

def gerar_resumo_vendedor(conversa, analise, contexto_empresa=None):
    nome_empresa = obter_nome_empresa(contexto_empresa)
    nome_especialista = obter_nome_especialista(contexto_empresa, nome_servico=getattr(conversa, 'servico', None))
    responsavel_acao = nome_especialista if nome_especialista else 'A equipe comercial'
    try:
        return gerar_resumo_comercial_gpt(conversa, analise, contexto_empresa=contexto_empresa, nome_especialista=nome_especialista)
    except Exception:
        canal = formatar_canal_atendimento(getattr(conversa, 'canal', None))
        origem = formatar_origem_aquisicao(getattr(conversa, 'origem_aquisicao', None))
        servico = getattr(conversa, 'servico', None) or (analise or {}).get('produto') or 'Não informado'
        temperatura = (analise or {}).get('temperatura') or 'Não informado'
        prioridade = (analise or {}).get('prioridade') or 'Não informado'
        score = (analise or {}).get('score', 0)
        return f'''\nNova lead qualificada — {nome_empresa}\n\nNome: {conversa.nome or 'Não informado'}\nEmpresa: {conversa.empresa or 'Não informado'}\nSegmento: {conversa.segmento or 'Não informado'}\nCanal de atendimento: {canal}\nOrigem da lead: {origem}\nWhatsApp: {conversa.telefone or 'Não informado'}\nServiço de interesse: {servico}\nTemperatura: {str(temperatura).capitalize()}\nPrioridade: {str(prioridade).capitalize()}\nScore: {score}\n\nResumo da conversa:\nA lead demonstrou interesse em {servico} e informou como principal objetivo: "{conversa.objetivo or 'não informado'}".\n\nPróxima ação recomendada:\n{responsavel_acao} deve entrar em contato com a lead de forma consultiva e aprofundar o entendimento do cenário.\n'''.strip()





def sofia_ja_se_apresentou(
    conversa,
    contexto_empresa=None,
):
    historico = conversa.historico or ""

    nome_agente = obter_nome_agente(
        contexto_empresa
    )

    nome_empresa = obter_nome_empresa(
        contexto_empresa
    )

    apresentacao = (
        f"Sou a {nome_agente}, da {nome_empresa}."
    )

    return (
        apresentacao in historico
        or "Agente:" in historico
        or f"{nome_agente}:" in historico
    )


def resposta_inicial_por_servico(intencao, mensagem='', contexto_empresa=None):
    saudacao = saudacao_personalizada(mensagem)
    nome_agente = obter_nome_agente(contexto_empresa)
    nome_empresa = obter_nome_empresa(contexto_empresa)
    referencia_especialista = "a equipe comercial"
    if intencao == 'saudacao':
        return f'{saudacao}\nTudo bem?\nSou a {nome_agente}, da {nome_empresa}.\nComo posso ajudar você hoje?'
    if intencao == 'conhecer_servicos':
        return resposta_servicos_empresa(contexto_empresa=contexto_empresa)
    if intencao == 'trafego':
        return f'{saudacao}\nPosso te ajudar com tr\u00e1fego pago sim \U0001f60a\nComo posso te chamar?'
    if intencao == 'orcamento':
        return f'{saudacao}\nPara falar de valores sem te passar algo genérico, o ideal é entender primeiro seu cenário.\nMe fala seu nome?'
    if intencao == 'reuniao':
        return f'{saudacao}\nClaro \U0001f60a Vou entender rapidinho seu cen\u00e1rio antes de falar com {referencia_especialista}.\nQual \u00e9 o seu nome?'
    if intencao == 'automacao':
        return f'{saudacao}\nAutoma\u00e7\u00e3o com IA pode ajudar bastante quando a empresa recebe muitos contatos e quer responder com mais agilidade.\nMe fala seu nome para eu entender seu cen\u00e1rio?'
    if intencao == 'social_media':
        return f'{saudacao}\nA {nome_empresa} trabalha social media de forma estratégica, pensando em posicionamento e resultado, não só postagem.\nComo posso te chamar?'
    if intencao == 'web_design':
        return f'{saudacao}\nUm site bem estruturado ajuda muito na credibilidade e também na geração de contatos.\nMe fala seu nome?'
    if intencao == 'design':
        return f'{saudacao}\nDesign e identidade visual fazem muita diferença na forma como o cliente percebe a empresa.\nComo posso te chamar?'
    if intencao == 'estrutura_completa':
        texto_normalizado = normalizar_linguagem_cliente(mensagem)
        nome_empresa_normalizado = normalizar_linguagem_cliente(
            nome_empresa
        )

        referencia_empresa = any(
            referencia in texto_normalizado
            for referencia in (
                f'estrutura da {nome_empresa_normalizado}',
                f'estrutura do {nome_empresa_normalizado}',
                f'estrutura de {nome_empresa_normalizado}',
            )
        )

        referencia_resultado = (
            referencia_empresa
            and any(
                termo in texto_normalizado
                for termo in (
                    '50k',
                    '50 k',
                    '50 mil',
                    'vendeu',
                    'vender',
                    'vendas',
                )
            )
        )

        if referencia_resultado:
            return (
                f'{saudacao}\n'
                'Vi que voc\u00ea quer conhecer melhor a estrutura '
                'que usamos nesse projeto. \U0001f60a\n'
                'Para eu entender melhor seu cen\u00e1rio, como posso te chamar?'
            )

        return (
            f'{saudacao}\n'
            'Vi que voc\u00ea quer conhecer melhor a nossa '
            'estrutura de marketing. \U0001f60a\n'
            'Para eu entender melhor seu cen\u00e1rio, como posso te chamar?'
        )
    if intencao == 'contratacao':
        return f'{saudacao}\nPerfeito \U0001f60a\nComo posso te chamar?'
    if intencao == 'objetivo_comercial':
        return f'{saudacao}\nEntendi 😊\nEsse é exatamente o tipo de objetivo que vale analisar com mais contexto.\nComo posso te chamar?'
    return f'{saudacao}\nSou a {nome_agente}, da {nome_empresa}.\nComo posso ajudar você hoje?'


def comentario_segmento(segmento: str):
    texto = segmento.lower()

    if "moda" in texto or "roupa" in texto:
        return (
            "Que legal 😊\n"
            "Moda é um segmento onde uma boa presença digital e um posicionamento bem trabalhado podem ajudar bastante a atrair clientes e fortalecer a marca."
        )

    return (
        "Entendi 😊\n"
        "Agora já consigo ter uma visão melhor do seu cenário."
    )


def resposta_apos_encaminhamento(
    texto,
    nome=None,
    contexto_empresa=None,
    nome_servico=None,
):
    interacao = detectar_interacao_social(texto)

    nome_especialista = obter_nome_especialista(
        contexto_empresa,
        nome_servico=nome_servico,
    )

    nome_empresa = obter_nome_empresa(
        contexto_empresa
    )

    especialistas = (
        getattr(
            contexto_empresa,
            "especialistas",
            (),
        )
        if contexto_empresa is not None
        else ()
    ) or ()

    if nome_especialista:
        referencia_contato = nome_especialista
        referencia_destino = nome_especialista
        referencia_responsavel = (
            f"{nome_especialista}, "
            f"responsável pela {nome_empresa}"
        )

        referencia_contato_de = f"de {nome_especialista}"
    elif especialistas and nome_servico:
        referencia_contato = (
            "a equipe responsável por esse atendimento"
        )
        referencia_destino = (
            "a equipe responsável por esse atendimento"
        )
        referencia_responsavel = (
            "a equipe responsável por esse atendimento"
        )

        referencia_contato_de = "da equipe respons\u00e1vel por esse atendimento"
    else:
        referencia_contato = "a equipe comercial"
        referencia_destino = "a equipe comercial"
        referencia_responsavel = "a equipe comercial"

        referencia_contato_de = "da equipe comercial"
    if interacao == "agradecimento":
        return resposta_aleatoria([
            (
                f"Eu que agrade\u00e7o"
                f"{(', ' + nome if nome else '')} \U0001f60a "
                f"{referencia_contato.capitalize()} vai falar com voc\u00ea "
                f"assim que poss\u00edvel."
            ),
            (
                f"Obrigado pelo contato"
                f"{(', ' + nome if nome else '')} \U0001f60a "
                f"Agora \u00e9 s\u00f3 aguardar o contato "
                f"{referencia_contato_de}."
            ),
        ])

    if interacao == "confirmacao":
        return resposta_aleatoria([
            (
                f"Combinado \U0001f60a "
                f"Agora \u00e9 s\u00f3 aguardar o contato "
                f"{referencia_contato_de}."
            ),
            (
                f"Perfeito \U0001f60a "
                f"{referencia_contato.capitalize()} vai falar com voc\u00ea "
                f"assim que poss\u00edvel."
            ),
        ])

    if interacao == "despedida":
        return resposta_aleatoria([
            (
                f"Combinado \U0001f60a "
                f"Obrigado pelo contato."
            ),
            (
                f"Tudo certo \U0001f60a "
                f"Foi um prazer te atender."
            ),
        ])

    return resposta_aleatoria([
        (
            f"{referencia_contato.capitalize()} vai te passar esses detalhes "
            f"assim que falar com voc\u00ea \U0001f60a"
        ),
        (
            f"Seu atendimento j\u00e1 est\u00e1 com {referencia_destino}. "
            f"{referencia_contato.capitalize()} vai falar com voc\u00ea "
            f"assim que poss\u00edvel \U0001f60a"
        ),
    ])


def resposta_base_por_servico(conversa, intencao, contexto_empresa=None):
    nome_especialista = obter_nome_especialista(contexto_empresa, nome_servico=getattr(conversa, 'servico', None))
    if nome_especialista:
        referencia_especialista = nome_especialista
    else:
        especialistas = (
            getattr(
                contexto_empresa,
                "especialistas",
                (),
            )
            if contexto_empresa is not None
            else ()
        ) or ()

        if (
            especialistas
            and getattr(
                conversa,
                "servico",
                None,
            )
        ):
            referencia_especialista = (
                "a equipe responsável por esse atendimento"
            )
        else:
            referencia_especialista = (
                "a equipe comercial"
            )
    if intencao == 'duvida_lead':
        return 'Lead é um possível cliente 😊\nPode ser alguém que chamou no WhatsApp, pediu orçamento, veio pelo Instagram ou demonstrou interesse em algum serviço.'
    if intencao == 'objecao_experiencia_ruim':
        return f'Entendo seu cuidado.\nQuando uma experiência anterior não foi boa, o ideal é olhar o que foi feito, o público, a comunicação e o acompanhamento.\nAssim {referencia_especialista} consegue analisar seu cenário e orientar você com mais segurança.'
    if conversa.servico == 'Gestão de Tráfego Pago':
        return 'Entendi.\nNesse caso, o foco não é só colocar anúncio no ar, mas atrair pessoas com perfil real de compra.'
    if conversa.servico == 'Estrutura Completa':
        return 'Entendi.\nNesse cenário, faz sentido trabalhar geração de vendas, fortalecimento da marca e presença digital de forma integrada.'
    if conversa.servico == 'Atendimento com IA':
        return 'Entendi.\nNesse cenário, a automação pode ajudar a organizar o primeiro contato sem perder o tom humano do atendimento.'
    if conversa.servico == 'Social Media Estratégico':
        return 'Entendi.\nNesse cenário, faz sentido trabalhar posicionamento, conteúdo e presença digital para fortalecer a marca de forma estratégica.'
    if conversa.servico == 'Web Design':
        return 'Entendi.\nUm site pode funcionar como uma vitrine mais profissional e também apoiar a geração de contatos.'
    if conversa.servico == 'Design':
        return 'Entendi.\nA identidade visual influencia muito na percepção de profissionalismo e confiança da empresa.'
    return 'Entendi.\nJá deu para ter uma boa noção do que você busca.'



def deve_usar_extrator_contexto(texto: str) -> bool:
    """
    Decide se a mensagem tem contexto suficiente para justificar
    uma chamada ao extrator semantico.

    Mensagens curtas e simples permanecem no fluxo deterministico.
    """
    valor = (texto or "").strip()

    if not valor:
        return False

    palavras = re.findall(
        r"[A-Za-z\u00c0-\u00ff0-9]+",
        valor,
    )

    # Respostas curtas normalmente pertencem ao fluxo cadastral
    # ou a detectores determin\u00edsticos j\u00e1 existentes.
    if len(palavras) < 5:
        return False

    normalizado = normalizar_linguagem_cliente(valor)

    # Aberturas comerciais sobre uma estrutura/solucao anunciada
    # permanecem no fluxo deterministico. O servico exato sera
    # resolvido depois com o catalogo do tenant.
    consulta_estrutura = (
        "estrutura" in normalizado
        and any(
            termo in normalizado
            for termo in (
                "quero saber",
                "saber sobre",
                "saber mais",
                "informacoes",
                "conhecer",
            )
        )
    )

    if consulta_estrutura:
        return False


    sinais_contexto = (
        "meu nome",
        "me chamo",
        "sou ",
        "minha empresa",
        "minha loja",
        "meu negocio",
        "se chama",
        "trabalho com",
        "trabalhamos com",
        "atuo com",
        "atuamos com",
        "tenho uma",
        "tenho um",
        "vendo ",
        "vendemos ",
        "quero ",
        "preciso ",
        "gostaria de",
        "meu objetivo",
        "minhas vendas",
        "nossas vendas",
        "poucos clientes",
        "poucos contatos",
        "mais clientes",
        "mais vendas",
        "mais contatos",
        "fortalecer",
        "aumentar",
        "melhorar",
    )

    quantidade_sinais = sum(
        1
        for sinal in sinais_contexto
        if sinal in normalizado
    )

    sinais_dados_negocio = (
        "meu nome",
        "me chamo",
        "minha empresa",
        "minha loja",
        "meu negocio",
        "se chama",
        "trabalho com",
        "trabalhamos com",
        "atuo com",
        "atuamos com",
        "tenho uma",
        "tenho um",
        "vendo ",
        "vendemos ",
        "meu objetivo",
        "minhas vendas",
        "nossas vendas",
        "poucos clientes",
        "poucos contatos",
        "mais clientes",
        "mais vendas",
        "mais contatos",
        "fortalecer",
        "aumentar",
        "melhorar",
    )

    tem_dados_negocio = any(
        sinal in normalizado
        for sinal in sinais_dados_negocio
    )

    intencao_deterministica = detectar_intencao_cliente(valor)

    intencoes_ja_resolvidas_sem_contexto = {
        "conhecer_servicos",
        "estrutura_completa",
        "trafego",
        "automacao",
        "social_media",
        "web_design",
        "design",
        "orcamento",
        "reuniao",
        "contratacao",
    }

    if (
        intencao_deterministica
        in intencoes_ja_resolvidas_sem_contexto
        and not tem_dados_negocio
    ):
        return False

    # Uma frase mais curta precisa combinar pelo menos dois sinais
    # comerciais/contextuais para justificar o uso do GPT.
    if len(palavras) < 10:
        return quantidade_sinais >= 2

    # Mensagens maiores podem trazer contexto \u00fatil mesmo quando
    # escritas de forma menos padronizada.
    return quantidade_sinais >= 1


def aplicar_contexto_extraido(conversa, contexto_extraido):
    """
    Aproveita somente campos confiaveis ainda vazios da conversa.

    Nao sobrescreve dados existentes.
    Nao altera servico, origem, etapa ou status.
    """
    if not isinstance(contexto_extraido, dict):
        return []

    campos_permitidos = (
        "nome",
        "empresa",
        "segmento",
        "objetivo",
    )

    campos_aplicados = []

    for campo in campos_permitidos:
        atual = getattr(conversa, campo, None)

        if isinstance(atual, str):
            atual = atual.strip()

        if atual:
            continue

        candidato = contexto_extraido.get(campo)

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

        # A IA ajuda a extrair o contexto, mas a validacao
        # deterministica continua sendo a barreira final antes
        # de gravar dados na conversa.
        if campo == "nome" and not parece_nome(valor):
            continue

        if campo == "empresa" and resposta_sem_conteudo_util(valor):
            continue

        if campo == "segmento" and not parece_segmento_valido(valor):
            continue

        if campo == "objetivo" and not parece_objetivo_valido(valor):
            continue

        setattr(
            conversa,
            campo,
            valor,
        )

        campos_aplicados.append(campo)

    return campos_aplicados


def determinar_proxima_etapa_contextual(conversa) -> str:
    """
    Determina o proximo dado realmente ausente depois que
    uma mensagem contextual foi compreendida.

    Nao altera a conversa.
    """
    if not getattr(conversa, "nome", None):
        return "coletar_nome"

    if not getattr(conversa, "empresa", None):
        return "coletar_empresa"

    if not getattr(conversa, "segmento", None):
        return "coletar_segmento"

    if not getattr(conversa, "objetivo", None):
        return "entender_objetivo"

    if not getattr(conversa, "origem_aquisicao", None):
        return "coletar_origem"

    canal = (
        getattr(conversa, "canal", "")
        or ""
    ).lower()

    telefone = (
        getattr(conversa, "telefone", None)
        or ""
    ).strip()

    if (
        canal in {
            "instagram",
            "facebook",
            "messenger",
        }
        and not telefone
    ):
        return "coletar_whatsapp"

    return "aguardando_humano"


def resposta_proxima_etapa_contextual(
    conversa,
    proxima_etapa: str,
    contexto_empresa=None,
):
    """
    Gera uma resposta curta para o proximo dado realmente ausente.

    Nao altera a conversa.
    """
    nome_empresa = obter_nome_empresa(
        contexto_empresa
    )

    if proxima_etapa == "coletar_nome":
        return (
            "Entendi melhor o seu cenário 😊\n"
            "E como posso te chamar?"
        )

    if proxima_etapa == "coletar_empresa":
        return (
            "Entendi 😊\n"
            "E qual é o nome da sua empresa?"
        )

    if proxima_etapa == "coletar_segmento":
        return (
            "Perfeito 😊\n"
            "E qual é a área de atuação da empresa?"
        )

    if proxima_etapa == "entender_objetivo":
        return (
            "Agora já consigo entender melhor o seu cenário 😊\n"
            "O que você mais gostaria de melhorar hoje no seu negócio?"
        )

    if proxima_etapa == "coletar_origem":
        return (
            "Perfeito, entendi \U0001f60a\n"
            f"E como voc\u00ea conheceu a {nome_empresa}?"
        )

    if proxima_etapa == "coletar_whatsapp":
        return (
            "Perfeito \U0001f60a\n"
            "Me passa seu WhatsApp para a gente seguir por l\u00e1?"
        )

    if proxima_etapa == "aguardando_humano":
        nome_especialista = obter_nome_especialista(
            contexto_empresa,
            nome_servico=getattr(
                conversa,
                "servico",
                None,
            ),
        )

        if nome_especialista:
            referencia = nome_especialista
        else:
            especialistas = (
                getattr(
                    contexto_empresa,
                    "especialistas",
                    (),
                )
                if contexto_empresa is not None
                else ()
            ) or ()

            if (
                especialistas
                and getattr(
                    conversa,
                    "servico",
                    None,
                )
            ):
                referencia = (
                    "a equipe responsável por esse atendimento"
                )
            else:
                referencia = "a equipe comercial"

        return (
            "Perfeito \U0001f60a "
            "J\u00e1 passei as informa\u00e7\u00f5es para "
            f"{referencia}. "
            "O contato será feito assim que possível."
        )

    return (
        "Entendi 😊\n"
        "Já consegui ter uma visão melhor do seu cenário."
    )




def sincronizar_status_atendimento(conversa):
    if conversa.humano_assumiu:
        conversa.status_atendimento = "em_atendimento_humano"
    elif conversa.etapa == "aguardando_humano":
        conversa.status_atendimento = "aguardando_humano"
    else:
        conversa.status_atendimento = "em_atendimento_ia"

def conduzir_conversa(conversa, mensagem: str, contexto_empresa=None):
    sincronizar_status_atendimento(conversa)
    nome_empresa = obter_nome_empresa(contexto_empresa)

    def obter_referencia_especialista_atual():
        nome_servico = getattr(
            conversa,
            "servico",
            None,
        )

        nome_especialista = obter_nome_especialista(
            contexto_empresa,
            nome_servico=nome_servico,
        )

        if nome_especialista:
            return nome_especialista

        especialistas = (
            getattr(
                contexto_empresa,
                "especialistas",
                (),
            )
            if contexto_empresa is not None
            else ()
        ) or ()

        if especialistas and nome_servico:
            return (
                "a equipe responsável "
                "por esse atendimento"
            )

        return "a equipe comercial"

    def obter_referencia_responsavel_atual():
        nome_servico = getattr(
            conversa,
            "servico",
            None,
        )

        nome_especialista = obter_nome_especialista(
            contexto_empresa,
            nome_servico=nome_servico,
        )

        if nome_especialista:
            return (
                f"{nome_especialista}, "
                f"responsável pela {nome_empresa}"
            )

        especialistas = (
            getattr(
                contexto_empresa,
                "especialistas",
                (),
            )
            if contexto_empresa is not None
            else ()
        ) or ()

        if especialistas and nome_servico:
            return (
                "a equipe responsável "
                "por esse atendimento"
            )

        return "a equipe comercial"

    texto = mensagem.strip()
    canal = conversa.canal.lower()
    if conversa.etapa == 'aguardando_humano':
        ultima_fala_cliente = obter_ultima_fala_cliente(
            conversa.historico or ""
        )
        interacao_atual = detectar_interacao_social(texto)
        interacao_anterior = detectar_interacao_social(
            ultima_fala_cliente or ""
        )

        if (
            interacao_atual == "confirmacao"
            and interacao_anterior == "confirmacao"
        ):
            conversa.historico = (
                conversa.historico or ""
            ) + f'\nCliente: {texto}'
            return (
                None,
                analisar_mensagem(
                    montar_texto_comercial_cliente(conversa),
                    contexto_empresa=contexto_empresa,
                ),
            )

        resposta = resposta_apos_encaminhamento(
            texto,
            conversa.nome,
            contexto_empresa=contexto_empresa,
            nome_servico=getattr(conversa, 'servico', None),
        )
        conversa.historico = (
            conversa.historico or ""
        ) + f'\nCliente: {texto}'
        conversa.historico += f'\nAgente: {resposta}'
        return (
            resposta,
            analisar_mensagem(
                montar_texto_comercial_cliente(conversa),
                contexto_empresa=contexto_empresa,
            ),
        )
    campos_contexto_aplicados = []

    if deve_usar_extrator_contexto(texto):
        contexto_extraido = extrair_contexto_lead_gpt(
            texto
        )

        campos_contexto_aplicados = aplicar_contexto_extraido(
            conversa,
            contexto_extraido,
        )

    intencao = detectar_intencao_cliente(texto)

    if not conversa.servico:
        servico_explicito = identificar_servico_explicito_na_mensagem(
            texto,
            contexto_empresa=contexto_empresa,
        )

        if servico_explicito:
            conversa.servico = servico_explicito

    # Reconhece de forma dinamica referencias como
    # "estrutura da Forway", sem fixar o nome da empresa no motor.
    texto_normalizado_intencao = normalizar_linguagem_cliente(texto)
    nome_empresa_normalizado = normalizar_linguagem_cliente(nome_empresa)

    referencias_estrutura_empresa = [
        f"estrutura da {nome_empresa_normalizado}",
        f"estrutura do {nome_empresa_normalizado}",
        f"estrutura de {nome_empresa_normalizado}",
    ]

    if any(
        referencia in texto_normalizado_intencao
        for referencia in referencias_estrutura_empresa
    ):
        intencao = 'estrutura_completa'

        if not conversa.servico:
            servico_estrutura = identificar_servico_empresa(
                'estrutura completa',
                contexto_empresa,
            )

            if servico_estrutura:
                conversa.servico = servico_estrutura

    etapas_cadastrais_sem_deteccao_servico = {
        "coletar_nome",
        "coletar_empresa",
        "coletar_segmento",
        "coletar_origem",
        "coletar_whatsapp",
    }

    if (
        conversa.servico is None
        and conversa.etapa not in etapas_cadastrais_sem_deteccao_servico
    ):
        servico_explicito = identificar_servico_empresa(
            texto,
            contexto_empresa=contexto_empresa,
        )

        if (
            servico_explicito is None
            and contexto_empresa is None
        ):
            servico_explicito = servico_por_intencao(
                intencao
            )

        if servico_explicito:
            conversa.servico = servico_explicito

    contexto_aquisicao = detectar_contexto_aquisicao(texto)
    if contexto_aquisicao and (not conversa.origem_aquisicao):
        conversa.origem_aquisicao = obter_origem_aquisicao(contexto_aquisicao)
    texto_para_analise = montar_texto_comercial_cliente(conversa, texto)
    analise = analisar_mensagem(texto_para_analise, contexto_empresa=contexto_empresa)
    etapas_que_podem_identificar_servico = ['inicio', 'entender_objetivo_inicial', 'entender_objetivo']
    if conversa.etapa in etapas_que_podem_identificar_servico and conversa.servico is None and (analise['produto'] != 'não identificado'):
        conversa.servico = analise['produto']
    conversa.historico = (conversa.historico or '') + f'\nCliente: {texto}'

    if campos_contexto_aplicados:
        classificar_servico_por_objetivo_contextual(
            conversa,
            analise=analise,
            contexto_empresa=contexto_empresa,
        )

        proxima_etapa = determinar_proxima_etapa_contextual(
            conversa
        )

        conversa.etapa = proxima_etapa

        resposta = resposta_proxima_etapa_contextual(
            conversa,
            proxima_etapa,
            contexto_empresa=contexto_empresa,
        )

    elif conversa.etapa == 'inicio':
        if intencao == 'duvida_lead':
            conversa.etapa = 'coletar_nome'
            resposta = 'Boa pergunta 😊\nLead é um possível cliente, como alguém que chama no WhatsApp, pede orçamento ou vem pelo Instagram.\nMe fala seu nome para eu entender melhor seu cenário?'
        elif intencao == 'objecao_experiencia_ruim':
            conversa.etapa = 'entender_objetivo_inicial'
            resposta = f'Entendo seu cuidado.\nMuita empresa chega até a {nome_empresa} depois de uma experiência que não funcionou bem.\nAntes de indicar qualquer caminho, o ideal é entender o que aconteceu e qual é seu objetivo agora.'
        elif intencao == 'conhecer_servicos':
            conversa.etapa = 'coletar_nome'
            resposta = resposta_inicial_por_servico('conhecer_servicos', texto, contexto_empresa=contexto_empresa)
        elif intencao == 'saudacao':
            conversa.etapa = 'inicio'
            if sofia_ja_se_apresentou(conversa, contexto_empresa=contexto_empresa):
                resposta = 'Como posso ajudar você hoje? 😊'
            else:
                resposta = resposta_inicial_por_servico('saudacao', texto, contexto_empresa=contexto_empresa)
        elif contexto_aquisicao and intencao == 'geral':
            conversa.etapa = 'inicio'
            resposta = combinar_contexto_com_resposta(contexto_aquisicao, 'Me conta, o que você está buscando para sua empresa hoje?', contexto_empresa=contexto_empresa)
        elif intencao in ['orcamento', 'reuniao', 'estrutura_completa', 'trafego', 'automacao', 'social_media', 'web_design', 'design', 'contratacao', 'objetivo_comercial']:
            conversa.etapa = 'coletar_nome'
            if sofia_ja_se_apresentou(conversa, contexto_empresa=contexto_empresa):
                if intencao == 'trafego':
                    resposta = 'Posso te ajudar com tr\u00e1fego pago sim \U0001f60a\nComo posso te chamar?'
                elif intencao == 'orcamento':
                    resposta = 'Para falar de valores sem te passar algo genérico, o ideal é entender primeiro seu cenário.\nMe fala seu nome?'
                elif intencao == 'reuniao':
                    resposta = f'Claro \U0001f60a Vou entender rapidinho seu cen\u00e1rio antes de falar com {obter_referencia_responsavel_atual()}.\nQual \u00e9 o seu nome?'
                elif intencao == 'automacao':
                    resposta = 'Automa\u00e7\u00e3o com IA pode ajudar bastante quando a empresa recebe muitos contatos e quer responder com mais agilidade.\nMe fala seu nome para eu entender seu cen\u00e1rio?'
                elif intencao == 'social_media':
                    resposta = f'A {nome_empresa} trabalha social media de forma estratégica, pensando em posicionamento e resultado, não só postagem.\nComo posso te chamar?'
                elif intencao == 'web_design':
                    resposta = 'Um site bem estruturado ajuda muito na credibilidade e também na geração de contatos.\nMe fala seu nome?'
                elif intencao == 'design':
                    resposta = 'Design e identidade visual fazem muita diferença na forma como o cliente percebe a empresa.\nComo posso te chamar?'
                elif intencao == 'estrutura_completa':
                    if conversa.servico is None:
                        servico_estrutura = identificar_servico_empresa(
                            'estrutura completa',
                            contexto_empresa,
                        )
                        if servico_estrutura:
                            conversa.servico = servico_estrutura

                    texto_normalizado = normalizar_linguagem_cliente(texto)
                    nome_empresa_normalizado = normalizar_linguagem_cliente(
                        nome_empresa
                    )

                    referencia_empresa = any(
                        referencia in texto_normalizado
                        for referencia in (
                            f'estrutura da {nome_empresa_normalizado}',
                            f'estrutura do {nome_empresa_normalizado}',
                            f'estrutura de {nome_empresa_normalizado}',
                        )
                    )

                    referencia_resultado = (
                        referencia_empresa
                        and any(
                            termo in texto_normalizado
                            for termo in (
                                '50k',
                                '50 k',
                                '50 mil',
                                'vendeu',
                                'vender',
                                'vendas',
                            )
                        )
                    )

                    if referencia_resultado:
                        resposta = (
                            'Vi que você quer conhecer melhor a estrutura '
                            'que usamos nesse projeto. 😊\n'
                            'Para eu entender melhor seu cenário, como posso te chamar?'
                        )
                    else:
                        resposta = (
                            'Vi que você quer conhecer melhor a nossa '
                            'estrutura de marketing. 😊\n'
                            'Para eu entender melhor seu cenário, como posso te chamar?'
                        )
                elif intencao == 'contratacao':
                    resposta = f'Perfeito \U0001f60a\nComo posso te chamar?'
                else:
                    resposta = 'Entendi 😊\nEsse é exatamente o tipo de objetivo que vale analisar com mais contexto.\nComo posso te chamar?'
            else:
                resposta = resposta_inicial_por_servico(intencao, texto, contexto_empresa=contexto_empresa)
        else:
            conversa.etapa = 'coletar_nome'
            if sofia_ja_se_apresentou(conversa, contexto_empresa=contexto_empresa):
                resposta = 'Claro 😊\nPara eu entender melhor seu cenário, como posso te chamar?'
            else:
                resposta = resposta_inicial_por_servico('geral', texto, contexto_empresa=contexto_empresa)
        if contexto_aquisicao and intencao != 'geral':
            resposta = combinar_contexto_com_resposta(
                contexto_aquisicao,
                resposta,
                contexto_empresa=contexto_empresa,
                saudacao=(
                    saudacao_personalizada(texto)
                    if re.search(
                        r'\b(bom dia|boa tarde|boa noite|ola|oi)\b',
                        normalizar_linguagem_cliente(texto),
                    )
                    else None
                ),
            )
    elif conversa.etapa == 'entender_objetivo_inicial':
        conversa.objetivo = texto
        analise = analisar_mensagem(montar_texto_comercial_cliente(conversa, texto), contexto_empresa=contexto_empresa)
        if conversa.servico is None:
            classificar_servico_por_objetivo_contextual(
                conversa,
                analise=analise,
                contexto_empresa=contexto_empresa,
            )
        conversa.etapa = 'coletar_nome'
        resposta = 'Entendi \U0001f60a\nComo posso te chamar?'
    elif conversa.etapa == 'coletar_nome':
        nova_intencao = detectar_intencao_cliente(texto)
        if nova_intencao == 'conhecer_servicos':
            conversa.etapa = 'coletar_nome'
            resposta = resposta_servicos_empresa(contexto_empresa=contexto_empresa)
            conversa.historico += f'\nAgente: {resposta}'
            return (resposta, analise)
        if nova_intencao in ['orcamento', 'reuniao', 'estrutura_completa', 'trafego', 'automacao', 'social_media', 'web_design', 'design', 'contratacao', 'objetivo_comercial']:
            analise = analisar_mensagem(montar_texto_comercial_cliente(conversa, texto), contexto_empresa=contexto_empresa)
            if analise['produto'] != 'não identificado':
                conversa.servico = analise['produto']
            resposta = f'{resposta_base_por_servico(conversa, nova_intencao, contexto_empresa=contexto_empresa)}\nComo posso te chamar?'
            conversa.historico += f'\nAgente: {resposta}'
            return (resposta, analise)
        if parece_contexto_segmento(texto):
            conversa.segmento = limpar_segmento(texto)
            resposta = (
                f'Entendi, voc\u00eas trabalham com {conversa.segmento} \U0001f60a\n'
                'E como posso te chamar?'
            )
            conversa.historico += f'\nAgente: {resposta}'
            return (resposta, analise)

        if not parece_nome(texto):
            resposta = resposta_nome_nao_identificado()
            conversa.historico += f'\nAgente: {resposta}'
            return (resposta, analise)
        conversa.nome = limpar_nome_cliente(texto)
        conversa.etapa = 'coletar_empresa'
        resposta = f'Prazer, {conversa.nome} 😊\nQual é o nome da sua empresa?'
    elif conversa.etapa == 'coletar_empresa':
        if resposta_sem_conteudo_util(texto):
            resposta = (
                "Me conta uma coisa \U0001f60a\n"
                "Qual \u00e9 o nome da sua empresa ou neg\u00f3cio?"
            )
            conversa.historico += f'\nAgente: {resposta}'
            return (resposta, analise)

        if cliente_informa_nao_ter_empresa(texto):
            conversa.empresa = "Sem empresa formal"

            if conversa.segmento:
                conversa.etapa = 'entender_objetivo'
                resposta = (
                    "Sem problema 😊\n"
                    "E o que voc\u00ea mais busca hoje: gerar mais vendas, "
                    "receber mais contatos ou fortalecer sua presen\u00e7a?"
                )
            else:
                conversa.etapa = 'coletar_segmento'
                resposta = (
                    "Sem problema 😊\n"
                    "E hoje voc\u00ea trabalha com o qu\u00ea?"
                )

            conversa.historico += f'\nAgente: {resposta}'
            return (resposta, analise)

        conversa.empresa = limpar_nome_empresa(texto)

        if conversa.segmento:
            if conversa.objetivo:
                if not conversa.origem_aquisicao:
                    conversa.etapa = 'coletar_origem'
                    resposta = f'Legal \U0001f60a\nE como voc\u00ea conheceu a {nome_empresa}?'
                elif canal in ['instagram', 'facebook', 'messenger']:
                    conversa.etapa = 'coletar_whatsapp'
                    resposta = f'Legal \U0001f60a\nMe passa seu WhatsApp para {obter_referencia_especialista_atual()} falar com voc\u00ea?'
                else:
                    conversa.etapa = 'aguardando_humano'
                    resposta = f'Legal \U0001f60a J\u00e1 passei as informa\u00e7\u00f5es para {obter_referencia_especialista_atual()}. O contato ser\u00e1 feito assim que poss\u00edvel.'
            else:
                conversa.etapa = 'entender_objetivo'
                resposta = 'Legal \U0001f60a\nHoje o que voc\u00ea mais busca: gerar mais vendas, receber mais contatos ou fortalecer a presen\u00e7a da marca?'
        else:
            conversa.etapa = 'coletar_segmento'
            resposta = 'Legal! E voc\u00eas trabalham com o qu\u00ea?'
    elif conversa.etapa == 'coletar_segmento':
        if not parece_segmento_valido(texto):
            if conversa.empresa == "Sem empresa formal":
                resposta = (
                    "Entendi \U0001f60a E hoje voc\u00ea trabalha com o qu\u00ea?"
                )
            else:
                resposta = (
                    "Entendi \U0001f60a E qual \u00e9 o ramo da empresa?"
                )
            conversa.historico += f'\nAgente: {resposta}'
            return (resposta, analise)

        conversa.segmento = limpar_segmento(texto)
        if conversa.objetivo:
            if not conversa.origem_aquisicao:
                conversa.etapa = 'coletar_origem'
                resposta = f'{comentario_segmento(conversa.segmento)}\nE como voc\u00ea conheceu a {nome_empresa}?'
            elif canal in ['instagram', 'facebook', 'messenger']:
                conversa.etapa = 'coletar_whatsapp'
                resposta = f'{comentario_segmento(conversa.segmento)}\nMe passa seu WhatsApp para {obter_referencia_especialista_atual()} falar com voc\u00ea?'
            else:
                conversa.etapa = 'aguardando_humano'
                resposta = f'{comentario_segmento(conversa.segmento)}\nPerfeito \U0001f60a J\u00e1 passei as informa\u00e7\u00f5es para {obter_referencia_especialista_atual()}. O contato ser\u00e1 feito assim que poss\u00edvel.'
        else:
            conversa.etapa = 'entender_objetivo'
            if conversa.empresa == "Sem empresa formal":
                resposta = (
                    f'{comentario_segmento(conversa.segmento)}\n'
                    'E o que voc\u00ea mais quer melhorar hoje: vendas, '
                    'n\u00famero de contatos ou presen\u00e7a da marca?'
                )
            else:
                resposta = (
                    f'{comentario_segmento(conversa.segmento)}\n'
                    'E o que voc\u00eas mais querem melhorar hoje: vendas, '
                    'n\u00famero de contatos ou presen\u00e7a da marca?'
                )
    elif conversa.etapa == 'entender_objetivo':
        if not parece_objetivo_valido(texto):
            if conversa.empresa == "Sem empresa formal":
                resposta = (
                    "Entendi \U0001f60a E o que voc\u00ea quer melhorar hoje: "
                    "vendas, n\u00famero de contatos ou presen\u00e7a da marca?"
                )
            else:
                resposta = (
                    "Entendi \U0001f60a E o que voc\u00eas querem melhorar hoje: "
                    "vendas, n\u00famero de contatos ou presen\u00e7a da marca?"
                )
            conversa.historico += f'\nAgente: {resposta}'
            return (resposta, analise)

        conversa.objetivo = texto
        analise = analisar_mensagem(montar_texto_comercial_cliente(conversa, texto), contexto_empresa=contexto_empresa)
        if conversa.servico is None:
            classificar_servico_por_objetivo_contextual(
                conversa,
                analise=analise,
                contexto_empresa=contexto_empresa,
            )
        resposta_base = resposta_base_por_servico(conversa, intencao, contexto_empresa=contexto_empresa)
        if not conversa.origem_aquisicao:
            conversa.etapa = 'coletar_origem'
            resposta = f'{resposta_base}\nE como voc\u00ea conheceu a {nome_empresa}?'
        elif canal in ['instagram', 'facebook', 'messenger']:
            conversa.etapa = 'coletar_whatsapp'
            resposta = f'{resposta_base}\nMe passa seu WhatsApp para {obter_referencia_especialista_atual()} falar com voc\u00ea?'
        else:
            conversa.etapa = 'aguardando_humano'
            resposta = f'{resposta_base}\nPerfeito \U0001f60a J\u00e1 passei as informa\u00e7\u00f5es para {obter_referencia_especialista_atual()}. O contato ser\u00e1 feito assim que poss\u00edvel.'
    elif conversa.etapa == 'coletar_origem':
        origem = detectar_origem_aquisicao_resposta(texto)

        if origem:
            if not conversa.origem_aquisicao:
                conversa.origem_aquisicao = origem

            if canal in ['instagram', 'facebook', 'messenger']:
                conversa.etapa = 'coletar_whatsapp'
                resposta = f'Perfeito \U0001f60a\nMe passa seu WhatsApp para {obter_referencia_especialista_atual()} falar com voc\u00ea?'
            else:
                conversa.etapa = 'aguardando_humano'
                resposta = f'Perfeito \U0001f60a J\u00e1 passei as informa\u00e7\u00f5es para {obter_referencia_especialista_atual()}. O contato ser\u00e1 feito assim que poss\u00edvel.'
        else:
            parece_complemento_objetivo = (
                objetivo_multiplo_para_estrutura(texto)
                or objetivo_vendas_para_estrutura(texto)
                or objetivo_marca_para_social_media(texto)
            )

            if parece_complemento_objetivo:
                objetivo_anterior = (conversa.objetivo or '').strip()

                if objetivo_anterior:
                    conversa.objetivo = f'{objetivo_anterior}. {texto}'
                else:
                    conversa.objetivo = texto

                servico_estrutura = identificar_servico_empresa(
                    "estrutura completa",
                    contexto_empresa,
                )
                servico_social = identificar_servico_empresa(
                    "social media",
                    contexto_empresa,
                )

                if objetivo_multiplo_para_estrutura(conversa.objetivo):
                    if (
                        servico_estrutura
                        and conversa.servico in [None, servico_social]
                    ):
                        conversa.servico = servico_estrutura

                elif conversa.servico is None:
                    classificar_servico_por_objetivo_contextual(
                        conversa,
                        contexto_empresa=contexto_empresa,
                    )

                conversa.etapa = 'coletar_origem'
                resposta = (
                    'Perfeito, entendi melhor agora \U0001f60a\n'
                    f'E como voc\u00ea conheceu a {nome_empresa}?'
                )
            else:
                conversa.etapa = 'coletar_origem'
                resposta = f'E como voc\u00ea conheceu a {nome_empresa}? Foi por indica\u00e7\u00e3o, Instagram, Facebook ou algum an\u00fancio?'
    elif conversa.etapa == 'coletar_whatsapp':
        conversa.telefone = texto
        conversa.etapa = 'aguardando_humano'
        resposta = f'Perfeito \U0001f60a J\u00e1 passei as informa\u00e7\u00f5es para {obter_referencia_especialista_atual()}. O contato ser\u00e1 feito assim que poss\u00edvel.'
    else:
        resposta = resposta_apos_encaminhamento(texto, conversa.nome, contexto_empresa=contexto_empresa, nome_servico=getattr(conversa, 'servico', None))
    conversa.historico += f'\nAgente: {resposta}'
    analise = analisar_mensagem(montar_texto_comercial_cliente(conversa), contexto_empresa=contexto_empresa)
    sincronizar_status_atendimento(conversa)
    return (resposta, analise)

