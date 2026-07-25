# Dashboard – Página Conversas

## Arquivo

`dashboard/app_pages/conversas.py`

---

# Objetivo

A página **Conversas** permite visualizar o histórico completo das interações realizadas entre a Sofia SDR e os clientes.

Seu principal objetivo é fornecer ao especialista humano todo o contexto da negociação antes da continuidade do atendimento, evitando que informações importantes sejam perdidas durante a transição entre a IA e a equipe comercial.

---

# Responsabilidades

Este módulo é responsável por:

- Listar todas as conversas disponíveis.
- Permitir a seleção de uma conversa específica.
- Exibir informações resumidas da oportunidade.
- Apresentar o resumo comercial gerado pela Sofia SDR.
- Exibir o histórico completo da conversa.

A página possui função exclusivamente consultiva, não realizando alterações nas informações armazenadas.

---

# Fluxo de Execução

```text
Dashboard
      │
      ▼
Recebe lista de Leads
      │
      ▼
Normalização dos dados
      │
      ▼
Lista de Conversas
      │
      ▼
Seleção da Conversa
      │
      ▼
Exibição dos Indicadores
      │
      ▼
Resumo Comercial
      │
      ▼
Histórico Completo
```

---

# Carregamento das Conversas

O módulo recebe um DataFrame contendo todas as leads cadastradas.

Antes da renderização, realiza uma normalização dos dados para garantir que os principais campos estejam sempre disponíveis.

Os campos tratados incluem:

- ID
- Produto
- Origem
- Canal
- Responsável
- Score
- Temperatura
- Status
- Histórico
- Resumo Comercial

Caso algum campo não exista, um valor padrão é utilizado para evitar erros durante a exibição.

---

# Seleção da Conversa

Cada conversa é apresentada no formato:

```
#ID | Produto | Canal
```

Exemplo:

```
#18 | Gestão de Tráfego Pago | WhatsApp
```

Após a seleção, todas as informações relacionadas àquela oportunidade são carregadas automaticamente.

---

# Informações da Lead

Após selecionar uma conversa, a interface apresenta os principais indicadores da oportunidade.

São exibidos:

- Produto de interesse
- Canal de origem
- Score da Lead
- Temperatura
- Responsável
- Status Comercial

Esses dados permitem ao especialista compreender rapidamente o estágio da negociação.

---

# Resumo Comercial

O módulo apresenta o resumo gerado automaticamente pela Sofia SDR durante o processo de qualificação.

Esse resumo reúne as principais informações coletadas ao longo da conversa, reduzindo o tempo necessário para análise da oportunidade.

Caso ainda não exista um resumo disponível, uma mensagem informativa é exibida ao usuário.

---

# Histórico da Conversa

O histórico completo da conversa é apresentado em formato textual.

Esse histórico representa toda a comunicação realizada entre o cliente e a Sofia SDR, preservando o contexto da negociação.

Caso ainda não exista histórico disponível, o sistema informa essa condição ao usuário.

---

# Principais Funções

## render_conversas()

Função principal responsável pela renderização da página.

Suas responsabilidades incluem:

- normalizar os dados recebidos;
- montar a lista de conversas;
- permitir a seleção de uma oportunidade;
- exibir indicadores da lead;
- apresentar o resumo comercial;
- apresentar o histórico completo.

---

# Interface

A página utiliza componentes nativos do Streamlit para construção da interface.

Os principais componentes utilizados são:

- Title
- Selectbox
- Columns
- Metric
- Markdown
- Info
- Warning
- Text

A interface foi projetada para oferecer uma visualização simples, rápida e objetiva.

---

# Dependências

- Streamlit

O módulo recebe os dados já processados pelo Dashboard Principal, não realizando consultas diretas ao banco de dados.

---

# Integração com outros módulos

A página Conversas integra-se diretamente com:

- Dashboard Principal
- Página Leads
- Sofia SDR
- Banco PostgreSQL (indiretamente através do Dashboard)

---

# Considerações Técnicas

Este módulo possui responsabilidade exclusivamente de visualização.

Toda a lógica de carregamento e preparação dos dados ocorre em módulos superiores do Dashboard, mantendo a página focada apenas na apresentação das informações.

Essa separação facilita futuras evoluções, como:

- pesquisa por palavras-chave;
- filtros por período;
- exportação do histórico;
- visualização em formato de chat;
- anexos de mídia.

---

# Resumo

A página Conversas funciona como o histórico operacional da Sofia SDR dentro do Orion CRM AI.

Ela permite que especialistas humanos compreendam rapidamente o contexto completo de cada atendimento, garantindo continuidade ao processo comercial sem perda de informações e mantendo a transição entre IA e equipe de vendas de forma organizada e eficiente.