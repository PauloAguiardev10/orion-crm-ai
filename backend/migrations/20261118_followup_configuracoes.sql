-- Configuracoes do Follow-up Automatico - Orion CRM AI
-- Esta migracao cria estruturas. Nao ativa disparos.

CREATE TABLE IF NOT EXISTS followup_configuracoes (
    id BIGSERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL UNIQUE
        REFERENCES empresas(id) ON DELETE RESTRICT,
    ativo BOOLEAN NOT NULL DEFAULT FALSE,
    modo VARCHAR(20) NOT NULL DEFAULT 'padrao_orion',
    quantidade_tentativas INTEGER NOT NULL DEFAULT 3,
    fuso_horario VARCHAR(80) NOT NULL DEFAULT 'America/Sao_Paulo',
    segunda_sexta_inicio TIME NOT NULL DEFAULT '08:00',
    segunda_sexta_fim TIME NOT NULL DEFAULT '18:00',
    sabado_ativo BOOLEAN NOT NULL DEFAULT TRUE,
    sabado_inicio TIME NOT NULL DEFAULT '08:00',
    sabado_fim TIME NOT NULL DEFAULT '12:00',
    domingo_ativo BOOLEAN NOT NULL DEFAULT FALSE,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_followup_modo
        CHECK (modo IN ('padrao_orion', 'personalizado')),
    CONSTRAINT ck_followup_quantidade
        CHECK (quantidade_tentativas BETWEEN 1 AND 10),
    CONSTRAINT ck_followup_semana_horarios
        CHECK (segunda_sexta_inicio < segunda_sexta_fim),
    CONSTRAINT ck_followup_sabado_horarios
        CHECK (sabado_inicio < sabado_fim)
);

CREATE TABLE IF NOT EXISTS followup_modelos_mensagem (
    id BIGSERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL
        REFERENCES empresas(id) ON DELETE RESTRICT,
    numero_tentativa INTEGER NOT NULL,
    intervalo_minutos INTEGER NOT NULL,
    texto TEXT NOT NULL,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_followup_modelo_empresa_tentativa
        UNIQUE (empresa_id, numero_tentativa),
    CONSTRAINT ck_followup_modelo_tentativa
        CHECK (numero_tentativa BETWEEN 1 AND 10),
    CONSTRAINT ck_followup_modelo_intervalo
        CHECK (intervalo_minutos BETWEEN 1 AND 43200),
    CONSTRAINT ck_followup_modelo_texto
        CHECK (length(trim(texto)) BETWEEN 1 AND 4000)
);

CREATE INDEX IF NOT EXISTS ix_followup_modelos_empresa
    ON followup_modelos_mensagem (empresa_id);

-- Modelos recomendados pela Orion Systems.
-- Cadastra modelos apenas para empresas que possuem configuracao.
-- Nao ativa o envio automatico.

INSERT INTO followup_modelos_mensagem
    (empresa_id, numero_tentativa, intervalo_minutos, texto)
SELECT
    c.empresa_id,
    padrao.numero_tentativa,
    padrao.intervalo_minutos,
    padrao.texto
FROM followup_configuracoes AS c
CROSS JOIN (
    VALUES
        (1, 180, 'Olá! Tudo bem? Vi que ainda não conseguimos continuar nossa conversa. Gostaria de saber mais sobre como podemos ajudar?'),
        (2, 1440, 'Olá! Passando para saber se ainda podemos ajudar você. Se tiver alguma dúvida, estamos à disposição.'),
        (3, 2880, 'Olá! Este é nosso último contato por enquanto. Se precisar de ajuda futuramente, será um prazer conversar com você.')
) AS padrao(numero_tentativa, intervalo_minutos, texto)
ON CONFLICT (empresa_id, numero_tentativa) DO NOTHING;

-- Inicializa as configuracoes das empresas existentes.
-- O Follow-up permanece desativado ate a ativacao autorizada.

INSERT INTO followup_configuracoes (empresa_id)
SELECT id
FROM empresas
ON CONFLICT (empresa_id) DO NOTHING;

-- Cadastra os modelos Orion para as empresas inicializadas.
INSERT INTO followup_modelos_mensagem
    (empresa_id, numero_tentativa, intervalo_minutos, texto)
SELECT
    c.empresa_id,
    p.numero_tentativa,
    p.intervalo_minutos,
    p.texto
FROM followup_configuracoes c
CROSS JOIN (
    VALUES
        (1, 180, 'Olá! Tudo bem? Vi que ainda não conseguimos continuar nossa conversa. Gostaria de saber mais sobre como podemos ajudar?'),
        (2, 1440, 'Olá! Passando para saber se ainda podemos ajudar você. Se tiver alguma dúvida, estamos à disposição.'),
        (3, 2880, 'Olá! Este é nosso último contato por enquanto. Se precisar de ajuda futuramente, será um prazer conversar com você.')
) AS p(numero_tentativa, intervalo_minutos, texto)
ON CONFLICT (empresa_id, numero_tentativa) DO NOTHING;
