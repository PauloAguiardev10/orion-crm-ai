# Dashboard – Página Serviços e Canais

## Arquivo

`dashboard/app_pages/servicos_canais.py`

---

# Objetivo

A página **Serviços e Canais** apresenta uma visão analítica da origem das oportunidades comerciais registradas no Orion CRM AI.

Seu propósito é identificar quais serviços despertam maior interesse dos clientes e quais canais de comunicação geram maior volume de leads, auxiliando gestores na tomada de decisões estratégicas.

---

# Responsabilidades

Este módulo é responsável por:

- Consolidar os serviços mais procurados.
- Consolidar os canais de entrada das leads.
- Gerar gráficos comparativos.
- Exibir rankings quantitativos.
- Fornecer indicadores para análise comercial.

---

# Fluxo de Execução

```text
Dashboard
      │
      ▼
Recebe lista de Leads
      │
      ▼
Normalização dos Dados
      │
      ▼
Agrupamento por Produto
      │
      ▼
Agrupamento por Canal
      │
      ▼
Geração dos Gráficos
      │
      ▼
Exibição dos Rankings
```

---

# Tratamento dos Dados

Antes da geração dos gráficos, o módulo verifica a existência dos campos necessários.

São normalizados os seguintes atributos:

- Produto
- Canal
- Origem

Quando o canal não está disponível, o sistema utiliza automaticamente o campo de origem da lead.

---

# Indicadores Apresentados

A página apresenta dois gráficos principais:

## Serviços Mais Procurados

Exibe a distribuição das leads conforme o serviço ou produto de interesse informado durante a qualificação realizada pela Sofia SDR.

---

## Leads por Canal

Exibe a distribuição das oportunidades conforme o canal de origem.

Exemplos:

- WhatsApp
- Instagram
- Facebook
- Outros canais futuros

---

# Rankings

Além dos gráficos, o sistema apresenta dois rankings detalhados.

## Ranking de Serviços

Lista todos os serviços ordenados pela quantidade de leads recebidas.

---

## Ranking de Canais

Lista todos os canais de aquisição classificados pelo volume de oportunidades geradas.

---

# Interface

A interface utiliza:

- Gráficos Donut
- Tabelas de Ranking
- Layout dividido em duas colunas

Essa organização facilita a comparação entre produtos e canais.

---

# Principais Funções

## render_servicos_canais()

Função responsável por:

- normalizar os dados recebidos;
- gerar os gráficos;
- calcular os rankings;
- apresentar os resultados ao usuário.

---

# Dependências

- Streamlit
- components.graficos

---

# Integração com outros módulos

Este módulo integra-se diretamente com:

- Dashboard Principal
- Página Visão Geral
- Página Resultados
- Banco PostgreSQL (através do Dashboard)

---

# Aplicação Comercial

As informações apresentadas nesta página permitem responder perguntas como:

- Qual serviço gera mais interesse?
- Qual canal gera mais oportunidades?
- Existe concentração excessiva em um único canal?
- Quais campanhas estão trazendo mais leads?

Esses indicadores auxiliam gestores na definição de estratégias de marketing e vendas.

---

# Considerações Técnicas

O módulo possui responsabilidade exclusivamente analítica.

Não realiza alterações no banco de dados e utiliza apenas os dados previamente carregados pelo Dashboard.

Sua implementação favorece futuras expansões, como:

- filtros por período;
- comparação entre empresas;
- comparação entre campanhas;
- evolução mensal dos canais;
- evolução mensal dos serviços.

---

# Resumo

A página Serviços e Canais oferece uma visão estratégica sobre a origem das oportunidades comerciais e os serviços mais demandados pelos clientes.

Esses indicadores permitem identificar tendências de mercado, avaliar campanhas de aquisição e apoiar decisões comerciais baseadas em dados.