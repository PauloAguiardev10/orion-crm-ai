# Fluxo Conversacional da Sofia SDR

## Visão Geral

O fluxo conversacional da Sofia SDR é controlado por uma máquina de estados.

Cada conversa possui uma etapa atual (estado), armazenada no banco de dados, que determina qual será o próximo comportamento da agente.

Essa abordagem garante que cada atendimento siga um processo organizado e consistente.

---

# Fluxo Geral

O atendimento segue, em linhas gerais, a sequência abaixo:

Cliente

↓

Recebimento da mensagem

↓

Identificação da intenção

↓

Coleta das informações

↓

Análise comercial

↓

Qualificação

↓

Resumo comercial

↓

Encaminhamento ao especialista

---

# Estados da Conversa

## 1. inicio

É o estado inicial de toda nova conversa.

Nesta etapa, a Sofia:

- identifica a intenção inicial do cliente;
- reconhece saudações;
- identifica pedidos de orçamento;
- identifica interesse em serviços;
- detecta objeções;
- reconhece dúvidas comuns.

Dependendo da intenção detectada, a conversa pode seguir caminhos diferentes.

---

## 2. entender_objetivo_inicial

Utilizado quando o cliente demonstra um objetivo antes mesmo da coleta de dados.

Exemplos:

- veio por anúncio;
- relata uma experiência ruim;
- já informa sua necessidade logo na primeira mensagem.

A Sofia registra esse objetivo e continua normalmente o fluxo.

---

## 3. coletar_nome

Primeira etapa de coleta de dados.

Nesta fase a Sofia:

- valida se a resposta realmente parece um nome;
- remove expressões como "meu nome é";
- padroniza o nome;
- armazena a informação.

---

## 4. coletar_empresa

Após identificar o nome do cliente, a Sofia solicita o nome da empresa.

O texto recebido passa por um processo de normalização antes de ser salvo.

---

## 5. coletar_segmento

Nesta etapa a Sofia identifica o segmento de atuação da empresa.

Exemplos:

- Moda
- Clínica
- Restaurante
- Advocacia
- Engenharia

Após registrar o segmento, o fluxo pode seguir por caminhos diferentes dependendo das informações já coletadas.

---

## 6. entender_objetivo

Caso ainda não exista um objetivo comercial registrado, a Sofia pergunta ao cliente qual é sua principal necessidade.

Exemplos:

- vender mais;
- gerar contatos;
- fortalecer a marca.

Essa informação influencia diretamente a classificação comercial.

---

## 7. coletar_whatsapp

Utilizado principalmente quando o atendimento começou por Instagram ou Facebook.

A Sofia solicita um número de WhatsApp para que o especialista continue o atendimento.

---

## 8. aguardando_humano

Último estado do fluxo.

Nesse momento:

- a qualificação já foi concluída;
- o resumo comercial já foi preparado;
- o especialista humano assume a negociação.

Caso o cliente envie novas mensagens antes do especialista responder, a Sofia apenas informa que o atendimento já foi encaminhado, evitando reiniciar o processo de vendas.

---

# Histórico da Conversa

Durante todo o fluxo, cada mensagem enviada e recebida é registrada no histórico da conversa.

Esse histórico é utilizado para:

- acompanhamento do atendimento;
- geração do resumo comercial;
- consultas futuras;
- auditoria do processo.

---

# Características do Fluxo

O fluxo atual possui as seguintes propriedades:

- Conversa orientada por estados.
- Ordem controlada de coleta de informações.
- Persistência do estado no banco de dados.
- Continuidade entre mensagens.
- Encaminhamento controlado ao especialista.
- Evita reiniciar o atendimento após o encaminhamento.

---

# Benefícios da Arquitetura

A utilização de uma máquina de estados oferece diversas vantagens:

- previsibilidade do comportamento;
- facilidade de manutenção;
- redução de inconsistências;
- facilidade para adicionar novas etapas;
- melhor controle do atendimento.