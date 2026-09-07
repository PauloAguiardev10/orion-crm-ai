BEGIN;

CREATE TABLE IF NOT EXISTS empresa_atendimento_config (
    id SERIAL PRIMARY KEY,

    empresa_id INTEGER NOT NULL UNIQUE,

    descricao_empresa TEXT,

    whatsapp_comercial VARCHAR(80),
    email_comercial VARCHAR(150),

    site TEXT,
    instagram_url TEXT,
    facebook_url TEXT,

    horario_atendimento TEXT,
    regiao_atendimento TEXT,

    informacoes_comerciais TEXT,
    observacoes_atendimento TEXT,

    responsavel_leads VARCHAR(150),
    whatsapp_notificacao VARCHAR(80),
    email_notificacao VARCHAR(150),

    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_empresa_atendimento_config_empresa
        FOREIGN KEY (empresa_id)
        REFERENCES empresas(id)
        ON DELETE CASCADE
);
COMMIT;
