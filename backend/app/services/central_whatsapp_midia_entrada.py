import requests
from sqlalchemy import func

from app.models.models import ConexaoCanal, Conversa
from app.services.central_whatsapp_midia import (
    FORMATOS, baixar_midia_waha, caminho_midia, guardar_midia,
)
from app.services.mensagem_service import registrar_mensagem
from app.services.followup_vinculo_conversa_waha import localizar_conversa_entrada_waha


def registrar_midia_recebida(db, *, empresa_id, conexao_id, sessao, chat_id, mensagem_id, payload):
    # Serializa a criação da primeira conversa de mídia nesta conexão.
    conexao = db.query(ConexaoCanal).filter_by(
        id=conexao_id, empresa_id=empresa_id, sessao_waha=sessao,
        canal="whatsapp", provedor="waha", ativo=True,
    ).with_for_update().one_or_none()
    if conexao is None or conexao.operacao_suspensa:
        return "conexao_indisponivel"

    conversa = localizar_conversa_entrada_waha(
        db,
        empresa_id=empresa_id, conexao_id=conexao.id, chat_id=chat_id,
    )
    if conversa is None:
        dados_internos = payload.get("_data")
        nome = payload.get("pushName") or (
            dados_internos.get("notifyName") if isinstance(dados_internos, dict) else None
        )
        conversa = Conversa(
            empresa_id=empresa_id, conexao_canal_id=conexao.id,
            especialista_id=conexao.especialista_id,
            canal="whatsapp", identificador=chat_id, etapa="inicio",
            nome=nome.strip()[:150] if isinstance(nome, str) and nome.strip() else None,
            telefone=chat_id.split("@", 1)[0] if chat_id.endswith("@c.us") else None,
        )
        db.add(conversa)
        db.flush()
    legenda = payload.get("body")
    registro, criado = registrar_mensagem(
        db, empresa_id=empresa_id, conversa_id=conversa.id, remetente="cliente", from_me=False,
        cliente_id=conversa.cliente_id, mensagem_id_externo=mensagem_id,
        texto=legenda[:4096] if isinstance(legenda, str) else "",
    )
    if registro.remetente != "cliente" or registro.from_me is not False:
        return "id_mensagem_em_conflito"
    if criado:
        registro.conexao_canal_id = conexao.id
        registro.sessao_waha = sessao
        registro.tipo = "midia"
        conversa.atualizado_em = func.now()
    motivo = anexar_midia_waha(db, registro=registro, empresa_id=empresa_id,
                                sessao=sessao, mensagem_id=mensagem_id, payload=payload)
    db.commit()
    return motivo


def anexar_midia_waha(db, *, registro, empresa_id, sessao, mensagem_id, payload):
    from app.services.central_whatsapp_eventos_mensagem import aplicar_eventos_pendentes

    aplicar_eventos_pendentes(db, registro, mensagem_id)
    if registro.tipo == "excluida":
        return "mensagem_excluida"
    if registro.midia_url:
        return "midia_duplicada"
    midia = payload.get("media")
    if not isinstance(midia, dict) or not isinstance(midia.get("url"), str):
        return "arquivo_indisponivel"
    caminho = None
    try:
        nome, mime, dados = baixar_midia_waha(midia, sessao=sessao, mensagem_id=mensagem_id)
        registro.midia_url = guardar_midia(empresa_id, nome, dados)
        caminho, _ = caminho_midia(empresa_id, registro.midia_url)
        registro.midia_tipo = mime
        registro.tipo = FORMATOS[mime][0]
    except (OSError, ValueError, requests.RequestException):
        return "arquivo_indisponivel"
    try:
        db.flush()
    except Exception:
        if caminho is not None:
            caminho.unlink(missing_ok=True)
        raise
    return "midia_registrada"
