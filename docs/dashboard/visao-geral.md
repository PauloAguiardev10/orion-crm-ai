# Dashboard – Página Visão Geral

## Arquivo

`dashboard/app_pages/visao_geral.py`

---

# Objetivo

A página **Visão Geral** é a tela inicial do Dashboard do Orion CRM AI. Seu objetivo é apresentar um panorama da operação comercial por meio de indicadores, gráficos e diagnósticos automáticos, permitindo que gestores e clientes acompanhem rapidamente a situação das leads e dos resultados da empresa.

A interface é adaptada automaticamente conforme o perfil do usuário autenticado.

---

# Responsabilidades

Este módulo é responsável por:

- Identificar o perfil do usuário logado.
- Carregar informações da empresa.
- Consultar dados de leads, pedidos e produtos.
- Calcular indicadores comerciais.
- Renderizar gráficos.
- Exibir diagnósticos da operação.
- Mostrar as últimas leads cadastradas.

---

# Perfis de Acesso

A página possui dois modos de funcionamento.

## Cliente

O usuário visualiza apenas os dados da própria empresa.

São apresentados:

- Total de leads
- Leads quentes
- Leads em atendimento
- Leads aguardando atendimento
- Negócios fechados
- Negócios perdidos
- Gráficos
- Últimas leads

---

## Administrador

Disponível para:

- orion_admin
- parceiro_admin

Além das informações do cliente, este perfil pode:

- visualizar empresas cadastradas;
- selecionar qualquer empresa;
- acompanhar indicadores individuais;
- gerar diagnósticos comerciais.

---

# Fluxo de Execução

```text
Usuário realiza login
        │
        ▼
Leitura do nível de acesso
        │
        ▼
Cliente ou Administrador
        │
        ▼
Consulta ao PostgreSQL
        │
        ▼
Processamento das métricas
        │
        ▼
Renderização dos indicadores
        │
        ▼
Gráficos
        │
        ▼
Diagnóstico Comercial
```

---

# Consultas ao Banco

O módulo realiza consultas às seguintes tabelas:

- empresas
- leads
- pedidos
- produtos

As consultas utilizam o `empresa_id` armazenado na sessão para limitar o acesso aos dados permitidos.

---

# Indicadores Calculados

Durante o carregamento da página são calculados automaticamente:

- Total de Leads
- Leads Quentes
- Leads em Atendimento
- Leads Aguardando Atendimento
- Negócios Fechados
- Negócios Não Fechados
- Quantidade de Pedidos
- Quantidade de Produtos
- Valor Total dos Pedidos

---

# Diagnóstico Comercial

A página gera automaticamente um diagnóstico baseado nas métricas da operação.

Quando existem leads aguardando atendimento humano, o sistema informa que pode haver perda de oportunidades e recomenda atenção à operação.

Esse recurso auxilia gestores na identificação de gargalos comerciais.

---

# Visualizações

A página apresenta gráficos do tipo Donut para:

- Status das Leads
- Temperatura das Leads

Esses gráficos permitem uma leitura rápida da distribuição das oportunidades comerciais.

---

# Interface

A interface utiliza componentes personalizados desenvolvidos em Streamlit com CSS próprio, incluindo:

- cartões de métricas;
- painel superior;
- cartões de insights;
- cartões de diagnóstico;
- gráficos.

---

# Principais Funções

## buscar_empresas_permitidas()

Retorna as empresas que o usuário pode visualizar conforme seu nível de acesso.

---

## buscar_dados_empresa()

Consulta leads, pedidos e produtos da empresa selecionada.

---

## calcular_metricas()

Processa os dados retornados pelo banco e calcula todos os indicadores utilizados pelo Dashboard.

---

## render_cliente()

Renderiza a visão destinada aos clientes.

---

## render_admin_ou_parceiro()

Renderiza a visão administrativa utilizada pela Orion Systems e parceiros.

---

## render_visao_geral()

Define automaticamente qual interface será exibida de acordo com o perfil do usuário.

---

# Dependências

- Streamlit
- Pandas
- PostgreSQL
- database.db
- components.graficos

---

# Considerações Técnicas

A página centraliza boa parte da lógica de apresentação do Dashboard.

Embora cumpra corretamente sua função, futuras evoluções podem separar responsabilidades entre camada de serviços, consultas e renderização, facilitando manutenção e testes.

---

# Resumo

A página Visão Geral funciona como painel executivo do Orion CRM AI, reunindo indicadores estratégicos da operação comercial e fornecendo uma visão consolidada do desempenho da empresa para clientes, parceiros e administradores.