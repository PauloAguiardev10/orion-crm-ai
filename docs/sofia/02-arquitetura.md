# Arquitetura da Sofia SDR

## Visão Geral

A Sofia SDR é implementada atualmente como um núcleo de inteligência conversacional centralizado no arquivo `backend/app/agents/sdr_agent.py`.

Esse núcleo reúne as regras de negócio responsáveis por interpretar mensagens, conduzir o fluxo da conversa, classificar comercialmente as leads e preparar o encaminhamento para o especialista humano.

Embora hoje esteja concentrada em um único arquivo, sua organização interna já é dividida em responsabilidades bem definidas.

---

# Arquitetura Atual

A estrutura lógica da Sofia pode ser representada da seguinte forma:

Cliente

↓

Recebimento da Mensagem

↓

Interpretação da Mensagem

↓

Identificação da Intenção

↓

Análise Comercial

↓

Fluxo Conversacional

↓

Geração do Resumo Comercial

↓

Encaminhamento

---

# Componentes Internos

Atualmente o núcleo da Sofia é composto pelos seguintes grupos de responsabilidades:

## Utilidades

Responsável por funções auxiliares utilizadas durante toda a conversa.

Exemplos:

- pesquisa de termos;
- respostas aleatórias;
- validações simples.

---

## Normalização de Dados

Responsável por tratar informações recebidas do cliente antes de armazená-las.

Inclui:

- limpeza de nomes;
- limpeza da empresa;
- limpeza do segmento.

---

## Interpretação da Linguagem

Responsável por compreender a intenção da mensagem enviada pelo cliente.

Entre as intenções reconhecidas atualmente estão:

- saudação;
- orçamento;
- conhecer serviços;
- reunião;
- tráfego pago;
- social media;
- design;
- web design;
- automação;
- objeções;
- dúvidas.

---

## Classificação Comercial

Responsável por identificar:

- serviço de interesse;
- score;
- temperatura;
- prioridade.

Essa classificação utiliza regras de negócio previamente definidas.

---

## Fluxo Conversacional

Controla todas as etapas do atendimento.

Entre elas:

- início;
- coleta de nome;
- coleta da empresa;
- coleta do segmento;
- entendimento do objetivo;
- coleta de WhatsApp;
- aguardando especialista.

---

## Respostas

Responsável pela geração das mensagens enviadas ao cliente.

As respostas seguem padrões definidos para manter consistência no atendimento.

---

## Resumo Comercial

Após a qualificação da lead, a Sofia gera um resumo comercial contendo as principais informações coletadas durante a conversa.

Esse resumo é utilizado pelo especialista humano para continuar o atendimento.

---

# Integração com o Backend

A Sofia não recebe mensagens diretamente dos canais de atendimento.

O fluxo ocorre da seguinte forma:

Canal

↓

FastAPI

↓

Sofia SDR

↓

Banco de Dados

↓

Resposta

↓

Canal

---

# Arquitetura Híbrida

A Sofia utiliza uma arquitetura híbrida.

Sempre que possível utiliza regras de negócio implementadas em código.

A Inteligência Artificial é utilizada apenas em tarefas onde ela agrega valor, como a geração do resumo comercial.

Essa estratégia reduz o consumo de tokens, aumenta a velocidade das respostas e torna o comportamento do agente mais previsível.

---

# Evolução Prevista

Embora atualmente o núcleo esteja concentrado em um único arquivo, a arquitetura foi planejada para permitir sua futura divisão em módulos independentes, preservando o comportamento já implementado.