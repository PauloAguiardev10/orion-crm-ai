from collections.abc import Callable

from sqlalchemy.orm import Session

from app.models.models import Mensagem
from app.services.central_whatsapp_resultado import registrar_resultado_envio_central
from app.services.estados_mensagem import (
    STATUS_PROCESSANDO,
    STATUS_ENVIO_CONFIRMADO_HTTP,
    STATUS_ENVIO_FALHA,
    STATUS_ENVIO_INCONCLUSIVO,
)


def executar_envio_central(
    db: Session,
    *,
    empresa_id: int,
    conversa_id: int,
    mensagem_id: int,
    especialista_id: int,
    sessao: str,
    chat_id: str,
    transportador: Callable,
) -> tuple[bool, str]:
    """Executa mensagem ja assumida, sem commit ou nova tentativa."""

    mensagem = (
        db.query(Mensagem)
        .filter(
            Mensagem.id == mensagem_id,
            Mensagem.empresa_id == empresa_id,
            Mensagem.conversa_id == conversa_id,
            Mensagem.especialista_id == especialista_id,
            Mensagem.remetente == "humano",
            Mensagem.from_me.is_(True),
            Mensagem.status_processamento == STATUS_PROCESSANDO,
            Mensagem.status_envio.is_(None),
            Mensagem.sessao_waha == sessao,
        )
        .first()
    )

    if mensagem is None:
        return False, "mensagem_indisponivel"

    if not sessao or not chat_id.endswith("@c.us"):
        return False, "destinatario_invalido"

    if not chat_id[:-5].isdigit():
        return False, "destinatario_invalido"

    if not mensagem.midia_url and not (mensagem.texto or "").strip():
        return False, "texto_invalido"

    if not callable(transportador):
        return False, "transportador_invalido"

    try:
        sucesso, erro, id_waha = transportador(
            sessao,
            chat_id,
            mensagem.texto,
        )
    except Exception:
        sucesso, erro, id_waha = (
            False,
            STATUS_ENVIO_INCONCLUSIVO,
            None,
        )

    if sucesso is True:
        estado = STATUS_ENVIO_CONFIRMADO_HTTP
    elif erro == STATUS_ENVIO_INCONCLUSIVO:
        estado = STATUS_ENVIO_INCONCLUSIVO
    else:
        estado = STATUS_ENVIO_FALHA

    registrado = registrar_resultado_envio_central(
        db,
        empresa_id=empresa_id,
        conversa_id=conversa_id,
        mensagem_id=mensagem_id,
        especialista_id=especialista_id,
        status_envio=estado,
        mensagem_id_waha=id_waha if sucesso is True else None,
        sessao_waha=sessao,
    )

    if not registrado:
        return False, "resultado_nao_registrado"

    return sucesso is True, estado
