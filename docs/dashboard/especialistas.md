# Dashboard – Página Especialistas

## Arquivo

`dashboard/app_pages/especialistas.py`

---

# Objetivo

A página **Especialistas** apresenta o desempenho individual dos profissionais responsáveis pelo atendimento e acompanhamento das leads dentro do Orion CRM AI.

Seu objetivo é permitir que gestores visualizem, de forma rápida, quantas oportunidades estão atribuídas a cada especialista, em quais etapas do funil essas leads se encontram e quais serviços estão sendo atendidos.

---

# Responsabilidades

Este módulo é responsável por:

- Listar os especialistas encontrados nas leads.
- Permitir a seleção de um responsável.
- Filtrar as leads atribuídas ao especialista selecionado.
- Calcular métricas individuais.
- Exibir gráficos de desempenho.
- Apresentar os dados das leads vinculadas ao especialista.

---

# Fluxo de Execução

```text
Dashboard
      │
      ▼
Recebe lista de Leads
      │
      ▼
Normalização das Colunas
      │
      ▼
Identificação dos Responsáveis
      │
      ▼
Seleção do Especialista
      │
      ▼
Filtragem das Leads
      │
      ▼
Cálculo das Métricas
      │
      ▼
Gráficos de Performance
      │
      ▼
Exibição das Leads
```

---

# Tratamento Inicial dos Dados

A função principal recebe um DataFrame contendo as leads carregadas pelo Dashboard.

Caso não existam registros, a página apresenta a mensagem:

```text
Nenhuma lead encontrada.
```

A execução é encerrada para evitar operações sobre um conjunto vazio.

Antes de utilizar os dados, o módulo cria uma cópia do DataFrame:

```python
leads = leads.copy()
```

Isso evita alterações acidentais no objeto original recebido pela página.

---

# Normalização das Colunas

O módulo garante a existência das seguintes colunas:

- Nome
- Empresa
- Produto
- Score
- Temperatura
- Canal
- Origem
- Status
- Responsável

Caso alguma dessas colunas não esteja presente, é criado um valor padrão.

Exemplos:

- Nome: `Lead sem nome`
- Empresa: `Empresa não informada`
- Produto: `Produto não informado`
- Score: `0`
- Temperatura: `fria`
- Status: `Aguardando atendimento`
- Responsável: `Não atribuído`

---

# Tratamento do Canal

Caso a coluna `canal` não exista ou todos os seus valores estejam vazios, o sistema utiliza a coluna `origem`.

```python
leads["canal"] = leads["origem"]
```

Esse comportamento garante que a origem da lead continue visível mesmo quando o campo específico de canal ainda não estiver preenchido.

---

# Normalização do Responsável

A coluna `responsavel` recebe tratamento para substituir valores ausentes por:

```text
Não atribuído
```

Em seguida, todos os valores são convertidos para texto.

Isso garante consistência durante a criação da lista de especialistas e durante a filtragem das leads.

---

# Seleção do Especialista

Os responsáveis são obtidos diretamente da coluna `responsavel`.

A lista é:

- convertida para valores únicos;
- ordenada alfabeticamente;
- apresentada em um componente `selectbox`.

```python
especialista = st.selectbox(
    "Selecione especialista:",
    responsaveis
)
```

Após a seleção, o módulo filtra apenas as leads atribuídas ao profissional escolhido.

```python
leads_resp = leads[
    leads["responsavel"] == especialista
]
```

---

# Métricas Individuais

O painel calcula quatro indicadores principais para o especialista selecionado.

## Total de Leads

Representa a quantidade total de oportunidades atribuídas ao especialista.

```python
total = len(leads_resp)
```

---

## Em Atendimento

Conta as leads cujo status contém a expressão:

```text
em atendimento
```

A comparação é realizada após a normalização do status para letras minúsculas.

---

## Propostas

Conta as leads cujo status contém a palavra:

```text
proposta
```

Esse indicador representa oportunidades que já avançaram para uma etapa de apresentação ou envio de proposta comercial.

---

## Fechados

Conta as leads cujo status contém a palavra:

```text
fechado
```

Esse indicador representa os registros reconhecidos pelo código como negócios concluídos.

---

# Observação sobre o Cálculo de Fechados

A implementação atual considera qualquer status que contenha a palavra `fechado`.

Isso significa que, dependendo dos valores existentes no banco, um status como:

```text
Não fechado
```

também pode ser contado nesse indicador.

Para evitar essa possibilidade, uma evolução futura poderá excluir explicitamente os status contendo:

```text
não fechado
```

ou:

```text
nao fechado
```

---

# Cards de Indicadores

As quatro métricas são exibidas em cards personalizados:

- Total Leads
- Em atendimento
- Propostas
- Fechados

Os cards são construídos com HTML e CSS incorporados ao Streamlit.

A estilização utiliza:

- fundo em gradiente;
- bordas arredondadas;
- sombras;
- títulos secundários;
- valores em destaque.

---

# Performance do Especialista

A seção **Performance** apresenta dois gráficos do tipo Donut.

## Pipeline do Especialista

Exibe a distribuição das leads por status.

```python
grafico_donut(
    leads_resp,
    "status",
    "Pipeline Especialista"
)
```

Esse gráfico permite visualizar em quais etapas do processo comercial estão concentradas as oportunidades do responsável selecionado.

---

## Serviços Atendidos

Exibe a distribuição das leads por produto ou serviço.

```python
grafico_donut(
    leads_resp,
    "produto",
    "Serviços Atendidos"
)
```

Esse indicador permite identificar quais soluções estão sendo atendidas com maior frequência por determinado especialista.

---

# Exibição das Leads

Após as métricas e gráficos, o módulo apresenta todas as leads atribuídas ao especialista.

Cada oportunidade é exibida em um card individual.

As informações apresentadas são:

- Nome
- Empresa
- Produto
- Score
- Temperatura
- Canal
- Status

---

# Cards das Leads

Os cards utilizam HTML e CSS personalizados.

Cada card contém:

## Título

Nome da lead.

## Dados Comerciais

- Empresa
- Produto ou serviço
- Score
- Temperatura
- Canal de origem
- Status atual

Essa estrutura oferece uma visão resumida das oportunidades sob responsabilidade de cada profissional.

---

# Funções do Módulo

## valor_seguro()

```python
def valor_seguro(lead, coluna, padrao="Não informado"):
```

Função auxiliar responsável por recuperar um valor da lead de forma segura.

Retorna o valor padrão quando:

- a coluna não existe;
- o valor é `None`;
- o valor é `NaN`;
- o conteúdo está vazio;
- ocorre alguma exceção durante a leitura.

Essa função evita erros durante a renderização dos cards.

---

## render_especialistas()

```python
def render_especialistas(leads):
```

Função principal responsável pela construção completa da página.

Suas etapas incluem:

- validação do DataFrame;
- normalização das colunas;
- identificação dos responsáveis;
- seleção do especialista;
- filtragem das leads;
- cálculo das métricas;
- renderização dos cards;
- geração dos gráficos;
- exibição das oportunidades.

---

# Dependências

O módulo utiliza:

- Streamlit
- `components.graficos`

A função importada é:

```python
grafico_donut
```

---

# Integração com outros módulos

A página Especialistas integra-se com:

- Dashboard principal
- Página Leads
- Página Resultados
- Serviço de carregamento das leads
- Componente de gráficos
- Banco de dados, indiretamente

O módulo não realiza consultas diretas ao banco.

As leads são recebidas prontas através do parâmetro da função `render_especialistas()`.

---

# Separação de Responsabilidades

Este módulo possui responsabilidade de visualização e análise.

Ele não realiza:

- cadastro de especialistas;
- alteração do responsável;
- atualização de status;
- exclusão de registros;
- gravação direta no banco de dados.

A atribuição e o gerenciamento das leads são realizados em outros módulos do CRM.

---

# Aplicação Comercial

A página permite responder perguntas como:

- Quantas leads cada especialista possui?
- Quantas oportunidades estão em atendimento?
- Quantas propostas estão em andamento?
- Quantos negócios foram fechados?
- Quais serviços cada profissional atende com maior frequência?
- Como está distribuído o pipeline individual?
- Quais leads estão sob responsabilidade de cada atendente?

---

# Considerações Técnicas

A lista de especialistas é formada a partir dos nomes existentes na coluna `responsavel` das leads.

Isso significa que o módulo não consulta diretamente o cadastro oficial de usuários ou especialistas.

Dessa forma, serão exibidos apenas os responsáveis que já apareçam em algum registro de lead.

O valor `Não atribuído` também poderá aparecer como uma opção quando existirem oportunidades sem responsável definido.

---

# Evoluções Futuras

A estrutura atual permite implementar funcionalidades como:

- cálculo correto de fechamentos, excluindo `Não fechado`;
- filtro por período;
- filtro por canal;
- filtro por serviço;
- filtro por temperatura;
- metas por especialista;
- taxa de conversão individual;
- valor total vendido por profissional;
- receita recorrente por especialista;
- tempo médio de atendimento;
- ranking geral da equipe;
- comparação entre especialistas;
- exibição de especialistas sem leads;
- alertas para leads paradas;
- exportação de relatórios individuais.

---

# Resumo

A página Especialistas oferece uma visão individualizada do desempenho da equipe comercial dentro do Orion CRM AI.

Por meio de métricas, gráficos e cards de oportunidades, o gestor consegue acompanhar o volume de trabalho de cada profissional, a distribuição do pipeline e os serviços atendidos.

O módulo atua exclusivamente como painel analítico, utilizando as informações de responsabilidade já registradas nas leads.