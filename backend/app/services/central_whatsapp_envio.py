from sqlalchemy.orm import Session

from app.models.models import Conversa, ConexaoCanal, Especialista
from app.services.central_whatsapp_atendimento import ATENDIMENTO_ENCERRADO


def preparar_destino_central(
    db: Session,
    *,
    empresa_id: int,
    usuario_id: int,
    conversa_id: int,
) -> tuple[dict | None, str]:
    """Valida o responsavel e o destino WhatsApp da Central."""

    especialista = (
        db.query(Especialista)
        .filter(
            Especialista.empresa_id == empresa_id,
            Especialista.usuario_id == usuario_id,
        )
        .first()
    )

    if especialista is None:
        return None, "especialista_nao_vinculado"

    conversa = (
        db.query(Conversa)
        .filter(
            Conversa.id == conversa_id,
            Conversa.empresa_id == empresa_id,
            Conversa.canal == "whatsapp",
            Conversa.especialista_id == especialista.id,
            Conversa.humano_assumiu.is_(True),
            Conversa.status_atendimento.is_distinct_from(ATENDIMENTO_ENCERRADO),
        )
        .first()
    )

    if conversa is None:
        return None, "conversa_nao_autorizada"

    conexao = (
        db.query(ConexaoCanal)
        .filter(
            ConexaoCanal.id == conversa.conexao_canal_id,
            ConexaoCanal.empresa_id == empresa_id,
            ConexaoCanal.canal == "whatsapp",
            ConexaoCanal.provedor == "waha",
            ConexaoCanal.ativo.is_(True),
        )
        .first()
    )

    if conexao is None or not conexao.sessao_waha:
        return None, "conexao_waha_indisponivel"

    if conexao.operacao_suspensa:
        return None, "conexao_waha_suspensa"

    if (
        conexao.especialista_id is not None
        and conexao.especialista_id != especialista.id
    ):
        return None, "conexao_de_outro_especialista"

    destinatario = (conversa.identificador or "").strip()

    if (
        not destinatario.endswith("@c.us")
        or not destinatario[:-5].isdigit()
    ):
        return None, "destinatario_invalido"

    return {
        "empresa_id": empresa_id,
        "conversa_id": conversa.id,
        "cliente_id": conversa.cliente_id,
        "conexao_canal_id": conexao.id,
        "especialista_id": especialista.id,
        "sessao": conexao.sessao_waha,
        "chat_id": destinatario,
    }, "destino_autorizado"
