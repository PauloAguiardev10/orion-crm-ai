BEGIN;
ALTER TABLE mensagens ADD COLUMN IF NOT EXISTS central_resposta_waha varchar(180);
ALTER TABLE mensagens ADD COLUMN IF NOT EXISTS central_eventos jsonb;
ALTER TABLE conversas ADD COLUMN IF NOT EXISTS central_arquivada boolean NOT NULL DEFAULT FALSE;
ALTER TABLE conversas ADD COLUMN IF NOT EXISTS central_digitando_ate timestamptz;
COMMIT;
