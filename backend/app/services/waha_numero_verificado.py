"""Vinculo global por telefone confirmado pela WAHA."""

import re

from sqlalchemy import text

from app.services.waha_gestao_transporte import ErroGestaoWaha


def confirmar_numero_waha(db, conexao, estado):
    numero = estado.get("numero")
    if estado.get("estado") != "WORKING" or not isinstance(numero, str) or not re.fullmatch(
        r"[1-9][0-9]{7,14}", numero,
    ):
        raise ErroGestaoWaha("numero_waha_nao_confirmado", 409)

    inventario_pendente = db.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM conexoes_canais c
            WHERE c.canal = 'whatsapp' AND c.provedor = 'waha' AND c.ativo
              AND (NOT c.gerenciada_crm OR c.sofia_institucional)
              AND NOT EXISTS (SELECT 1 FROM waha_numeros_verificados n WHERE n.conexao_id = c.id)
        )
    """)).scalar_one()
    if inventario_pendente:
        raise ErroGestaoWaha("inventario_waha_pendente", 409)

    dados = {"id": conexao.id, "numero": f"+{numero}"}
    db.execute(text("""
        INSERT INTO waha_numeros_verificados (conexao_id, numero_e164)
        VALUES (:id, :numero) ON CONFLICT DO NOTHING
    """), dados)
    confirmada = db.execute(text("""
        SELECT 1 FROM waha_numeros_verificados
        WHERE conexao_id = :id AND numero_e164 = :numero
    """), dados).scalar_one_or_none()
    if confirmada is None:
        raise ErroGestaoWaha("numero_waha_indisponivel", 409)
    conexao.pareamento_waha_pendente = False
    conexao.operacao_suspensa = False
