"""Importa somente o historico explicitamente solicitado de uma conversa existente."""

from datetime import datetime, timezone
from urllib.parse import quote

import requests

from app.models.models import Conversa, Mensagem
from app.services.followup_destinatario_service import chat_id_whatsapp_valido
from app.services.waha_destino import PREFIXO, ConfiguracaoWahaInvalida, resolver_waha


def sincronizar_conversa_noweb(db, conexao, conversa_id):
    conversa = db.query(Conversa).filter_by(
        id=conversa_id, empresa_id=conexao.empresa_id, conexao_canal_id=conexao.id,
        canal="whatsapp",
    ).with_for_update().one_or_none()
    if conversa is None or not chat_id_whatsapp_valido(conversa.identificador):
        raise ValueError("conversa_indisponivel")

    try:
        rota = resolver_waha(conexao.sessao_waha)
        if not rota.chave_api:
            raise ValueError
        sessao = quote(rota.sessao, safe="")
        chat = quote(conversa.identificador, safe="")
        with requests.Session() as http:
            def consultar(caminho, params=None):
                resposta = http.get(
                    rota.origem + caminho, params=params, headers=rota.headers,
                    timeout=(3, 8), allow_redirects=False,
                )
                if resposta.status_code != 200:
                    raise ValueError
                return resposta.json()

            estado = consultar(f"/api/sessions/{sessao}")
            config = estado.get("config") or {}
            metadata = config.get("metadata") or {}
            if conexao.sessao_waha.startswith(PREFIXO) and metadata.get("orionSessao") != conexao.sessao_waha:
                raise ValueError
            engine = estado.get("engine")
            nome_engine = engine.get("engine") if isinstance(engine, dict) else engine
            store = config.get("noweb", {}).get("store", {})
            if (estado.get("name") != rota.sessao or estado.get("status") != "WORKING"
                    or nome_engine != "NOWEB" or store.get("enabled") is not True):
                raise ValueError
            historico = consultar(f"/api/{sessao}/chats/{chat}/messages", {
                "limit": 50, "downloadMedia": "false",
            })
            contato = consultar("/api/contacts", {"session": rota.sessao, "contactId": conversa.identificador})
    except (requests.RequestException, ConfiguracaoWahaInvalida, ValueError, AttributeError, TypeError) as erro:
        raise ValueError("historico_noweb_indisponivel") from erro
    if not isinstance(historico, list) or len(historico) > 50:
        raise ValueError("historico_noweb_invalido")

    if isinstance(contato, dict) and not conversa.nome:
        nome = contato.get("name") or contato.get("pushname") or contato.get("pushName")
        if isinstance(nome, str) and nome.strip():
            conversa.nome = nome.strip()[:150]

    importadas = 0
    for item in historico:
        if not isinstance(item, dict):
            continue
        ident, texto, timestamp = item.get("id"), item.get("body"), item.get("timestamp")
        saida = item.get("fromMe")
        if (type(saida) is not bool or not isinstance(ident, str) or not 0 < len(ident) <= 180
                or not isinstance(texto, str) or not texto.strip() or type(timestamp) is not int):
            continue
        if item.get("to" if saida else "from") != conversa.identificador:
            continue
        try:
            criado = datetime.fromtimestamp(timestamp, timezone.utc)
        except (OSError, ValueError, OverflowError):
            continue
        if db.query(Mensagem.id).filter_by(
            empresa_id=conversa.empresa_id, conversa_id=conversa.id,
        ).filter((Mensagem.mensagem_id_externo == ident) | (Mensagem.mensagem_id_waha == ident)).first():
            continue
        # Importacao historica nao chama o servico de mensagens em tempo real.
        db.add(Mensagem(
            empresa_id=conversa.empresa_id, conversa_id=conversa.id,
            cliente_id=conversa.cliente_id, conexao_canal_id=conexao.id,
            remetente="historico", from_me=saida, texto=texto[:4096], criado_em=criado,
            mensagem_id_externo=ident, sessao_waha=conexao.sessao_waha,
            status_processamento="concluida",
        ))
        importadas += 1
    return importadas
