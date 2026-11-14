BEGIN;

-- Uma solicitacao de envio humano so pode ser reservada
-- uma vez por empresa e conversa.

CREATE UNIQUE INDEX IF NOT EXISTS
uq_mensagens_humanas_solicitacao
ON mensagens (
    empresa_id,
    conversa_id,
    mensagem_id_externo
)
WHERE remetente = 'humano'
  AND from_me IS TRUE
  AND mensagem_id_externo IS NOT NULL;

COMMIT;
