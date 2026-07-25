# Regras de Negócio da Sofia SDR

## Visão Geral

As regras de negócio definem o comportamento da Sofia SDR durante todo o atendimento.

Seu objetivo é garantir que todas as conversas sigam um padrão consistente, independentemente do canal de atendimento ou do tipo de cliente.

---

# Regra 1 — Atendimento Inicial

Toda nova conversa inicia no estado **inicio**.

A partir da primeira mensagem recebida, a Sofia identifica a intenção do cliente antes de decidir qual será o próximo passo do atendimento.

---

# Regra 2 — Identificação da Intenção

Antes de iniciar a coleta de informações, a Sofia tenta identificar automaticamente o motivo do contato.

Entre as intenções atualmente reconhecidas estão:

- saudação;
- pedido de orçamento;
- conhecer serviços;
- reunião;
- tráfego pago;
- social media;
- design;
- web design;
- atendimento com IA;
- estrutura completa;
- objeções;
- dúvidas.

---

# Regra 3 — Validação do Nome

A Sofia somente registra o nome quando considera que a resposta realmente representa um nome.

Caso a informação não pareça válida, ela solicita novamente essa informação.

Essa validação evita que frases como pedidos de orçamento ou descrições de serviços sejam armazenadas incorretamente como nome do cliente.

---

# Regra 4 — Ordem da Qualificação

A coleta de informações segue uma ordem pré-definida.

1. Nome
2. Empresa
3. Segmento
4. Objetivo comercial
5. WhatsApp (quando necessário)

Essa sequência garante maior organização durante o atendimento.

---

# Regra 5 — Identificação do Serviço

Sempre que possível, a Sofia identifica automaticamente o serviço mais adequado com base nas mensagens enviadas pelo cliente.

Caso ainda não existam informações suficientes, essa identificação poderá ocorrer em etapas posteriores da conversa.

---

# Regra 6 — Classificação Comercial

Durante toda a conversa, a Sofia pode atualizar:

- score;
- temperatura;
- prioridade;
- serviço identificado.

A classificação evolui conforme novas informações são recebidas.

---

# Regra 7 — Histórico

Todas as mensagens enviadas pelo cliente e pela Sofia são adicionadas ao histórico da conversa.

Esse histórico serve de base para:

- geração do resumo comercial;
- consultas futuras;
- auditoria do atendimento.

---

# Regra 8 — Encaminhamento

Após concluir a qualificação, a Sofia altera o estado da conversa para **aguardando_humano**.

A partir desse momento, considera-se que o atendimento automatizado foi concluído.

---

# Regra 9 — Atendimento Após Encaminhamento

Quando a conversa já foi encaminhada ao especialista:

- a Sofia não reinicia o processo de qualificação;
- não volta a fazer perguntas comerciais;
- apenas informa que o especialista continuará o atendimento assim que possível.

Essa regra evita duplicidade de atendimento.

---

# Regra 10 — Resumo Comercial

Ao finalizar a qualificação, a Sofia gera automaticamente um resumo comercial.

Esse resumo reúne:

- informações da empresa;
- dados da lead;
- classificação comercial;
- contexto da conversa;
- recomendação para continuidade do atendimento.

---

# Regra 11 — Especialista Humano

A negociação comercial é responsabilidade exclusiva do especialista humano.

A Sofia não:

- fecha contratos;
- negocia valores;
- promete resultados;
- conclui vendas.

Seu papel é preparar a conversa para que o vendedor assuma o atendimento.

---

# Regra 12 — Arquitetura Híbrida

Sempre que possível, a Sofia utiliza regras implementadas em código.

A Inteligência Artificial é empregada apenas quando agrega valor ao processo, como na geração do resumo comercial.

Essa estratégia reduz custos, aumenta a velocidade do atendimento e torna o comportamento do sistema mais previsível.

---

# Evolução das Regras

As regras de negócio poderão evoluir conforme novas funcionalidades forem incorporadas ao Orion CRM AI.

Toda alteração deverá manter compatibilidade com a arquitetura atual e ser devidamente documentada para preservar a consistência do comportamento da Sofia.