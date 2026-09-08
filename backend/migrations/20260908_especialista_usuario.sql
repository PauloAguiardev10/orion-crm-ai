BEGIN;

-- ============================================================
-- 1. IDENTIDADE DO USUARIO NO ESPECIALISTA
-- ============================================================

ALTER TABLE especialistas
ADD COLUMN IF NOT EXISTS usuario_id INTEGER;


-- ============================================================
-- 2. CHAVE CANDIDATA MULTIEMPRESA EM USUARIOS
-- Necessaria para a FK composta.
-- ============================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'uq_usuarios_empresa_id_id'
          AND conrelid = 'usuarios'::regclass
    ) THEN
        ALTER TABLE usuarios
        ADD CONSTRAINT uq_usuarios_empresa_id_id
        UNIQUE (empresa_id, id);
    END IF;
END
$$;


-- ============================================================
-- 3. BACKFILL SEGURO DOS ESPECIALISTAS EXISTENTES
--
-- Vincula somente quando:
--   - pertencem a mesma empresa;
--   - nome do especialista corresponde ao nome OU login;
--   - existe exatamente um usuario correspondente.
--
-- Casos ambiguos ou sem correspondencia permanecem NULL.
-- ============================================================

WITH correspondencias AS (
    SELECT
        e.id AS especialista_id,
        e.empresa_id,
        MIN(u.id) AS usuario_id,
        COUNT(DISTINCT u.id) AS quantidade

    FROM especialistas e

    INNER JOIN usuarios u
        ON u.empresa_id = e.empresa_id
       AND u.status = 'ativo'
       AND (
            LOWER(TRIM(COALESCE(u.nome, ''))) =
            LOWER(TRIM(COALESCE(e.nome, '')))

            OR

            LOWER(TRIM(COALESCE(u.usuario, ''))) =
            LOWER(TRIM(COALESCE(e.nome, '')))
       )

    WHERE e.usuario_id IS NULL

    GROUP BY
        e.id,
        e.empresa_id
)

UPDATE especialistas e

SET usuario_id = c.usuario_id

FROM correspondencias c

WHERE e.id = c.especialista_id
  AND e.empresa_id = c.empresa_id
  AND c.quantidade = 1;


-- ============================================================
-- 4. INDICE DE CONSULTA
-- ============================================================

CREATE INDEX IF NOT EXISTS
ix_especialistas_usuario_id
ON especialistas (usuario_id);


-- ============================================================
-- 5. UM USUARIO NAO PODE REPRESENTAR DOIS ESPECIALISTAS
-- DA MESMA EMPRESA
-- ============================================================

CREATE UNIQUE INDEX IF NOT EXISTS
uq_especialistas_empresa_usuario
ON especialistas (empresa_id, usuario_id)
WHERE usuario_id IS NOT NULL;


-- ============================================================
-- 6. FK MULTIEMPRESA
--
-- Impede vincular especialista de uma empresa
-- a usuario pertencente a outro tenant.
-- ============================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_especialistas_empresa_usuario'
          AND conrelid = 'especialistas'::regclass
    ) THEN
        ALTER TABLE especialistas
        ADD CONSTRAINT fk_especialistas_empresa_usuario
        FOREIGN KEY (empresa_id, usuario_id)
        REFERENCES usuarios (empresa_id, id)
        ON DELETE RESTRICT;
    END IF;
END
$$;


COMMIT;
