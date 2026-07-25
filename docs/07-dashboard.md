# Dashboard - Página Visão Geral

## Arquivo

dashboard/app_pages/visao_geral.py

---

# Objetivo

A página **Visão Geral** é a tela inicial do Dashboard Orion CRM AI.

Seu objetivo é fornecer uma visão rápida da operação comercial utilizando indicadores estratégicos, gráficos, diagnósticos automáticos e métricas de desempenho.

A interface é adaptada automaticamente conforme o perfil do usuário logado.

---

# Arquitetura

A página possui dois modos distintos de funcionamento.

## Painel do Cliente

Exibido para usuários pertencentes à empresa.

Disponibiliza:

- Indicadores das leads
- Status da operação
- Gráficos comerciais
- Últimas leads
- Insights automáticos

---

## Painel Administrativo

Disponível para:

- orion_admin
- parceiro_admin

Além das informações do cliente, permite:

- visualizar empresas cadastradas
- selecionar qualquer cliente
- acompanhar indicadores individuais
- gerar diagnóstico comercial
- identificar oportunidades de upgrade

---

# Fluxo da Página

Login

↓

Identificação do nível do usuário

↓

Cliente ou Administrador

↓

Consulta ao PostgreSQL

↓

Processamento das métricas

↓

Renderização dos indicadores

↓

Renderização dos gráficos

↓

Diagnóstico Comercial

---

# Consultas ao Banco

A página consulta diretamente o banco PostgreSQL.

São carregadas informações de:

- Empresas
- Leads
- Pedidos
- Produtos

Todas as consultas são filtradas utilizando o empresa_id armazenado na sessão.

---

# Indicadores

A página calcula automaticamente:

- Total de Leads
- Leads Quentes
- Leads em Atendimento
- Leads Aguardando Atendimento
- Negócios Fechados
- Negócios Perdidos
- Total de Pedidos
- Total de Produtos
- Valor Comercial dos Pedidos

---

# Diagnóstico Comercial

O sistema realiza uma análise automática da operação.

Caso existam leads aguardando atendimento humano, é exibido um diagnóstico indicando possível perda de oportunidades e sugerindo upgrade para versões mais avançadas da IA.

Esse recurso transforma o Dashboard em uma ferramenta consultiva.

---

# Analytics

São apresentados gráficos do tipo Donut para:

- Status das Leads
- Temperatura das Leads

Esses gráficos permitem identificar rapidamente gargalos da operação.

---

# Últimas Leads

A página apresenta uma tabela contendo as últimas oportunidades cadastradas.

Esse recurso facilita o acompanhamento diário das atividades comerciais.

---

# Controle de Permissões

A renderização da página depende do nível do usuário.

Usuário comum

↓

Visualiza apenas sua empresa

Parceiro

↓

Visualiza empresas permitidas

Administrador Orion

↓

Visualiza todas as empresas

---

# Componentes Utilizados

- Streamlit
- Pandas
- PostgreSQL
- CSS personalizado
- Componentes gráficos
- Session State

---

# Melhorias Futuras

- Cache das consultas
- Diagnósticos utilizando IA
- Comparativos mensais
- Indicadores financeiros
- Ranking de desempenho
- SLA de atendimento
- Alertas em tempo real

---

# Conclusão

A página Visão Geral concentra os principais indicadores do Orion CRM AI.

Ela fornece ao usuário uma visão rápida da saúde comercial da operação e serve como ponto central para acompanhamento dos resultados gerados pela Sofia SDR.