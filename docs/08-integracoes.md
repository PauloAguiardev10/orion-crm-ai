# Dashboard – Página Integrações

## Arquivo

`dashboard/app_pages/integracoes.py`

---

# Objetivo

A página **Integrações** apresenta os canais de comunicação previstos para integração com o Orion CRM AI.

No estado atual do projeto, esta página possui caráter informativo, exibindo quais plataformas serão conectadas futuramente ao sistema e o status de implantação de cada uma.

---

# Responsabilidades

Este módulo é responsável por:

- Exibir os canais previstos para integração.
- Informar o status atual de cada canal.
- Apresentar uma visão geral da expansão do CRM.
- Servir como área de acompanhamento das futuras integrações.

---

# Fluxo de Execução

```text
Usuário acessa a página
        │
        ▼
Renderização do título
        │
        ▼
Exibição dos três canais planejados
        │
        ▼
Mensagem informando que as integrações
serão realizadas futuramente
```

---

# Interface

Ao acessar a página, o sistema apresenta o título:

```text
Integrações
```

Em seguida é exibida a seção:

```text
Canais planejados
```

A interface utiliza três colunas do Streamlit para organizar visualmente as futuras integrações.

---

# Canais Apresentados

## WhatsApp

O painel informa:

- Canal principal de atendimento.
- Status atual:

```text
Aguardando integração
```

Essa integração será responsável pelo atendimento automatizado via WhatsApp.

---

## Instagram Direct

O painel apresenta:

- Leads provenientes do Instagram.
- Status:

```text
Aguardando integração
```

Esta integração permitirá o atendimento de mensagens recebidas pelo Direct.

---

## Facebook Messenger

O painel apresenta:

- Leads provenientes da página do Facebook.
- Status:

```text
Aguardando integração
```

Esse canal será utilizado para atendimento das mensagens recebidas pelo Messenger.

---

# Layout

Cada canal é apresentado em um card construído com HTML utilizando:

```python
st.markdown(..., unsafe_allow_html=True)
```

Todos os cards utilizam a classe CSS:

```text
metric-card
```

A estilização dessa classe é definida em outro ponto da aplicação.

---

# Mensagem Final

Ao final da página é exibido um aviso informativo:

> Quando o gestor liberar os acessos, conectaremos os canais reais ao CRM SDR.

Essa mensagem indica que as integrações ainda dependem da disponibilização dos acessos pelos responsáveis.

---

# Funções do Módulo

## render_integracoes()

```python
def render_integracoes():
```

Função responsável por renderizar toda a página.

Suas etapas são:

- exibir o título;
- criar três colunas;
- renderizar os cards das integrações planejadas;
- apresentar a mensagem informativa final.

---

# Dependências

O módulo utiliza apenas:

- Streamlit

Não há chamadas para banco de dados, APIs externas ou serviços internos.

---

# Integração com outros módulos

Atualmente este módulo não realiza integração funcional com nenhuma outra parte do sistema.

Sua função é exclusivamente informativa.

No futuro deverá integrar-se com:

- Evolution API / WAHA (WhatsApp);
- Instagram Graph API;
- Facebook Messenger API;
- Backend FastAPI;
- Banco de dados de conversas;
- Dashboard de Leads;
- Dashboard de Conversas.

---

# Estado Atual

O código não realiza:

- autenticação;
- conexão com APIs;
- envio de mensagens;
- recebimento de mensagens;
- sincronização de contatos;
- leitura de webhooks.

Ele apenas apresenta os canais previstos para integração.

---

# Evoluções Futuras

A estrutura atual permite evoluir a página para incluir:

- conexão do WhatsApp em tempo real;
- conexão do Instagram Direct;
- conexão do Facebook Messenger;
- status online/offline das integrações;
- geração de QR Code para WhatsApp;
- teste de conexão;
- configuração de tokens;
- configuração de webhooks;
- monitoramento das APIs;
- histórico de sincronização;
- indicadores de disponibilidade;
- logs de integração.

---

# Resumo

A página **Integrações** funciona como um painel de planejamento da arquitetura de comunicação do Orion CRM AI.

Na versão atual ela apresenta os canais que serão integrados ao sistema futuramente e informa que essas conexões dependem da liberação dos acessos pelo gestor.

Ainda não existem integrações funcionais implementadas neste módulo, que atua apenas como uma interface informativa para a expansão futura do CRM.