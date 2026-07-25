# 4. Backend

## 4.1 Visão geral

O backend do Orion CRM AI é desenvolvido em Python com FastAPI.

Seu ponto de entrada atual é o arquivo:

`backend/main.py`

Esse arquivo recebe mensagens, gerencia conversas, chama a Sofia SDR, cria clientes e leads no PostgreSQL e envia respostas ao WhatsApp por meio do WAHA.

## 4.2 Responsabilidades do `main.py`

O arquivo possui as seguintes responsabilidades:

- iniciar a aplicação FastAPI;
- verificar e criar tabelas do SQLAlchemy;
- validar os dados recebidos;
- abrir e fechar sessões do PostgreSQL;
- localizar ou criar conversas;
- chamar a lógica da Sofia SDR;
- salvar as alterações da conversa;
- gerar clientes e leads;
- evitar a criação de leads duplicadas;
- gerar o resumo para o vendedor;
- receber webhooks do WAHA;
- simular o indicador de digitação;
- enviar respostas para o WhatsApp.

## 4.3 Dependências internas

O `main.py` depende diretamente de:

- `app.database.database`;
- `app.models.models`;
- `app.agents.sdr_agent`.

As principais funções importadas do agente são:

- `conduzir_conversa`;
- `gerar_resumo_vendedor`.

## 4.4 Modelos utilizados

O arquivo utiliza os seguintes modelos:

### Conversa

Representa o atendimento em andamento, incluindo dados coletados, histórico e etapa atual.

### Cliente

Representa a pessoa ou empresa atendida.

### Lead

Representa a oportunidade comercial gerada pela qualificação.

## 4.5 Modelo de entrada

A classe `MensagemRequest` define o formato interno das mensagens.

Campos:

- `nome`: opcional;
- `telefone`: opcional;
- `canal`: obrigatório;
- `identificador`: obrigatório;
- `mensagem`: obrigatório.

## 4.6 Rota `/mensagem`

Método:

`POST`

Finalidade:

Processar uma nova mensagem dentro do fluxo comercial.

Fluxo:

1. abre uma sessão com o banco;
2. procura uma conversa pelo identificador;
3. cria uma conversa quando ela ainda não existe;
4. chama `conduzir_conversa`;
5. salva as alterações;
6. verifica se a conversa chegou ao encaminhamento;
7. procura uma lead existente;
8. cria Cliente e Lead quando necessário;
9. gera o resumo para o vendedor;
10. retorna a resposta e a classificação;
11. fecha a sessão com o banco.

## 4.7 Criação da conversa

Uma conversa nova é iniciada com:

- canal informado;
- identificador informado;
- nome e telefone, quando disponíveis;
- etapa `inicio`;
- histórico vazio.

O identificador é utilizado para continuar o atendimento nas próximas mensagens.

## 4.8 Chamada da Sofia

A função `conduzir_conversa` recebe:

- o objeto da conversa;
- a mensagem enviada pelo cliente.

Ela retorna:

- a resposta da Sofia;
- uma análise comercial.

A análise é utilizada pelo `main.py` para acessar:

- temperatura;
- prioridade;
- score.

## 4.9 Criação de Cliente e Lead

Cliente e Lead são criados quando a conversa chega às etapas:

- `encaminhar`;
- `aguardando_humano`.

Antes da criação, o sistema procura uma lead com o mesmo telefone e canal.

Quando não encontra, cria primeiro o Cliente e depois a Lead.

A Lead recebe:

- cliente relacionado;
- produto ou serviço;
- temperatura;
- prioridade;
- score;
- origem;
- observações;
- resumo para o vendedor;
- status `Aguardando atendimento`.

## 4.10 Prevenção de duplicidade

A verificação atual utiliza:

- telefone do cliente;
- canal de origem.

Quando uma lead existente é encontrada, o sistema reutiliza seu ID e seu resumo.

No estado atual, essa lead não é atualizada automaticamente com novas informações.

## 4.11 Retorno da rota `/mensagem`

A resposta contém:

- canal;
- etapa atual;
- resposta do agente;
- produto identificado;
- temperatura;
- prioridade;
- score;
- status;
- resumo do vendedor;
- ID da lead.

O status é `encaminhado` quando a conversa está nas etapas de encaminhamento. Nas demais etapas, o status é `em_atendimento`.

## 4.12 Rota `/webhook/waha`

Método:

`POST`

Finalidade:

Receber eventos enviados pelo WAHA.

A rota:

1. aceita somente eventos do tipo `message`;
2. ignora mensagens enviadas pelo próprio número;
3. extrai texto, identificador e nome;
4. ignora eventos sem texto ou identificador;
5. converte o evento para `MensagemRequest`;
6. chama a função `receber_mensagem`;
7. obtém a resposta da Sofia;
8. calcula um tempo de digitação;
9. ativa o indicador de digitação no WAHA;
10. aguarda o tempo calculado;
11. encerra o indicador;
12. envia a resposta ao WhatsApp.

## 4.13 Humanização da resposta

O atraso depende do tamanho do texto:

- até 120 caracteres: de 2 a 4 segundos;
- até 350 caracteres: de 4 a 7 segundos;
- acima de 350 caracteres: de 7 a 12 segundos.

Essa lógica procura evitar respostas instantâneas e artificiais.

## 4.14 Fluxo completo

Cliente envia mensagem pelo WhatsApp.

WAHA recebe a mensagem.

WAHA envia o evento para `/webhook/waha`.

O webhook converte o evento para o formato interno.

A função `/mensagem` recupera ou cria a conversa.

A Sofia conduz o atendimento.

O PostgreSQL recebe as alterações.

Quando a qualificação termina, Cliente e Lead são criados.

O backend devolve a resposta.

O WAHA envia a resposta para o WhatsApp.

## 4.15 Tratamento de erros

A função principal utiliza `try`, `except` e `finally`.

Em caso de erro:

- o traceback é exibido no terminal;
- o nome e a mensagem da exceção são retornados.

A sessão com o banco é fechada no bloco `finally`.

## 4.16 Configuração atual do WAHA

A implementação atual utiliza:

- endereço local do WAHA;
- porta 3000;
- sessão `default`;
- endpoints `startTyping`, `stopTyping` e `sendText`.

Por segurança, o valor da chave da API não deve ser registrado nesta documentação.

## 4.17 Pontos de atenção

- chave do WAHA gravada diretamente no código;
- URL e sessão do WAHA fixas;
- uso de chamadas bloqueantes em endpoint assíncrono;
- ausência de tratamento detalhado no envio final;
- erros podem ser devolvidos com status HTTP de sucesso;
- detalhes internos podem ser expostos na resposta de erro;
- dependência das chaves temperatura, prioridade e score;
- lead existente não é atualizada;
- mensagens não textuais são ignoradas;
- rota `/mensagem` sem autenticação aparente;
- tabelas verificadas ou criadas durante a inicialização;
- configuração ainda parcialmente específica da Forway.

## 4.18 Estado atual

O `main.py` já implementa o fluxo principal entre:

- WhatsApp;
- WAHA;
- FastAPI;
- Sofia SDR;
- PostgreSQL;
- CRM.

Antes de testes reais em maior escala, os pontos de segurança, confiabilidade e concorrência devem ser revisados de forma controlada.