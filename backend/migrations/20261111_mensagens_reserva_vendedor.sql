BEGIN;

ALTER TABLE mensagens
    ADD COLUMN IF NOT EXISTS conexao_canal_id INTEGER,
    ADD COLUMN IF NOT EXISTS especialista_id INTEGER;

ALTER TABLE mensagens
    ADD CONSTRAINT fk_mensagens_reserva_conexao
    FOREIGN KEY (empresa_id, conexao_canal_id)
    REFERENCES conexoes_canais (empresa_id, id)
    ON DELETE RESTRICT;

ALTER TABLE mensagens
    ADD CONSTRAINT fk_mensagens_reserva_especialista
    FOREIGN KEY (empresa_id, especialista_id)
    REFERENCES especialistas (empresa_id, id)
    ON DELETE RESTRICT;

COMMIT;
