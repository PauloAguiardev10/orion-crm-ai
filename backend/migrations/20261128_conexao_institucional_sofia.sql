BEGIN;

ALTER TABLE conexoes_canais
    ADD COLUMN IF NOT EXISTS sofia_institucional boolean NOT NULL DEFAULT FALSE;

ALTER TABLE conexoes_canais
    DROP CONSTRAINT IF EXISTS ck_conexao_sofia_institucional,
    ADD CONSTRAINT ck_conexao_sofia_institucional CHECK (
        NOT sofia_institucional OR
        (canal = 'whatsapp' AND provedor = 'waha' AND sofia_ativa)
    );

CREATE UNIQUE INDEX IF NOT EXISTS uq_conexao_sofia_institucional_empresa
ON conexoes_canais(empresa_id) WHERE sofia_institucional;

CREATE OR REPLACE FUNCTION orion_validar_franquia_central()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    recurso text;
    plano_atual text;
    limite integer;
    utilizados bigint;
BEGIN
    IF TG_TABLE_NAME = 'usuarios' THEN
        IF lower(btrim(coalesce(NEW.nivel, ''))) = 'orion_admin' THEN RETURN NEW; END IF;
        IF TG_OP = 'UPDATE' THEN
            IF NEW.empresa_id IS NOT DISTINCT FROM OLD.empresa_id
               AND lower(btrim(coalesce(OLD.nivel, ''))) <> 'orion_admin' THEN RETURN NEW; END IF;
        END IF;
        recurso := 'usuarios';
    ELSE
        IF lower(btrim(coalesce(NEW.canal, ''))) <> 'whatsapp' OR NEW.sofia_institucional THEN RETURN NEW; END IF;
        IF TG_OP = 'UPDATE' THEN
            IF NEW.empresa_id IS NOT DISTINCT FROM OLD.empresa_id
               AND lower(btrim(coalesce(OLD.canal, ''))) = 'whatsapp'
               AND NOT OLD.sofia_institucional THEN RETURN NEW; END IF;
        END IF;
        recurso := 'conexoes';
    END IF;

    -- Uma nova versão da linha serializa admissões e mudanças de plano,
    -- inclusive com isolamento superior a READ COMMITTED.
    UPDATE empresas AS e SET plano = e.plano WHERE e.id = NEW.empresa_id
    RETURNING e.plano INTO plano_atual;
    limite := orion_limite_plano(plano_atual, recurso);
    IF limite IS NULL THEN
        RAISE EXCEPTION 'Plano inválido para uma nova vaga' USING
            ERRCODE = '23514', CONSTRAINT = 'orion_plano_invalido';
    END IF;

    IF recurso = 'usuarios' THEN
        SELECT count(*) INTO utilizados FROM usuarios u WHERE u.empresa_id = NEW.empresa_id
            AND lower(btrim(coalesce(u.nivel, ''))) <> 'orion_admin';
    ELSE
        SELECT count(*) INTO utilizados FROM conexoes_canais c WHERE c.empresa_id = NEW.empresa_id
            AND lower(btrim(coalesce(c.canal, ''))) = 'whatsapp' AND NOT c.sofia_institucional;
    END IF;
    IF utilizados >= limite THEN
        RAISE EXCEPTION 'Franquia do plano atingida' USING
            ERRCODE = '23514', CONSTRAINT = 'orion_limite_' || recurso;
    END IF;
    RETURN NEW;
END
$$;

DROP TRIGGER IF EXISTS orion_franquia_conexoes ON conexoes_canais;
CREATE TRIGGER orion_franquia_conexoes
BEFORE INSERT OR UPDATE OF empresa_id, canal, sofia_institucional ON conexoes_canais
FOR EACH ROW EXECUTE FUNCTION orion_validar_franquia_central();

COMMIT;
