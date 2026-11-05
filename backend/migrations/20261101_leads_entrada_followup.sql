-- Orion CRM AI - data persistente de entrada para follow-up
-- Executar somente apos backup e validacao em homologacao.

BEGIN;

ALTER TABLE public.leads
ADD COLUMN IF NOT EXISTS entrada_followup_em TIMESTAMPTZ;

COMMIT;
