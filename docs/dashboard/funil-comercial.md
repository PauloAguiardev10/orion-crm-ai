# Dashboard – Página Funil Comercial

## Arquivo

`dashboard/app_pages/funil_comercial.py`

---

# Objetivo

A página **Funil Comercial** apresenta todas as oportunidades comerciais organizadas por estágio da negociação.

Sua principal finalidade é fornecer uma visão visual do pipeline de vendas, permitindo acompanhar em qual etapa cada lead se encontra e identificar rapidamente gargalos no processo comercial.

A interface segue o conceito de um quadro Kanban, onde cada coluna representa um status da negociação.

---

# Responsabilidades

Este módulo é responsável por:

- Organizar as leads por status comercial.
- Exibir um quadro visual semelhante ao Kanban.
- Mostrar a quantidade de leads em cada etapa.
- Apresentar informações resumidas de cada oportunidade.
- Facilitar o acompanhamento do funil de vendas.

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
Separação por Status
      │
      ▼
Criação das Colunas do Funil
      │
      ▼
Renderização dos Cards
      │
      ▼
Visualização do Pipeline Comercial
```

---

# Estrutura do Funil

O número de colunas exibidas é definido automaticamente pela constante `STATUS_LISTA`.

Cada status representa uma etapa do processo comercial.

Exemplos de etapas:

- Aguardando Atendimento
- Em Atendimento
- Proposta Enviada
- Negócio Fechado
- Não Fechado

Caso novos status sejam adicionados ao sistema, o funil será atualizado automaticamente.

---

# Organização das Leads

Cada lead é posicionada na coluna correspondente ao seu status atual.

Para cada oportunidade são exibidas as seguintes informações:

- Nome
- Produto de Interesse
- Temperatura
- Score
- Responsável
- Canal de Origem

Essa organização permite que a equipe visualize rapidamente o andamento das negociações.

---

# Temperatura da Lead

A temperatura é representada por ícones para facilitar a identificação visual.

### Lead Quente

🔥 Lead com alta probabilidade de conversão.

---

### Lead Morna

⚡ Lead com potencial de conversão moderado.

---

### Lead Fria

❄️ Lead com baixa prioridade comercial.

---

# Contador de Leads

Cada coluna do funil apresenta automaticamente a quantidade de oportunidades existentes naquele estágio.

Esse indicador auxilia gestores na identificação de gargalos durante o processo de vendas.

---

# Interface

O módulo utiliza componentes personalizados desenvolvidos em HTML e CSS dentro do Streamlit.

Os principais elementos visuais incluem:

- Colunas Kanban
- Cards das Leads
- Contador de oportunidades
- Indicadores de temperatura

A interface foi desenvolvida para oferecer uma leitura rápida do pipeline comercial.

---

# Principais Funções

## valor_seguro()

Retorna um valor padrão quando determinada informação está ausente.

Essa função evita erros de renderização e garante consistência na apresentação dos dados.

---

## render_funil()

Função principal responsável pela construção do quadro Kanban.

Suas responsabilidades incluem:

- normalizar os dados recebidos;
- criar as colunas do funil;
- agrupar as leads conforme o status;
- renderizar os cards das oportunidades;
- exibir indicadores resumidos.

---

# Dependências

- Streamlit
- leads_service

O módulo utiliza a constante `STATUS_LISTA`, garantindo que o funil permaneça sincronizado com os status definidos para o CRM.

---

# Integração com outros módulos

A página Funil Comercial integra-se diretamente com:

- Dashboard Principal
- Página Leads
- Leads Service
- Banco PostgreSQL (através do Dashboard)

---

# Considerações Técnicas

O módulo possui responsabilidade exclusivamente de visualização.

Não realiza alterações nas informações das leads, funcionando como um painel de acompanhamento do pipeline comercial.

A utilização da constante `STATUS_LISTA` elimina duplicação de configurações e facilita futuras expansões do processo comercial.

---

# Evoluções Futuras

A estrutura atual permite implementar facilmente novos recursos, como:

- Arrastar e soltar (Drag and Drop) para alterar o status das leads.
- Atualização automática do status ao mover um card.
- Filtros por responsável.
- Filtros por canal.
- Filtros por temperatura.
- Pesquisa por nome da empresa.
- Indicadores de tempo em cada etapa.
- Alertas para leads paradas por longos períodos.
- Métricas de conversão entre etapas do funil.

---

# Resumo

A página Funil Comercial oferece uma visão estratégica do pipeline de vendas do Orion CRM AI.

Sua organização em formato Kanban permite acompanhar a evolução das oportunidades de maneira simples e intuitiva, auxiliando gestores e especialistas na identificação de gargalos, priorização de atendimentos e monitoramento do desempenho comercial da operação.