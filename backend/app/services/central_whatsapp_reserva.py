import re

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.models import Conversa, FollowupAgendamento, Mensagem
from app.services.central_whatsapp_atendimento import gerenciar_atendimento_whatsapp

from app.services.central_whatsapp_envio import preparar_destino_central
from app.services.mensagem_service import registrar_mensagem


def reservar_mensagem_central(
    db: Session,
    *,
    empresa_id: int,
    usuario_id: int,
    conversa_id: int,
    texto: str,
    chave_solicitacao: str,
    mime: str | None = None,
    responder_mensagem_id: int | None = None,
    encaminhar_conversa_id: int | None = None,
) -> tuple[int | None, str]:
    """Reserva mensagem humana sem enviar nem efetuar commit."""

    if not isinstance(texto, str) or (mime is None and not texto.strip()):
        return None, "texto_invalido"

    texto = texto.strip()

    if len(texto) > 4096:
        return None, "texto_muito_longo"

    if not isinstance(chave_solicitacao, str):
        return None, "chave_invalida"

    chave = chave_solicitacao.strip()

    if not chave or len(chave) > 180:
        return None, "chave_invalida"

    # Revalida o responsável após adquirir o mesmo bloqueio da gestão.
    conversa_bloqueada = (
        db.query(Conversa.id)
        .filter(
            Conversa.empresa_id == empresa_id,
            Conversa.id == conversa_id,
        )
        .with_for_update()
        .first()
    )

    if conversa_bloqueada is None:
        return None, "conversa_nao_encontrada"

    destino, situacao = preparar_destino_central(
        db,
        empresa_id=empresa_id,
        usuario_id=usuario_id,
        conversa_id=conversa_id, permitir_assumir=True,
    )
    if destino is None:
        return None, situacao

    resposta_waha = None
    if responder_mensagem_id is not None:
        origem = destino
        if encaminhar_conversa_id is not None:
            origem, _ = preparar_destino_central(
                db, empresa_id=empresa_id, usuario_id=usuario_id, conversa_id=encaminhar_conversa_id,
            )
            if origem is None or origem["conexao_canal_id"] != destino["conexao_canal_id"]:
                return None, "encaminhamento_indisponivel"
        original = db.query(Mensagem).filter_by(
            id=responder_mensagem_id, empresa_id=empresa_id, conversa_id=origem["conversa_id"],
            conexao_canal_id=destino["conexao_canal_id"], sessao_waha=destino["sessao"],
        ).first()
        if original is None or original.tipo == "excluida":
            return None, "citacao_indisponivel"
        resposta_waha = original.mensagem_id_waha or (
            original.mensagem_id_externo if original.from_me is False else None
        )
        direcao = "true" if original.from_me else "false"
        chat = re.escape(origem["chat_id"])
        if not resposta_waha or not re.fullmatch(rf"{direcao}_{chat}_[A-Za-z0-9-]{{1,130}}", resposta_waha):
            return None, "citacao_indisponivel"
        if encaminhar_conversa_id is not None:
            resposta_waha = "ENC:" + resposta_waha
            texto = (original.texto or "Mensagem encaminhada")[:4096]

    # Preserva a idempotencia: a mesma chave deve ser tratada
    # pelo registrar_mensagem, sem criar outra mensagem.
    solicitacao_existente = (
        db.query(Mensagem.id)
        .filter(
            Mensagem.empresa_id == empresa_id,
            Mensagem.conversa_id == conversa_id,
            Mensagem.remetente == "humano",
            Mensagem.from_me.is_(True),
            Mensagem.mensagem_id_externo == chave,
        )
        .first()
    )

    if solicitacao_existente is None:
        pendencia = (
            db.query(Mensagem.id)
            .filter(
                Mensagem.empresa_id == empresa_id,
                Mensagem.conversa_id == conversa_id,
                Mensagem.remetente == "humano",
                Mensagem.from_me.is_(True),
                or_(
                    Mensagem.status_envio.is_(None),
                    Mensagem.status_envio == "timeout_envio_inconclusivo",
                ),
            )
            .first()
        )

        if pendencia is not None:
            return None, "envio_anterior_pendente"

    if db.query(FollowupAgendamento.id).filter(
        FollowupAgendamento.empresa_id == empresa_id,
        FollowupAgendamento.conversa_id == conversa_id,
        FollowupAgendamento.status == "processando",
        FollowupAgendamento.envio_iniciado_em.is_not(None),
    ).first() is not None:
        return None, "followup_envio_em_andamento"

    if destino["assumir"]:
        assumido, motivo = gerenciar_atendimento_whatsapp(
            db, empresa_id=empresa_id, identidade={"usuario_id": usuario_id},
            conversa_id=conversa_id, acao="assumir",
        )
        if not assumido:
            return None, motivo

    registro, criado = registrar_mensagem(
        db,
        empresa_id=empresa_id,
        conversa_id=conversa_id,
        cliente_id=destino["cliente_id"],
        remetente="humano",
        texto=texto,
        from_me=True,
        mensagem_id_externo=chave,
    )

    if not criado:
        mesma_solicitacao = (
            registro.remetente == "humano"
            and registro.from_me is True
            and registro.texto == texto
            and registro.midia_tipo == mime
            and registro.central_resposta_waha == resposta_waha
            and registro.especialista_id == destino["especialista_id"]
            and registro.conexao_canal_id == destino["conexao_canal_id"]
            and registro.sessao_waha == destino["sessao"]
        )

        if not mesma_solicitacao:
            return None, "chave_solicitacao_em_conflito"

        return registro.id, "solicitacao_duplicada"

    registro.especialista_id = destino["especialista_id"]
    registro.conexao_canal_id = destino["conexao_canal_id"]
    registro.sessao_waha = destino["sessao"]
    registro.midia_tipo = mime
    registro.central_resposta_waha = resposta_waha

    db.flush()

    return registro.id, "envio_reservado"
