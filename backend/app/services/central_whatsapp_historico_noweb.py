"""Importa somente o historico explicitamente solicitado de uma conversa existente."""

import json
import os
from hashlib import sha256

from datetime import datetime, timezone
from urllib.parse import quote

import requests

from app.models.models import Conversa, Mensagem
from app.services.central_whatsapp_citacoes import extrair_citacao_waha
from app.services.followup_destinatario_service import chat_id_whatsapp_valido
from app.services.central_whatsapp_grupos import nome_grupo
from app.services.waha_destino import PREFIXO, ConfiguracaoWahaInvalida, resolver_waha
from app.services.waha_gestao_transporte import extrair_numero_conta
from app.services.waha_identificadores import aliases_chat, aliases_mensagem, chat_canonico, chat_no_id_mensagem, jid_noweb
from app.services.central_whatsapp_ack import ACKS


class NumeroNowebDivergente(ValueError):
    pass


def chats_autorizados_noweb(sessao):
    try:
        valores = json.loads(os.getenv("ORION_WAHA_PAREAMENTO_CONTATOS", "{}"))[sessao]
    except (KeyError, ValueError, TypeError):
        return ()
    if not isinstance(valores, list):
        return ()
    return tuple(dict.fromkeys(chat_canonico(chat) for chat in valores if destinatario_noweb_valido(sessao, chat)))


def destinatario_noweb_valido(sessao, chat):
    return chat_id_whatsapp_valido(chat_canonico(chat)) or nome_grupo(sessao, chat) is not None


def catalogo_comercial_ativo(sessao):
    try:
        autorizadas = json.loads(os.getenv("ORION_WAHA_CATALOGO_COMERCIAL", "[]"))
    except ValueError:
        return False
    return isinstance(autorizadas, list) and sessao in autorizadas


def _consultar_noweb(cliente, rota, caminho, params=None, *, aceitar_ausente=False):
    resposta = cliente.get(rota.origem + caminho, headers=rota.headers, params=params,
                           timeout=(3, 8), allow_redirects=False)
    if aceitar_ausente and resposta.status_code == 404:
        return None
    if resposta.status_code != 200:
        raise ValueError
    return resposta.json()


def _rota_noweb(http, sessao, numero_esperado=None):
    rota = resolver_waha(sessao)
    if not rota.chave_api:
        raise ValueError
    fisica = quote(rota.sessao, safe="")
    estado = _consultar_noweb(http, rota, f"/api/sessions/{fisica}")
    config = estado.get("config") or {}
    engine = estado.get("engine")
    engine = engine.get("engine") if isinstance(engine, dict) else engine
    if (estado.get("name") != rota.sessao or estado.get("status") != "WORKING" or engine != "NOWEB"
            or config.get("noweb", {}).get("store", {}).get("enabled") is not True
            or sessao.startswith(PREFIXO) and (config.get("metadata") or {}).get("orionSessao") != sessao):
        raise ValueError
    if numero_esperado is not None:
        eu = estado.get("me")
        if not extrair_numero_conta(eu):
            eu = _consultar_noweb(http, rota, f"/api/sessions/{fisica}/me")
        if extrair_numero_conta(eu) != numero_esperado.lstrip("+"):
            raise NumeroNowebDivergente("numero_noweb_divergente")
    return rota, fisica


def pagina_catalogo_noweb(sessao, deslocamento, numero_esperado=None):
    if not catalogo_comercial_ativo(sessao):
        return [], None
    with requests.Session() as http:
        rota, fisica = _rota_noweb(http, sessao, numero_esperado)
        pagina = _consultar_noweb(http, rota, f"/api/{fisica}/chats", {
            "limit": 100, "offset": deslocamento, "sortBy": "id", "sortOrder": "asc",
        })
    if not isinstance(pagina, list) or len(pagina) > 100:
        raise ValueError("catalogo_noweb_invalido")
    ids = [item.get("id") for item in pagina if isinstance(item, dict)]
    chats = list(dict.fromkeys(chat_canonico(chat) for chat in ids if destinatario_noweb_valido(sessao, chat)))
    return chats, assinatura_pagina(ids) if pagina else None


def assinatura_pagina(ids):
    return sha256(json.dumps(ids, sort_keys=True).encode()).hexdigest()


def obter_pagina_noweb(sessao_logica, identificador, *, deslocamento=0, ate=None,
                      pagina=False, desde=None, numero_esperado=None):
    from app.services.central_whatsapp_midia import midia_ativa

    baixar_midia = pagina and midia_ativa()
    limite = 20 if baixar_midia else 50
    try:
        grupo = nome_grupo(sessao_logica, identificador)
        chat = quote(jid_noweb(identificador), safe="")
        with requests.Session() as http:
            rota, sessao = _rota_noweb(http, sessao_logica, numero_esperado)
            historico = _consultar_noweb(http, rota, f"/api/{sessao}/chats/{chat}/messages", {
                "limit": limite, "offset": deslocamento, "downloadMedia": str(baixar_midia).lower(),
                **({"filter.timestamp.lte": ate} if ate is not None else {}),
                **({"filter.timestamp.gte": desde} if desde is not None else {}),
            })
            contato = None if grupo else _consultar_noweb(http, rota, "/api/contacts", {
                "session": rota.sessao, "contactId": chat_canonico(identificador),
            }, aceitar_ausente=numero_esperado is not None)
    except NumeroNowebDivergente:
        raise
    except (requests.RequestException, ConfiguracaoWahaInvalida, ValueError, AttributeError, TypeError) as erro:
        raise ValueError("historico_noweb_indisponivel") from erro
    if not isinstance(historico, list) or len(historico) > limite:
        raise ValueError("historico_noweb_invalido")
    return historico, contato, grupo, baixar_midia, limite


def contato_confirma_chat(contato, identificador):
    aliases = aliases_chat(identificador)
    return isinstance(contato, dict) and not contato.get("isMe") and not contato.get("isGroup") and (
        contato.get("id") in aliases or (aliases[0].endswith("@lid") and contato.get("lid") in aliases)
    )


def aliases_contato(contato, identificador):
    aliases = aliases_chat(identificador)
    if not contato_confirma_chat(contato, identificador):
        return aliases
    lid = contato.get("lid")
    confirmados = (contato.get("id"), lid if isinstance(lid, str) and lid.endswith("@lid") else None)
    return tuple(dict.fromkeys((
        *aliases, *(alias for chat in confirmados if chat_id_whatsapp_valido(chat_canonico(chat))
                    for alias in aliases_chat(chat)),
    )))


def sincronizar_conversa_noweb(db, conexao, conversa_id, *, exigir_contato_confirmado=False,
                              deslocamento=0, ate=None, pagina=False, desde=None, captura=None, chat_waha=None):
    from app.services.central_whatsapp_midia_entrada import anexar_midia_waha

    conversa = db.query(Conversa).filter_by(
        id=conversa_id, empresa_id=conexao.empresa_id, conexao_canal_id=conexao.id,
        canal="whatsapp",
    ).with_for_update().one_or_none()
    if conversa is None or not destinatario_noweb_valido(conexao.sessao_waha, conversa.identificador):
        raise ValueError("conversa_indisponivel")
    identificador = chat_waha or conversa.identificador
    historico, contato, grupo, baixar_midia, limite = captura or obter_pagina_noweb(
        conexao.sessao_waha, identificador, deslocamento=deslocamento, ate=ate, pagina=pagina,
    )
    aliases = aliases_contato(contato, identificador)
    if conversa.identificador not in aliases:
        raise ValueError("conversa_noweb_ambigua")
    contato_confirmado = contato_confirma_chat(contato, identificador)
    if exigir_contato_confirmado and not grupo and not contato_confirmado:
        raise ValueError("contato_noweb_nao_confirmado")
    if contato_confirmado and not conversa.telefone:
        from app.services.central_whatsapp_contatos import telefone_confirmado_contato

        conversa.telefone = telefone_confirmado_contato(contato, identificador)
    if grupo and not conversa.nome:
        conversa.nome = grupo
    if contato_confirmado and not conversa.nome:
        nome = contato.get("name") or contato.get("pushname") or contato.get("pushName")
        if isinstance(nome, str) and nome.strip():
            conversa.nome = nome.strip()[:150]

    importadas = 0
    vistos = set()
    for item in historico:
        if not isinstance(item, dict):
            continue
        ident, texto, timestamp = item.get("id"), item.get("body"), item.get("timestamp")
        saida = item.get("fromMe")
        tem_midia = item.get("hasMedia") is True
        texto = texto if isinstance(texto, str) else ""
        if (type(saida) is not bool or not isinstance(ident, str) or not 0 < len(ident) <= 180
                or (not texto.strip() and not tem_midia) or type(timestamp) is not int):
            continue
        if captura is not None and ((desde is not None and timestamp < desde) or timestamp > ate):
            continue
        destino = item.get("to" if saida else "from")
        chat_do_id = chat_no_id_mensagem(ident, saida)
        if not destino:
            destino = chat_do_id
        if destino not in aliases or (chat_do_id is not None and chat_do_id not in aliases):
            continue
        participante = item.get("participant") if grupo else None
        if grupo and not saida and not chat_id_whatsapp_valido(chat_canonico(participante)):
            continue
        try:
            criado = datetime.fromtimestamp(timestamp, timezone.utc)
        except (OSError, ValueError, OverflowError):
            continue
        ids = aliases_mensagem(ident, aliases)
        if vistos.intersection(ids):
            continue
        vistos.update(ids)
        existente = db.query(Mensagem).filter_by(
            empresa_id=conversa.empresa_id, conversa_id=conversa.id,
        ).filter(Mensagem.mensagem_id_externo.in_(ids) | Mensagem.mensagem_id_waha.in_(ids)).first()
        if existente is not None:
            if baixar_midia and tem_midia and existente.conexao_canal_id == conexao.id and existente.sessao_waha == conexao.sessao_waha:
                anexar_midia_waha(db, registro=existente, empresa_id=conexao.empresa_id,
                                  sessao=conexao.sessao_waha, mensagem_id=ident, payload=item)
            continue
        # Importacao historica nao chama o servico de mensagens em tempo real.
        ack = item.get("ack")
        confirmacao = ACKS.get(ack) if saida and type(ack) is int else None
        status = confirmacao[1] if confirmacao and item.get("ackName") == confirmacao[0] else None
        registro = Mensagem(
            empresa_id=conversa.empresa_id, conversa_id=conversa.id,
            cliente_id=conversa.cliente_id, conexao_canal_id=conexao.id,
            remetente="historico", from_me=saida, texto=texto[:4096], criado_em=criado,
            mensagem_id_externo=ident, sessao_waha=conexao.sessao_waha,
            status_processamento="concluida", tipo="midia" if tem_midia else "texto",
            status_envio=status,
            central_resposta_waha=extrair_citacao_waha(item, conversa.identificador),
            central_eventos={"participante": participante} if participante else None,
        )
        db.add(registro)
        if baixar_midia and tem_midia:
            anexar_midia_waha(db, registro=registro, empresa_id=conexao.empresa_id,
                              sessao=conexao.sessao_waha, mensagem_id=ident, payload=item)
        importadas += 1
    if pagina:
        resultado = {"importadas": importadas, "proxima": deslocamento + limite if historico else None}
        if captura is not None and historico:
            resultado["assinatura"] = assinatura_pagina([
                item.get("id") for item in historico if isinstance(item, dict)
            ])
        return resultado
    return importadas
