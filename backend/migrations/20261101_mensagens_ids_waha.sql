-- Orion CRM AI - Identificadores de mensagens WAHA
-- Migracao local. Nao executar diretamente em producao.
-- Validar previamente em banco de homologacao.

BEGIN;

ALTER TABLE public.mensagens
    ADD COLUMN IF NOT EXISTS mensagem_id_waha VARCHAR(180);

ALTER TABLE public.mensagens
    ADD COLUMN IF NOT EXISTS sessao_waha VARCHAR(120);

CREATE UNIQUE INDEX IF NOT EXISTS
    ux_mensagens_empresa_sessao_id_waha
ON public.mensagens (
    empresa_id,
    sessao_waha,
    mensagem_id_waha
)
WHERE
    mensagem_id_waha IS NOT NULL
    AND sessao_waha IS NOT NULL;

COMMIT;
