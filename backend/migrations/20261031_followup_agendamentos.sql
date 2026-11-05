-- Orion CRM AI - Follow-up Automatico
-- Migracao local. Executar somente apos backup e testes em homologacao.

BEGIN;

-- Chaves candidatas para relacionamentos multiempresa.

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'uq_leads_empresa_id_id'
          AND conrelid = 'public.leads'::regclass
    ) THEN
        ALTER TABLE public.leads
        ADD CONSTRAINT uq_leads_empresa_id_id
        UNIQUE (empresa_id, id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'uq_conversas_empresa_id_id'
          AND conrelid = 'public.conversas'::regclass
    ) THEN
        ALTER TABLE public.conversas
        ADD CONSTRAINT uq_conversas_empresa_id_id
        UNIQUE (empresa_id, id);
    END IF;
END
$$;

-- Chave candidata para validar empresa e conversa da mensagem.

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'uq_mensagens_empresa_conversa_id'
          AND conrelid = 'public.mensagens'::regclass
    ) THEN
        ALTER TABLE public.mensagens
        ADD CONSTRAINT uq_mensagens_empresa_conversa_id
        UNIQUE (empresa_id, conversa_id, id);
    END IF;
END
$$;

CREATE TABLE IF NOT EXISTS public.followup_agendamentos (
    id BIGSERIAL PRIMARY KEY,

    empresa_id INTEGER NOT NULL,
    lead_id INTEGER NOT NULL,
    conversa_id INTEGER,

    numero_tentativa INTEGER NOT NULL DEFAULT 1,

    entrada_lead_em TIMESTAMPTZ NOT NULL,
    agendado_para TIMESTAMPTZ NOT NULL,

    status VARCHAR(30) NOT NULL DEFAULT 'pendente',
    tentativas_envio INTEGER NOT NULL DEFAULT 0,

    mensagem_id INTEGER,
    mensagem_id_externo VARCHAR(180),
    erro_envio TEXT,

    reservado_em TIMESTAMPTZ,
    reserva_token VARCHAR(100),
    reserva_expira_em TIMESTAMPTZ,

    criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    enviado_em TIMESTAMPTZ,
    cancelado_em TIMESTAMPTZ,

    CONSTRAINT fk_followup_empresa
        FOREIGN KEY (empresa_id)
        REFERENCES public.empresas(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_followup_lead_empresa
        FOREIGN KEY (empresa_id, lead_id)
        REFERENCES public.leads(empresa_id, id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_followup_conversa_empresa
        FOREIGN KEY (empresa_id, conversa_id)
        REFERENCES public.conversas(empresa_id, id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_followup_mensagem
        FOREIGN KEY (empresa_id, conversa_id, mensagem_id)
        REFERENCES public.mensagens(empresa_id, conversa_id, id)
        ON DELETE RESTRICT,

    CONSTRAINT ck_followup_mensagem_exige_conversa
        CHECK (
            mensagem_id IS NULL
            OR conversa_id IS NOT NULL
        ),

    CONSTRAINT ck_followup_numero_tentativa
        CHECK (numero_tentativa >= 1),

    CONSTRAINT ck_followup_tentativas_envio
        CHECK (tentativas_envio >= 0),

    CONSTRAINT ck_followup_status
        CHECK (
            status IN (
                'pendente',
                'processando',
                'enviado',
                'cancelado',
                'falha',
                'inconclusivo'
            )
        ),

    CONSTRAINT uq_followup_empresa_lead_tentativa
        UNIQUE (empresa_id, lead_id, numero_tentativa)
);

CREATE INDEX IF NOT EXISTS ix_followup_status_agendado
ON public.followup_agendamentos (status, agendado_para);

CREATE INDEX IF NOT EXISTS ix_followup_empresa_conversa
ON public.followup_agendamentos (empresa_id, conversa_id);

COMMIT;
