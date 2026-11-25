from sqlalchemy.orm import Session

from app.models.models import Mensagem
from app.services.central_whatsapp_envio import preparar_destino_central
from app.services.estados_mensagem import STATUS_PROCESSANDO


def preparar_envio_central(
    db: Session,
    *,
    empresa_id: int,
    usuario_id: int,
    conversa_id: int,
    mensagem_id: int,
) -> tuple[dict | None, str]:
    """Prepara envio usando dados autorizados do banco."""

    destino, situacao = preparar_destino_central(
        db,
        empresa_id=empresa_id,
        usuario_id=usuario_id,
        conversa_id=conversa_id,
    )

    if destino is None:
        return None, situacao

    mensagem = (
        db.query(Mensagem)
        .filter(
            Mensagem.id == mensagem_id,
            Mensagem.empresa_id == empresa_id,
            Mensagem.conversa_id == conversa_id,
            Mensagem.conexao_canal_id == destino["conexao_canal_id"],
            Mensagem.especialista_id == destino["especialista_id"],
            Mensagem.remetente == "humano",
            Mensagem.from_me.is_(True),
            Mensagem.status_processamento == STATUS_PROCESSANDO,
            Mensagem.status_envio.is_(None),
            Mensagem.mensagem_id_externo.is_not(None),
            Mensagem.sessao_waha == destino["sessao"],
        )
        .first()
    )

    if mensagem is None:
        return None, "mensagem_indisponivel"

    texto = (mensagem.texto or "").strip()

    if not texto and not mensagem.midia_url:
        return None, "texto_invalido"

    return {
        **destino,
        "mensagem_id": mensagem.id,
        "texto": texto,
        "midia_tipo": mensagem.midia_tipo,
        "midia_url": mensagem.midia_url,
    }, "envio_preparado"
