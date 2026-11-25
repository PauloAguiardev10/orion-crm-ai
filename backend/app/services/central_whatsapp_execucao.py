from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models.models import Mensagem, Conversa, ConexaoCanal
from app.services.central_whatsapp_atendimento import ATENDIMENTO_ENCERRADO
from app.services.estados_mensagem import (
    STATUS_RECEBIDA,
    STATUS_PROCESSANDO,
)


def assumir_envio_central(
    db: Session,
    *,
    empresa_id: int,
    conversa_id: int,
    mensagem_id: int,
    especialista_id: int,
) -> bool:
    """Reserva atomicamente a execucao de uma mensagem da Central."""

    if any(
        not isinstance(valor, int)
        or isinstance(valor, bool)
        or valor <= 0
        for valor in (
            empresa_id,
            conversa_id,
            mensagem_id,
            especialista_id,
        )
    ):
        return False

    conversa = (
        db.query(Conversa.id)
        .filter(
            Conversa.id == conversa_id,
            Conversa.empresa_id == empresa_id,
            Conversa.especialista_id == especialista_id,
            Conversa.humano_assumiu.is_(True),
            Conversa.status_atendimento.is_distinct_from(ATENDIMENTO_ENCERRADO),
            Conversa.canal == "whatsapp",
        )
        .with_for_update()
        .first()
    )
    if conversa is None:
        return False

    conversa_autorizada = (
        db.query(Conversa.id)
        .filter(
            Conversa.id == conversa_id,
            Conversa.empresa_id == empresa_id,
            Conversa.especialista_id == especialista_id,
            Conversa.humano_assumiu.is_(True),
            Conversa.canal == "whatsapp",
            Conversa.conexao_canal_id == Mensagem.conexao_canal_id,
        )
        .exists()
    )

    conexao_autorizada = (
        db.query(ConexaoCanal.id)
        .filter(
            ConexaoCanal.id == Mensagem.conexao_canal_id,
            ConexaoCanal.empresa_id == empresa_id,
            ConexaoCanal.canal == "whatsapp",
            ConexaoCanal.provedor == "waha",
            ConexaoCanal.ativo.is_(True),
            ConexaoCanal.operacao_suspensa.is_(False),
            ConexaoCanal.sessao_waha == Mensagem.sessao_waha,
            (
                (ConexaoCanal.especialista_id.is_(None))
                | (ConexaoCanal.especialista_id == especialista_id)
            ),
        )
        .exists()
    )

    comando = (
        update(Mensagem)
        .where(
            Mensagem.id == mensagem_id,
            Mensagem.empresa_id == empresa_id,
            Mensagem.conversa_id == conversa_id,
            Mensagem.especialista_id == especialista_id,
            Mensagem.remetente == "humano",
            Mensagem.from_me.is_(True),
            Mensagem.mensagem_id_externo.is_not(None),
            Mensagem.sessao_waha.is_not(None),
            Mensagem.status_processamento == STATUS_RECEBIDA,
            conversa_autorizada,
            conexao_autorizada,
        )
        .values(status_processamento=STATUS_PROCESSANDO)
    )

    resultado = db.execute(comando)

    return resultado.rowcount == 1
