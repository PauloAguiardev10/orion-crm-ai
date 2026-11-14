from sqlalchemy.orm import Session

from app.services.followup_autorizacao_vendedor import (
    autorizar_vendedor_conversa,
)
from app.services.mensagem_service import registrar_mensagem


def reservar_envio_humano(
    db: Session,
    *,
    usuario_id: int,
    empresa_id: int,
    conversa_id: int,
    conexao_canal_id: int,
    texto: str,
    chave_solicitacao: str,
) -> tuple[int | None, str]:

    if not isinstance(texto, str) or not texto.strip():
        return None, "texto_invalido"

    if not isinstance(chave_solicitacao, str):
        return None, "chave_invalida"

    chave = chave_solicitacao.strip()

    if not chave or len(chave) > 180:
        return None, "chave_invalida"

    autorizado, motivo = autorizar_vendedor_conversa(
        db,
        usuario_id=usuario_id,
        empresa_id=empresa_id,
        conversa_id=conversa_id,
        conexao_canal_id=conexao_canal_id,
    )

    if not autorizado:
        return None, motivo

    from app.models.models import Especialista, ConexaoCanal

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

    conexao = (
        db.query(ConexaoCanal)
        .filter(
            ConexaoCanal.id == conexao_canal_id,
            ConexaoCanal.empresa_id == empresa_id,
            ConexaoCanal.especialista_id == especialista.id,
            ConexaoCanal.canal == "whatsapp",
            ConexaoCanal.provedor == "waha",
            ConexaoCanal.ativo.is_(True),
        )
        .first()
    )

    if conexao is None or not conexao.sessao_waha:
        return None, "sessao_waha_indisponivel"

    registro, criado = registrar_mensagem(
        db,
        empresa_id=empresa_id,
        conversa_id=conversa_id,
        remetente="humano",
        texto=texto.strip(),
        from_me=True,
        mensagem_id_externo=chave,
    )

    if not criado:
        mesma_solicitacao = (
            registro.empresa_id == empresa_id
            and registro.conversa_id == conversa_id
            and registro.conexao_canal_id == conexao_canal_id
            and registro.especialista_id == especialista.id
            and registro.sessao_waha == conexao.sessao_waha
            and registro.texto == texto.strip()
            and registro.remetente == "humano"
            and registro.from_me is True
        )

        if not mesma_solicitacao:
            return None, "chave_solicitacao_em_conflito"

        return registro.id, "solicitacao_duplicada"

    registro.conexao_canal_id = conexao_canal_id
    registro.especialista_id = especialista.id
    registro.sessao_waha = conexao.sessao_waha

    db.flush()

    return registro.id, "envio_reservado"
