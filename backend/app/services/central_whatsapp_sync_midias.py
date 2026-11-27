"""Recuperação de anexos do Store, independente do cursor do catálogo."""

import logging
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

import requests
from sqlalchemy import text

from app.database.database import SessionLocal
from app.models.models import ConexaoCanal, Conversa, Mensagem
from app.services.central_whatsapp_historico_noweb import (
    ErroConsultaNoweb, _consultar_noweb, _rota_noweb, catalogo_comercial_ativo,
    chats_autorizados_noweb, destinatario_noweb_valido,
)
from app.services.central_whatsapp_midia import FORMATOS, ErroHTTPArquivoWaha, baixar_midia_waha, guardar_midia
from app.services.waha_identificadores import aliases_mensagem, jid_noweb


logger = logging.getLogger(__name__)
TIMEOUT_MIDIA = (3, 45)
MAX_FALHAS = 8


def _conexao(db, job, *, bloquear=False):
    consulta = db.query(ConexaoCanal).filter_by(
        id=job["conexao_id"], empresa_id=job["empresa_id"], sessao_waha=job["sessao"],
        ativo=True, gerenciada_crm=True, sofia_institucional=False, operacao_suspensa=False,
        pareamento_waha_pendente=False, canal="whatsapp", provedor="waha",
    )
    return (consulta.with_for_update() if bloquear else consulta).first()


def _mensagem(db, job, *, bloquear=False):
    consulta = db.query(Mensagem).join(Conversa, Mensagem.conversa_id == Conversa.id).filter(
        Mensagem.id == job["mensagem_id"], Mensagem.empresa_id == job["empresa_id"],
        Mensagem.conexao_canal_id == job["conexao_id"], Mensagem.sessao_waha == job["sessao"],
        Mensagem.midia_url.is_(None), Mensagem.tipo != "excluida",
        Conversa.empresa_id == job["empresa_id"], Conversa.conexao_canal_id == job["conexao_id"],
        Conversa.canal == "whatsapp",
    )
    return (consulta.with_for_update(of=Mensagem) if bloquear else consulta).first()


def _recuperar(job):
    chat = quote(jid_noweb(job["chat"]), safe="")
    ident = quote(job["id_waha"], safe="")
    with requests.Session() as http:
        rota, fisica = _rota_noweb(http, job["sessao"], job["numero_e164"])
        dados = _consultar_noweb(http, rota, f"/api/{fisica}/chats/{chat}/messages/{ident}",
                               {"downloadMedia": "true"}, timeout=TIMEOUT_MIDIA)
    if not isinstance(dados, dict) or dados.get("id") not in aliases_mensagem(job["id_waha"]):
        raise ErroConsultaNoweb("midia_dados_incompativeis")
    midia = dados.get("media")
    if dados.get("hasMedia") is not True or not isinstance(midia, dict) or not isinstance(midia.get("url"), str):
        raise ErroConsultaNoweb("midia_indisponivel")
    return baixar_midia_waha(midia, sessao=job["sessao"], mensagem_id=dados["id"], timeout=TIMEOUT_MIDIA)


def executar_midia(db, agora=None):
    agora = agora or datetime.now(timezone.utc)
    if not db.execute(text("SELECT pg_try_advisory_xact_lock(707241003)")).scalar_one():
        return False
    job = db.execute(text("""
        SELECT j.*, n.numero_e164 FROM central_sync_midias j
        JOIN waha_numeros_verificados n ON n.conexao_id = j.conexao_id
        WHERE NOT j.concluido AND j.executar_em <= :agora
        ORDER BY j.executar_em, j.mensagem_id LIMIT 1 FOR UPDATE OF j SKIP LOCKED
    """), {"agora": agora}).mappings().first()
    if not job:
        return False
    falhas = job["falhas"]
    erro = None
    sessao, chat = job["sessao"], job["chat"]
    autorizado = destinatario_noweb_valido(sessao, chat) and (
        catalogo_comercial_ativo(sessao) or chat in chats_autorizados_noweb(sessao)
    )
    if autorizado and _conexao(db, job) and _mensagem(db, job):
        try:
            nome, mime, dados = _recuperar(job)
            # A rede não mantém bloqueios na conexão ou conversa.
            registro = _mensagem(db, job, bloquear=True) if _conexao(db, job, bloquear=True) else None
            if registro is not None:
                registro.midia_url = guardar_midia(job["empresa_id"], nome, dados)
                registro.midia_tipo = mime
                registro.tipo = FORMATOS[mime][0]
        except ErroConsultaNoweb as falha:
            erro = falha.codigo
        except requests.Timeout:
            erro = "midia_timeout"
        except ErroHTTPArquivoWaha as falha:
            erro = f"midia_http_{falha.status}"
        except (TypeError, AttributeError):
            erro = "midia_dados_incompativeis"
        except (OSError, ValueError, requests.RequestException):
            erro = "midia_download_indisponivel"
        if erro:
            falhas += 1
    db.execute(text("""
        UPDATE central_sync_midias SET falhas=:falhas, erro=:erro, concluido=:concluido,
            executar_em=:quando WHERE mensagem_id=:id
    """), {"falhas": falhas, "erro": erro, "concluido": not erro or falhas >= MAX_FALHAS,
           "quando": agora + timedelta(seconds=min(900, 5 * 2 ** falhas)), "id": job["mensagem_id"]})
    return True


def executar_worker_midias(parar):
    while not parar.is_set():
        espera = 2
        try:
            with SessionLocal.begin() as db:
                if executar_midia(db):
                    espera = 0.2
        except Exception as erro:
            logger.warning("Fila de mídias NOWEB indisponível (%s)", type(erro).__name__)
            espera = 30
        parar.wait(espera)
