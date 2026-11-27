from sqlalchemy import func

from app.models.models import ConexaoCanal, Conversa
from app.services.followup_destinatario_service import chat_id_whatsapp_valido
from app.services.mensagem_service import registrar_mensagem
from app.services.central_whatsapp_midia import midia_ativa
from app.services.central_whatsapp_midia_entrada import anexar_midia_waha
from app.services.followup_service import REMETENTE_SAIDA_APLICATIVO
from app.services.waha_identificadores import aliases_chat


def registrar_saida_aplicativo(
    db, *, conexao, destinatario, mensagem_id, payload,
):
    if not isinstance(mensagem_id, str) or not 0 < len(mensagem_id) <= 180:
        return "id_invalido"

    if not chat_id_whatsapp_valido(destinatario):
        return "destinatario_invalido"

    conexao = db.query(ConexaoCanal).filter_by(
        id=conexao.id,
        empresa_id=conexao.empresa_id,
        canal="whatsapp",
        provedor="waha",
        ativo=True,
    ).with_for_update().populate_existing().one_or_none()

    if conexao is None or conexao.operacao_suspensa:
        return "conexao_indisponivel"

    texto = payload.get("body")
    texto = texto.strip()[:4096] if isinstance(texto, str) else ""
    tem_midia = midia_ativa() and payload.get("hasMedia") is True
    if not texto and not tem_midia:
        return "saida_sem_texto"

    conversa = db.query(Conversa).filter_by(
        empresa_id=conexao.empresa_id,
        conexao_canal_id=conexao.id,
        canal="whatsapp",
    ).filter(Conversa.identificador.in_(aliases_chat(destinatario))).with_for_update().limit(2).all()
    if len(conversa) > 1:
        return "conversa_ambigua"
    conversa = conversa[0] if conversa else None

    if conversa is None:
        conversa = Conversa(
            empresa_id=conexao.empresa_id,
            conexao_canal_id=conexao.id,
            especialista_id=conexao.especialista_id,
            canal="whatsapp",
            identificador=destinatario,
            etapa="inicio",
            status_atendimento="aguardando_humano",
            historico="",
        )
        db.add(conversa)
        db.flush()

    registro, criado = registrar_mensagem(
        db,
        empresa_id=conexao.empresa_id,
        conversa_id=conversa.id,
        cliente_id=conversa.cliente_id,
        remetente=REMETENTE_SAIDA_APLICATIVO,
        texto=texto,
        from_me=True,
        mensagem_id_externo=mensagem_id,
    )

    if registro.remetente != REMETENTE_SAIDA_APLICATIVO:
        return "id_mensagem_em_conflito"

    if not criado and (registro.texto or registro.midia_url) and not tem_midia:
        return "mensagem_duplicada"

    registro.texto = texto or registro.texto
    registro.conexao_canal_id = conexao.id
    registro.especialista_id = conexao.especialista_id
    registro.sessao_waha = conexao.sessao_waha
    registro.status_processamento = "concluida"
    registro.processado_em = func.now()

    conversa.ultima_mensagem_humano_em = func.now()
    conversa.atualizado_em = func.now()

    if not tem_midia:
        from app.services.central_whatsapp_eventos_mensagem import aplicar_eventos_pendentes

        aplicar_eventos_pendentes(db, registro, mensagem_id)
    if tem_midia:
        if registro.midia_url is None:
            registro.tipo = "midia"
        return anexar_midia_waha(db, registro=registro, empresa_id=conexao.empresa_id,
                                 sessao=conexao.sessao_waha, mensagem_id=mensagem_id, payload=payload)
    db.flush()
    return "saida_aplicativo_registrada"
