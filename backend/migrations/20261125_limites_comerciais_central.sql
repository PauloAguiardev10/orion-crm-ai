BEGIN;

CREATE OR REPLACE FUNCTION orion_limite_plano(plano_atual text, recurso text)
RETURNS integer LANGUAGE sql IMMUTABLE AS $$
    SELECT CASE upper(btrim(plano_atual))
        WHEN 'LITE' THEN CASE recurso WHEN 'usuarios' THEN 2 WHEN 'conexoes' THEN 1 END
        WHEN 'PRO' THEN CASE recurso WHEN 'usuarios' THEN 5 WHEN 'conexoes' THEN 2 END
        WHEN 'PREMIUM' THEN CASE recurso WHEN 'usuarios' THEN 10 WHEN 'conexoes' THEN 5 END
    END
$$;

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
        IF lower(btrim(coalesce(NEW.canal, ''))) <> 'whatsapp' THEN RETURN NEW; END IF;
        IF TG_OP = 'UPDATE' THEN
            IF NEW.empresa_id IS NOT DISTINCT FROM OLD.empresa_id
               AND lower(btrim(coalesce(OLD.canal, ''))) = 'whatsapp' THEN RETURN NEW; END IF;
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
            AND lower(btrim(coalesce(c.canal, ''))) = 'whatsapp';
    END IF;
    IF utilizados >= limite THEN
        RAISE EXCEPTION 'Franquia do plano atingida' USING
            ERRCODE = '23514', CONSTRAINT = 'orion_limite_' || recurso;
    END IF;
    RETURN NEW;
END
$$;

DROP TRIGGER IF EXISTS orion_franquia_usuarios ON usuarios;
CREATE TRIGGER orion_franquia_usuarios BEFORE INSERT OR UPDATE OF empresa_id, nivel ON usuarios
FOR EACH ROW EXECUTE FUNCTION orion_validar_franquia_central();

DROP TRIGGER IF EXISTS orion_franquia_conexoes ON conexoes_canais;
CREATE TRIGGER orion_franquia_conexoes BEFORE INSERT OR UPDATE OF empresa_id, canal ON conexoes_canais
FOR EACH ROW EXECUTE FUNCTION orion_validar_franquia_central();

COMMIT;
