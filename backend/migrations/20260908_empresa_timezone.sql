BEGIN;

ALTER TABLE empresas
ADD COLUMN IF NOT EXISTS timezone VARCHAR(80);

UPDATE empresas
SET timezone = 'America/Fortaleza'
WHERE timezone IS NULL
   OR BTRIM(timezone) = '';

ALTER TABLE empresas
ALTER COLUMN timezone SET DEFAULT 'America/Fortaleza';

ALTER TABLE empresas
ALTER COLUMN timezone SET NOT NULL;

COMMIT;
