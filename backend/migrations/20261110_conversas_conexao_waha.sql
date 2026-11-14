BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'uq_conexoes_canais_empresa_id_id'
          AND conrelid = 'conexoes_canais'::regclass
    ) THEN
        ALTER TABLE conexoes_canais
        ADD CONSTRAINT uq_conexoes_canais_empresa_id_id
        UNIQUE (empresa_id, id);
    END IF;
END
$$;

ALTER TABLE conversas
    ADD COLUMN IF NOT EXISTS conexao_canal_id INTEGER;

CREATE INDEX IF NOT EXISTS
    ix_conversas_empresa_conexao
ON conversas (empresa_id, conexao_canal_id);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_conversas_conexao_empresa'
          AND conrelid = 'conversas'::regclass
    ) THEN
        ALTER TABLE conversas
        ADD CONSTRAINT fk_conversas_conexao_empresa
        FOREIGN KEY (empresa_id, conexao_canal_id)
        REFERENCES conexoes_canais (empresa_id, id)
        ON DELETE RESTRICT;
    END IF;
END
$$;

COMMIT;
