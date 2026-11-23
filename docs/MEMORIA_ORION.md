# Memória técnica e histórica do Orion CRM AI

As decisões de negócio registradas aqui foram fornecidas pelo responsável pelo projeto. As descrições de implementação refletem a análise estática do código. O funcionamento em ambiente deve ser confirmado separadamente.

## Identidade

O Orion CRM AI é um CRM multiempresa da Orion Systems. A Forway é a empresa parceira inicial, e Luciano é o principal responsável pelo atendimento comercial.

## Arquitetura

Componentes identificados no código:

| Componente | Caminhos e responsabilidades |
| --- | --- |
| Backend FastAPI e WAHA | [backend/main.py](../backend/main.py) recebe mensagens em `/mensagem` e eventos de WhatsApp em `/webhook/waha`. O [serviço de mensagens](../backend/app/services/mensagem_service.py) controla persistência, deduplicação e estados de processamento e envio. |
| Sofia SDR | [sdr_agent.py](../backend/app/agents/sdr_agent.py) conduz a conversa e aplica regras comerciais. [gpt_service.py](../backend/app/services/gpt_service.py) usa OpenAI para extração de contexto, geração de respostas e resumo comercial. |
| Dashboard Streamlit | [dashboard/app.py](../dashboard/app.py) concentra login, sessão, seleção da empresa e navegação. As [páginas do dashboard](../dashboard/app_pages) incluem leads, funil, conversas, configurações e follow-up. |
| PostgreSQL | O backend usa [SQLAlchemy](../backend/app/database/database.py) e [modelos ORM](../backend/app/models/models.py). O dashboard usa [psycopg2 e SQL direto](../dashboard/database/db.py). Os scripts SQL versionados ficam em [backend/migrations](../backend/migrations). |
| Follow-up Automático | A [página de follow-up](../dashboard/app_pages/followup.py) reúne configuração e acompanhamento. Os serviços de backend tratam elegibilidade, agendamento e processamento. O [scheduler](../backend/app/workers/followup_scheduler.py) e o [worker](../backend/app/workers/followup_worker.py) executam o ciclo em processo separado. |
| Central WhatsApp | A [página de conversas](../dashboard/app_pages/conversas.py) consome [rotas autenticadas](../backend/app/routes/central_whatsapp_api.py) para atendimento humano, pendências e envio de mensagens. |

## Sofia SDR

### Decisões de negócio

- A Sofia é uma agente SDR híbrida. Ela combina regras de negócio e inteligência artificial.
- O fluxo inclui saudação, coleta de nome, empresa, segmento, objetivo e origem, qualificação, resumo comercial e encaminhamento humano.
- Após encaminhar a conversa ao humano, a Sofia não deve reiniciar o atendimento comercial.
- Emojis são permitidos apenas na saudação inicial e na mensagem final de agradecimento.
- Luciano deve receber notificações de todas as conversas recebidas pela Sofia, inclusive contatos que apenas dizem “Oi”. A cobertura dessa regra ainda precisa ser validada.

### Implementação identificada

O código conduz a conversa com regras e extração estruturada de contexto, classifica a lead, gera resumo para o vendedor e registra estados de atendimento por IA e humano. O backend contém rotinas de alerta comercial e de atendimento humano.

## Follow-up Automático

### Decisões de negócio

- O Follow-up Automático faz parte do CRM como módulo interno.
- O follow-up inicial atende exclusivamente leads originadas de anúncios ou campanhas Click-to-WhatsApp que receberam a primeira resposta da Sofia e não responderam depois.
- Qualquer resposta do cliente após a primeira mensagem da Sofia torna a lead inelegível para esse follow-up inicial, mesmo que o cliente volte a ficar em silêncio.
- Leads qualificadas e encaminhadas ao atendimento humano ficam fora desse fluxo inicial.
- Horários, dias, intervalos, quantidade de tentativas e modelos de mensagem são configuráveis por empresa.

### Configuração padrão recomendada

| Parâmetro | Valor recomendado |
| --- | --- |
| Espera inicial | 3 horas |
| Segunda a sexta | 08h às 18h |
| Sábado | 08h às 12h |
| Domingo | Sem disparos |
| Fuso horário | `America/Sao_Paulo` |

Esses valores são a referência de negócio. A configuração aplicada a cada empresa ainda precisa ser confirmada em ambiente.

### Implementação identificada

O webhook contém o gatilho para criar o primeiro agendamento após persistir o sucesso da resposta da Sofia. O [serviço de elegibilidade](../backend/app/services/followup_service.py) verifica a origem, os estados da lead e da conversa, a confirmação HTTP da primeira resposta e se o cliente respondeu depois. O [serviço de agendamento](../backend/app/services/followup_agendamento_service.py) aplica configuração, modelo e janela de atendimento da empresa.

O dashboard permite editar a configuração e os modelos e consultar agendamentos por status. O [serviço de processamento](../backend/app/services/followup_processamento_service.py) controla reserva, autorização, início, cancelamento e finalização. Quando o cliente responde, o fluxo cancela tentativas pendentes ou reservadas cujo envio ainda não começou. Reservas expiradas podem voltar a pendente caso o envio ainda não tenha começado. Quando o início já foi registrado e o resultado é desconhecido, a tentativa fica inconclusiva.

## Regras Multiempresa

**Decisão de negócio.** O Follow-up deve respeitar a empresa, a conexão WhatsApp e o responsável pela conversa. A configuração das tentativas e dos modelos pertence à empresa.

**Implementação identificada.** O backend carrega o [contexto comercial por empresa](../backend/app/services/empresa_context_service.py). O modelo de dados inclui vínculos da conversa com a conexão de canal e com o especialista responsável. O scheduler processa por empresa, e o worker resolve o destino e a sessão WAHA antes do envio.

## Pendências

- Validar que Luciano recebe notificações de todas as conversas recebidas pela Sofia, inclusive quando o único conteúdo é “Oi”.
- Confirmar o comportamento da Sofia após o encaminhamento humano e o uso de emojis nas mensagens previstas.
- Verificar a elegibilidade do follow-up com os metadados reais de Click-to-WhatsApp, incluindo a exclusão de quem respondeu ou já foi encaminhado ao humano.
- Validar a configuração aplicada, as janelas de envio, o vínculo com a conexão WhatsApp e o responsável e o isolamento entre empresas.
- Validar o ciclo com concorrência, resposta próxima ao início do envio, expiração de reservas e resultado inconclusivo. A confirmação HTTP registrada pelo sistema e a entrega no WhatsApp devem ser verificadas separadamente.
- Confirmar em ambiente o schema aplicado e a configuração operacional do scheduler e da WAHA.

## Prioridades

1. Concluir, testar e validar o Follow-up Automático antes de iniciar outros módulos.
2. Retomar a Central WhatsApp integrada ao CRM somente após a conclusão do Follow-up.
