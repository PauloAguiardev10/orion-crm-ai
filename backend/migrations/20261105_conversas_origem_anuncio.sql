-- Orion CRM AI - Proveniencia tecnica de anuncio Click-to-WhatsApp
-- Aplicar somente apos backup e testes em banco isolado.
-- Nao confundir com origem_aquisicao informada pelo cliente.

BEGIN;

ALTER TABLE public.conversas
ADD COLUMN IF NOT EXISTS anuncio_referral_confirmado BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE public.conversas
ADD COLUMN IF NOT EXISTS anuncio_referral_id VARCHAR(180);

ALTER TABLE public.conversas
ADD COLUMN IF NOT EXISTS anuncio_referral_recebido_em TIMESTAMPTZ;

COMMIT;
