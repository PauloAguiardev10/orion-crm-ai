BEGIN;

ALTER TABLE especialistas
    ADD COLUMN IF NOT EXISTS somente_atendimento_manual boolean NOT NULL DEFAULT FALSE;

CREATE UNIQUE INDEX IF NOT EXISTS uq_especialistas_empresa_usuario
    ON especialistas (empresa_id, usuario_id) WHERE usuario_id IS NOT NULL;

CREATE OR REPLACE FUNCTION orion_vincular_usuario_comercial()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.empresa_id IS NOT NULL AND NEW.status = 'ativo'
       AND NEW.nivel IN ('vendedor', 'usuario') THEN
        INSERT INTO especialistas (empresa_id, usuario_id, nome, somente_atendimento_manual)
        VALUES (NEW.empresa_id, NEW.id, COALESCE(NULLIF(btrim(NEW.nome), ''), 'Usuário #' || NEW.id), TRUE)
        ON CONFLICT (empresa_id, usuario_id) WHERE usuario_id IS NOT NULL DO NOTHING;
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS orion_vincular_usuario_comercial ON usuarios;
CREATE TRIGGER orion_vincular_usuario_comercial
AFTER INSERT OR UPDATE OF empresa_id, nivel, status ON usuarios
FOR EACH ROW EXECUTE FUNCTION orion_vincular_usuario_comercial();

INSERT INTO especialistas (empresa_id, usuario_id, nome, somente_atendimento_manual)
SELECT empresa_id, id, COALESCE(NULLIF(btrim(nome), ''), 'Usuário #' || id), TRUE
FROM usuarios
WHERE empresa_id IS NOT NULL AND status = 'ativo' AND nivel IN ('vendedor', 'usuario')
ON CONFLICT (empresa_id, usuario_id) WHERE usuario_id IS NOT NULL DO NOTHING;

COMMIT;
