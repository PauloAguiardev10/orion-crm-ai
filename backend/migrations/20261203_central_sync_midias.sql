BEGIN;
CREATE TABLE IF NOT EXISTS central_sync_midias (
    mensagem_id integer PRIMARY KEY REFERENCES mensagens(id) ON DELETE CASCADE,
    empresa_id integer NOT NULL,
    conexao_id integer NOT NULL REFERENCES conexoes_canais(id) ON DELETE CASCADE,
    sessao text NOT NULL,
    chat text NOT NULL,
    id_waha text NOT NULL,
    executar_em timestamptz NOT NULL DEFAULT now(),
    falhas integer NOT NULL DEFAULT 0,
    erro text,
    concluido boolean NOT NULL DEFAULT false
);
CREATE INDEX IF NOT EXISTS ix_central_sync_midias_execucao
    ON central_sync_midias (executar_em, mensagem_id) WHERE NOT concluido;
COMMIT;
