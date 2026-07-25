# Arquitetura Geral do Orion CRM AI

## Introdução

O **Orion CRM AI** é uma plataforma de atendimento comercial inteligente desenvolvida para automatizar o primeiro contato com clientes, qualificar oportunidades de negócio e organizar todo o processo comercial até o encaminhamento ao especialista humano.

Sua arquitetura foi projetada para ser modular, escalável e de fácil manutenção, permitindo a evolução contínua da plataforma sem necessidade de reconstrução da base existente.

O principal núcleo de inteligência da plataforma é a **Sofia SDR**, responsável pelo atendimento inicial, qualificação das leads e geração de informações para o setor comercial.

---

# Objetivos da Plataforma

O Orion CRM AI foi desenvolvido com os seguintes objetivos:

- Automatizar o primeiro atendimento comercial;
- Qualificar leads de forma inteligente;
- Centralizar atendimentos em múltiplos canais;
- Organizar informações comerciais;
- Gerar indicadores para acompanhamento das operações;
- Reduzir o tempo gasto na qualificação manual;
- Apoiar o especialista humano com informações estruturadas.

---

# Visão Geral da Arquitetura

A plataforma é composta por módulos independentes que trabalham em conjunto durante todo o fluxo de atendimento.

```text
                         ORION CRM AI

                    Cliente
                        │
                        ▼
      WhatsApp / Instagram / Facebook
                        │
                        ▼
             WAHA / Meta APIs
                        │
                        ▼
               FastAPI (Backend)
                        │
                        ▼
                  Sofia SDR
                        │
            ┌───────────┴───────────┐
            ▼                       ▼
      PostgreSQL              Dashboard
            │
            ▼
 Especialista Comercial
```

Cada componente possui responsabilidades específicas e comunica-se através de interfaces bem definidas.

---

# Arquitetura Lógica

A arquitetura lógica da plataforma está organizada em seis grandes componentes.

## 1. Canais de Atendimento

Responsáveis pela comunicação entre clientes e a plataforma.

### Atualmente

- WhatsApp

### Planejado

- Instagram Direct
- Facebook Messenger
- Telegram
- Web Chat

---

## 2. Camada de Integração

Responsável por conectar os canais de atendimento ao Backend.

### Atualmente

- WAHA

### Futuramente

- Meta API
- Telegram API
- Outros conectores

---

## 3. Backend

O Backend representa o núcleo operacional da plataforma.

Responsabilidades:

- Receber mensagens;
- Gerenciar conversas;
- Persistir informações;
- Integrar a Sofia SDR;
- Disponibilizar APIs;
- Integrar serviços externos.

Tecnologia utilizada:

- FastAPI

---

## 4. Sofia SDR

A Sofia representa o núcleo de inteligência comercial da plataforma.

Responsabilidades:

- Interpretar mensagens;
- Identificar intenções;
- Conduzir o fluxo conversacional;
- Qualificar leads;
- Identificar serviços;
- Calcular score;
- Definir temperatura;
- Definir prioridade;
- Gerar resumo comercial;
- Encaminhar a lead ao especialista.

Toda sua documentação encontra-se em:

```
docs/
└── sofia/
```

---

## 5. Banco de Dados

Responsável pela persistência de todas as informações da plataforma.

Tecnologia utilizada:

- PostgreSQL

Principais entidades armazenadas:

- Clientes
- Conversas
- Leads
- Histórico
- Resumos Comerciais

---

## 6. Dashboard

Responsável pela visualização operacional das informações.

Atualmente apresenta:

- Leads
- Conversas
- Funil
- Serviços
- Temperatura
- Prioridade
- Canais

Tecnologia utilizada:

- Streamlit

---

## 7. Especialista Comercial

Após a qualificação realizada pela Sofia SDR, o atendimento é transferido ao especialista humano.

A negociação, elaboração de propostas e fechamento da venda permanecem sob responsabilidade da equipe comercial.

---

# Fluxo de Atendimento

O fluxo operacional da plataforma ocorre da seguinte forma:

1. O cliente envia uma mensagem.
2. O canal de atendimento recebe essa mensagem.
3. A integração encaminha a mensagem ao Backend.
4. O Backend registra a conversa.
5. A Sofia interpreta a intenção do cliente.
6. A Sofia conduz a qualificação.
7. As informações são classificadas.
8. O resumo comercial é gerado.
9. Os dados são gravados no PostgreSQL.
10. O Dashboard é atualizado.
11. O especialista humano assume o atendimento.

---

# Arquitetura Física

Atualmente a plataforma utiliza os seguintes componentes tecnológicos:

| Camada | Tecnologia |
|---------|------------|
| Backend | FastAPI |
| Banco de Dados | PostgreSQL |
| Dashboard | Streamlit |
| Inteligência | Sofia SDR |
| Integração WhatsApp | WAHA |
| IA | OpenAI GPT |

---

# Estrutura Geral do Projeto

A organização atual da plataforma segue uma arquitetura modular.

```text
backend/
dashboard/
docs/
whatsapp/
database/
```

Cada módulo possui responsabilidades independentes, reduzindo o acoplamento e facilitando futuras evoluções.

---

# Princípios Arquiteturais

O Orion CRM AI foi desenvolvido seguindo os seguintes princípios.

## Modularidade

Cada componente possui responsabilidades específicas.

---

## Escalabilidade

Novas funcionalidades poderão ser adicionadas sem necessidade de alterar a arquitetura principal.

---

## Baixo Acoplamento

Os componentes comunicam-se por interfaces bem definidas, reduzindo dependências entre módulos.

---

## Arquitetura Híbrida

Sempre que possível, regras de negócio são executadas diretamente em código.

A Inteligência Artificial é utilizada apenas quando agrega valor ao processo, como geração de resumos comerciais e interpretação contextual.

Essa estratégia proporciona:

- menor consumo de tokens;
- maior previsibilidade;
- respostas mais rápidas;
- facilidade de manutenção.

---

# Estado Atual da Plataforma

Atualmente o Orion CRM AI possui:

- Backend funcional;
- Sofia SDR operacional;
- PostgreSQL integrado;
- Dashboard operacional;
- Integração com WAHA;
- Fluxo completo de qualificação de leads;
- Geração automática de resumo comercial.

---

# Evolução Planejada

As próximas evoluções previstas incluem:

- Multiempresa;
- Atendimento Omnichannel;
- Configuração personalizada por cliente;
- CRM completo;
- Dashboard administrativo;
- Base de conhecimento;
- Memória inteligente;
- Recomendações comerciais;
- Integrações adicionais.

Essas evoluções deverão manter compatibilidade com a arquitetura existente.

---

# Conclusão

O Orion CRM AI foi concebido como uma plataforma de atendimento comercial inteligente, organizada em módulos independentes e preparada para crescimento contínuo.

A separação entre Backend, Sofia SDR, Banco de Dados, Dashboard e Integrações permite que novas funcionalidades sejam incorporadas de forma gradual, preservando a estabilidade do sistema e facilitando sua manutenção ao longo do tempo.

Este documento serve como referência arquitetural de alto nível para todo o projeto e deve ser atualizado sempre que houver mudanças significativas na estrutura da plataforma.