# Dashboard – Página Resultados Comerciais

## Arquivo

`dashboard/app_pages/resultados.py`

---

# Objetivo

A página **Resultados Comerciais** consolida os principais indicadores de desempenho do processo comercial do Orion CRM AI.

Seu objetivo é transformar os dados coletados durante o atendimento da Sofia SDR em informações estratégicas para gestores, permitindo acompanhar conversões, faturamento, desempenho dos especialistas e principais motivos de perda.

---

# Responsabilidades

Este módulo é responsável por:

- Calcular indicadores comerciais.
- Apresentar métricas financeiras.
- Calcular taxa de conversão.
- Identificar os melhores canais.
- Identificar os serviços mais vendidos.
- Identificar o especialista com maior desempenho.
- Exibir motivos de perda.
- Gerar gráficos analíticos.
- Exibir ranking de especialistas.

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
Separação entre Negócios Fechados
e Não Fechados
      │
      ▼
Cálculo dos Indicadores
      │
      ▼
Geração dos Gráficos
      │
      ▼
Exibição dos Rankings
```

---

# Processamento dos Dados

Antes da geração dos indicadores, o módulo normaliza os principais campos da base de dados.

São tratados automaticamente:

- Status
- Produto
- Responsável
- Canal
- Origem
- Valor do Negócio
- Mensalidade
- Motivo da Perda
- Observações Comerciais

---

# Indicadores Principais

A página calcula automaticamente:

## Negócios Fechados

Quantidade total de oportunidades convertidas em vendas.

---

## Negócios Perdidos

Quantidade de oportunidades encerradas sem conversão.

---

## Taxa de Conversão

Percentual de conversão calculado considerando:

- Total de Leads
- Total de Negócios Fechados

---

## Valor Total Fechado

Soma de todos os contratos fechados registrados no CRM.

---

## Receita Mensal

Soma das mensalidades recorrentes provenientes dos contratos fechados.

---

## Melhor Canal

Identifica automaticamente o canal que gerou maior número de vendas.

Exemplos:

- WhatsApp
- Instagram
- Facebook

---

## Serviço Campeão

Apresenta o serviço mais vendido.

---

## Especialista Destaque

Identifica o especialista responsável pelo maior número de fechamentos.

---

# Motivos de Perda

Quando existem oportunidades classificadas como "Não Fechado", o sistema apresenta uma tabela contendo os principais motivos registrados pela equipe comercial.

Esse recurso auxilia na identificação dos maiores obstáculos durante o processo de vendas.

---

# Visualizações

O módulo gera gráficos do tipo Donut para:

- Conversões por Canal
- Serviços Mais Vendidos

Essas visualizações facilitam a interpretação dos resultados comerciais.

---

# Ranking de Especialistas

É apresentado automaticamente um ranking contendo:

- Nome do Especialista
- Quantidade de Fechamentos

Esse indicador permite acompanhar o desempenho individual da equipe comercial.

---

# Interface

A página utiliza componentes personalizados para apresentar:

- Cards de métricas
- Indicadores financeiros
- Insights comerciais
- Gráficos
- Rankings
- Tabelas analíticas

O layout foi desenvolvido para oferecer uma leitura rápida dos resultados da operação.

---

# Principais Funções

## melhor_valor()

Identifica o valor mais frequente de uma determinada coluna.

É utilizada para determinar:

- melhor canal;
- serviço campeão;
- especialista destaque.

---

## formatar_moeda()

Formata valores monetários para o padrão brasileiro.

---

## card()

Renderiza os cartões de indicadores.

---

## render_resultados()

Função principal responsável pela construção da página.

Executa:

- normalização dos dados;
- cálculo dos indicadores;
- geração dos gráficos;
- criação dos rankings;
- exibição dos insights.

---

# Dependências

- Streamlit
- Pandas
- components.graficos

---

# Integração com outros módulos

Este módulo integra-se diretamente com:

- Dashboard Principal
- Página Leads
- Página Serviços e Canais
- Página Especialistas
- Banco PostgreSQL (através do Dashboard)

---

# Aplicação Comercial

Os indicadores apresentados permitem responder questões como:

- Quanto foi vendido?
- Qual serviço gera maior faturamento?
- Qual canal converte mais clientes?
- Qual especialista possui melhor desempenho?
- Qual é a taxa atual de conversão?
- Quais são os principais motivos de perda?

Essas informações auxiliam gestores na tomada de decisões estratégicas.

---

# Considerações Técnicas

O módulo possui responsabilidade exclusivamente analítica.

Nenhuma informação é alterada no banco de dados.

Todos os cálculos são realizados utilizando os dados carregados pelo Dashboard.

A arquitetura facilita futuras implementações como:

- comparação mensal;
- metas comerciais;
- evolução por período;
- ranking por receita;
- dashboards executivos.

---

# Resumo

A página Resultados Comerciais representa o painel executivo do Orion CRM AI.

Ela consolida informações financeiras, comerciais e operacionais em uma única interface, permitindo acompanhar o desempenho da operação e orientar decisões estratégicas baseadas em dados.