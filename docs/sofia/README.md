# Sofia SDR

## Visão Geral

A Sofia SDR é o agente inteligente de atendimento e qualificação de leads da plataforma **Orion CRM AI**.

Sua principal responsabilidade é realizar o primeiro atendimento aos clientes, compreender suas necessidades, identificar oportunidades comerciais e encaminhar leads qualificadas para o especialista responsável pelo fechamento da venda.

Atualmente a Sofia atende principalmente pelo WhatsApp, mas sua arquitetura foi projetada para suportar futuramente outros canais, como Instagram Direct, Facebook Messenger, Telegram e Web Chat, utilizando o mesmo núcleo de inteligência.

---

# Objetivos da Sofia

A Sofia foi desenvolvida para:

- Realizar o primeiro atendimento ao cliente.
- Identificar a intenção da conversa.
- Descobrir o objetivo comercial da empresa.
- Coletar informações importantes da lead.
- Classificar automaticamente o interesse da lead.
- Identificar o serviço mais adequado da Forway.
- Calcular score, temperatura e prioridade.
- Gerar um resumo comercial para o vendedor.
- Encaminhar a conversa para um especialista humano.

---

# Papel dentro do Orion CRM AI

Dentro da arquitetura da plataforma, a Sofia é responsável exclusivamente pelo atendimento comercial.

Ela não executa funções administrativas do CRM, nem substitui o vendedor humano.

Seu objetivo é reduzir o tempo gasto na qualificação inicial, organizar as informações da lead e permitir que o especialista comercial receba cada atendimento já contextualizado.

---

# Fluxo Geral

O funcionamento da Sofia pode ser resumido da seguinte forma:

Cliente

↓

Recebimento da mensagem

↓

Identificação da intenção

↓

Coleta de informações

↓

Análise comercial

↓

Classificação da lead

↓

Geração do resumo comercial

↓

Encaminhamento ao especialista

---

# Documentação

Esta pasta contém toda a documentação técnica da Sofia SDR.

Arquivos disponíveis:

- 01-visao-geral.md
- 02-arquitetura.md
- 03-fluxo-conversacional.md
- 04-classificacao-comercial.md
- 05-linguagem-e-respostas.md
- 06-resumo-vendedor.md
- 07-regras-de-negocio.md
- 08-roadmap.md

Cada documento aborda uma parte específica do funcionamento interno da Sofia.

---

# Tecnologias utilizadas

Atualmente a Sofia utiliza:

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- OpenAI GPT
- WAHA
- WhatsApp

---

# Estado Atual

Versão atual:

- Atendimento funcional.
- Qualificação automática.
- Identificação de intenção.
- Classificação comercial.
- Geração de resumo para o vendedor.
- Integração com PostgreSQL.
- Integração com WAHA.
- Encaminhamento para especialista humano.

A documentação desta pasta será atualizada sempre que novas funcionalidades forem incorporadas ao núcleo da Sofia SDR.