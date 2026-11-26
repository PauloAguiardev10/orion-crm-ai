BEGIN;

ALTER TABLE conexoes_canais
    ADD COLUMN IF NOT EXISTS pareamento_waha_pendente boolean NOT NULL DEFAULT FALSE;

CREATE TABLE IF NOT EXISTS waha_numeros_verificados (
    numero_e164 varchar(16) PRIMARY KEY CHECK (numero_e164 ~ '^[+][1-9][0-9]{7,14}$'),
    conexao_id integer NOT NULL UNIQUE REFERENCES conexoes_canais(id) ON DELETE RESTRICT,
    verificado_em timestamptz NOT NULL DEFAULT now()
);

-- A sessao institucional legada continua no fluxo existente durante o inventario.
UPDATE conexoes_canais c
SET operacao_suspensa = TRUE
WHERE c.provedor = 'waha' AND c.canal = 'whatsapp'
  AND c.gerenciada_crm AND NOT c.sofia_institucional AND c.ativo
  AND NOT EXISTS (SELECT 1 FROM waha_numeros_verificados n WHERE n.conexao_id = c.id);

COMMIT;
