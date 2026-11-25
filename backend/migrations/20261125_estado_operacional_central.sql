BEGIN;
CREATE TABLE IF NOT EXISTS central_ack_pendente (
    empresa_id integer NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
    conexao_id integer NOT NULL REFERENCES conexoes_canais(id) ON DELETE CASCADE,
    sessao varchar(120) NOT NULL,
    mensagem_waha varchar(180) NOT NULL,
    ack integer NOT NULL CHECK (ack IN (-1,1,2,3,4)),
    registrado_em timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (empresa_id, sessao, mensagem_waha)
);
CREATE INDEX IF NOT EXISTS ix_central_ack_pendente_retencao ON central_ack_pendente (registrado_em);

CREATE TABLE IF NOT EXISTS central_conversa_leitura (
    empresa_id integer NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
    usuario_id integer NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    conversa_id integer NOT NULL REFERENCES conversas(id) ON DELETE CASCADE,
    ultima_mensagem_id integer NOT NULL,
    PRIMARY KEY (empresa_id, usuario_id, conversa_id)
);
COMMIT;
