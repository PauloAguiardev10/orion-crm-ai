from collections.abc import Callable

from sqlalchemy.orm import Session

from app.services.followup_executor_envio_humano import (
    executar_envio_humano,
)


def executar_envio_controlado(
    db: Session,
    *,
    empresa_id: int,
    conversa_id: int,
    mensagem_id: int,
    conexao_canal_id: int,
    especialista_id: int,
    transportador: Callable,
) -> tuple[bool, str]:
    """
    Executa apenas mensagens previamente assumidas.

    O estado 'processando' deve estar confirmado
    no banco antes da chamada deste servico.

    Nunca realiza nova tentativa automaticamente.
    """

    try:
        sucesso, situacao = executar_envio_humano(
            db,
            empresa_id=empresa_id,
            conversa_id=conversa_id,
            mensagem_id=mensagem_id,
            conexao_canal_id=conexao_canal_id,
            especialista_id=especialista_id,
            transportador=transportador,
        )

        if situacao in (
            "mensagem_indisponivel",
            "conversa_invalida",
            "conexao_invalida",
            "sessao_waha_alterada",
            "destinatario_invalido",
            "texto_invalido",
            "transportador_invalido",
            "resultado_nao_registrado",
        ):
            db.rollback()
            return False, situacao

        db.commit()
        return sucesso, situacao

    except Exception:
        db.rollback()
        raise
