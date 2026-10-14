
from sqlalchemy.orm import Session

from app.models.models import Conversa, Mensagem


def registrar_mensagem(
    db: Session,
    *,
    empresa_id: int,
    conversa_id: int,
    remetente: str,
    texto: str,
    from_me: bool,
    cliente_id: int | None = None,
    mensagem_id_externo: str | None = None,
) -> tuple[Mensagem | None, bool]:
    """Registra uma mensagem sem efetuar commit da transacao."""

    conversa = (
        db.query(Conversa)
        .filter(
            Conversa.id == conversa_id,
            Conversa.empresa_id == empresa_id,
        )
        .first()
    )

    if conversa is None:
        raise ValueError(
            "Conversa nao encontrada para a empresa informada."
        )

    if cliente_id is not None:
        if conversa.cliente_id != cliente_id:
            raise ValueError(
                "Cliente nao corresponde ao vinculo da conversa."
            )

    if mensagem_id_externo:
        existente = (
            db.query(Mensagem)
            .filter(
                Mensagem.empresa_id == empresa_id,
                Mensagem.conversa_id == conversa_id,
                Mensagem.mensagem_id_externo == mensagem_id_externo,
            )
            .first()
        )

        if existente is not None:
            return existente, False

    registro = Mensagem(
        empresa_id=empresa_id,
        conversa_id=conversa_id,
        cliente_id=cliente_id,
        remetente=remetente,
        texto=texto,
        from_me=from_me,
        mensagem_id_externo=mensagem_id_externo,
        status_processamento="recebida",
    )

    db.add(registro)
    db.flush()

    return registro, True


def persistir_mensagem_segura(
    *,
    empresa_id: int,
    conversa_id: int,
    remetente: str,
    texto: str,
    from_me: bool,
    cliente_id: int | None = None,
    mensagem_id_externo: str | None = None,
    retornar_id: bool = False,
) -> str | tuple[str, int | None]:
    """Retorna o resultado e, opcionalmente, o ID interno."""

    from app.database.database import SessionLocal

    db = None

    try:
        db = SessionLocal()
        registro, criado = registrar_mensagem(
            db,
            empresa_id=empresa_id,
            conversa_id=conversa_id,
            remetente=remetente,
            texto=texto,
            from_me=from_me,
            cliente_id=cliente_id,
            mensagem_id_externo=mensagem_id_externo,
        )

        db.commit()
        resultado = "criada" if criado else "duplicada"
        if retornar_id:
            return resultado, registro.id
        return resultado

    except Exception as erro:
        if db is not None:
            try:
                db.rollback()
            except Exception:
                pass

        print(
            "[CRM MENSAGENS] falha ao persistir: "
            f"{type(erro).__name__}: {erro}",
            flush=True,
        )

        return ("erro", None) if retornar_id else "erro"

    finally:
        if db is not None:
            try:
                db.close()
            except Exception as erro:
                print(
                    "[CRM MENSAGENS] falha ao fechar sessao: "
                    f"{type(erro).__name__}: {erro}",
                    flush=True,
                )


def assumir_processamento_mensagem(
    db: Session,
    *,
    empresa_id: int,
    conversa_id: int,
    mensagem_id: int,
) -> bool:
    """Reserva uma mensagem para processamento na transacao atual."""

    atualizados = (
        db.query(Mensagem)
        .filter(
            Mensagem.id == mensagem_id,
            Mensagem.empresa_id == empresa_id,
            Mensagem.conversa_id == conversa_id,
            Mensagem.status_processamento == "recebida",
        )
        .update(
            {
                Mensagem.status_processamento: "processando",
            },
            synchronize_session=False,
        )
    )

    return atualizados == 1


def concluir_processamento_mensagem(
    db: Session,
    *,
    empresa_id: int,
    conversa_id: int,
    mensagem_id: int,
) -> bool:
    """Conclui uma mensagem reservada na transacao atual."""

    from sqlalchemy import func

    atualizados = (
        db.query(Mensagem)
        .filter(
            Mensagem.id == mensagem_id,
            Mensagem.empresa_id == empresa_id,
            Mensagem.conversa_id == conversa_id,
            Mensagem.status_processamento == "processando",
        )
        .update(
            {
                Mensagem.status_processamento: "concluida",
                Mensagem.processado_em: func.now(),
            },
            synchronize_session=False,
        )
    )

    return atualizados == 1


def registrar_resultado_envio(
    db: Session,
    *,
    empresa_id: int,
    conversa_id: int,
    mensagem_id: int,
    status_envio: str,
) -> bool:
    """Registra o resultado do envio sem efetuar commit."""

    from app.services.estados_mensagem import (
        STATUS_ENVIO_CONFIRMADO_HTTP,
        STATUS_ENVIO_FALHA,
        STATUS_ENVIO_INCONCLUSIVO,
        STATUS_ENVIO_NAO_APLICAVEL,
    )

    permitidos = {
        STATUS_ENVIO_CONFIRMADO_HTTP,
        STATUS_ENVIO_FALHA,
        STATUS_ENVIO_INCONCLUSIVO,
        STATUS_ENVIO_NAO_APLICAVEL,
    }

    if status_envio not in permitidos:
        raise ValueError("Status de envio invalido.")

    atualizados = (
        db.query(Mensagem)
        .filter(
            Mensagem.id == mensagem_id,
            Mensagem.empresa_id == empresa_id,
            Mensagem.conversa_id == conversa_id,
            Mensagem.status_envio.is_(None),
        )
        .update(
            {
                Mensagem.status_envio: status_envio,
            },
            synchronize_session=False,
        )
    )

    return atualizados == 1


def consultar_estado_mensagem(
    db: Session,
    *,
    empresa_id: int,
    conversa_id: int,
    mensagem_id_externo: str,
) -> str | None:
    """Consulta o estado persistido de uma mensagem da conversa."""

    if not mensagem_id_externo or not mensagem_id_externo.strip():
        return None

    registro = (
        db.query(Mensagem)
        .filter(
            Mensagem.empresa_id == empresa_id,
            Mensagem.conversa_id == conversa_id,
            Mensagem.mensagem_id_externo == mensagem_id_externo,
        )
        .first()
    )

    if registro is None:
        return None

    return registro.status_processamento


def registrar_resposta_agente(
    db: Session,
    *,
    empresa_id: int,
    conversa_id: int,
    texto: str,
    cliente_id: int | None = None,
    mensagem_id_externo: str | None = None,
) -> Mensagem:
    """Registra uma resposta da IA antes do envio pelo WAHA."""

    if not texto or not texto.strip():
        raise ValueError("Resposta do agente vazia.")

    registro, criado = registrar_mensagem(
        db,
        empresa_id=empresa_id,
        conversa_id=conversa_id,
        cliente_id=cliente_id,
        remetente="agente",
        texto=texto,
        from_me=True,
        mensagem_id_externo=mensagem_id_externo,
    )

    if not criado or registro is None:
        raise RuntimeError("Falha ao criar registro da resposta.")

    registro.status_processamento = "concluida"

    return registro
