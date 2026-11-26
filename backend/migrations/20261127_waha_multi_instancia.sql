BEGIN;

CREATE TABLE IF NOT EXISTS waha_capacidade (
    sessao_crm varchar(120) PRIMARY KEY,
    conexao_id integer UNIQUE REFERENCES conexoes_canais(id) ON DELETE RESTRICT,
    CONSTRAINT waha_capacidade_alias CHECK (
        sessao_crm ~ '^orion-waha:[a-zA-Z0-9_-]{1,48}:[a-zA-Z0-9_-]{1,48}$'
    )
);

COMMIT;
