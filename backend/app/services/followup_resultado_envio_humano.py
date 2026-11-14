from sqlalchemy.orm import Session

from app.models.models import Mensagem
from app.services.estados_mensagem import STATUS_PROCESSANDO
from app.services.mensagem_service import registrar_resultado_envio


def registrar_resultado_envio_humano(
    db: Session,
    *,
    empresa_id: int,
    conversa_id: int,
    mensagem_id: int,
    conexao_canal_id: int,
    especialista_id: int,
    status_envio: str,
    mensagem_id_waha: str | None = None,
    sessao_waha: str | None = None,
) -> bool:
    """Registra resultado apenas de envio humano ja assumido."""

    mensagem = (
        db.query(Mensagem)
        .filter(
            Mensagem.id == mensagem_id,
            Mensagem.empresa_id == empresa_id,
            Mensagem.conversa_id == conversa_id,
            Mensagem.conexao_canal_id == conexao_canal_id,
            Mensagem.especialista_id == especialista_id,
            Mensagem.remetente == "humano",
            Mensagem.from_me.is_(True),
            Mensagem.status_processamento == STATUS_PROCESSANDO,
            Mensagem.status_envio.is_(None),
        )
        .with_for_update()
        .first()
    )

    if mensagem is None:
        return False

    # Confirma a sessao originalmente reservada na mensagem.
    # Alteracoes posteriores na conexao nao impedem o registro.
    if (
        not sessao_waha
        or not mensagem.sessao_waha
        or mensagem.sessao_waha != sessao_waha
    ):
        return False

    return registrar_resultado_envio(
        db,
        empresa_id=empresa_id,
        conversa_id=conversa_id,
        mensagem_id=mensagem_id,
        status_envio=status_envio,
        mensagem_id_waha=mensagem_id_waha,
        sessao_waha=sessao_waha,
    )
