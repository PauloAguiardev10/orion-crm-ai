BEGIN;

CREATE TABLE IF NOT EXISTS central_sync_noweb (
    conexao_id integer PRIMARY KEY REFERENCES conexoes_canais(id) ON DELETE CASCADE,
    empresa_id integer NOT NULL,
    sessao text NOT NULL,
    escopo text NOT NULL,
    cursor jsonb NOT NULL DEFAULT '{}'::jsonb,
    executar_em timestamptz NOT NULL DEFAULT now(),
    ultimo_sucesso timestamptz,
    falhas integer NOT NULL DEFAULT 0,
    erro text
);

CREATE INDEX IF NOT EXISTS ix_central_sync_noweb_execucao
    ON central_sync_noweb (executar_em, conexao_id);

CREATE TABLE IF NOT EXISTS central_sync_noweb_chats (
    conexao_id integer NOT NULL REFERENCES central_sync_noweb(conexao_id) ON DELETE CASCADE,
    chat text NOT NULL,
    ate bigint NOT NULL,
    ultima_varredura_completa bigint NOT NULL,
    PRIMARY KEY (conexao_id, chat)
);

COMMIT;
