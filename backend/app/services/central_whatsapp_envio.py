from sqlalchemy.orm import Session

from app.models.models import Conversa, ConexaoCanal
from app.services.central_whatsapp_atendimento import ATENDIMENTO_ENCERRADO, atendentes_autorizados
from app.services.central_whatsapp_grupos import destinatario_central_valido


def preparar_destino_central(
    db: Session,
    *,
    empresa_id: int,
    usuario_id: int,
    conversa_id: int,
    permitir_assumir: bool = False,
) -> tuple[dict | None, str]:
    """Valida o responsavel e o destino WhatsApp da Central."""

    especialista = next(
        (item for item in atendentes_autorizados(db, empresa_id) if item.usuario_id == usuario_id),
        None,
    )

    if especialista is None:
        return None, "especialista_nao_vinculado"

    conversa = (
        db.query(Conversa)
        .filter(
            Conversa.id == conversa_id,
            Conversa.empresa_id == empresa_id,
            Conversa.canal == "whatsapp",
            (Conversa.especialista_id == especialista.id) | (
                Conversa.especialista_id.is_(None) & Conversa.humano_assumiu.is_not(True)
                if permitir_assumir else False
            ),
            Conversa.status_atendimento.is_distinct_from(ATENDIMENTO_ENCERRADO),
        )
        .first()
    )

    if conversa is None or (not permitir_assumir and conversa.humano_assumiu is not True):
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

    if conexao.sofia_institucional:
        return None, "conexao_institucional_exclusiva"

    if conexao.operacao_suspensa:
        return None, "conexao_waha_suspensa"

    if (
        conexao.especialista_id is not None
        and conexao.especialista_id != especialista.id
    ):
        return None, "conexao_de_outro_especialista"

    destinatario = (conversa.identificador or "").strip()

    if not destinatario_central_valido(conexao.sessao_waha, destinatario):
        return None, "destinatario_invalido"

    return {
        "assumir": conversa.humano_assumiu is not True,
        "empresa_id": empresa_id,
        "conversa_id": conversa.id,
        "cliente_id": conversa.cliente_id,
        "conexao_canal_id": conexao.id,
        "especialista_id": especialista.id,
        "sessao": conexao.sessao_waha,
        "chat_id": destinatario,
    }, "destino_autorizado"
