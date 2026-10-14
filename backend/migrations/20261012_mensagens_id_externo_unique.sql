-- Protecao contra duplicidade de mensagens WAHA.
-- Executar somente apos backup e validacao em banco de teste.

CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS
    ux_mensagens_empresa_conversa_id_externo
ON public.mensagens (
    empresa_id,
    conversa_id,
    mensagem_id_externo
)
WHERE mensagem_id_externo IS NOT NULL;
