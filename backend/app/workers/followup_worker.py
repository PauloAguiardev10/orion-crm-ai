"""Worker de follow-up automatico do Orion CRM AI.

A execucao real permanece desabilitada ate a integracao
e validacao completa das transacoes e do transporte WAHA.
"""

import os

MENSAGEM_PADRAO_PRIMEIRO_FOLLOWUP = (
    "Ol?! Tudo bem? Vi que ainda n?o conseguimos continuar nossa "
    "conversa. Voc? gostaria de saber mais sobre como podemos ajudar?"
)


def executar_ciclo_followup(
    *,
    empresa_id: int,
    modo_simulacao: bool = True,
    session_factory=None,
    mapa_sessoes=None,
    simulador_envio=None,
) -> tuple[bool, str]:
    """Ponto de entrada seguro do worker de follow-up."""

    if type(empresa_id) is not int or empresa_id < 1:
        return False, "empresa_invalida"

    if not modo_simulacao:
        if os.getenv("FOLLOWUP_WORKER_ATIVO") != "1":
            return False, "worker_desabilitado"

        if os.getenv("FOLLOWUP_ENVIO_REAL_ATIVO") != "1":
            return False, "envio_real_desabilitado"

        if not callable(session_factory):
            return False, "session_factory_invalida"

        return executar_ciclo_followup_simulado(
            empresa_id=empresa_id,
            session_factory=session_factory,
            mapa_sessoes=mapa_sessoes,
            simulador_envio=enviar_followup_via_waha,
        )

    if (
        session_factory is None
        and mapa_sessoes is None
        and simulador_envio is None
    ):
        return True, "simulacao_sem_envio"

    if (
        not callable(session_factory)
        or mapa_sessoes is None
        or not callable(simulador_envio)
    ):
        return False, "configuracao_simulacao_invalida"

    return executar_ciclo_followup_simulado(
        empresa_id=empresa_id,
        session_factory=session_factory,
        mapa_sessoes=mapa_sessoes,
        simulador_envio=simulador_envio,
    )



def simular_reserva_followup(
    db,
    *,
    empresa_id: int,
) -> tuple[int | None, str]:
    """Simula a reserva sem confirmar alteracoes no banco.

    Requer uma Session dedicada e sem transacao externa.
    """

    from app.services.followup_processamento_service import (
        reservar_agendamento_pendente,
    )

    if type(empresa_id) is not int or empresa_id < 1:
        return None, "empresa_invalida"

    if db.in_transaction():
        return None, "sessao_com_transacao_ativa"

    try:
        agendamento_id, motivo = reservar_agendamento_pendente(
            db,
            empresa_id=empresa_id,
        )
        return agendamento_id, motivo
    finally:
        db.rollback()


def simular_reserva_e_autorizacao_followup(
    db,
    *,
    empresa_id: int,
) -> tuple[bool, str]:
    """Testa reserva e autorizacao com rollback obrigatorio.

    Exige uma Session dedicada e sem transacao ativa.
    Nao executa commit nem envia mensagens.
    """

    from app.models.models import FollowupAgendamento
    from app.services.followup_processamento_service import (
        reservar_agendamento_pendente,
        autorizar_envio_followup_reservado,
    )

    if type(empresa_id) is not int or empresa_id < 1:
        return False, "empresa_invalida"

    if db.in_transaction():
        return False, "sessao_com_transacao_ativa"

    try:
        agendamento_id, motivo = reservar_agendamento_pendente(
            db,
            empresa_id=empresa_id,
        )

        if agendamento_id is None:
            return False, motivo

        agendamento = (
            db.query(FollowupAgendamento)
            .filter(
                FollowupAgendamento.id == agendamento_id,
                FollowupAgendamento.empresa_id == empresa_id,
            )
            .first()
        )

        if (
            agendamento is None
            or not agendamento.reserva_token
        ):
            return False, "token_reserva_ausente"

        autorizado, motivo = autorizar_envio_followup_reservado(
            db,
            empresa_id=empresa_id,
            agendamento_id=agendamento_id,
            reserva_token=agendamento.reserva_token,
        )

        return autorizado, motivo

    finally:
        db.rollback()



def _confirmar_cancelamento_followup(db, empresa_id: int) -> bool:
    """Confirma somente cancelamento identificado nesta operacao."""
    from app.models.models import FollowupAgendamento

    referencia = db.info.pop("followup_cancelamento_atual", None)

    if not isinstance(referencia, tuple) or len(referencia) != 2:
        return False

    empresa_cancelada, agendamento_id = referencia

    if empresa_cancelada != empresa_id:
        return False

    agendamento = db.get(FollowupAgendamento, agendamento_id)

    if (
        agendamento is None
        or agendamento.empresa_id != empresa_id
        or agendamento.status != "cancelado"
        or agendamento.cancelado_em is None
    ):
        return False

    db.commit()
    return True


def reservar_followup_transacional(
    db,
    *,
    empresa_id: int,
) -> tuple[int | None, str]:
    """Reserva um follow-up em transacao dedicada.

    Confirma somente a reserva no PostgreSQL.
    Nao autoriza nem envia mensagens.
    Nao e chamada pelo ciclo automatico.
    """

    from app.services.followup_processamento_service import (
        reservar_agendamento_pendente,
    )

    if type(empresa_id) is not int or empresa_id < 1:
        return None, "empresa_invalida"

    if db.in_transaction():
        return None, "sessao_com_transacao_ativa"

    db.info.pop("followup_cancelamento_atual", None)

    try:
        agendamento_id, motivo = reservar_agendamento_pendente(
            db,
            empresa_id=empresa_id,
        )

        if agendamento_id is None:
            if not _confirmar_cancelamento_followup(db, empresa_id):
                db.rollback()
            return None, motivo

        db.commit()
        return agendamento_id, "reserva_confirmada"

    except Exception:
        db.rollback()
        raise


def autorizar_followup_transacional(
    db,
    *,
    empresa_id: int,
    agendamento_id: int,
    reserva_token: str,
) -> tuple[bool, str]:
    """Autoriza reserva existente e confirma a transacao.

    Nao envia mensagens e nao e chamada pelo ciclo automatico.
    Exige uma Session dedicada, sem transacao ativa.
    """

    from app.services.followup_processamento_service import (
        autorizar_envio_followup_reservado,
    )

    if type(empresa_id) is not int or empresa_id < 1:
        return False, "empresa_invalida"

    if type(agendamento_id) is not int or agendamento_id < 1:
        return False, "agendamento_invalido"

    if not isinstance(reserva_token, str) or not reserva_token.strip():
        return False, "token_invalido"

    if db.in_transaction():
        return False, "sessao_com_transacao_ativa"

    db.info.pop("followup_cancelamento_atual", None)

    try:
        autorizado, motivo = autorizar_envio_followup_reservado(
            db,
            empresa_id=empresa_id,
            agendamento_id=agendamento_id,
            reserva_token=reserva_token,
        )

        if not autorizado:
            if motivo == "fora_horario_reagendado":
                referencia = db.info.pop(
                    "followup_reagendamento_atual", None
                )

                if referencia != (empresa_id, agendamento_id):
                    db.rollback()
                    return False, "reagendamento_nao_confirmado"

                db.commit()
                return False, motivo

            if not _confirmar_cancelamento_followup(db, empresa_id):
                db.rollback()
            return False, motivo

        db.commit()
        return True, "autorizacao_confirmada"

    except Exception:
        db.rollback()
        raise


def finalizar_followup_transacional(
    db,
    *,
    empresa_id: int,
    agendamento_id: int,
    reserva_token: str,
    status_envio: str,
    mensagem_id_externo: str | None = None,
) -> tuple[bool, str]:
    """Confirma o resultado de um envio previamente autorizado.

    Nao envia mensagens e nao e chamada pelo ciclo automatico.
    Exige Session dedicada sem transacao ativa.
    """

    from app.services.followup_processamento_service import (
        finalizar_agendamento_reservado,
    )

    if type(empresa_id) is not int or empresa_id < 1:
        return False, "empresa_invalida"

    if type(agendamento_id) is not int or agendamento_id < 1:
        return False, "agendamento_invalido"

    if not isinstance(reserva_token, str) or not reserva_token.strip():
        return False, "token_invalido"

    status_permitidos = {
        "aceito_waha",
        "falha_envio",
        "timeout_envio_inconclusivo",
    }

    if status_envio not in status_permitidos:
        return False, "status_envio_invalido"

    if db.in_transaction():
        return False, "sessao_com_transacao_ativa"

    try:
        finalizado, motivo = finalizar_agendamento_reservado(
            db,
            empresa_id=empresa_id,
            agendamento_id=agendamento_id,
            reserva_token=reserva_token,
            status_envio=status_envio,
            mensagem_id_externo=mensagem_id_externo,
        )

        if not finalizado:
            db.rollback()
            return False, motivo

        db.commit()
        return True, "finalizacao_confirmada"

    except Exception:
        db.rollback()
        raise


def recuperar_followups_expirados_transacional(
    db,
    *,
    empresa_id: int,
    limite: int = 100,
) -> tuple[int, str]:
    """Recupera reservas expiradas em transacao dedicada.

    Nao envia mensagens e nao e chamada pelo ciclo automatico.
    Reservas com envio iniciado permanecem sem reenvio automatico.
    """

    from app.services.followup_processamento_service import (
        recuperar_reservas_expiradas,
    )

    if type(empresa_id) is not int or empresa_id < 1:
        return 0, "empresa_invalida"

    if type(limite) is not int or limite < 1:
        return 0, "limite_invalido"

    if db.in_transaction():
        return 0, "sessao_com_transacao_ativa"

    try:
        quantidade = recuperar_reservas_expiradas(
            db,
            empresa_id=empresa_id,
            limite=limite,
        )

        if quantidade == 0:
            db.rollback()
            return 0, "nenhuma_reserva_expirada"

        db.commit()
        return quantidade, "recuperacao_confirmada"

    except Exception:
        db.rollback()
        raise


def preparar_destino_followup(
    db,
    *,
    empresa_id: int,
    agendamento_id: int,
    mapa_sessoes,
) -> tuple[dict | None, str]:
    """Prepara o destino usando a conexao WAHA da conversa."""

    from app.models.models import (
        Conversa,
        FollowupAgendamento,
        FollowupConfiguracao,
        FollowupModeloMensagem,
    )
    from app.services.followup_sessao_waha_service import (
        resolver_sessao_waha_conversa,
    )
    from app.services.followup_consulta_destinatario_service import (
        consultar_destinatario_followup,
    )

    if type(empresa_id) is not int or empresa_id < 1:
        return None, "empresa_invalida"

    if type(agendamento_id) is not int or agendamento_id < 1:
        return None, "agendamento_invalido"

    vinculo = (
        db.query(Conversa.conexao_canal_id)
        .join(
            FollowupAgendamento,
            (FollowupAgendamento.conversa_id == Conversa.id)
            & (FollowupAgendamento.empresa_id == Conversa.empresa_id),
        )
        .filter(
            FollowupAgendamento.id == agendamento_id,
            FollowupAgendamento.empresa_id == empresa_id,
        )
        .first()
    )

    if vinculo is None or vinculo.conexao_canal_id is None:
        return None, "conexao_conversa_nao_identificada"

    sessao, motivo = resolver_sessao_waha_conversa(
        db,
        empresa_id=empresa_id,
        conexao_canal_id=vinculo.conexao_canal_id,
    )

    if sessao is None:
        return None, motivo

    chat_id, motivo = consultar_destinatario_followup(
        db,
        empresa_id=empresa_id,
        agendamento_id=agendamento_id,
    )

    if chat_id is None:
        return None, motivo

    agendamento = (
        db.query(FollowupAgendamento)
        .filter(
            FollowupAgendamento.id == agendamento_id,
            FollowupAgendamento.empresa_id == empresa_id,
        )
        .first()
    )

    if agendamento is None:
        return None, "agendamento_nao_encontrado"

    configuracao = (
        db.query(FollowupConfiguracao)
        .filter(FollowupConfiguracao.empresa_id == empresa_id)
        .first()
    )

    if configuracao is None or not configuracao.ativo:
        return None, "followup_empresa_desativado"

    if agendamento.numero_tentativa > configuracao.quantidade_tentativas:
        return None, "limite_tentativas_atingido"

    modelo = (
        db.query(FollowupModeloMensagem)
        .filter(
            FollowupModeloMensagem.empresa_id == empresa_id,
            FollowupModeloMensagem.numero_tentativa == agendamento.numero_tentativa,
            FollowupModeloMensagem.ativo.is_(True),
        )
        .first()
    )

    if modelo is None or not isinstance(modelo.texto, str) or not modelo.texto.strip():
        return None, "modelo_mensagem_indisponivel"

    return {
        "empresa_id": empresa_id,
        "agendamento_id": agendamento_id,
        "sessao": sessao,
        "chat_id": chat_id,
        "texto": modelo.texto,
    }, "destino_preparado"


def liberar_reserva_followup_transacional(
    db,
    *,
    empresa_id: int,
    agendamento_id: int,
    reserva_token: str,
) -> tuple[bool, str]:
    """Libera reserva sem envio iniciado, preservando o agendamento."""
    from datetime import datetime, timezone
    from app.models.models import FollowupAgendamento

    if db.in_transaction():
        return False, "transacao_ativa"

    try:
        agendamento = (
            db.query(FollowupAgendamento)
            .filter(
                FollowupAgendamento.id == agendamento_id,
                FollowupAgendamento.empresa_id == empresa_id,
            )
            .with_for_update()
            .first()
        )

        if (
            agendamento is None
            or agendamento.status != "processando"
            or agendamento.reserva_token != reserva_token
            or agendamento.envio_iniciado_em is not None
        ):
            db.rollback()
            return False, "reserva_nao_liberavel"

        agendamento.status = "pendente"
        agendamento.reserva_token = None
        agendamento.reservado_em = None
        agendamento.reserva_expira_em = None
        agendamento.atualizado_em = datetime.now(timezone.utc)

        db.commit()
        return True, "reserva_liberada"

    except Exception:
        db.rollback()
        raise


def executar_ciclo_followup_simulado(
    *,
    empresa_id: int,
    session_factory,
    mapa_sessoes,
    simulador_envio,
) -> tuple[bool, str]:
    """Executa um ciclo completo usando somente envio simulado.

    Reserva, prepara destino, autoriza e finaliza.
    O simulador e injetado pelo chamador.
    Nenhum cliente WAHA e importado aqui.
    """
    from app.models.models import FollowupAgendamento

    if type(empresa_id) is not int or empresa_id < 1:
        return False, "empresa_invalida"

    if not callable(session_factory):
        return False, "session_factory_invalida"

    if not callable(simulador_envio):
        return False, "simulador_invalido"

    # Etapa 1: reserva em transacao independente.
    with session_factory() as db:
        agendamento_id, motivo = reservar_followup_transacional(
            db,
            empresa_id=empresa_id,
        )

    if agendamento_id is None:
        return False, motivo

    # Etapa 2: consulta da reserva e preparacao do destino.
    with session_factory() as db:
        agendamento = db.get(
            FollowupAgendamento,
            agendamento_id,
        )

        if (
            agendamento is None
            or agendamento.empresa_id != empresa_id
            or agendamento.status != "processando"
            or not agendamento.reserva_token
        ):
            return False, "reserva_invalida"

        reserva_token = agendamento.reserva_token

        destino, motivo = preparar_destino_followup(
            db,
            empresa_id=empresa_id,
            agendamento_id=agendamento_id,
            mapa_sessoes=mapa_sessoes,
        )

        db.rollback()

    if destino is None:
        with session_factory() as db:
            liberado, motivo_liberacao = liberar_reserva_followup_transacional(
                db,
                empresa_id=empresa_id,
                agendamento_id=agendamento_id,
                reserva_token=reserva_token,
            )

        if not liberado:
            return False, f"{motivo};{motivo_liberacao}"

        return False, motivo

    # Etapa 3: autorizacao em transacao independente.
    with session_factory() as db:
        autorizado, motivo = autorizar_followup_transacional(
            db,
            empresa_id=empresa_id,
            agendamento_id=agendamento_id,
            reserva_token=reserva_token,
        )

    if not autorizado:
        return False, motivo

    # Etapa 4: simulador de envio.
    # A funcao injetada deve retornar:
    # (status_envio, mensagem_id_externo)
    try:
        status_envio, mensagem_id_externo = simulador_envio(
            destino
        )
    except Exception:
        status_envio = "timeout_envio_inconclusivo"
        mensagem_id_externo = None

    # Etapa 5: finalizacao transacional.
    with session_factory() as db:
        return finalizar_followup_transacional(
            db,
            empresa_id=empresa_id,
            agendamento_id=agendamento_id,
            reserva_token=reserva_token,
            status_envio=status_envio,
            mensagem_id_externo=mensagem_id_externo,
        )


def enviar_followup_via_waha(destino: dict) -> tuple[str, str | None]:
    """Adapta o transporte WAHA ao retorno esperado pelo worker."""

    from app.services.followup_transporte_waha import (
        transportar_mensagem_waha,
    )

    if not isinstance(destino, dict):
        return "falha_envio", None

    sessao = destino.get("sessao")
    chat_id = destino.get("chat_id")
    texto_mensagem = destino.get("texto")

    if (
        not isinstance(sessao, str)
        or not sessao.strip()
        or not isinstance(chat_id, str)
        or not chat_id.strip()
        or not isinstance(texto_mensagem, str)
        or not texto_mensagem.strip()
    ):
        return "falha_envio", None

    try:
        sucesso, erro, mensagem_id_externo = transportar_mensagem_waha(
            sessao=sessao,
            chat_id=chat_id,
            texto=texto_mensagem,
        )
    except Exception:
        return "timeout_envio_inconclusivo", None

    if sucesso:
        return "aceito_waha", mensagem_id_externo

    if erro == "timeout_envio_inconclusivo":
        return "timeout_envio_inconclusivo", None

    return "falha_envio", None
