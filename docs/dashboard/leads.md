# Dashboard – Página Leads

## Arquivo

`dashboard/app_pages/leads.py`

---

# Objetivo

A página **Leads** é o núcleo operacional do Orion CRM AI. Toda oportunidade gerada pela Sofia SDR é centralizada nesta tela, permitindo que a equipe comercial acompanhe, organize e atualize cada negociação durante todo o ciclo de vendas.

Além da visualização das informações, este módulo permite alterar o status da negociação, atribuir responsáveis, registrar informações financeiras, documentar perdas comerciais e consultar o histórico completo das conversas realizadas pela IA.

---

# Responsabilidades

Este módulo é responsável por:

- Exibir todas as leads cadastradas.
- Disponibilizar filtros de pesquisa.
- Organizar as oportunidades em cards.
- Permitir alterações comerciais.
- Registrar negócios fechados.
- Registrar motivos de perda.
- Exibir o resumo comercial produzido pela Sofia SDR.
- Exibir o histórico completo das conversas.
- Persistir todas as alterações no banco de dados.

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
Aplicação dos filtros
      │
      ▼
Renderização dos Cards
      │
      ▼
Atualização Comercial
      │
      ▼
Persistência no Banco
      │
      ▼
Atualização da Interface
```

---

# Carregamento dos Dados

A página recebe um DataFrame contendo todas as leads carregadas pelo Dashboard.

Antes da renderização, é realizada uma etapa de normalização para garantir que todas as colunas necessárias existam, evitando erros caso algum campo ainda não tenha sido preenchido.

Entre os campos tratados estão:

- Nome
- Empresa
- Telefone
- Canal
- Origem
- Produto
- Temperatura
- Score
- Status
- Responsável
- Resumo Comercial
- Histórico
- Valor do Negócio
- Mensalidade
- Motivo da Perda
- Observação Comercial

---

# Filtros

A interface oferece filtros para facilitar a localização das oportunidades.

## Status

Permite visualizar:

- Todos
- Aguardando Atendimento
- Em Atendimento
- Proposta Enviada
- Negócio Fechado
- Não Fechado

---

## Canal

Filtra as leads conforme sua origem.

Exemplos:

- WhatsApp
- Instagram
- Facebook

---

## Responsável

Permite visualizar apenas as leads atribuídas a um especialista específico.

Os responsáveis são carregados automaticamente pelo módulo de configurações.

---

## Pesquisa

A pesquisa textual localiza oportunidades utilizando:

- Nome
- Empresa
- Produto

---

# Card da Lead

Cada oportunidade é apresentada em um card contendo:

- ID
- Nome
- Empresa
- Telefone
- Canal
- Produto
- Temperatura
- Score
- Status Atual
- Responsável

Essa visualização facilita a identificação rápida da situação comercial de cada lead.

---

# Atualização Comercial

Cada card permite alterar informações diretamente pelo Dashboard.

É possível modificar:

- Status
- Responsável

Dependendo do novo status, novos campos são apresentados automaticamente.

---

# Negócio Fechado

Ao selecionar o status **Negócio Fechado**, o sistema solicita:

- Valor do Contrato
- Mensalidade

Essas informações são utilizadas posteriormente para indicadores financeiros e análises comerciais.

---

# Negócio Não Fechado

Quando o status é alterado para **Não Fechado**, torna-se obrigatório registrar o motivo da perda.

Os motivos disponíveis são:

- Sem orçamento
- Sem interesse
- Fechou com concorrente
- Não respondeu
- Momento errado
- Outro motivo

Também é possível registrar uma observação comercial detalhando o motivo da perda.

---

# Persistência dos Dados

Após qualquer alteração, a função responsável pela atualização grava as informações no banco de dados.

São persistidos:

- Status
- Responsável
- Valor do Contrato
- Mensalidade
- Motivo da Perda
- Observação Comercial

Após salvar, a interface é atualizada automaticamente.

---

# Resumo Comercial

Cada lead possui um painel expansível denominado **Resumo Comercial**.

Esse conteúdo é produzido automaticamente pela Sofia SDR durante a qualificação da oportunidade.

O resumo reúne as principais informações necessárias para que o especialista humano continue o atendimento sem precisar reler toda a conversa.

---

# Histórico da Conversa

Outro painel expansível apresenta todo o histórico da conversa realizada pela Sofia.

Esse histórico permite que o especialista compreenda o contexto completo da negociação antes de entrar em contato com o cliente.

---

# Principais Funções

## valor_seguro()

Retorna um valor padrão quando determinado campo está vazio ou inexistente.

---

## normalizar_status()

Padroniza todos os status utilizados pelo CRM.

---

## render_leads()

Responsável pela renderização completa da página.

Executa:

- carregamento;
- filtros;
- renderização dos cards;
- atualização comercial;
- persistência dos dados;
- exibição do resumo;
- exibição do histórico.

---

# Dependências

- Streamlit
- leads_service
- configuracoes_service

---

# Integração com outros módulos

Este módulo integra-se diretamente com:

- Dashboard Principal
- Leads Service
- Configurações
- Cadastro de Especialistas
- Banco PostgreSQL
- Sofia SDR

---

# Considerações Técnicas

A página concentra toda a operação comercial do CRM.

Sua implementação foi desenvolvida para reduzir a quantidade de telas utilizadas pelo vendedor, permitindo que toda a negociação seja conduzida em uma única interface.

A arquitetura também facilita futuras integrações com automações, notificações e distribuição automática de oportunidades.

---

# Resumo

A página Leads representa o principal ambiente operacional do Orion CRM AI. Ela centraliza todas as oportunidades geradas pela Sofia SDR e fornece aos especialistas uma interface completa para acompanhamento, atualização e conclusão do processo comercial.