BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'uq_especialistas_empresa_id_id'
          AND conrelid = 'especialistas'::regclass
    ) THEN
        ALTER TABLE especialistas
        ADD CONSTRAINT uq_especialistas_empresa_id_id
        UNIQUE USING INDEX uq_especialistas_empresa_id_id;
    END IF;
END
$$;

ALTER TABLE conversas
    ADD COLUMN IF NOT EXISTS especialista_id INTEGER;

CREATE INDEX IF NOT EXISTS ix_conversas_empresa_especialista
    ON conversas (empresa_id, especialista_id);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_conversas_especialista_empresa'
          AND conrelid = 'conversas'::regclass
    ) THEN
        ALTER TABLE conversas
        ADD CONSTRAINT fk_conversas_especialista_empresa
        FOREIGN KEY (empresa_id, especialista_id)
        REFERENCES especialistas (empresa_id, id)
        ON DELETE RESTRICT;
    END IF;
END
$$;

COMMIT;
