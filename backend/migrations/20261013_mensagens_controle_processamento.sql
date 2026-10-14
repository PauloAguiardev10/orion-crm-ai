-- Controle persistente do processamento de mensagens WAHA.
-- Executar somente apos backup e testes em banco de homologacao.

ALTER TABLE public.mensagens
    ADD COLUMN IF NOT EXISTS status_processamento VARCHAR(30),
    ADD COLUMN IF NOT EXISTS processado_em TIMESTAMP,
    ADD COLUMN IF NOT EXISTS status_envio VARCHAR(40);

COMMENT ON COLUMN public.mensagens.status_processamento
    IS 'Estado do processamento da mensagem pelo backend';

COMMENT ON COLUMN public.mensagens.processado_em
    IS 'Momento em que o processamento foi concluido';

COMMENT ON COLUMN public.mensagens.status_envio
    IS 'Resultado da tentativa de envio pela API WAHA';
