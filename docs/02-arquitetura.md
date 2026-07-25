# 2. Arquitetura do Orion CRM AI

## 2.1 Visão arquitetural

O Orion CRM AI é uma plataforma de automação comercial, atendimento inteligente e gestão de leads.

A arquitetura foi definida para permitir que um único núcleo tecnológico atenda diferentes empresas, canais de comunicação e equipes comerciais.

A primeira implementação operacional da plataforma é a Sofia SDR para a Forway.

Embora o sistema atual ainda possua partes específicas da Forway, a arquitetura oficial do produto será orientada para uma plataforma multiempresa.

---

## 2.2 Objetivo da arquitetura

A arquitetura do Orion CRM AI deve permitir:

- atendimento por múltiplos canais;
- centralização das regras comerciais;
- reaproveitamento do mesmo núcleo de inteligência;
- armazenamento organizado de clientes, conversas e leads;
- visualização dos dados em um CRM;
- isolamento dos dados de cada empresa;
- configuração individual por cliente;
- evolução para um produto SaaS;
- inclusão de novos canais sem reconstruir o sistema;
- manutenção e crescimento com menor retrabalho.

---

## 2.3 Arquitetura geral

O fluxo principal da plataforma é:

```text
Cliente
   ↓
Canal de atendimento
   ↓
Adaptador de integração
   ↓
Backend FastAPI
   ↓
Agente SDR e regras comerciais
   ↓
PostgreSQL
   ↓
Dashboard CRM
   ↓
Equipe comercial
