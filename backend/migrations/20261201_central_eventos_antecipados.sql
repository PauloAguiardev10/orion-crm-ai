BEGIN;

CREATE TABLE IF NOT EXISTS central_eventos_mensagem_pendentes (
    conexao_id integer NOT NULL REFERENCES conexoes_canais(id) ON DELETE CASCADE,
    alvo varchar(180) NOT NULL,
    chave varchar(24) NOT NULL,
    tipo varchar(32) NOT NULL,
    instante double precision NOT NULL,
    corpo text,
    registrado_em timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (conexao_id, alvo, chave)
);
CREATE INDEX IF NOT EXISTS ix_central_eventos_mensagem_pendentes_expiracao
ON central_eventos_mensagem_pendentes (registrado_em);

COMMIT;
