from sqlalchemy.orm import Session

from app.models.models import Mensagem, Conversa, ConexaoCanal
from app.services.estados_mensagem import STATUS_PROCESSANDO


def preparar_envio_humano(
    db: Session,
    *,
    empresa_id: int,
    conversa_id: int,
    mensagem_id: int,
    conexao_canal_id: int,
    especialista_id: int,
) -> tuple[dict | None, str]:
    """Prepara envio humano usando exclusivamente dados do banco."""

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
        .first()
    )

    if mensagem is None:
        return None, "mensagem_indisponivel"

    conversa = (
        db.query(Conversa)
        .filter(
            Conversa.id == conversa_id,
            Conversa.empresa_id == empresa_id,
            Conversa.conexao_canal_id == conexao_canal_id,
            Conversa.canal == "whatsapp",
        )
        .first()
    )

    if conversa is None:
        return None, "conversa_invalida"

    conexao = (
        db.query(ConexaoCanal)
        .filter(
            ConexaoCanal.id == conexao_canal_id,
            ConexaoCanal.empresa_id == empresa_id,
            ConexaoCanal.especialista_id == especialista_id,
            ConexaoCanal.canal == "whatsapp",
            ConexaoCanal.provedor == "waha",
            ConexaoCanal.ativo.is_(True),
        )
        .first()
    )

    if conexao is None:
        return None, "conexao_invalida"

    if (
        not mensagem.sessao_waha
        or mensagem.sessao_waha != conexao.sessao_waha
    ):
        return None, "sessao_waha_alterada"

    destinatario = (conversa.identificador or "").strip()
    texto = (mensagem.texto or "").strip()

    if (
        not destinatario.endswith("@c.us")
        or not destinatario[:-5].isdigit()
    ):
        return None, "destinatario_invalido"

    if not texto:
        return None, "texto_invalido"

    return {
        "sessao": mensagem.sessao_waha,
        "chat_id": destinatario,
        "texto": texto,
        "mensagem_id": mensagem.id,
    }, "envio_preparado"
