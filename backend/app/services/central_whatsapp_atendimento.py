from typing import Literal

from sqlalchemy import bindparam, func, text
from sqlalchemy.orm import Session

from app.models.models import Conversa, ConexaoCanal, Especialista
from app.services.central_whatsapp_consultas import PERFIS_ADMINISTRATIVOS, PERFIS_CENTRAL
from app.services.central_whatsapp_pendencias import listar_pendencias_envio_central


ATENDIMENTO_HUMANO = "em_atendimento_humano"
ATENDIMENTO_ENCERRADO = "finalizado"


def atendentes_autorizados(db, empresa_id):
    consulta = text("""
        SELECT e.id, e.nome, u.id AS usuario_id
        FROM especialistas e
        JOIN usuarios u ON u.id = e.usuario_id AND u.empresa_id = e.empresa_id
        WHERE e.empresa_id = :empresa_id AND u.status = 'ativo'
          AND u.nivel IN :perfis
        ORDER BY e.nome, e.id
    """).bindparams(bindparam("perfis", expanding=True))
    return db.execute(consulta, {"empresa_id": empresa_id, "perfis": PERFIS_CENTRAL}).mappings()


def gerenciar_atendimento_whatsapp(
    db: Session,
    *,
    empresa_id: int,
    identidade: dict,
    conversa_id: int,
    acao: Literal["assumir", "transferir", "encerrar"],
    responsavel_atual_id: int | None = None,
    destino_id: int | None = None,
) -> tuple[bool, str]:
    """Valida a transição com a conversa bloqueada até o fim da transação."""
    conversa = (
        db.query(Conversa)
        .filter(
            Conversa.id == conversa_id,
            Conversa.empresa_id == empresa_id,
            Conversa.canal == "whatsapp",
        )
        .with_for_update()
        .populate_existing()
        .first()
    )

    if conversa is None:
        return False, "conversa_nao_encontrada"

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
        return False, "conexao_waha_indisponivel"

    atendentes = list(atendentes_autorizados(db, empresa_id))
    especialista_id = next(
        (a.id for a in atendentes if a.usuario_id == identidade["usuario_id"]), None
    )
    corporativa = conexao.especialista_id is None
    if not corporativa and (
        conexao.especialista_id != especialista_id or acao == "transferir"
    ):
        return False, "conexao_de_outro_especialista"

    responsavel = conversa.especialista_id
    if acao == "assumir":
        if especialista_id is None:
            return False, "especialista_nao_vinculado"
        if responsavel not in (None, especialista_id):
            return False, "atendimento_ja_assumido"
        if conversa.humano_assumiu and conversa.status_atendimento == ATENDIMENTO_ENCERRADO:
            return False, "atendimento_encerrado"
        if (
            responsavel == especialista_id
            and conversa.humano_assumiu is True
            and conversa.status_atendimento == ATENDIMENTO_HUMANO
        ):
            return True, "atendimento_ja_pertence_ao_especialista"
        destino_id = especialista_id
        situacao = (
            "atendimento_ja_pertence_ao_especialista"
            if responsavel == especialista_id else "atendimento_assumido"
        )
    else:
        supervisor = corporativa and identidade["nivel"] in PERFIS_ADMINISTRATIVOS
        if not supervisor and (especialista_id is None or responsavel != especialista_id):
            return False, "usuario_nao_autorizado"
        if responsavel != responsavel_atual_id or (
            conversa.status_atendimento != ATENDIMENTO_HUMANO
            or conversa.humano_assumiu is not True
        ):
            return False, "atendimento_alterado"
        if acao == "transferir" and (
            destino_id == responsavel or not any(a.id == destino_id for a in atendentes)
        ):
            return False, "destino_nao_autorizado"
        if listar_pendencias_envio_central(
            db, empresa_id=empresa_id, conversa_id=conversa_id, especialista_id=responsavel,
        ):
            return False, "envio_pendente"
        situacao = "atendimento_transferido" if acao == "transferir" else "atendimento_encerrado"

    if acao != "encerrar":
        conversa.especialista_id = destino_id
    conversa.humano_assumiu = True
    conversa.status_atendimento = (
        ATENDIMENTO_ENCERRADO if acao == "encerrar" else ATENDIMENTO_HUMANO
    )
    conversa.atualizado_em = func.now()
    db.flush()
    from app.services.followup_processamento_service import cancelar_followups_pendentes_por_resposta

    cancelar_followups_pendentes_por_resposta(db, empresa_id=empresa_id, conversa_id=conversa_id)
    return True, situacao
