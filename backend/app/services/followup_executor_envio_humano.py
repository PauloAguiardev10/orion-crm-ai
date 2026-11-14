from collections.abc import Callable

from sqlalchemy.orm import Session

from app.services.estados_mensagem import (
    STATUS_ENVIO_CONFIRMADO_HTTP,
    STATUS_ENVIO_FALHA,
    STATUS_ENVIO_INCONCLUSIVO,
)
from app.services.followup_preparacao_envio_humano import (
    preparar_envio_humano,
)
from app.services.followup_resultado_envio_humano import (
    registrar_resultado_envio_humano,
)


def executar_envio_humano(
    db: Session,
    *,
    empresa_id: int,
    conversa_id: int,
    mensagem_id: int,
    conexao_canal_id: int,
    especialista_id: int,
    transportador: Callable,
) -> tuple[bool, str]:
    """Executa envio previamente assumido, sem commit automatico."""

    parametros = dict(
        empresa_id=empresa_id,
        conversa_id=conversa_id,
        mensagem_id=mensagem_id,
        conexao_canal_id=conexao_canal_id,
        especialista_id=especialista_id,
    )

    dados, motivo = preparar_envio_humano(db, **parametros)

    if dados is None:
        return False, motivo

    if not callable(transportador):
        return False, "transportador_invalido"

    try:
        sucesso, erro, id_waha = transportador(
            dados["sessao"],
            dados["chat_id"],
            dados["texto"],
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

    registrado = registrar_resultado_envio_humano(
        db,
        **parametros,
        status_envio=estado,
        mensagem_id_waha=id_waha if sucesso is True else None,
        sessao_waha=dados["sessao"],
    )

    if not registrado:
        return False, "resultado_nao_registrado"

    return sucesso is True, estado
