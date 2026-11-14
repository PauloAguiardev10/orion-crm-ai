BEGIN;

ALTER TABLE conexoes_canais
    ADD COLUMN IF NOT EXISTS sessao_waha VARCHAR(120),
    ADD COLUMN IF NOT EXISTS especialista_id INTEGER;

CREATE UNIQUE INDEX IF NOT EXISTS
    uq_conexoes_canais_sessao_waha
ON conexoes_canais (sessao_waha)
WHERE sessao_waha IS NOT NULL;

CREATE INDEX IF NOT EXISTS
    ix_conexoes_canais_empresa_especialista
ON conexoes_canais (empresa_id, especialista_id);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_conexoes_canais_especialista_empresa'
          AND conrelid = 'conexoes_canais'::regclass
    ) THEN
        ALTER TABLE conexoes_canais
        ADD CONSTRAINT fk_conexoes_canais_especialista_empresa
        FOREIGN KEY (empresa_id, especialista_id)
        REFERENCES especialistas (empresa_id, id)
        ON DELETE RESTRICT;
    END IF;
END
$$;

COMMIT;
