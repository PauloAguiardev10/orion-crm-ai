# Operação do scheduler de Follow-up Automático

O scheduler roda em processo próprio, no diretório `backend`, com o Python do ambiente virtual do backend. O ponto de entrada é `python -m app.workers.followup_scheduler`. O intervalo padrão é de 60 segundos.

Para uma VPS com systemd, uma unidade dedicada mantém o processo independente do FastAPI. Exemplo para adaptar aos caminhos e à conta de serviço da VPS:

```ini
[Unit]
Description=Orion CRM AI - Follow-up Automático
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=CONTA_DO_SERVICO
WorkingDirectory=/CAMINHO/ORION/backend
EnvironmentFile=/etc/orion/followup-scheduler.conf
ExecStart=/CAMINHO/VENV/bin/python -m app.workers.followup_scheduler
Restart=on-failure
RestartSec=10s

[Install]
WantedBy=multi-user.target
```

O processo precisa receber estas variáveis antes de iniciar. O backend e o scheduler devem apontar para o mesmo banco.

| Variável | Valor para validação operacional sem disparo | Efeito |
| --- | --- | --- |
| `FOLLOWUP_EMPRESA_IDS` | IDs reais das empresas autorizadas, separados por vírgula | Limita o ciclo às empresas listadas. |
| `FOLLOWUP_AGENDAMENTO_ATIVO` | `1` no scheduler e no processo do FastAPI | Registra o marco da primeira resposta confirmada e permite criar agendamentos. |
| `FOLLOWUP_WORKER_ATIVO` | `1` no scheduler | Libera a execução do processo periódico. |
| `FOLLOWUP_ENVIO_REAL_ATIVO` | `0` no scheduler | Mantém o transporte real bloqueado enquanto o ciclo agenda e recupera reservas. |
| `DATABASE_URL` | Fornecida pela configuração protegida do ambiente | Seleciona o banco do CRM. |

Após instalação e autorização separadas, consulte `systemctl is-enabled orion-followup-scheduler.service`, `systemctl is-active orion-followup-scheduler.service` e `journalctl -u orion-followup-scheduler.service`. Confirme ciclos periódicos por empresa, recuperação de reservas e o registro de envio real desativado. Este exemplo documenta a configuração esperada. O serviço instalado, os caminhos, a conta e a seleção de empresas ainda precisam ser confirmados na VPS.

## Preparação da versão

1. Prepare uma branch limpa a partir da revisão em produção. Inclua somente os serviços de Follow-up, a integração compartilhada de mensagens, o scheduler, o teste e este runbook. Selecione separadamente os trechos de `backend/main.py`. A inclusão da rota da Central WhatsApp pertence à Central. Em `models.py`, as chaves compostas correspondem ao schema de Follow-up. A coluna `Conversa.especialista_id` pertence à integração da Central.
2. Revise o diff preparado e rode a suíte no PostgreSQL isolado a partir da própria branch candidata. Depois da autorização, faça o commit, publique a branch em revisão e registre o SHA aprovado. Use esse SHA na VPS.
3. Antes da instalação, registre o SHA atual, as unidades e a configuração protegida em uso. Gere backup protegido do PostgreSQL e confirme sua restauração em instância isolada. Confira no catálogo o schema de agendamentos, configurações, conexões, idempotência e as chaves compostas. Aplique qualquer migração necessária somente em uma janela autorizada.
4. Na primeira instalação, mantenha `FOLLOWUP_AGENDAMENTO_ATIVO=0` no backend e no scheduler, `FOLLOWUP_WORKER_ATIVO=0` e `FOLLOWUP_ENVIO_REAL_ATIVO=0`. Mantenha a unidade do scheduler parada. Valide o backend, a assinatura WAHA e a topologia de acesso antes de liberar os ciclos. Restrinja `/mensagem` a consumidores internos autorizados e confirme que a porta direta do FastAPI segue a mesma restrição.
5. Configure a WAHA para emitir `message.any` com assinatura e configure `WAHA_WEBHOOK_HMAC_KEY` no backend via armazenamento protegido. Valide todos os webhooks da instalação antes de exigir a assinatura. Depois, habilite agendamento e worker somente para a empresa de teste, mantendo `FOLLOWUP_ENVIO_REAL_ATIVO=0`. Reinicie os processos que receberam novas flags e confira os ciclos e os agendamentos gerados.

## Verificação com um número autorizado

- Use empresa e sessão de teste dedicadas e confirme que a sessão, a conexão e a conversa têm o mesmo vínculo. `FOLLOWUP_EMPRESA_IDS` filtra empresas. Para limitar por número, use uma empresa de teste sem outros contatos elegíveis ou um bloqueio de destinatário no ponto de saída.
- Confira os eventos assinados de texto, áudio, imagem, reação e saída pelo aplicativo. Confirme `fromMe`, `source`, o identificador, a sessão e o chat na versão instalada. Verifique que um evento adulterado é rejeitado e que eventos duplicados não criam novos registros.
- Com envio desligado, confira os cinco minutos de espera e o cancelamento por resposta do cliente ou contato do vendedor pelo aplicativo. Confira que tentativas reservadas ainda não iniciadas são canceladas.
- Somente com autorização separada, limite o cenário a uma tentativa para o número autorizado. Confira a aceitação HTTP, a entrega no aparelho e a ausência de outros destinatários. Volte o envio para `0` ao terminar e reinicie o scheduler para aplicar a flag.

## Rollback

Pare a unidade do scheduler, mantenha as três flags em `0` e restaure o SHA anterior e a configuração compatível dos processos envolvidos. Valide o webhook e o backend após o reinício. Preserve o banco e revise as tentativas reservadas, enviadas e inconclusivas antes de retomar. Caso a reversão exija restauração de banco, trate-a como operação separada e avalie as gravações ocorridas após o backup.


## Comandos para a janela aprovada

Adapte os caminhos e nomes de serviços à VPS. Use a configuração protegida do ambiente para credenciais. Após aprovação do commit e push, recupere a revisão com estes comandos:

    git fetch origin followup/candidato-implantacao
    git worktree add --detach /opt/orion/releases/FOLLOWUP_SHA SHA_APROVADO
    cd /opt/orion/releases/FOLLOWUP_SHA
    python3 -m venv .venv
    .venv/bin/python -m pip install -r requirements.txt
    .venv/bin/python -m pip check

Faça backup e ensaie a restauração em um banco separado e vazio antes da instalação:

    umask 077
    pg_dump --dbname='service=orion_producao' --format=custom --file=/CAMINHO_PROTEGIDO/orion-pre-followup.dump
    pg_restore --list /CAMINHO_PROTEGIDO/orion-pre-followup.dump
    pg_restore --exit-on-error --dbname='service=orion_restore_isolado' /CAMINHO_PROTEGIDO/orion-pre-followup.dump

Instale a unidade do exemplo acima mantendo as três flags em 0 no backend e no scheduler:

    sudoedit /etc/orion/followup-scheduler.conf
    sudoedit /etc/systemd/system/orion-followup-scheduler.service
    sudo systemd-analyze verify /etc/systemd/system/orion-followup-scheduler.service
    sudo systemctl daemon-reload
    sudo systemctl disable --now orion-followup-scheduler.service
    systemctl is-active orion-followup-scheduler.service
    systemctl is-enabled orion-followup-scheduler.service

Após confirmar o schema, a proteção das rotas e o SHA instalado, reinicie apenas a unidade existente do FastAPI (sudo systemctl restart UNIDADE_FASTAPI.service). A etapa posterior de observação usa sudo systemctl enable --now orion-followup-scheduler.service com agendamento e worker em 1 e envio real em 0. Consulte journalctl -u orion-followup-scheduler.service --since today. Em rollback, volte as flags para 0, pare e desabilite o scheduler, restaure o SHA e a configuração anteriores e reinicie a unidade FastAPI.

## Inventário de schema

O candidato alinha três constraints no ORM aos nomes das migrações existentes:

- uq_conversas_empresa_id_id em conversas (empresa_id, id).
- uq_leads_empresa_id_id em leads (empresa_id, id).
- uq_mensagens_empresa_conversa_id em mensagens (empresa_id, conversa_id, id).

A proteção de saída manual usa campos existentes em mensagens. Confira em modo somente leitura as tabelas, colunas, chaves compostas, os índices de idempotência e a unicidade da tentativa por empresa, lead e número. Compare com estes scripts existentes em backend/migrations:

- 20260908_especialista_usuario.sql, 20261012_mensagens_id_externo_unique.sql e 20261013_mensagens_controle_processamento.sql.
- 20261031_followup_agendamentos.sql, 20261101_leads_entrada_followup.sql e 20261103_followup_autorizacao_envio.sql.
- 20261101_mensagens_ids_waha.sql e 20261105_conversas_origem_anuncio.sql.
- 20261110_conexoes_waha_vendedores.sql e 20261110_conversas_conexao_waha.sql.
- 20261111_mensagens_humanas_idempotencia.sql, 20261111_mensagens_reserva_vendedor.sql e 20261118_followup_configuracoes.sql.

O candidato não adiciona migrações. Se houver schema faltante, pare e aprove o delta separadamente. O backend chama Base.metadata.create_all na inicialização mesmo com as flags em 0. Confirme o schema antes do primeiro start e use um papel de runtime sem permissão efetiva de DDL.

## Acesso a /mensagem

O FastAPI registra POST /mensagem sem autenticação de rota. O webhook WAHA chama o manipulador internamente em Python. O caminho HTTP pode ficar fora da lista de rotas públicas sem interromper o webhook. Valide os consumidores HTTP existentes e preserve-os em uma entrada privada com controle de rede ou autenticação entre serviços. Restrinja o FastAPI a loopback, socket Unix ou rede privada acessível pelos consumidores aprovados.

Verifique externamente que um POST com JSON vazio em /mensagem e /mensagem/ recebe bloqueio do proxy, sem redirecionamento para a aplicação. Confirme também que o endereço ou a porta direta estão inacessíveis externamente. Um erro de validação do FastAPI indica que a chamada atravessou o perímetro. Valide o webhook assinado e as integrações internas separadamente.
