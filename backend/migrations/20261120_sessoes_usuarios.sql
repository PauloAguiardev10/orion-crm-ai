
-- Orion CRM AI
-- Sessoes persistentes de autenticacao
-- Nao altera usuarios, empresas ou Follow-up.

CREATE TABLE IF NOT EXISTS sessoes_usuarios (
    id BIGSERIAL PRIMARY KEY,

    usuario_id INTEGER NOT NULL
        REFERENCES usuarios(id) ON DELETE CASCADE,

    token_hash CHAR(64) NOT NULL UNIQUE,

    criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    expira_em TIMESTAMPTZ NOT NULL,

    revogado_em TIMESTAMPTZ,

    CONSTRAINT ck_sessoes_validade
        CHECK (expira_em > criado_em)
);

CREATE INDEX IF NOT EXISTS ix_sessoes_usuarios_usuario
    ON sessoes_usuarios (usuario_id);

CREATE INDEX IF NOT EXISTS ix_sessoes_usuarios_validade
    ON sessoes_usuarios (expira_em)
    WHERE revogado_em IS NULL;
