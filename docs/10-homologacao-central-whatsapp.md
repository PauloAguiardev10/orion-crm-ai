# Homologação da Central WhatsApp

A gestão cadastra conexões no CRM e reserva uma vaga do plano antes de provisionar a sessão na WAHA. O administrador pode iniciar ou reconectar sessões gerenciadas, consultar o QR Code e suspender a operação mediante confirmação. A suspensão usa o comando de parada da WAHA e conserva o pareamento. As sessões legadas, inclusive a da Forway, podem ser consultadas por administradores autorizados e ficam protegidas contra mudanças pela gestão.

## Configuração a validar

- Aplicar a migração de franquias antes de publicar esta revisão. Os limites são definidos no PostgreSQL e validados em todas as novas admissões. As variáveis antigas de limites por plano deixaram de ser usadas.
- Revisar a migração `20261125_gestao_conexoes_waha.sql` antes de qualquer aplicação autorizada. Os campos novos atribuem comportamento legado como padrão e não modificam o vínculo das conversas existentes.
- Confirmar versão, edição, engine, eventos, API de sessão, formato do QR e limites de sessões da WAHA instalada. Validar o webhook assinado usando `ORION_WAHA_WEBHOOK_URL` e `WAHA_WEBHOOK_HMAC_KEY` no ambiente de homologação. Habilitar `ORION_WAHA_GESTAO_ATIVA` somente após essa validação.
- Manter `ORION_CENTRAL_WHATSAPP_MIDIA_ATIVA` desativada por padrão e validar a reprodução de mídias reais no navegador.
- Validar a atualização automática do painel com um rascunho aberto no navegador.
- Revalidar no ambiente integrado os ACKs antecipados e a persistência de não lidas. A Central agora registra ACKs assinados no PostgreSQL e reconcilia o estado durante a confirmação do envio. A marca de leitura pertence ao usuário e à conversa e resiste a sessões concorrentes.

## Interface da Central

- A lista e o histórico usam o escopo de leitura existente. A ficha comercial exige acesso à conversa fora da fila compartilhada e reúne apenas registros vinculados à mesma empresa.
- O cadastro atual não oferece foto de perfil do contato. A interface usa iniciais até existir uma fonte de fotos autorizada.
- A interface mantém a atualização de cinco segundos e permite carregar mensagens anteriores pelo cursor do histórico. A homologação da atualização automática com um rascunho aberto deve ser repetida no ambiente integrado, conforme a pendência acima.

## Voz e armazenamento

- A gravação do navegador usa o microfone com permissão explícita. A prévia fica no navegador até o atendente anexar o áudio e confirmar o envio.
- Usar HTTPS na homologação integrada e validar microfone, pausa, descarte e velocidade nos navegadores suportados. O localhost é suficiente para a simulação local.
- Configurar `ORION_WAHA_FFMPEG` com o caminho absoluto de um executável confiável com libopus para gravações WebM, MP4 e WAV. A saída é OGG/Opus e usa a operação de voz da WAHA. Manter a flag de mídia desligada até confirmar a operação na instalação real.
- Dar acesso ao diretório `ORION_CENTRAL_WHATSAPP_MIDIA_DIR` apenas à conta do backend. Incluir o diretório no backup e validar recuperação de um anexo por meio da rota autenticada. Configurar a ACL equivalente em Windows.

## Consulta manual da VPS

No terminal autorizado da VPS, executar o bloco como um único comando. Para um backend em contêiner, preencher `ORION_BACKEND_CONTAINER` com o nome do contêiner antes do bloco. Para a consulta do PostgreSQL, configurar `PGSERVICE` com um serviço de conexão já existente para o banco do CRM e com o papel do aplicativo. Compartilhar apenas o resumo de capacidades.

```sh
bash <<'ORION_LEITURA'
set -o pipefail
base=http://127.0.0.1:3000
for container in $(docker ps --format '{{.Names}} {{.Image}}' | awk 'tolower($2) ~ /waha/ {print $1}'); do
  docker inspect --format '{{.Config.Image}} {{.Image}}' "$container"
done
{ curl -fsS --max-time 5 "$base/api/server/version" ||
  curl -fsS --max-time 5 "$base/api/version"; } |
  jq '{version, edition: (.edition // .tier), engine}' ||
  echo 'Versão indisponível sem autenticação'
for rota in /api-json /swagger-json; do
  if curl -fsS --max-time 5 "$base$rota" |
    jq -e '[.paths | to_entries[] | select(.key | test("sendVoice|sendImage|sendVideo|sendFile|auth/qr|sessions|api/files")) | {path:.key, methods:(.value|keys)}]'; then break; fi
done
verificar_ffmpeg='
  bin=${ORION_WAHA_FFMPEG:-ffmpeg}
  if command -v "$bin" >/dev/null 2>&1; then
    "$bin" -version | head -n 1
    "$bin" -hide_banner -encoders 2>/dev/null | grep -w libopus || echo "libopus indisponível"
  else
    echo "FFmpeg indisponível neste ambiente"
  fi'
if [ -n "${ORION_BACKEND_CONTAINER:-}" ]; then
  docker exec "$ORION_BACKEND_CONTAINER" sh -c "$verificar_ffmpeg"
else
  sh -c "$verificar_ffmpeg"
fi
if [ -n "${PGSERVICE:-}" ]; then
  psql -X -w -v ON_ERROR_STOP=1 <<'SQL'
SELECT to_regclass('empresas') IS NOT NULL AS empresas,
       to_regclass('usuarios') IS NOT NULL AS usuarios,
       to_regclass('conversas') IS NOT NULL AS conversas,
       to_regclass('conexoes_canais') IS NOT NULL AS conexoes,
       to_regclass('central_ack_pendente') IS NOT NULL AS ack_pendente,
       to_regclass('central_conversa_leitura') IS NOT NULL AS leitura,
       to_regprocedure('orion_limite_plano(text,text)') IS NOT NULL AS franquia;
SELECT CASE WHEN to_regclass('empresas') IS NOT NULL AND EXISTS (
  SELECT 1 FROM pg_attribute WHERE attrelid = to_regclass('empresas')
    AND attname = 'plano' AND NOT attisdropped
) THEN has_column_privilege(to_regclass('empresas'), 'plano', 'UPDATE')
  ELSE false END AS privilegio_atualizacao_plano;
SQL
else
  echo 'Catálogo PostgreSQL pendente: executar com PGSERVICE configurado'
fi
ORION_LEITURA
```

Conferir no Swagger da instalação o corpo de envio de voz, a resposta do QR, a edição e os endpoints de sessões. Confirmar o suporte a múltiplas sessões e o formato de ACK e mídia através de documentação correspondente à versão e amostras já existentes com dados pessoais removidos. A consulta de leitura não cria sessões nem envia mensagens. Para fotos, exigir um mecanismo validado de obtenção de imagem que não aceite URLs arbitrárias, credenciais na URL ou redirecionamentos. Até lá, manter as iniciais.

## Franquias aprovadas

| Plano | Conexões WhatsApp | Usuários |
|---|---:|---:|
| LITE | 1 | 2 |
| PRO | 2 | 5 |
| PREMIUM | 5 | 10 |

Administradores e atendentes cadastrados na empresa ocupam vaga, inclusive contas inativas ainda cadastradas. O perfil `orion_admin` fica fora da contagem. Conexões cadastradas continuam ocupando vaga quando paradas. A migração preserva todos os cadastros e mantém o atendimento existente acima da franquia. Admissões, transferências de cadastro entre empresas e mudanças que passem a ocupar vaga são verificadas na mesma transação que grava os dados.

## Candidato das sete fases

- Atendimento, histórico, permissões e envio com reserva idempotente.
- Atendimento humano, transferência, encerramento e supervisão multiempresa.
- Mídias autenticadas com armazenamento privado e transporte WAHA.
- Atualização incremental, estados de envio autenticados e leitura por usuário.
- Gerenciamento de conexões, QR Code e política da Sofia por conexão.
- Interface de atendimento em três painéis, pesquisa, ficha comercial e histórico paginado.
- Gravação e reprodução de voz, ACKs antecipados, deduplicação e franquias transacionais.

## Sequência proposta de implantação e retorno

1. Revisar o diff e separar os arquivos da Central das mudanças preexistentes no workspace. Executar a suíte, a simulação da WAHA e a aplicação das migrações duas vezes em um banco descartável.
2. Registrar a revisão implantada, a configuração de flags e a identificação das sessões legadas. Preparar um backup consistente em formato custom do PostgreSQL e do diretório privado de mídia. Verificar o catálogo com `pg_restore --list` e ensaiar a restauração em outro banco. Guardar os backups em armazenamento privado.
3. Após autorização, separar os arquivos e hunks do candidato no índice, conferir `git diff --cached --check` e inspecionar `git diff --cached --stat`. Fazer o commit apenas do candidato, enviar para a branch aprovada e aguardar a validação. Validar previamente a presença de `usuarios`, `empresas`, `conexoes_canais`, `conversas` e das migrações anteriores da Central no ambiente.
4. Em janela autorizada, aplicar com interrupção em erro, nesta ordem, `20261114_conversas_especialista_responsavel.sql` (caso pendente), `20261125_gestao_conexoes_waha.sql`, `20261125_estado_operacional_central.sql` e `20261125_limites_comerciais_central.sql`. Confirmar as duas tabelas operacionais, a função de limites e os gatilhos de usuários e conexões. Verificar que o papel do aplicativo pode atualizar a coluna `empresas.plano` na transação de admissão, como exige o bloqueio da franquia. Só então publicar backend e dashboard com as duas flags desligadas.
5. Conferir login, escopos, conversas legadas da Forway e saúde da Sofia e do Follow-up. Homologar cada flag separadamente em sessão de teste autorizada, preservando a sessão atual.
6. Para voltar, desativar as flags e restaurar a revisão anterior do código. Manter as tabelas e colunas aditivas para preservar ACKs, leituras e configuração das conexões. Se for necessário voltar também à política anterior de franquias, remover somente os gatilhos em transação autorizada. A função de consulta pode permanecer. Para restauração integral, parar as escritas, preservar os dados produzidos desde o backup e testar a restauração em instância isolada antes do corte.

### Evidências exigidas antes da publicação

- Gerar o dump em formato custom com `pg_dump --format=custom` usando a conexão protegida já configurada no host. Arquivar o armazenamento privado de mídias com uma janela consistente com o dump e preservar a configuração protegida e o volume de sessão atual da WAHA. Não copiar esses arquivos para o GitHub.
- Validar cada artefato pelo checksum SHA-256 e catálogo do dump. Restaurar com `pg_restore --exit-on-error` em banco descartável e conferir tabelas, contagens, amostras referenciadas de mídia e vínculos da sessão Forway antes de autorizar o corte.
- Homologar texto, voz nativa, imagem, vídeo e documento em conversa dedicada. Verificar reprodução, ACK, deduplicação e acesso autorizado. Validar QR, provisionamento e segunda sessão apenas se a edição instalada suportar a operação, sem alterar o pareamento da Forway.
- Confirmar que a Sofia responde somente onde habilitada e que o Follow-up preserva sessão, agenda, cancelamento por atendimento humano e tratamento de reservas. Não alterar as flags operacionais atuais da Sofia ou do Follow-up sem validação no ambiente.

## WAHA CORE com múltiplas instâncias

O CRM mantém o nome interno da sessão em `conexoes_canais.sessao_waha`. Para conexões novas, ele usa `orion-waha:<instância>:<sessão física>`. O nome interno permanece o mesmo em conversas, mensagens e ACKs. Duas instâncias podem usar `default` sem compartilhar identidade. A sessão legada da Forway conserva o nome, os IDs, o volume e a rota de webhook existentes.

### Configuração e implantação do piloto

1. Faça backup do PostgreSQL, das configurações e dos volumes das sessões antes da implantação. Preserve a configuração da Forway. Confirme que `WAHA_API_URL` resolve a própria instância legada a partir do backend e do worker, e mantenha as variáveis existentes de chave e webhook.
2. Provisione instâncias em rede privada, com origem, chave de API, HMAC e volume próprios. Fixe e registre o digest, a versão, a edição e a engine da imagem. Separe também o armazenamento de mídia. Reserve somente sessões novas e vazias. A API de gestão recusa uma sessão preexistente sem o marcador de propriedade do CRM.
3. Configure `ORION_WAHA_INSTANCIAS` no backend e no worker. O catálogo contém referências aos nomes das variáveis de segredo, por exemplo:

   ```json
   {"piloto_a":{"origem":"http://waha-piloto-a:3000","api_key_env":"ORION_WAHA_A_API_KEY","hmac_env":"ORION_WAHA_A_HMAC","sessoes":["default"]}}
   ```

   Mantenha `ORION_WAHA_WEBHOOK_URL` apontando para a URL base da rota `/webhook/waha`. O cadastro acrescenta o identificador da instância ao registrar o webhook. Use o mesmo catálogo nos processos do backend e do worker. Cada rota de instância exige a assinatura SHA-512 da instância configurada.
4. Aplique `20261127_waha_multi_instancia.sql` depois das migrações de gestão e franquia. Cadastre as vagas aprovadas em `waha_capacidade` pelo papel de operação. Exemplo para o piloto:

   ```sql
   INSERT INTO waha_capacidade (sessao_crm)
   VALUES ('orion-waha:piloto_a:default');
   ```

   O papel da aplicação precisa de leitura da tabela e atualização de `conexao_id` para reservar a vaga. O cadastro valida o plano e o vendedor, e vincula conexão e vaga na mesma transação. Uma desconexão suspende a operação e preserva a reserva e o histórico. Troca de locatário ou reuso de uma vaga vinculada exige um procedimento operacional explícito com saneamento do estado da WAHA.
5. Em homologação, habilite a gestão somente após conferir o catálogo, as vagas e o acesso de rede privado. Use o CRM para cadastrar uma conexão, selecionar o vendedor, conectar e abrir o QR. O QR é entregue pela API autenticada com `no-store`. A Forway permanece protegida contra ações de gestão.

### Testes e critérios de homologação

- Rodar o teste de multi-instância e as suítes da Central, de mídia, de gestão e de Follow-up contra o banco de testes após aplicar as migrações. Usar transporte simulado.
- No piloto autorizado, conferir dois containers com `default`, HMAC trocado, ACK antes da confirmação HTTP, IDs repetidos, conversa com `@lid`, permissões por empresa/vendedor, QR, parada e retomada. Conferir também a continuidade da Forway, Sofia e Follow-up.
- Confirmar que a imagem WAHA retorna os metadados de sessão no endpoint de consulta e entrega PNG no endpoint de QR utilizado. Validar as APIs e eventos efetivamente disponíveis no digest instalado.
- Com mídia ainda desabilitada em produção, validar imagens, vídeo, documentos, voz em OGG/Opus, disponibilidade do FFmpeg e reprodução no navegador no ambiente piloto. Medir CPU, RAM, disco e latência em pareamento e reconexão antes de ampliar a capacidade.

### Rollback

Suspenda as novas conexões com o código atual e desabilite a gestão. Confirme que workers e webhooks das instâncias piloto deixaram de operar antes de reverter a aplicação. Preserve o cadastro, as reservas, os históricos e os volumes. O código anterior desconhece os aliases novos e pode tentar usar o host legado, portanto mantenha as conexões piloto suspensas e seus webhooks desativados durante o rollback. Conserve a tabela aditiva para retomada ou remova-a somente se estiver vazia e após verificação do backup. Valide Forway, Sofia e Follow-up pelo caminho legado.
## Sincronização e conexão institucional

- Antes da publicação, aplicar a migração `20261128_conexao_institucional_sofia.sql`. Ela deixa as conexões existentes com `sofia_institucional=false`. Após conferir o ID e a empresa da conexão institucional, o operador pode marcar exclusivamente essa linha como institucional. O índice permite uma por empresa e a conexão marcada precisa ser WhatsApp WAHA, com Sofia ativa. O vínculo ao especialista é preservado, inclusive o de Luciano na Forway. Ela fica fora da franquia e indisponível para novos envios manuais pelo CRM.
- Para restringir a exceção do contato interno, configurar `ORION_LUCIANO_EMPRESA_ID`, `ORION_LUCIANO_CONEXAO_ID` e `LUCIANO_WHATSAPP_LID`. O bloqueio só se aplica à conexão institucional indicada pelos dois IDs. A rota legada permanece compatível com o modo sem HMAC já existente exclusivamente para a Forway (empresa 1, conexão 1, sessão default).
- A configuração privada de cada instância em `ORION_WAHA_INSTANCIAS` pode ter `webhook_url` com a URL completa que encaminha à rota da mesma instância. Sem esse campo, permanece a composição a partir de `ORION_WAHA_WEBHOOK_URL`. Alterações em sessões já cadastradas exigem atualização de configuração na WAHA durante a homologação.
- Mantenha as flags de envio, mídia e gestão atuais. Habilite `ORION_WAHA_HISTORICO_ATIVO` apenas no piloto autorizado. A importação é individual, exige confirmação e consulta somente a conversa vinculada à conexão. O primeiro suporte importa até 50 entradas textuais identificáveis, sem disparar automações. O NOWEB precisa de Store habilitado antes do pareamento. A disponibilidade de histórico, fotos, nomes e mapeamentos de LID depende dos dados disponibilizados pelo WhatsApp e pela engine.
- Homologar leitura do QR, reautenticação com o mesmo número, status, foto, eventos móveis nos dois sentidos e arquivos permitidos. A reautenticação pode apagar dados da sessão armazenados na WAHA. O histórico do CRM é preservado. Conferir rascunho e rolagem em navegador, com atualização de fundo e ao usar a pausa manual.
- Para rollback, desabilitar a importação e a gestão das novas rotinas antes de reverter o código. Restaurar a regra antiga de franquia exige reconciliar primeiro empresas que passaram a usar a vaga liberada pela conexão institucional. Preserve os históricos importados e os vínculos existentes.
## Atendimento automático e verificação de números

A Central usa componentes Streamlit e a API existente. O primeiro envio reservado na Central, inclusive de anexo, assume a conversa sob o mesmo bloqueio usado pela Sofia e pelo worker. A reserva cancela follow-ups ainda não iniciados e recusa o envio se um follow-up já começou. Consultar mensagens ou pendências não muda o atendimento. A conexão institucional continua protegida.

A migração `20261129_waha_numeros_verificados.sql` deve vir após `20261128_conexao_institucional_sofia.sql`. A reserva de número é global e persistente. O cadastro da sessão e a leitura do QR não liberam tráfego. A confirmação consulta o número reportado pela WAHA e, na reautenticação, exige o mesmo número já reservado. Desconectar preserva a reserva.

1. Em homologação, tire backup e inventarie todas as conexões WAHA, incluindo a Forway. Confirme o E.164 diretamente em cada sessão autorizada. Em caso de divergência, resolva o conflito com o administrador antes da publicação.
2. Aplique as migrações e classifique a conexão legada conforme o procedimento anterior. Insira na tabela `waha_numeros_verificados` os pares de número confirmado e ID de conexão auditados. Evite aceitar o número informado pelo operador sem confirmação do provedor.
3. As conexões comerciais gerenciadas sem número inventariado ficam suspensas. A Forway legada segue operando. O CRM só confirma novas sessões depois que as sessões legadas ativas estão inventariadas. Valide tentativa duplicada e reconexão no piloto antes de liberar a gestão.
4. Para rollback, desative a gestão, mantenha conexões não verificadas suspensas e confira suas sessões no provedor antes de voltar a uma versão que desconhece a verificação. Preserve as reservas e os vínculos para reimplantação.

A atualização desta versão permanece por fragmentos com consulta HTTP condicional e pausa manual. A busca de mensagens é restrita ao conteúdo já carregado. Homologue rascunho e rolagem no navegador. A adoção de um componente dedicado e as capacidades adicionais de grupos, reações, respostas citadas, figurinhas e chamadas exigem implementação e verificação separadas no digest da WAHA instalado.
## Central React

A interface React/TypeScript é restrita à Central WhatsApp. A configuração é opcional e a Central clássica continua disponível no dashboard. A API e o bundle têm a mesma origem, e o Streamlit passa o token ao iframe por mensagem de integração. O token fica em memória. A configuração pública precisa apontar para a própria origem confiável do CRM.

- Compilar a partir de `dashboard/central_ui` com `npm ci` e `npm run build`. Disponibilizar `dashboard/central_ui/dist` junto à árvore lida pelo FastAPI antes de iniciar o serviço. O FastAPI monta `/central-ui/` se o bundle existir. Preservar essa rota no proxy e configurar `ORION_CENTRAL_UI_URL` no dashboard com sua URL HTTPS pública.
- O backend aplica o mesmo escopo de conversas e histórico a cada leitura SSE. O fluxo transmite diferenças com janela de 100 registros e envia um snapshot ao reconectar. Nesta versão o servidor consulta o PostgreSQL em intervalos de três segundos por conexão SSE. No piloto, medir o impacto com o número esperado de atendentes, manter o buffering do proxy desligado para `/api/central-whatsapp/eventos` e validar a desconexão por expiração de sessão.
- `ORION_WAHA_CONTATOS_ATIVO` habilita a consulta de contatos apenas para conexão autorizada com NOWEB Store. A pesquisa do frontend cobre as páginas carregadas. O seletor só usa um telefone confirmado no registro retornado; identificadores sem número permanecem visíveis sem conversão inventada.
- `ORION_WAHA_ACOES_MENSAGEM_ATIVAS` permite reagir, editar e excluir com a flag geral de envio ativa. Habilitar somente depois de conferir a resposta da imagem WAHA homologada. O servidor exige atendimento humano ativo, escopo da conexão e ID da WAHA compatível com o chat. Edição e exclusão exigem autoria humana e vínculo com o atendente. A reação é confirmada pela WAHA. A sincronização de edições e reações feitas no celular ainda requer integração com os respectivos eventos.
- No navegador de homologação, conferir foco, rascunho e rolagem durante eventos e reconexão, acesso em outra empresa, uploads, microfone, encaminhamento humano e troca de sessão. O teste Playwright local usa iframe e transporte SSE simulado, sem WAHA nem acesso ao banco.
- Para retornar à Central clássica, desativar `ORION_CENTRAL_UI_URL` ou escolher a opção clássica no dashboard. Nenhuma migração adicional é exigida pela interface React.
## Citações, encaminhamentos e eventos do aparelho

- Aplicar a migração aditiva `20261130_central_respostas_whatsapp.sql` após `20261129_waha_numeros_verificados.sql`, antes de iniciar o backend atualizado. A citação usa o identificador original da WAHA persistido na reserva. Nesta versão a citação é de saída textual. O encaminhamento usa a operação nativa da WAHA e exige duas conversas autorizadas na mesma conexão. A WAHA pode recusar destinos com os quais a sessão nunca conversou. Quando o arquivo encaminhado não está disponível no destino, a Central registra o encaminhamento sem replicar o binário.
- Figurinhas WebP usam `sendSticker` e as proteções existentes de mídia. Para receber a figurinha, a WAHA precisa entregar o arquivo e o MIME WebP reconhecível.
- Configurar webhooks autenticados com `message.edited`, `message.revoked` e `message.reaction` no piloto. As duas primeiras operações são incluídas ao criar sessões pelo CRM. Sessões já existentes precisam atualizar a configuração na janela aprovada. Os eventos alteram apenas mensagens já identificadas na mesma conversa e sessão. Eventos sem alvo comprovado ou recebidos antes da mensagem não são reaplicados automaticamente.
- `ORION_WAHA_ARQUIVO_ATIVO=1` oferece arquivar e desarquivar após confirmação da WAHA. No NOWEB, validar Store e os endpoints do digest instalado. O estado exibido é atualizado pelas ações do CRM. O evento de mudança de arquivo móvel não é documentado para NOWEB.
- `ORION_WAHA_PRESENCA_ATIVA=1` permite assinar presença ao abrir um atendimento autorizado e receber `presence.update` assinado. O indicador expira em oito segundos. A Central não publica a digitação do vendedor nesta versão.
- A pesquisa de contatos consulta páginas diretamente na sessão autorizada. Uma busca examina até quatro páginas de 50 registros por chamada e pode retornar cursor mesmo sem resultados, para continuar no provedor. O cursor cobre até 100.000 registros.

### Capacidade e rollback

O benchmark `backend/tests/benchmark_central_sse.py` roda somente em `127.0.0.1:55432/orion_crm_followup_test`, confirma a identidade do servidor e reverte as fixtures. Ele usa 12 vendedores de 12 empresas simultâneas, 15 conversas por vendedor e 20 mensagens por conversa. Cada amostra executa as consultas de autenticação, lista e histórico. Em regime, cada aba com uma conversa aberta executa cerca de uma consulta SQL por segundo, agregando as três operações por ciclo de três segundos. A supervisão em outra empresa pode acrescentar uma consulta de hierarquia por ciclo. O benchmark é sintético e não mede proxy, I/O de produção, anexos, saturação da rede ou concorrência com cargas reais. Medir latência e ocupação do pool no piloto antes de ampliar.

Preservar as novas colunas aditivas ao reverter a interface. Desativar a URL da Central React no dashboard para retornar à clássica. Se também reverter o backend, manter as alterações de configuração do provedor sob controle operacional e considerar que a versão anterior ignorará os novos eventos.

### Visualização local e build

Com Node.js conforme `dashboard/central_ui/.nvmrc` e as dependências fixadas por `package-lock.json`:

```sh
cd dashboard/central_ui
npm ci
npm run build
node tests/servidor.mjs
```

Abrir `http://127.0.0.1:48319/`. Esse servidor escuta apenas em loopback e contém dados fictícios. Para executar os testes automatizados no Edge local, rodar `npm test`. Para um deploy autorizado, compilar com o mesmo lockfile na árvore da revisão aprovada, disponibilizar `dist/` ao FastAPI, manter `/central-ui/` e `/api/central-whatsapp/` na mesma origem pública e validar a rota antes de configurar `ORION_CENTRAL_UI_URL`. O deploy não usa o servidor de teste.

A matriz pública da WAHA descreve fixação de **mensagens**, mas não confirma fixar conversas na lista. Para chamadas, descreve eventos e rejeição, sem API demonstrada para originar ou transportar voz e vídeo. Grupos têm API própria, mas a Central ainda precisa de regras de autorização por grupo, resolução de participantes e separação da Sofia e do Follow-up antes de habilitar esse fluxo.
Resultado local do benchmark sintético no schema validado: 240 ciclos, mediana de 25,22 ms, p95 de 42,27 ms e máximo de 53,36 ms. Em 60 abas com conversa aberta, estime cerca de 60 consultas SQL por segundo para contas na própria empresa, antes de leituras extras ou reconexões.
## Central Orion, grupos piloto e eventos antecipados

- O tema futurista e os estados ficam restritos à Central React. O relógio distingue reserva pendente de aceite HTTP. Os checks de envio, entrega e leitura usam os estados persistidos pelos ACKs. A confirmação de leitura tem dois checks em azul neon. Fixar uma conversa é uma preferência do usuário neste navegador, isolada por empresa. Essa preferência não é enviada à WAHA.
- Grupos de texto exigem uma autorização explícita. Configure `ORION_WAHA_GRUPOS_AUTORIZADOS` no backend, por exemplo `{"orion-waha:piloto:default":{"123456789@g.us":"Grupo comercial piloto"}}`. Use a chave interna da sessão cadastrada. A recepção exige webhook assinado, identificação individual do participante e conexão ativa, não institucional. A Central grava a conversa no escopo dessa conexão, sem chamar Sofia ou Follow-up. As permissões comerciais existentes controlam o acesso e envio. Não habilitar grupos particulares. Homologar no digest instalado o campo de participante e a origem de envios pelo celular. O piloto cobre texto e não implementa importação histórica de grupos, administração de membros ou confirmação de leitura por participante.
- A migração `20261201_central_eventos_antecipados.sql` segue a de `20261130`. Ela cria uma fila por conexão e identificador WAHA para edições, revogações e reações assinadas. A aplicação consome os eventos ao registrar o alvo ou confirmar o ID de envio. Revogação impede que edições atrasadas recriem o conteúdo. A retenção de sete dias é avaliada no consumo e na limpeza durante a chegada de eventos à conexão.
- Em homologação, validar grupos em conexão comercial isolada, eventos antecipados e atraso da WAHA, além de ACKs, rascunho e rolagem em navegador. Para rollback da interface, selecionar a Central clássica. Preservar a tabela aditiva durante a reversão do backend e desconfigurar o piloto de grupos conforme a janela operacional.
## Revisão da Central integrada ao Streamlit

O modo React ocupa a área útil da aba Central e mantém a navegação lateral. Histórico comercial e gestão de conexões têm abas próprias. O retorno administrativo usa `ORION_CENTRAL_UI_URL` vazio no dashboard. Reinicie somente o processo autorizado a receber essa configuração. As flags de envio, Store ou mídia permanecem independentes do frontend.

### Piloto de produção com autorização

1. Registre SHA, versões, digest e engine da WAHA e faça backup verificável da configuração, do volume de sessão e do banco. Confira `WORKING`, número verificado e Store na própria sessão por consulta autorizada. Evite reconfigurar a sessão institucional da Forway.
2. Para o piloto, prefira sessão comercial separada. Habilite NOWEB Store antes do pareamento se ainda não estiver habilitado. A WAHA alerta que mudar a configuração do Store com sessão já pareada pode perder dados locais do histórico. Avalie backup, compatibilidade e janela antes de qualquer alteração. Um novo QR só é necessário se o provedor exigir nova autenticação.
3. A sincronização pós-pareamento utiliza o escopo comercial configurado abaixo, sem chamar a Sofia ou o Follow-up. A importação individual continua disponível para sessões que já estão pareadas.
4. Habilite em janela autorizada as flags separadamente conforme a necessidade: `ORION_WAHA_CONTATOS_ATIVO`, `ORION_WAHA_HISTORICO_ATIVO`, `ORION_CENTRAL_WHATSAPP_MIDIA_ATIVA` e `ORION_CENTRAL_WHATSAPP_ENVIO_ATIVO`. As flags são por processo. Para ativar envio sem ampliar o acesso em uma instalação compartilhada, use um ambiente de homologação isolado ou confirme o impacto para todas as conexões liberadas antes da janela.
5. Confirme no PostgreSQL o fuso configurado pela empresa. Para a Forway, a referência esperada é `America/Fortaleza`. A Central usa o fuso lido da empresa autenticada. Os timestamps de mensagem persistidos sem offset seguem a convenção UTC.
6. Use o Node do `.nvmrc`, `npm ci`, `npm audit` e `npm run build` antes de disponibilizar o bundle ao FastAPI. Verifique SSE sem buffering no proxy e teste em 1366×768, 1920×1080 e mobile. Desative a URL da Central React para voltar à clássica. Em caso de problema operacional, desative primeiro a flag afetada. Preserve volumes, histórico, vínculos de sessão e reservas de números.

### Teste local da página Streamlit

Com a dependência Streamlit instalada no venv e Edge disponível, defina `ORION_TEST_PYTHON` como o executável do Python do venv, entre em `dashboard/central_ui` e execute `npm run build` e `npm exec -- playwright test --config=playwright.streamlit.config.ts`. O teste carrega o renderizador real da página Conversas no Streamlit com sessão e API fictícias, sem o fluxo de login de produção.
## Sincronização comercial paginada

O operador escolhe o escopo de uma destas formas. Em uma conta mista, configure `ORION_WAHA_PAREAMENTO_CONTATOS` com IDs explícitos por sessão, sem teto de dez. Para uma conta dedicada cujo conteúdo inteiro foi autorizado, inclua a chave interna da sessão na lista JSON `ORION_WAHA_CATALOGO_COMERCIAL`. A WAHA não classifica automaticamente o que é particular ou comercial. Mesmo em uma conta dedicada, grupos exigem entrada em `ORION_WAHA_GRUPOS_AUTORIZADOS`. A confirmação do número verificado dispara a tarefa. Para sessões existentes, a gestão oferece **Sincronizar escopo comercial autorizado**, sem alterar o pareamento.

A tarefa usa a conexão comercial ativa e verificada e busca o catálogo NOWEB em páginas de 100 chats. Importa a primeira página de cada conversa autorizada, usando transações separadas. Uma nova solicitação percorre o catálogo novamente e deduplica o histórico. Na Central, abrir a conversa importa a página recente quando habilitado. Ao subir no histórico, o CRM consulta suas páginas locais e, quando necessário, avança o cursor de páginas do provedor. A data de corte é fixada ao abrir o chat para limitar a interferência de mensagens novas. Nenhuma importação passa pelo pipeline da Sofia ou do Follow-up.

| Finalidade | Contrato NOWEB exigido |
| --- | --- |
| Confirmar compatibilidade | `GET /api/sessions/{session}`, estado WORKING, engine NOWEB e `config.noweb.store.enabled=true` |
| Agenda e busca | `GET /api/contacts/all?session=…&limit=…&offset=…` e `GET /api/contacts?contactId=…&session=…` |
| Catálogo autorizado | `GET /api/{session}/chats?limit=100&offset=…&sortBy=id&sortOrder=asc` |
| Histórico paginado | `GET /api/{session}/chats/{chatId}/messages` com `limit`, `offset`, `filter.timestamp.lte` e `downloadMedia` |
| Fotos | `GET /api/contacts/profile-picture` ou `GET /api/{session}/chats/{chatId}/picture`; proxy autenticado no CRM |
| Eventos novos | Webhooks assinados `message` e `message.any`; para saídas do celular ou WhatsApp Web, homologar `fromMe`, `source` e o ID real da versão instalada |

Use `ORION_WAHA_HISTORICO_ATIVO` para histórico e `ORION_WAHA_CONTATOS_ATIVO` para a agenda. Com mídia habilitada, a paginação pode recuperar anexos validados pelo mesmo armazenamento protegido da Central. Respeite a disponibilidade de mídia na WAHA, os limites por arquivo e a expiração no WhatsApp. Confirme nomes reais e o vínculo de LID no provedor. LID isolado não é telefone. O NOWEB Store depende dos dados recebidos no pareamento e não dá garantia de acervo completo. O parâmetro `fullSync` e a habilitação do Store devem ser avaliados em uma sessão piloto antes de parear. Não alterar a engine ou os volumes da Sofia para testar a Central. Em sessões já pareadas com Store desligado, a alternativa é manter sincronização prospectiva por webhook ou homologar uma conexão comercial separada com Store ativado. Uma sessão armazenada externa pode ser avaliada em laboratório somente mediante autorização e com outro número.

A paginação com offset depende da estabilidade da janela do provedor. A data de corte e a deduplicação reduzem efeitos de mensagens novas. Revogações e mudanças no Store durante o percurso podem exigir nova consulta.

## Contrato NOWEB observado no piloto

A sessão de teste ficou em `WORKING` com `noweb.store.enabled=true` e `noweb.store.fullSync=true`. A WAHA retornou 100 contatos na primeira página, 34 conversas (28 individuais e 6 grupos), 20 mensagens em um histórico individual (11 enviadas e 9 recebidas) e 20 recebidas em um grupo. Esses resultados demonstram as consultas do Store.

- Instâncias comerciais devem usar NOWEB e armazenamento persistente. A criação pelo CRM grava `config.noweb.store.enabled` e `config.noweb.store.fullSync` antes de iniciar a sessão e gerar o QR. Validar a configuração efetiva em `GET /api/sessions/{sessao}` antes do primeiro pareamento. Sessões existentes, incluindo a institucional, conservam sua configuração.
- `GET /api/contacts/all` fornece `id`, `name`, `lid` e `phoneNumber`. `GET /api/{sessao}/chats` usa `@s.whatsapp.net` para conversas individuais e `@g.us` para grupos. O histórico é recuperado em `GET /api/{sessao}/chats/{chatId}/messages`, com paginação e `downloadMedia` condicionado à flag de mídia.
- Autorizar o catálogo completo por sessão lógica em `ORION_WAHA_CATALOGO_COMERCIAL` somente para contas de uso exclusivamente comercial. Em sessões mistas, selecionar os contatos com `ORION_WAHA_PAREAMENTO_CONTATOS` e os grupos com `ORION_WAHA_GRUPOS_AUTORIZADOS`. Validar que um vendedor sem vínculo não acesse o catálogo, as fotos ou o histórico.
- Homologar no piloto as mensagens do celular, WhatsApp Web e CRM, ACKs, grupos autorizados, histórico após interrupção, mídia e regressão da Sofia e do Follow-up. Histórico, fotos e mídias continuam sujeitos ao acervo disponível no provedor.

## Sincronização durável

O FastAPI inicia o worker quando `ORION_WAHA_HISTORICO_ATIVO=1`. O pareamento grava a tarefa na mesma transação que confirma o número. O worker também encontra conexões comerciais elegíveis já pareadas e segue com o CRM fechado. A sessão precisa estar em `WORKING`, usar NOWEB Store e devolver o número reservado pelo CRM. As regras de autorização por sessão e grupo continuam obrigatórias.

`central_sync_noweb` guarda a próxima execução, o cursor do catálogo e da página de mensagens, as falhas, o código de diagnóstico e o último ciclo concluído. `central_sync_noweb_chats` guarda a data de corte concluída por chat. O progresso e as mensagens são confirmados juntos. Uma falha reverte a página em curso. Um bloqueio transacional no PostgreSQL limita a execução a uma página por vez mesmo com vários processos FastAPI.

Cada ciclo revisita o catálogo autorizado e consulta o histórico desde o último corte concluído de cada chat, com 15 minutos de sobreposição. Chats novos recebem a primeira importação completa disponível. Uma revisão completa semanal por chat busca mensagens que chegaram tardiamente ao Store. O ciclo concluído volta à fila após cinco minutos. Falhas transitórias são repetidas com intervalo de 10 segundos a 15 minutos. Identidades ambíguas ou contatos sem confirmação exigida ficam registrados como ignorados no ciclo. O worker importa pelo caminho histórico. O histórico operacional continua no PostgreSQL, com atualizações via SSE.

Para diagnóstico, consultar `conexao_id`, `empresa_id`, `executar_em`, `ultimo_sucesso`, `falhas` e `erro` na tabela de sincronização. O cursor contém identificadores de chats comerciais e deve ficar restrito à operação autorizada.

### Publicação e retorno

1. Fazer backup verificável do PostgreSQL e confirmar as migrações até `20261201_central_eventos_antecipados.sql`.
2. Em janela autorizada, aplicar `20261202_central_sync_noweb.sql` com `psql -v ON_ERROR_STOP=1 -f backend/migrations/20261202_central_sync_noweb.sql` usando a conexão administrativa já configurada. A migração cria tabelas e índice, sem alteração nos registros existentes.
3. Publicar o backend e manter a flag desligada até validar o escopo de cada sessão lógica. Manter a configuração e os volumes da sessão institucional. Para empacotar o frontend existente, usar `npm ci` e `npm run build` em `dashboard/central_ui`.
4. Ativar a flag no piloto e parear uma conta comercial NOWEB autorizada. Fechar o CRM, interromper temporariamente backend e WAHA em momentos distintos, enviar mensagens entre dispositivos de homologação na janela autorizada e confirmar progresso, retomada, deduplicação e isolamento. Validar a paginação do digest instalado e a disponibilidade de mídia.
5. Para interromper a sincronização, desativar `ORION_WAHA_HISTORICO_ATIVO` e reciclar o backend na janela autorizada. Preservar as tabelas de progresso para retomada. Em rollback do código, manter a flag desligada para evitar reativar o importador anterior.

### Referências de arquitetura

- A transferência inicial, o armazenamento local e a atualização contínua são responsabilidades distintas no desenho multi-device. [Engenharia da Meta](https://engineering.fb.com/2021/07/14/security/whatsapp-multi-device/)
- O tratamento de eventos em segundo plano, a exclusão mútua por escopo e as retentativas são padrões adotados pelo Chatwoot. [Job de eventos WhatsApp do Chatwoot](https://github.com/chatwoot/chatwoot/blob/develop/app/jobs/webhooks/whatsapp_events_job.rb)
- A configuração do Store, os contratos HTTP e as janelas paginadas são referências da integração existente. [WAHA CORE, sessão NOWEB](https://github.com/devlikeapro/waha/blob/core/src/core/engines/noweb/session.noweb.core.ts), [NOWEB Store](https://waha.devlike.pro/docs/engines/noweb/), [API de chats](https://waha.devlike.pro/docs/how-to/chats/)
- O histórico inicial e o relacionamento entre LID e PN permanecem conceitos distintos. O Orion usa somente vínculos devolvidos pela sessão e mantém os IDs originais do provedor. [Histórico do Baileys](https://github.com/WhiskeySockets/Baileys/blob/master/src/Utils/history.ts), [Mapeamento LID do Baileys](https://github.com/WhiskeySockets/Baileys/blob/master/src/Signal/lid-mapping.ts)
