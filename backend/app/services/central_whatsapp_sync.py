"""Sincronização durável do histórico comercial, executada pelo backend."""

import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from threading import Event, Thread

import requests
from sqlalchemy import text

from app.database.database import SessionLocal
from app.models.models import ConexaoCanal, Conversa
from app.services.central_whatsapp_grupos import nome_grupo
from app.services.central_whatsapp_historico_noweb import (
    ErroConsultaNoweb, aliases_contato, assinatura_pagina, catalogo_comercial_ativo, chats_autorizados_noweb,
    contato_confirma_chat, destinatario_noweb_valido, obter_pagina_noweb, pagina_catalogo_noweb,
    sincronizar_conversa_noweb,
)
from app.services.waha_destino import PREFIXO, ConfiguracaoWahaInvalida
from app.services.waha_identificadores import chat_canonico


logger = logging.getLogger(__name__)
INTERVALO_CICLO = timedelta(minutes=5)
SOBREPOSICAO = 900
RECONCILIACAO_COMPLETA = 7 * 86400
LOCK_SYNC_NOWEB = 707241002


def conexoes_elegiveis(db):
    return db.query(ConexaoCanal).filter_by(
        provedor="waha", canal="whatsapp", ativo=True, operacao_suspensa=False,
        pareamento_waha_pendente=False, sofia_institucional=False, gerenciada_crm=True,
    ).filter(ConexaoCanal.sessao_waha.startswith(PREFIXO))


def escopo_conexao(sessao):
    if not sessao:
        return None
    completo = catalogo_comercial_ativo(sessao)
    chats = sorted(chats_autorizados_noweb(sessao))
    if not completo and not chats:
        return None
    try:
        grupos = json.loads(os.getenv("ORION_WAHA_GRUPOS_AUTORIZADOS", "{}"))[sessao]
    except (KeyError, TypeError, ValueError):
        grupos = {}
    grupos = sorted((chat, nome_grupo(sessao, chat)) for chat in grupos
                    if nome_grupo(sessao, chat)) if isinstance(grupos, dict) else []
    return assinatura_pagina([completo, chats, grupos])


def agendar_sincronizacao(db, conexao, *, antecipar=False):
    escopo = escopo_conexao(conexao.sessao_waha)
    if not escopo:
        return
    db.execute(text("""
        INSERT INTO central_sync_noweb (conexao_id, empresa_id, sessao, escopo)
        VALUES (:id, :empresa, :sessao, :escopo)
        ON CONFLICT (conexao_id) DO NOTHING
    """), {"id": conexao.id, "empresa": conexao.empresa_id, "sessao": conexao.sessao_waha, "escopo": escopo})
    if antecipar:
        db.execute(text("""
            UPDATE central_sync_noweb SET executar_em = now()
            WHERE conexao_id = :id AND empresa_id = :empresa AND sessao = :sessao
        """), {"id": conexao.id, "empresa": conexao.empresa_id, "sessao": conexao.sessao_waha})


def _avancar_chat(db, conexao, cursor, numero):
    chat = cursor["chats"][0]
    sessao = conexao.sessao_waha
    completo = catalogo_comercial_ativo(sessao)
    autorizado = destinatario_noweb_valido(sessao, chat) and (completo or chat in chats_autorizados_noweb(sessao))
    if not autorizado:
        _proximo_chat(cursor)
        return
    parametros = {"id": conexao.id, "chat": chat, "ate": cursor["ate"]}
    anterior = db.execute(text("""
        SELECT ate, ultima_varredura_completa FROM central_sync_noweb_chats
        WHERE conexao_id = :id AND chat = :chat
    """), parametros).one_or_none()
    varredura = anterior is None or cursor["ate"] - anterior.ultima_varredura_completa >= RECONCILIACAO_COMPLETA
    desde = None if varredura else max(0, anterior.ate - SOBREPOSICAO)
    captura = obter_pagina_noweb(
        sessao, chat, pagina=True, deslocamento=cursor.get("mensagens", 0),
        ate=cursor["ate"], desde=desde, numero_esperado=numero,
    )
    _, contato, grupo, _, _ = captura
    if not completo and not grupo and not contato_confirma_chat(contato, chat):
        raise ValueError("contato_noweb_nao_confirmado")
    aliases = aliases_contato(contato, chat)
    conversas = db.query(Conversa).filter_by(
        empresa_id=conexao.empresa_id, conexao_canal_id=conexao.id, canal="whatsapp",
    ).filter(Conversa.identificador.in_(aliases)).with_for_update().limit(2).all()
    if len(conversas) > 1:
        raise ValueError("conversa_noweb_ambigua")
    if conversas:
        conversa = conversas[0]
    else:
        identificador = next((chat_canonico(alias) for alias in aliases if alias.endswith("@c.us")), chat)
        conversa = Conversa(
            empresa_id=conexao.empresa_id, conexao_canal_id=conexao.id, canal="whatsapp",
            identificador=identificador, especialista_id=conexao.especialista_id,
            etapa="inicio", status_atendimento="aguardando_humano", historico="",
        )
        db.add(conversa)
        db.flush()

    pagina = sincronizar_conversa_noweb(
        db, conexao, conversa.id, pagina=True, deslocamento=cursor.get("mensagens", 0),
        ate=cursor["ate"], desde=desde, captura=captura, chat_waha=chat,
    )
    if pagina["proxima"] is not None:
        if pagina["assinatura"] == cursor.get("assinatura_mensagens"):
            raise ValueError("paginacao_mensagens_repetida")
        cursor["mensagens"] = pagina["proxima"]
        cursor["assinatura_mensagens"] = pagina["assinatura"]
        return
    db.execute(text("""
        INSERT INTO central_sync_noweb_chats (conexao_id, chat, ate, ultima_varredura_completa)
        VALUES (:id, :chat, :ate, :varredura)
        ON CONFLICT (conexao_id, chat) DO UPDATE
        SET ate = EXCLUDED.ate, ultima_varredura_completa = EXCLUDED.ultima_varredura_completa
    """), {**parametros, "varredura": cursor["ate"] if varredura else anterior.ultima_varredura_completa})
    _proximo_chat(cursor)


def _proximo_chat(cursor):
    cursor["chats"].pop(0)
    cursor.pop("mensagens", None)
    cursor.pop("assinatura_mensagens", None)


def _avancar(db, conexao, cursor, agora, numero):
    cursor.setdefault("ate", int(agora.timestamp()))
    if cursor.get("chats"):
        _avancar_chat(db, conexao, cursor, numero)
        return False

    deslocamento = cursor.get("catalogo", 0)
    sessao = conexao.sessao_waha
    if catalogo_comercial_ativo(sessao):
        chats, assinatura = pagina_catalogo_noweb(sessao, deslocamento, numero)
        if assinatura is None:
            return True
        if assinatura == cursor.get("assinatura_catalogo"):
            raise ValueError("paginacao_catalogo_repetida")
        cursor.update(catalogo=deslocamento + 100, chats=chats, assinatura_catalogo=assinatura)
    else:
        chats = chats_autorizados_noweb(sessao)[deslocamento:deslocamento + 100]
        if not chats:
            return True
        cursor.update(catalogo=deslocamento + 100, chats=list(chats))
    return False


def executar_passo(db, agora=None):
    """Uma página por transação. O cursor e a importação são confirmados juntos."""
    agora = agora or datetime.now(timezone.utc)
    if not db.execute(text("SELECT pg_try_advisory_xact_lock(:chave)"),
                      {"chave": LOCK_SYNC_NOWEB}).scalar_one():
        return False
    elegiveis = conexoes_elegiveis(db)
    # A descoberta também inclui conexões pareadas antes da instalação do worker.
    for conexao in elegiveis.filter(text("""
        EXISTS (SELECT 1 FROM waha_numeros_verificados n WHERE n.conexao_id = conexoes_canais.id)
        AND NOT EXISTS (SELECT 1 FROM central_sync_noweb s WHERE s.conexao_id = conexoes_canais.id)
    """)).all():
        agendar_sincronizacao(db, conexao)
    job = db.execute(text("""
        SELECT s.*, n.numero_e164 FROM central_sync_noweb s
        JOIN conexoes_canais c ON c.id = s.conexao_id
        JOIN waha_numeros_verificados n ON n.conexao_id = c.id
        WHERE c.ativo AND c.gerenciada_crm AND NOT c.operacao_suspensa
          AND NOT c.pareamento_waha_pendente AND NOT c.sofia_institucional
          AND c.provedor = 'waha' AND c.canal = 'whatsapp'
          AND c.sessao_waha LIKE :prefixo AND s.executar_em <= :agora
        ORDER BY s.executar_em, s.conexao_id LIMIT 1 FOR UPDATE OF s, c SKIP LOCKED
    """), {"agora": agora, "prefixo": PREFIXO + "%"}).mappings().first()
    if not job:
        return False
    conexao = elegiveis.filter_by(id=job["conexao_id"]).populate_existing().one()
    params = {"id": conexao.id}
    escopo = escopo_conexao(conexao.sessao_waha)
    if not escopo:
        db.execute(text("DELETE FROM central_sync_noweb WHERE conexao_id = :id"), params)
        return True
    cursor = job["cursor"]
    if (job["empresa_id"], job["sessao"], job["escopo"]) != (conexao.empresa_id, conexao.sessao_waha, escopo):
        db.execute(text("DELETE FROM central_sync_noweb WHERE conexao_id = :id"), params)
        agendar_sincronizacao(db, conexao)
        return True

    try:
        # O savepoint reverte apenas a página que falhou.
        with db.begin_nested():
            finalizado = _avancar(db, conexao, cursor, agora, job["numero_e164"])
    except (requests.RequestException, ConfiguracaoWahaInvalida, ValueError, TypeError, AttributeError) as erro:
        falhas = min(job["falhas"] + 1, 16)
        codigo = str(erro) if isinstance(erro, ValueError) and str(erro) in {
            "contato_noweb_nao_confirmado", "conversa_noweb_ambigua",
            "paginacao_mensagens_repetida", "paginacao_catalogo_repetida", "catalogo_noweb_invalido",
            "numero_noweb_divergente",
        } else erro.codigo if isinstance(erro, ErroConsultaNoweb) else "noweb_dados_incompativeis"
        if codigo in {"contato_noweb_nao_confirmado", "conversa_noweb_ambigua"}:
            _proximo_chat(cursor)
            cursor["ignorados"] = cursor.get("ignorados", 0) + 1
            db.execute(text("""
                UPDATE central_sync_noweb SET cursor = CAST(:cursor AS jsonb),
                    falhas = 0, erro = :erro, executar_em = :agora WHERE conexao_id = :id
            """), {**params, "cursor": json.dumps(cursor), "erro": codigo, "agora": agora})
            return True
        db.execute(text("""
            UPDATE central_sync_noweb SET falhas = :falhas, erro = :erro, executar_em = :quando
            WHERE conexao_id = :id
        """), {**params, "falhas": falhas, "erro": codigo,
               "quando": agora + timedelta(seconds=min(900, 5 * 2 ** falhas))})
        return True
    db.execute(text("""
        UPDATE central_sync_noweb SET cursor = CAST(:cursor AS jsonb), falhas = 0, erro = :erro,
            executar_em = :quando, ultimo_sucesso = COALESCE(:sucesso, ultimo_sucesso)
        WHERE conexao_id = :id
    """), {**params, "cursor": json.dumps({} if finalizado else cursor),
           "quando": agora + (INTERVALO_CICLO if finalizado else timedelta(seconds=1)),
           "sucesso": agora if finalizado else None,
           "erro": "ciclo_com_chats_ignorados" if cursor.get("ignorados") else None})
    return True


def _executar_worker(parar):
    while not parar.is_set():
        espera = 2
        try:
            with SessionLocal.begin() as db:
                if executar_passo(db):
                    espera = 0.2
        except Exception as erro:
            logger.warning("Sincronização NOWEB indisponível (%s)", type(erro).__name__)
            espera = 30
        parar.wait(espera)


@asynccontextmanager
async def ciclo_sync_noweb(_app):
    from app.services.central_whatsapp_midia import midia_ativa
    from app.services.central_whatsapp_sync_midias import executar_worker_midias

    parar = Event()
    workers = []
    if os.getenv("ORION_WAHA_HISTORICO_ATIVO") == "1":
        workers.append(Thread(target=_executar_worker, args=(parar,), name="central-sync-noweb", daemon=True))
        if midia_ativa():
            workers.append(Thread(target=executar_worker_midias, args=(parar,), name="central-sync-midias", daemon=True))
    for worker in workers:
        worker.start()
    try:
        yield
    finally:
        parar.set()
        for worker in workers:
            worker.join(timeout=2)
