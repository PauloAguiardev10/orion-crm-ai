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
4. Em janela autorizada, aplicar com interrupção em erro, nesta ordem, `20261125_gestao_conexoes_waha.sql`, `20261125_estado_operacional_central.sql` e `20261125_limites_comerciais_central.sql`. Confirmar as duas tabelas operacionais, a função de limites e os gatilhos de usuários e conexões. Verificar que o papel do aplicativo pode atualizar a coluna `empresas.plano` na transação de admissão, como exige o bloqueio da franquia. Só então publicar backend e dashboard com as duas flags desligadas.
5. Conferir login, escopos, conversas legadas da Forway e saúde da Sofia e do Follow-up. Homologar cada flag separadamente em sessão de teste autorizada, preservando a sessão atual.
6. Para voltar, desativar as flags e restaurar a revisão anterior do código. Manter as tabelas e colunas aditivas para preservar ACKs, leituras e configuração das conexões. Se for necessário voltar também à política anterior de franquias, remover somente os gatilhos em transação autorizada. A função de consulta pode permanecer. Para restauração integral, parar as escritas, preservar os dados produzidos desde o backup e testar a restauração em instância isolada antes do corte.

### Evidências exigidas antes da publicação

- Gerar o dump em formato custom com `pg_dump --format=custom` usando a conexão protegida já configurada no host. Arquivar o armazenamento privado de mídias com uma janela consistente com o dump e preservar a configuração protegida e o volume de sessão atual da WAHA. Não copiar esses arquivos para o GitHub.
- Validar cada artefato pelo checksum SHA-256 e catálogo do dump. Restaurar com `pg_restore --exit-on-error` em banco descartável e conferir tabelas, contagens, amostras referenciadas de mídia e vínculos da sessão Forway antes de autorizar o corte.
- Homologar texto, voz nativa, imagem, vídeo e documento em conversa dedicada. Verificar reprodução, ACK, deduplicação e acesso autorizado. Validar QR, provisionamento e segunda sessão apenas se a edição instalada suportar a operação, sem alterar o pareamento da Forway.
- Confirmar que a Sofia responde somente onde habilitada e que o Follow-up preserva sessão, agenda, cancelamento por atendimento humano e tratamento de reservas. Não alterar as flags operacionais atuais da Sofia ou do Follow-up sem validação no ambiente.
