from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models.models import Mensagem, ConexaoCanal
from app.services.estados_mensagem import (
    STATUS_RECEBIDA,
    STATUS_PROCESSANDO,
)


def assumir_envio_humano(
    db: Session,
    *,
    empresa_id: int,
    conversa_id: int,
    mensagem_id: int,
    conexao_canal_id: int,
    especialista_id: int,
) -> bool:
    """
    Assume uma reserva humana de forma atomica.

    Nao executa commit e nao envia mensagens.
    O chamador deve confirmar a transacao antes de chamar o WAHA.
    """

    if any(
        not isinstance(valor, int)
        or isinstance(valor, bool)
        or valor <= 0
        for valor in (
            empresa_id,
            conversa_id,
            mensagem_id,
            conexao_canal_id,
            especialista_id,
        )
    ):
        return False

    comando = (
        update(Mensagem)
        .where(
            Mensagem.id == mensagem_id,
            Mensagem.empresa_id == empresa_id,
            Mensagem.conversa_id == conversa_id,
            Mensagem.conexao_canal_id == conexao_canal_id,
            Mensagem.especialista_id == especialista_id,
            Mensagem.sessao_waha.is_not(None),
            Mensagem.sessao_waha == (
                db.query(ConexaoCanal.sessao_waha)
                .filter(
                    ConexaoCanal.id == conexao_canal_id,
                    ConexaoCanal.empresa_id == empresa_id,
                    ConexaoCanal.especialista_id == especialista_id,
                    ConexaoCanal.canal == "whatsapp",
                    ConexaoCanal.provedor == "waha",
                    ConexaoCanal.ativo.is_(True),
                )
                .scalar_subquery()
            ),
            Mensagem.remetente == "humano",
            Mensagem.from_me.is_(True),
            Mensagem.mensagem_id_externo.is_not(None),
            Mensagem.status_processamento == STATUS_RECEBIDA,
        )
        .values(status_processamento=STATUS_PROCESSANDO)
    )

    resultado = db.execute(comando)

    return resultado.rowcount == 1
