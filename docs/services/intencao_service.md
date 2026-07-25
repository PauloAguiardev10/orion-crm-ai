# Serviço – Intenção

## Arquivo

`dashboard/services/intencao_service.py`

---

# Objetivo

O módulo `intencao_service.py` implementa a lógica de classificação automática das mensagens recebidas pelo sistema.

Sua função é transformar uma mensagem de texto em informações comerciais utilizadas pelo Dashboard e pelo agente SDR.

O serviço é responsável por:

- detectar a intenção da conversa;
- calcular um score baseado em palavras-chave;
- classificar a temperatura da lead;
- gerar um resumo inicial para o vendedor.

Este módulo não realiza consultas ao banco de dados e não depende de APIs externas.

Toda a classificação é baseada em regras definidas diretamente no código.

---

# Estrutura geral

O arquivo é composto por:

- listas de palavras-chave;
- detecção de intenção;
- cálculo de score;
- classificação da temperatura;
- geração de resumo.

Fluxo geral:

```text
Mensagem recebida
        │
        ▼
detectar_intencao()
        │
        ▼
calcular_score()
        │
        ▼
definir_temperatura()
        │
        ▼
gerar_resumo()
        │
        ▼
Resultado final
```

---

# Palavras-chave

O módulo utiliza três listas de palavras para calcular o interesse comercial.

---

## PALAVRAS_QUENTE

```python
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
```

Cada ocorrência encontrada adiciona:

```text
+15 pontos
```

---

## PALAVRAS_MORNO

```python
PALAVRAS_MORNO = [
    "como funciona",
    "explica",
    "informação",
    "informacao",
    "site",
    "instagram",
    "whatsapp",
]
```

Cada ocorrência encontrada adiciona:

```text
+5 pontos
```

---

## PALAVRAS_FRIO

```python
PALAVRAS_FRIO = [
    "não quero",
    "nao quero",
    "sem interesse",
]
```

Cada ocorrência reduz:

```text
-20 pontos
```

---

# Função detectar_intencao()

```python
detectar_intencao(mensagem)
```

Recebe uma mensagem e identifica a intenção predominante.

Primeiramente a mensagem é convertida para minúsculas:

```python
msg = mensagem.lower()
```

---

## Intenção REUNIAO

São verificadas as palavras:

```text
reunião
reuniao
agenda
marcar
```

Quando alguma delas é encontrada:

```python
return "REUNIAO"
```

---

## Intenção ORCAMENTO

São verificadas:

```text
valor
preço
preco
orçamento
orcamento
```

Quando alguma é encontrada:

```python
return "ORCAMENTO"
```

---

## Intenção IA_ATENDIMENTO

São verificadas:

```text
ia
automação
automacao
atendimento
```

Quando encontradas:

```python
return "IA_ATENDIMENTO"
```

---

## Intenção padrão

Quando nenhuma regra é atendida:

```python
return "GERAL"
```

---

# Ordem das verificações

A função executa as verificações na seguinte sequência:

```text
REUNIAO
      │
      ▼
ORCAMENTO
      │
      ▼
IA_ATENDIMENTO
      │
      ▼
GERAL
```

Isso significa que apenas a primeira intenção encontrada é retornada.

---

# Função calcular_score()

```python
calcular_score(mensagem)
```

Calcula uma pontuação baseada na quantidade de palavras encontradas.

Inicialmente:

```python
score = 0
```

Depois:

```python
msg = mensagem.lower()
```

---

## Palavras quentes

Cada palavra encontrada:

```text
+15 pontos
```

---

## Palavras mornas

Cada palavra encontrada:

```text
+5 pontos
```

---

## Palavras frias

Cada palavra encontrada:

```text
-20 pontos
```

---

## Acúmulo

O algoritmo é cumulativo.

Exemplo:

Mensagem:

```text
Quero contratar uma IA para automatizar meu atendimento.
```

Palavras encontradas:

```text
contratar
ia
automatizar
atendimento
```

Pontuação:

```text
15
+15
+15
+15

=60
```

---

Outro exemplo:

```text
Quero saber como funciona o Instagram.
```

Pontuação:

```text
como funciona  +5

instagram      +5

Total = 10
```

---

# Função definir_temperatura()

```python
definir_temperatura(score)
```

Converte a pontuação em temperatura comercial.

---

## Regras

```text
Score >= 40
```

Retorna:

```text
QUENTE
```

---

```text
Score >= 15
```

Retorna:

```text
MORNO
```

---

Caso contrário:

```text
FRIO
```

---

# Faixas

| Score | Temperatura |
|--------|-------------|
| 40 ou mais | QUENTE |
| 15 até 39 | MORNO |
| abaixo de 15 | FRIO |

---

# Função gerar_resumo()

```python
gerar_resumo(
    nome,
    mensagem,
    intencao,
    temperatura
)
```

Gera um resumo textual para o vendedor.

O texto é montado utilizando uma f-string.

Estrutura:

```text
Lead: Nome

Intenção identificada:
...

Temperatura:
...

Resumo:
Cliente demonstrou interesse em soluções da Forway.
A Sofia iniciou o atendimento, apresentou benefícios
e recomendou continuidade comercial com Luciano.
```

Ao final:

```python
return resumo.strip()
```

remove espaços e linhas em branco das extremidades.

---

# Fluxo completo

```text
Mensagem
    │
    ▼
Mensagem convertida para minúsculas
    │
    ▼
Detecta intenção
    │
    ▼
Calcula score
    │
    ▼
Define temperatura
    │
    ▼
Gera resumo
    │
    ▼
Retorna resultado
```

---

# Dependências

O módulo não depende de:

- banco de dados;
- PostgreSQL;
- SQLite;
- APIs externas;
- OpenAI;
- modelos de IA.

Todo o processamento ocorre localmente.

---

# Validações implementadas

O serviço implementa:

- conversão da mensagem para minúsculas;
- busca por palavras-chave;
- soma e subtração de pontuação;
- classificação automática da temperatura;
- geração padronizada do resumo.

---

# Validações não implementadas

O módulo não realiza:

- remoção de acentos;
- normalização completa do texto;
- stemming;
- lematização;
- processamento de linguagem natural (NLP);
- análise semântica;
- contexto da conversa;
- tratamento de negações complexas;
- aprendizado automático;
- ponderação por frequência;
- análise de sentimento.

---

# Pontos de atenção

## Busca simples

Toda a classificação utiliza:

```python
palavra in msg
```

Ou seja, busca textual simples.

---

## Ordem da intenção

Como a função retorna imediatamente após encontrar uma regra, uma mensagem contendo palavras de mais de uma categoria será classificada apenas pela primeira condição atendida.

---

## Score acumulativo

A pontuação aumenta conforme a quantidade de palavras encontradas.

Não existe limite máximo.

---

## Resumo fixo

A função `gerar_resumo()` utiliza um texto padrão.

Ela não resume efetivamente a mensagem enviada pelo cliente.

Os parâmetros utilizados dinamicamente são apenas:

- nome;
- intenção;
- temperatura.

O conteúdo descritivo permanece constante.

---

## Independência

Este serviço pode ser reutilizado em qualquer parte do sistema, pois não depende de banco ou interface gráfica.

---

# O módulo não implementa

Este arquivo não implementa:

- inteligência artificial;
- modelos de linguagem;
- embeddings;
- machine learning;
- análise contextual;
- histórico da conversa;
- personalização por empresa;
- regras por segmento;
- pesos configuráveis;
- persistência em banco;
- auditoria;
- logs.

---

# Possíveis evoluções

O serviço pode evoluir com:

- análise por IA (LLM);
- classificação por embeddings;
- regras configuráveis no banco;
- pesos personalizados;
- dicionário por segmento;
- aprendizado contínuo;
- resumo gerado por IA;
- detecção de múltiplas intenções;
- análise de sentimento;
- processamento semântico;
- remoção automática de acentos;
- tokenização.

Esses recursos não fazem parte da implementação atual.

---

# Resumo

O módulo `intencao_service.py` implementa um mecanismo determinístico de classificação baseado em palavras-chave.

Ele identifica a intenção principal da mensagem, calcula um score comercial, define a temperatura da lead e produz um resumo padronizado para o vendedor.

Toda a lógica é executada localmente por regras simples, sem dependência de banco de dados ou modelos de inteligência artificial.