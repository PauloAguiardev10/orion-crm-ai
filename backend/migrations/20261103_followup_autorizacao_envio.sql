-- Orion CRM AI - Autorizacao de envio do follow-up
-- Migracao incremental.
-- Aplicar somente apos validacao no PostgreSQL isolado.
-- Nao modifica a migracao original de 20261031.

BEGIN;

ALTER TABLE public.followup_agendamentos
ADD COLUMN IF NOT EXISTS envio_iniciado_em TIMESTAMPTZ;

COMMIT;
