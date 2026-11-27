from typing import Literal
from functools import partial
from hashlib import sha256

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from pydantic import BaseModel, Field, StrictBool, field_validator
from sqlalchemy import text
from sqlalchemy.orm import Session
from starlette.datastructures import UploadFile
from app.models.models import ConexaoCanal, Conversa, Mensagem
from app.services.central_whatsapp_contatos import identificar_telefone_waha, obter_foto_grupo_waha, obter_foto_waha
from app.services.central_whatsapp_midia import (
    FORMATOS, LIMITE_MIDIA, caminho_midia, enviar_midia_waha, guardar_midia, midia_ativa,
    validar_midia,
)
from app.services.waha_gestao_conexoes import (
    atualizar_conexao, cadastrar_conexao, capacidade_usuarios, contar_conexoes_comerciais, exigir_gerenciada, listar_conexoes,
    obter_conexao, plano_conexoes,
)
from app.services.waha_numero_verificado import confirmar_numero_waha
from app.services.waha_gestao_transporte import ErroGestaoWaha, TransporteGestaoWaha

from app.services.followup_dependencia_api import (
    bearer, exigir_usuario_api,
    obter_db_api,
)
from app.services.central_whatsapp_atendimento import (
    ATENDIMENTO_HUMANO, atendentes_autorizados,
    gerenciar_atendimento_whatsapp,
)
from app.services.central_whatsapp_consultas import (
    PERFIS_CENTRAL,
    PERFIS_ADMINISTRATIVOS,
    consultar_anexo,
    consultar_contexto_conversa,
    listar_filtros_conversas,
    registrar_leitura,
    listar_conversas,
    listar_historico,
)

router = APIRouter(
    prefix="/api/central-whatsapp",
    tags=["Central WhatsApp"],
)


def exigir_leitura_central(identidade: dict = Depends(exigir_usuario_api)) -> dict:
    if identidade["nivel"] not in PERFIS_CENTRAL:
        raise HTTPException(status_code=403, detail="Perfil sem acesso à Central.")
    return identidade


def exigir_empresa_central(
    empresa_id: int | None = Query(None, gt=0),
    identidade: dict = Depends(exigir_leitura_central),
    db: Session = Depends(obter_db_api),
) -> dict:
    if empresa_id is None or empresa_id == identidade["empresa_id"]:
        return identidade
    if identidade["nivel"] not in ("orion_admin", "parceiro_admin"):
        raise HTTPException(status_code=403, detail="empresa_nao_autorizada")
    permitida = db.execute(text("""
        SELECT id FROM empresas
        WHERE id = :empresa_id AND status = 'ativa'
          AND (:orion OR parceiro_id = :empresa_login_id)
    """), {
        "empresa_id": empresa_id,
        "empresa_login_id": identidade["empresa_id"],
        "orion": identidade["nivel"] == "orion_admin",
    }).scalar()
    if permitida is None:
        raise HTTPException(status_code=403, detail="empresa_nao_autorizada")
    return {**identidade, "empresa_id": empresa_id, "empresa_propria": False}


def exigir_gestao_conexoes(identidade: dict = Depends(exigir_empresa_central)):
    if identidade["nivel"] not in PERFIS_ADMINISTRATIVOS:
        raise HTTPException(status_code=403, detail="gestao_conexoes_nao_autorizada")
    return identidade


def _conexao_publica(conexao):
    return {
        "id": conexao.id, "nome": conexao.nome_conexao or f"WhatsApp legado #{conexao.id}",
        "especialista_id": conexao.especialista_id, "sofia_ativa": conexao.sofia_ativa,
        "gerenciada": conexao.gerenciada_crm, "suspensa": conexao.operacao_suspensa,
        "pareamento_pendente": conexao.pareamento_waha_pendente,
        "ativa": conexao.ativo, "sofia_institucional": conexao.sofia_institucional,
    }


class NovaConversaWhatsApp(BaseModel):
    conexao_id: int = Field(gt=0)
    telefone: str = Field(pattern=r"^\+?[1-9][0-9]{7,14}$")


@router.get("/conversas/iniciar")
def listar_conexoes_para_inicio(
    identidade: dict = Depends(exigir_empresa_central), db: Session = Depends(obter_db_api),
):
    empresa = identidade["empresa_id"]
    titular = next((item for item in atendentes_autorizados(db, empresa)
                    if item.usuario_id == identidade["usuario_id"]), None)
    if titular is None or not identidade.get("empresa_propria", True):
        return []
    conexoes = db.query(ConexaoCanal).filter_by(
        empresa_id=empresa, provedor="waha", canal="whatsapp", ativo=True, operacao_suspensa=False, sofia_institucional=False,
    ).filter(
        ConexaoCanal.sessao_waha.is_not(None),
        (ConexaoCanal.especialista_id.is_(None)) | (ConexaoCanal.especialista_id == titular.id),
    ).order_by(ConexaoCanal.id).all()
    return [{"id": item.id, "nome": item.nome_conexao or f"WhatsApp #{item.id}"} for item in conexoes]


@router.get("/conexoes/{conexao_id}/contatos")
def consultar_contatos_waha(
    conexao_id: int = Path(gt=0), deslocamento: int = Query(0, ge=0, le=100000),
    busca: str = Query("", max_length=120),
    identidade: dict = Depends(exigir_empresa_central), db: Session = Depends(obter_db_api),
):
    from app.services.central_whatsapp_contatos import listar_contatos_waha
    from app.services.central_whatsapp_historico_noweb import catalogo_comercial_ativo, chats_autorizados_noweb

    if os.getenv("ORION_WAHA_CONTATOS_ATIVO") != "1":
        raise HTTPException(403, "consulta_contatos_desativada")
    if not any(c["id"] == conexao_id for c in listar_conexoes_para_inicio(identidade, db)):
        raise HTTPException(404, "conexao_indisponivel")
    sessao = db.query(ConexaoCanal.sessao_waha).filter_by(
        id=conexao_id, empresa_id=identidade["empresa_id"],
    ).scalar()
    try:
        autorizados = None if catalogo_comercial_ativo(sessao) else chats_autorizados_noweb(sessao)
        return listar_contatos_waha(sessao, deslocamento, busca, autorizados=autorizados)
    except ValueError as erro:
        raise HTTPException(409, str(erro)) from None


@router.get("/conexoes/{conexao_id}/contatos/foto")
def consultar_foto_da_conexao(
    conexao_id: int = Path(gt=0), chat: str = Query(max_length=80),
    identidade: dict = Depends(exigir_empresa_central), db: Session = Depends(obter_db_api),
):
    from app.services.central_whatsapp_contatos import obter_foto_contato_cadastrado
    from app.services.central_whatsapp_historico_noweb import catalogo_comercial_ativo, chats_autorizados_noweb
    from app.services.waha_identificadores import chat_canonico

    if os.getenv("ORION_WAHA_CONTATOS_ATIVO") != "1" or not any(
        c["id"] == conexao_id for c in listar_conexoes_para_inicio(identidade, db)
    ):
        raise HTTPException(404, "foto_indisponivel")
    sessao = db.query(ConexaoCanal.sessao_waha).filter_by(
        id=conexao_id, empresa_id=identidade["empresa_id"],
    ).scalar()
    if not catalogo_comercial_ativo(sessao) and chat_canonico(chat) not in chats_autorizados_noweb(sessao):
        raise HTTPException(404, "foto_indisponivel")
    try:
        imagem, tipo = obter_foto_contato_cadastrado(sessao, chat)
    except ValueError:
        raise HTTPException(404, "foto_indisponivel") from None
    return Response(imagem, media_type=tipo, headers={
        "Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff",
    })


@router.post("/conversas/iniciar", status_code=201)
def iniciar_conversa(
    dados: NovaConversaWhatsApp,
    identidade: dict = Depends(exigir_empresa_central),
    db: Session = Depends(obter_db_api),
):
    empresa = identidade["empresa_id"]
    titular = next((item for item in atendentes_autorizados(db, empresa)
                    if item.usuario_id == identidade["usuario_id"]), None)
    if titular is None or not identidade.get("empresa_propria", True):
        raise HTTPException(403, "conversa_nao_autorizada")
    conexao = db.query(ConexaoCanal).filter_by(
        id=dados.conexao_id, empresa_id=empresa, provedor="waha", canal="whatsapp",
        ativo=True, operacao_suspensa=False, sofia_institucional=False,
    ).with_for_update().one_or_none()
    if conexao is None or not conexao.sessao_waha or conexao.especialista_id not in (None, titular.id):
        raise HTTPException(404, "conexao_indisponivel")
    telefone = dados.telefone.lstrip("+")
    try:
        identificador = identificar_telefone_waha(conexao.sessao_waha, telefone)
    except ValueError as erro:
        raise HTTPException(409, str(erro)) from None
    existentes = db.query(Conversa).filter_by(
        empresa_id=empresa, conexao_canal_id=conexao.id, canal="whatsapp",
    ).filter((Conversa.identificador.in_((identificador, f"{telefone}@c.us"))) | (Conversa.telefone == telefone)).limit(2).all()
    if existentes:
        if len(existentes) != 1 or existentes[0].especialista_id != titular.id:
            raise HTTPException(409, "conversa_indisponivel")
        return {"id": existentes[0].id}
    conversa = Conversa(
        empresa_id=empresa, conexao_canal_id=conexao.id, especialista_id=titular.id,
        canal="whatsapp", identificador=identificador, telefone=telefone,
        etapa="inicio", status_atendimento=ATENDIMENTO_HUMANO, humano_assumiu=True, historico="",
    )
    db.add(conversa)
    db.flush()
    resultado = {"id": conversa.id}
    db.commit()
    return resultado


class DadosConexaoWaha(BaseModel):
    nome_conexao: str = Field(min_length=1, max_length=100)
    especialista_id: int | None = Field(None, gt=0)
    sofia_ativa: StrictBool = True

    @field_validator("nome_conexao")
    @classmethod
    def limpar_nome(cls, valor):
        valor = valor.strip()
        if not valor or not valor.isprintable():
            raise ValueError("Nome inválido")
        return valor


class ConfirmacaoDesconexao(BaseModel):
    confirmar: StrictBool


@router.get("/conexoes")
def consultar_conexoes_waha(
    identidade: dict = Depends(exigir_gestao_conexoes), db: Session = Depends(obter_db_api),
):
    try:
        plano, limite = plano_conexoes(db, identidade["empresa_id"])
        return {"plano": plano, "limite": limite,
                **capacidade_usuarios(db, identidade["empresa_id"], plano),
                "conexoes_contabilizadas": contar_conexoes_comerciais(db, identidade["empresa_id"]),
                "conexoes": [_conexao_publica(c) for c in listar_conexoes(db, identidade)]}
    except ErroGestaoWaha as erro:
        raise HTTPException(erro.status, erro.motivo) from None


@router.post("/conexoes", status_code=201)
def criar_conexao_waha(
    dados: DadosConexaoWaha,
    identidade: dict = Depends(exigir_gestao_conexoes), db: Session = Depends(obter_db_api),
):
    try:
        resultado = _conexao_publica(cadastrar_conexao(db, identidade, dados.model_dump()))
        db.commit()
        return resultado
    except ErroGestaoWaha as erro:
        raise HTTPException(erro.status, erro.motivo) from None


@router.put("/conexoes/{conexao_id}")
def editar_conexao_waha(
    dados: DadosConexaoWaha, conexao_id: int = Path(gt=0),
    identidade: dict = Depends(exigir_gestao_conexoes), db: Session = Depends(obter_db_api),
):
    try:
        conexao = obter_conexao(db, identidade, conexao_id, bloquear=True)
        atualizar_conexao(db, identidade, conexao, dados.model_dump())
        resultado = _conexao_publica(conexao)
        db.commit()
        return resultado
    except ErroGestaoWaha as erro:
        raise HTTPException(erro.status, erro.motivo) from None


@router.post("/conexoes/{conexao_id}/sincronizar-noweb", status_code=202)
def solicitar_sincronizacao_noweb(
    conexao_id: int = Path(gt=0),
    identidade: dict = Depends(exigir_gestao_conexoes), db: Session = Depends(obter_db_api),
):
    from app.services.central_whatsapp_historico_noweb import (
        catalogo_comercial_ativo, chats_autorizados_noweb,
    )
    from app.services.central_whatsapp_sync import agendar_sincronizacao

    if os.getenv("ORION_WAHA_HISTORICO_ATIVO") != "1" or not identidade.get("empresa_propria", True):
        raise HTTPException(403, "historico_noweb_desativado")
    try:
        conexao = obter_conexao(db, identidade, conexao_id)
        exigir_gerenciada(conexao)
        if conexao.operacao_suspensa or conexao.pareamento_waha_pendente:
            raise ErroGestaoWaha("conexao_indisponivel", 409)
        if not (catalogo_comercial_ativo(conexao.sessao_waha) or chats_autorizados_noweb(conexao.sessao_waha)):
            raise ErroGestaoWaha("escopo_noweb_nao_autorizado", 409)
        agendar_sincronizacao(db, conexao, antecipar=True)
        db.commit()
        return {"situacao": "sincronizacao_solicitada"}
    except ErroGestaoWaha as erro:
        raise HTTPException(erro.status, erro.motivo) from None


@router.post("/conexoes/{conexao_id}/historico/{conversa_id}")
def importar_historico_noweb(
    dados: ConfirmacaoDesconexao,
    conexao_id: int = Path(gt=0), conversa_id: int = Path(gt=0),
    identidade: dict = Depends(exigir_gestao_conexoes), db: Session = Depends(obter_db_api),
):
    from app.services.central_whatsapp_historico_noweb import sincronizar_conversa_noweb

    if os.getenv("ORION_WAHA_HISTORICO_ATIVO") != "1":
        raise HTTPException(403, "historico_noweb_desativado")
    if not identidade.get("empresa_propria", True) or dados.confirmar is not True:
        raise HTTPException(403, "importacao_nao_autorizada")
    try:
        conexao = obter_conexao(db, identidade, conexao_id, bloquear=True)
        if not conexao.ativo or conexao.operacao_suspensa:
            raise ErroGestaoWaha("conexao_indisponivel", 404)
        importadas = sincronizar_conversa_noweb(db, conexao, conversa_id)
        db.commit()
        return {"importadas": importadas}
    except ErroGestaoWaha as erro:
        raise HTTPException(erro.status, erro.motivo) from None
    except ValueError as erro:
        raise HTTPException(409, str(erro)) from None


@router.post("/conversas/{conversa_id}/historico-noweb")
def importar_pagina_noweb(
    conversa_id: int = Path(gt=0), deslocamento: int = Query(0, ge=0, le=2147483647),
    ate: int = Query(ge=1, le=4102444800),
    identidade: dict = Depends(exigir_empresa_central), db: Session = Depends(obter_db_api),
):
    from app.services.central_whatsapp_historico_noweb import (
        catalogo_comercial_ativo, chats_autorizados_noweb, destinatario_noweb_valido, sincronizar_conversa_noweb,
    )
    from app.services.waha_identificadores import chat_canonico

    if (os.getenv("ORION_WAHA_HISTORICO_ATIVO") != "1" or not identidade.get("empresa_propria", True)
            or not consultar_contexto_conversa(db, identidade=identidade, conversa_id=conversa_id)):
        raise HTTPException(404, "historico_noweb_indisponivel")
    conversa = db.query(Conversa).filter_by(id=conversa_id, empresa_id=identidade["empresa_id"]).one_or_none()
    conexao = db.query(ConexaoCanal).filter_by(
        id=conversa.conexao_canal_id, empresa_id=identidade["empresa_id"], ativo=True,
        gerenciada_crm=True, provedor="waha", canal="whatsapp", operacao_suspensa=False,
        pareamento_waha_pendente=False, sofia_institucional=False,
    ).with_for_update().one_or_none() if conversa is not None else None
    if (conexao is None or not destinatario_noweb_valido(conexao.sessao_waha, conversa.identificador)
            or (chat_canonico(conversa.identificador) not in chats_autorizados_noweb(conexao.sessao_waha)
                and not catalogo_comercial_ativo(conexao.sessao_waha))):
        raise HTTPException(404, "historico_noweb_indisponivel")
    try:
        resultado = sincronizar_conversa_noweb(db, conexao, conversa_id, deslocamento=deslocamento,
                                               ate=ate, pagina=True, exigir_contato_confirmado=True)
        db.commit()
        return resultado
    except ValueError as erro:
        raise HTTPException(409, str(erro)) from None


@router.get("/conversas/{conversa_id}/foto")
def consultar_foto_contato(
    conversa_id: int = Path(gt=0), identidade: dict = Depends(exigir_empresa_central),
    db: Session = Depends(obter_db_api),
):
    if not consultar_contexto_conversa(db, identidade=identidade, conversa_id=conversa_id):
        raise HTTPException(404, "foto_indisponivel")
    vinculada = db.query(Conversa.identificador, ConexaoCanal.sessao_waha).join(
        ConexaoCanal, ConexaoCanal.id == Conversa.conexao_canal_id,
    ).filter(
        Conversa.id == conversa_id, Conversa.empresa_id == identidade["empresa_id"],
        ConexaoCanal.empresa_id == Conversa.empresa_id, ConexaoCanal.ativo.is_(True),
        ConexaoCanal.operacao_suspensa.is_(False), ConexaoCanal.provedor == "waha",
        ConexaoCanal.canal == "whatsapp",
    ).one_or_none()
    if vinculada is None:
        raise HTTPException(404, "foto_indisponivel")
    try:
        obter_foto = obter_foto_grupo_waha if vinculada.identificador.endswith("@g.us") else obter_foto_waha
        imagem, mime = obter_foto(vinculada.sessao_waha, vinculada.identificador)
    except ValueError:
        raise HTTPException(404, "foto_indisponivel") from None
    return Response(imagem, media_type=mime, headers={
        "Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff",
    })


@router.get("/conexoes/{conexao_id}/estado")
def consultar_estado_waha(
    conexao_id: int = Path(gt=0), identidade: dict = Depends(exigir_gestao_conexoes),
    db: Session = Depends(obter_db_api),
):
    try:
        conexao = obter_conexao(db, identidade, conexao_id)
        if not conexao.sessao_waha:
            return {"estado": "NAO_PROVISIONADA", "numero": None}
        try:
            resultado = TransporteGestaoWaha(conexao.sessao_waha).consultar(conexao.sessao_waha)
        except ErroGestaoWaha as erro:
            if erro.status != 404:
                raise
            resultado = {"estado": "NAO_PROVISIONADA", "numero": None}
        if conexao.pareamento_waha_pendente:
            resultado["numero"] = None
        return JSONResponse({**resultado, "pareamento_pendente": conexao.pareamento_waha_pendente},
                            headers={"Cache-Control": "private, no-store"})
    except ErroGestaoWaha as erro:
        raise HTTPException(erro.status, erro.motivo) from None


@router.post("/conexoes/{conexao_id}/conectar")
def conectar_sessao_waha(
    conexao_id: int = Path(gt=0), identidade: dict = Depends(exigir_gestao_conexoes),
    db: Session = Depends(obter_db_api),
):
    try:
        conexao = obter_conexao(db, identidade, conexao_id, bloquear=True)
        exigir_gerenciada(conexao)
        transporte = TransporteGestaoWaha(conexao.sessao_waha)
        sessao = conexao.sessao_waha
        try:
            estado = transporte.consultar(sessao)["estado"]
        except ErroGestaoWaha as erro:
            if erro.status != 404:
                raise
            transporte.criar(sessao)
            estado = "STOPPED"
        if estado == "WORKING" and not conexao.operacao_suspensa:
            return {"situacao": "conexao_solicitada"}
        if estado == "STOPPED":
            transporte.iniciar(sessao)
        elif estado == "FAILED":
            transporte.reiniciar(sessao)
        elif estado not in ("WORKING", "SCAN_QR_CODE", "STARTING"):
            raise ErroGestaoWaha("estado_waha_nao_suportado", 409)
        conexao.operacao_suspensa = True
        conexao.pareamento_waha_pendente = True
        db.commit()
        return {"situacao": "conexao_solicitada"}
    except ErroGestaoWaha as erro:
        raise HTTPException(erro.status, erro.motivo) from None


@router.post("/conexoes/{conexao_id}/desconectar")
def desconectar_sessao_waha(
    dados: ConfirmacaoDesconexao, conexao_id: int = Path(gt=0),
    identidade: dict = Depends(exigir_gestao_conexoes), db: Session = Depends(obter_db_api),
):
    if not dados.confirmar:
        raise HTTPException(422, "confirmacao_obrigatoria")
    try:
        conexao = obter_conexao(db, identidade, conexao_id, bloquear=True)
        exigir_gerenciada(conexao)
        transporte = TransporteGestaoWaha(conexao.sessao_waha)
        try:
            if transporte.consultar(conexao.sessao_waha)["estado"] != "STOPPED":
                transporte.desconectar(conexao.sessao_waha)
        except ErroGestaoWaha as erro:
            if erro.status != 404:
                raise
        conexao.operacao_suspensa = True
        conexao.pareamento_waha_pendente = False
        db.commit()
        return {"situacao": "conexao_suspensa"}
    except ErroGestaoWaha as erro:
        raise HTTPException(erro.status, erro.motivo) from None


@router.post("/conexoes/{conexao_id}/confirmar-numero")
def confirmar_pareamento_waha(
    conexao_id: int = Path(gt=0), identidade: dict = Depends(exigir_gestao_conexoes),
    db: Session = Depends(obter_db_api),
):
    try:
        conexao = obter_conexao(db, identidade, conexao_id, bloquear=True)
        exigir_gerenciada(conexao)
        if not conexao.pareamento_waha_pendente:
            return {"situacao": "sem_pareamento_pendente"}
        estado = TransporteGestaoWaha(conexao.sessao_waha).consultar(conexao.sessao_waha)
        confirmar_numero_waha(db, conexao, estado)
        if os.getenv("ORION_WAHA_HISTORICO_ATIVO") == "1":
            from app.services.central_whatsapp_sync import agendar_sincronizacao

            agendar_sincronizacao(db, conexao, antecipar=True)
        db.commit()
        return {"situacao": "numero_confirmado"}
    except ErroGestaoWaha as erro:
        raise HTTPException(erro.status, erro.motivo) from None


@router.post("/conexoes/{conexao_id}/reautenticar")
def reautenticar_sessao_waha(
    dados: ConfirmacaoDesconexao, conexao_id: int = Path(gt=0),
    identidade: dict = Depends(exigir_gestao_conexoes), db: Session = Depends(obter_db_api),
):
    if not dados.confirmar:
        raise HTTPException(422, "confirmacao_obrigatoria")
    try:
        conexao = obter_conexao(db, identidade, conexao_id, bloquear=True)
        exigir_gerenciada(conexao)
        sessao = conexao.sessao_waha
        transporte = TransporteGestaoWaha(sessao)
        estado = transporte.consultar(sessao)["estado"]
        if estado not in ("STOPPED", "FAILED"):
            raise ErroGestaoWaha("sessao_precisa_estar_desconectada", 409)
        conexao.operacao_suspensa = True
        conexao.pareamento_waha_pendente = False
        try:
            if estado == "FAILED":
                transporte.desconectar(sessao)
            transporte.esquecer_pareamento(sessao)
            transporte.iniciar(sessao)
        except ErroGestaoWaha:
            db.commit()
            raise
        conexao.operacao_suspensa = True
        conexao.pareamento_waha_pendente = True
        db.commit()
        return {"situacao": "nova_autenticacao_solicitada"}
    except ErroGestaoWaha as erro:
        raise HTTPException(erro.status, erro.motivo) from None


@router.get("/conexoes/{conexao_id}/qr")
def obter_qr_waha(
    conexao_id: int = Path(gt=0), identidade: dict = Depends(exigir_gestao_conexoes),
    db: Session = Depends(obter_db_api),
):
    try:
        conexao = obter_conexao(db, identidade, conexao_id, bloquear=True)
        exigir_gerenciada(conexao)
        transporte = TransporteGestaoWaha(conexao.sessao_waha)
        if not conexao.pareamento_waha_pendente or transporte.consultar(conexao.sessao_waha)["estado"] != "SCAN_QR_CODE":
            raise ErroGestaoWaha("qr_nao_disponivel", 409)
        return Response(transporte.qr(conexao.sessao_waha), media_type="image/png", headers={
            "Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff",
        })
    except ErroGestaoWaha as erro:
        raise HTTPException(erro.status, erro.motivo) from None


def _resposta_consulta(request, dados):
    resposta = JSONResponse(jsonable_encoder(dados))
    etag = '"' + sha256(resposta.body).hexdigest() + '"'
    cabecalhos = {"ETag": etag, "Cache-Control": "private, no-cache", "Vary": "Authorization"}
    if request.headers.get("If-None-Match") == etag:
        return Response(status_code=304, headers=cabecalhos)
    resposta.headers.update(cabecalhos)
    return resposta


def _autorizar_eventos(*, autorizar_leitura, empresa_id, db):
    identidade = exigir_leitura_central(autorizar_leitura)
    return exigir_empresa_central(empresa_id, identidade, db)


@router.get("/contexto-ui")
def consultar_contexto_ui(
    identidade: dict = Depends(exigir_empresa_central), db: Session = Depends(obter_db_api),
):
    fuso = db.execute(text("SELECT timezone FROM empresas WHERE id = :empresa"),
                      {"empresa": identidade["empresa_id"]}).scalar_one_or_none()
    return {"timezone": fuso or "America/Sao_Paulo"}


@router.get("/eventos")
def acompanhar_central(
    request: Request, empresa_id: int | None = Query(None, gt=0),
    conversa_id: int | None = Query(None, gt=0), credenciais=Depends(bearer),
):
    from app.services.central_whatsapp_eventos import snapshot, transmitir

    if credenciais is None or credenciais.scheme.lower() != "bearer":
        raise HTTPException(401, "autenticacao_obrigatoria")
    token = credenciais.credentials
    inicial = snapshot(token, empresa_id, conversa_id, _autorizar_eventos)
    return StreamingResponse(
        transmitir(request, token, empresa_id, conversa_id, _autorizar_eventos, inicial),
        media_type="text/event-stream",
        headers={"Cache-Control": "private, no-store", "X-Accel-Buffering": "no"},
    )


@router.get("/conversas")
def consultar_conversas(
    request: Request,
    limite: int = Query(100, ge=1, le=200),
    deslocamento: int = Query(0, ge=0),
    conexao_id: int | None = Query(None, gt=0),
    fixar_conversa_id: int | None = Query(None, gt=0),
    busca: str | None = Query(None, max_length=120),
    responsavel_id: int | None = Query(None, ge=0),
    status: str | None = Query(None, max_length=80),
    incluir_fila: bool = False,
    identidade: dict = Depends(exigir_empresa_central),
    db: Session = Depends(obter_db_api),
):
    conversas = listar_conversas(
        db, identidade=identidade, limite=limite,
        deslocamento=deslocamento, conexao_id=conexao_id, incluir_fila=incluir_fila,
        fixar_conversa_id=fixar_conversa_id,
        busca=busca, responsavel_id=responsavel_id, status=status,
    )
    return _resposta_consulta(request, conversas)


@router.get("/conversas/{conversa_id}/mensagens")
def consultar_historico(
    request: Request,
    conversa_id: int = Path(gt=0),
    limite: int = Query(100, ge=1, le=200),
    deslocamento: int = Query(0, ge=0),
    antes_id: int | None = Query(None, gt=0),
    incluir_fila: bool = False,
    identidade: dict = Depends(exigir_empresa_central),
    db: Session = Depends(obter_db_api),
):
    mensagens = listar_historico(
        db, identidade=identidade, conversa_id=conversa_id,
        limite=limite, deslocamento=deslocamento, incluir_fila=incluir_fila, antes_id=antes_id,
    )
    if mensagens is None:
        raise HTTPException(status_code=404, detail="Conversa indisponível.")
    return _resposta_consulta(request, mensagens)


@router.get("/filtros-conversas")
def consultar_filtros_conversas(
    request: Request, incluir_fila: bool = False,
    identidade: dict = Depends(exigir_empresa_central), db: Session = Depends(obter_db_api),
):
    return _resposta_consulta(request, listar_filtros_conversas(
        db, identidade=identidade, incluir_fila=incluir_fila,
    ))


@router.get("/conversas/{conversa_id}/detalhes")
def consultar_detalhes_conversa(
    request: Request, conversa_id: int = Path(gt=0),
    identidade: dict = Depends(exigir_empresa_central), db: Session = Depends(obter_db_api),
):
    detalhes = consultar_contexto_conversa(db, identidade=identidade, conversa_id=conversa_id)
    if detalhes is None:
        raise HTTPException(404, "conversa_indisponivel")
    return _resposta_consulta(request, detalhes)


class LeituraRequest(BaseModel):
    mensagem_id: int = Field(gt=0)


@router.post("/conversas/{conversa_id}/leitura")
def marcar_conversa_lida(
    dados: LeituraRequest, conversa_id: int = Path(gt=0),
    identidade: dict = Depends(exigir_empresa_central), db: Session = Depends(obter_db_api),
):
    ultima = registrar_leitura(
        db, identidade=identidade, conversa_id=conversa_id, mensagem_id=dados.mensagem_id,
    )
    if ultima is None:
        raise HTTPException(404, "mensagem_indisponivel")
    db.commit()
    return {"ultima_lida_id": ultima}


class AssumirAtendimentoRequest(BaseModel):
    conversa_id: int = Field(gt=0)


class AcaoMensagemWaha(BaseModel):
    acao: Literal["reagir", "editar", "excluir"]
    valor: str = Field("", max_length=4096)


@router.get("/capacidades")
def consultar_capacidades(identidade: dict = Depends(exigir_empresa_central)):
    return {"historico_progressivo": os.getenv("ORION_WAHA_HISTORICO_ATIVO") == "1",
            "envio": os.getenv("ORION_CENTRAL_WHATSAPP_ENVIO_ATIVO") == "1",
            "historico": os.getenv("ORION_WAHA_HISTORICO_ATIVO") == "1"
                         and identidade["nivel"] in PERFIS_ADMINISTRATIVOS
                         and identidade.get("empresa_propria", True),
            "presenca": os.getenv("ORION_WAHA_PRESENCA_ATIVA") == "1",
            "arquivo": os.getenv("ORION_WAHA_ARQUIVO_ATIVO") == "1",
            "acoes_mensagem": os.getenv("ORION_WAHA_ACOES_MENSAGEM_ATIVAS") == "1"
                             and os.getenv("ORION_CENTRAL_WHATSAPP_ENVIO_ATIVO") == "1"}


class ArquivarWhatsappRequest(BaseModel):
    arquivada: StrictBool


@router.post("/conversas/{conversa_id}/presenca")
def acompanhar_presenca(
    conversa_id: int = Path(gt=0), identidade: dict = Depends(exigir_empresa_central),
    db: Session = Depends(obter_db_api),
):
    from app.services.central_whatsapp_acoes import assinar_presenca_waha

    if not consultar_capacidades(identidade)["presenca"] or not consultar_contexto_conversa(
        db, identidade=identidade, conversa_id=conversa_id,
    ):
        raise HTTPException(404, "presenca_indisponivel")
    vinculada = db.query(Conversa.identificador, ConexaoCanal.sessao_waha).join(
        ConexaoCanal, ConexaoCanal.id == Conversa.conexao_canal_id,
    ).filter(
        Conversa.id == conversa_id, Conversa.empresa_id == identidade["empresa_id"],
        ConexaoCanal.empresa_id == Conversa.empresa_id, ConexaoCanal.canal == "whatsapp",
        ConexaoCanal.provedor == "waha", ConexaoCanal.ativo.is_(True),
        ConexaoCanal.operacao_suspensa.is_(False), ConexaoCanal.sofia_institucional.is_(False),
    ).one_or_none()
    if vinculada is None:
        raise HTTPException(404, "presenca_indisponivel")
    try:
        assinar_presenca_waha(vinculada.sessao_waha, vinculada.identificador)
    except ValueError as erro:
        raise HTTPException(409, str(erro)) from None
    return {"situacao": "confirmada_waha"}


@router.post("/conversas/{conversa_id}/arquivar")
def alterar_arquivo_whatsapp(
    dados: ArquivarWhatsappRequest, conversa_id: int = Path(gt=0),
    identidade: dict = Depends(exigir_empresa_central), db: Session = Depends(obter_db_api),
):
    from app.services.central_whatsapp_acoes import arquivar_conversa_waha

    if not identidade.get("empresa_propria", True) or not consultar_capacidades(identidade)["arquivo"]:
        raise HTTPException(403, "operacao_desativada")
    try:
        arquivar_conversa_waha(
            db, empresa_id=identidade["empresa_id"], usuario_id=identidade["usuario_id"],
            conversa_id=conversa_id, arquivar=dados.arquivada,
        )
        db.commit()
    except ValueError as erro:
        raise HTTPException(409, str(erro)) from None
    return {"arquivada": dados.arquivada}


@router.post("/conversas/{conversa_id}/mensagens/{mensagem_id}/acao")
def alterar_mensagem_waha(
    dados: AcaoMensagemWaha, conversa_id: int = Path(gt=0), mensagem_id: int = Path(gt=0),
    identidade: dict = Depends(exigir_empresa_central), db: Session = Depends(obter_db_api),
):
    from app.services.central_whatsapp_acoes import executar_acao_mensagem

    if not identidade.get("empresa_propria", True) or not consultar_capacidades(identidade)["acoes_mensagem"]:
        raise HTTPException(403, "operacao_desativada")
    if dados.acao == "reagir" and dados.valor not in ("", "👍", "❤️", "😂", "😮", "😢", "🙏"):
        raise HTTPException(422, "reacao_invalida")
    try:
        executar_acao_mensagem(
            db, empresa_id=identidade["empresa_id"], usuario_id=identidade["usuario_id"],
            conversa_id=conversa_id, mensagem_id=mensagem_id, acao=dados.acao, valor=dados.valor,
        )
        db.commit()
    except ValueError as erro:
        raise HTTPException(409, str(erro)) from None
    return {"situacao": "confirmada_waha"}


@router.get("/conversas/{conversa_id}/mensagens/{mensagem_id}/anexo")
def obter_anexo(
    conversa_id: int = Path(gt=0),
    mensagem_id: int = Path(gt=0),
    identidade: dict = Depends(exigir_empresa_central),
    db: Session = Depends(obter_db_api),
):
    anexo = consultar_anexo(
        db, identidade=identidade, conversa_id=conversa_id, mensagem_id=mensagem_id,
    )
    if anexo and anexo["midia_tipo"] in FORMATOS:
        try:
            arquivo, nome = caminho_midia(identidade["empresa_id"], anexo["midia_url"])
            if arquivo.is_file():
                return FileResponse(
                    arquivo, media_type=anexo["midia_tipo"], filename=nome,
                    headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"},
                )
        except (OSError, ValueError):
            pass
    raise HTTPException(status_code=404, detail="anexo_indisponivel")


class EncerrarAtendimentoRequest(AssumirAtendimentoRequest):
    responsavel_atual_id: int = Field(gt=0)


class TransferirAtendimentoRequest(EncerrarAtendimentoRequest):
    destino_id: int = Field(gt=0)


@router.post("/assumir-atendimento")
def assumir_atendimento(
    dados: AssumirAtendimentoRequest,
    identidade: dict = Depends(exigir_empresa_central),
    db: Session = Depends(obter_db_api),
):
    return _alterar_atendimento(db, identidade, dados, "assumir")


@router.post("/encerrar-atendimento")
def encerrar_atendimento(
    dados: EncerrarAtendimentoRequest,
    identidade: dict = Depends(exigir_empresa_central),
    db: Session = Depends(obter_db_api),
):
    return _alterar_atendimento(db, identidade, dados, "encerrar")


@router.post("/transferir-atendimento")
def transferir_atendimento(
    dados: TransferirAtendimentoRequest,
    identidade: dict = Depends(exigir_empresa_central),
    db: Session = Depends(obter_db_api),
):
    return _alterar_atendimento(db, identidade, dados, "transferir")


@router.get("/atendentes")
def consultar_atendentes(
    identidade: dict = Depends(exigir_empresa_central),
    db: Session = Depends(obter_db_api),
):
    atendentes = list(atendentes_autorizados(db, identidade["empresa_id"]))
    if identidade["nivel"] not in PERFIS_ADMINISTRATIVOS and not any(
        a.usuario_id == identidade["usuario_id"] for a in atendentes
    ):
        raise HTTPException(status_code=403, detail="usuario_nao_autorizado")
    return [{"id": a.id, "nome": a.nome} for a in atendentes]


def _alterar_atendimento(db, identidade, dados, acao):
    try:
        autorizado, situacao = gerenciar_atendimento_whatsapp(
            db,
            empresa_id=identidade["empresa_id"],
            identidade=identidade,
            acao=acao,
            **dados.model_dump(),
        )

        if not autorizado:
            db.rollback()
            codigo = 403 if situacao in (
                "usuario_nao_autorizado",
                "especialista_nao_vinculado",
                "conexao_de_outro_especialista",
                "destino_nao_autorizado",
            ) else 409

            raise HTTPException(
                status_code=codigo,
                detail=situacao,
            )

        db.commit()

        return {
            "conversa_id": dados.conversa_id,
            "situacao": situacao,
        }

    except HTTPException:
        raise
    except Exception:
        db.rollback()
        raise

from app.services.central_whatsapp_reserva import reservar_mensagem_central


class ReservarMensagemRequest(BaseModel):
    encaminhar_conversa_id: int | None = Field(None, gt=0)
    responder_mensagem_id: int | None = Field(None, gt=0)
    conversa_id: int = Field(gt=0)
    texto: str = Field(min_length=1, max_length=4096)
    chave_solicitacao: str = Field(min_length=1, max_length=180)


class ReservarAnexoRequest(AssumirAtendimentoRequest):
    chave_solicitacao: str = Field(min_length=1, max_length=180)
    legenda: str = Field("", max_length=4096)
    gravacao: bool = False


@router.post("/reservar-anexo")
async def reservar_anexo(
    request: Request,
    identidade: dict = Depends(exigir_leitura_central),
    db: Session = Depends(obter_db_api),
):
    if not midia_ativa() or os.getenv("ORION_CENTRAL_WHATSAPP_ENVIO_ATIVO") != "1":
        raise HTTPException(status_code=503, detail="envio_midia_desativado")
    tamanho = request.headers.get("content-length", "")
    if not tamanho.isascii() or not tamanho.isdigit() or len(tamanho) > 10:
        raise HTTPException(status_code=411, detail="tamanho_anexo_obrigatorio")
    if int(tamanho) > LIMITE_MIDIA + 16384:
        raise HTTPException(status_code=413, detail="tamanho_midia_invalido")
    async with request.form(max_files=1, max_fields=4, max_part_size=16384) as formulario:
        arquivo = formulario.get("arquivo")
        if not isinstance(arquivo, UploadFile):
            raise HTTPException(status_code=422, detail="arquivo_obrigatorio")
        try:
            dados = ReservarAnexoRequest.model_validate({
                campo: formulario[campo] for campo in ReservarAnexoRequest.model_fields
                if campo in formulario
            })
        except ValueError as erro:
            raise HTTPException(status_code=422, detail="solicitacao_invalida") from erro
        return await run_in_threadpool(
            _reservar_anexo, db, identidade, dados, arquivo.filename or "",
            arquivo.content_type or "", await arquivo.read(LIMITE_MIDIA + 1),
        )


def _reservar_anexo(db, identidade, solicitacao, nome, tipo, dados):
    conversa_id = solicitacao.conversa_id
    chave_solicitacao = solicitacao.chave_solicitacao
    legenda = solicitacao.legenda
    try:
        if solicitacao.gravacao:
            from app.services.central_whatsapp_envio import preparar_destino_central
            from app.services.central_whatsapp_voz import converter_gravacao

            destino, motivo = preparar_destino_central(
                db, empresa_id=identidade["empresa_id"], usuario_id=identidade["usuario_id"],
                conversa_id=conversa_id,
            )
            if destino is None:
                raise HTTPException(403, motivo)
            dados = converter_gravacao(dados, tipo)
            nome, tipo = "voz.ogg", "audio/ogg"
        mime = validar_midia(nome, tipo, dados)
    except ValueError as erro:
        raise HTTPException(status_code=422, detail=str(erro)) from erro
    if mime == "audio/ogg" and legenda.strip():
        raise HTTPException(status_code=422, detail="audio_sem_legenda")

    caminho = None
    try:
        mensagem_id, situacao = reservar_mensagem_central(
            db, empresa_id=identidade["empresa_id"], usuario_id=identidade["usuario_id"],
            conversa_id=conversa_id, texto=legenda, chave_solicitacao=chave_solicitacao,
            mime=mime,
        )
        if mensagem_id is None:
            codigo = 403 if situacao in (
                "especialista_nao_vinculado", "conversa_nao_autorizada",
                "conexao_de_outro_especialista",
            ) else 409
            raise HTTPException(status_code=codigo, detail=situacao)
        registro = db.get(Mensagem, mensagem_id)
        if situacao == "envio_reservado":
            registro.tipo = FORMATOS[mime][0]
            registro.midia_url = guardar_midia(identidade["empresa_id"], nome, dados)
            caminho, _ = caminho_midia(identidade["empresa_id"], registro.midia_url)
            db.flush()
        else:
            anterior, nome_anterior = caminho_midia(identidade["empresa_id"], registro.midia_url)
            if nome_anterior != nome or anterior.read_bytes() != dados:
                raise HTTPException(status_code=409, detail="chave_solicitacao_em_conflito")
    except (ValueError, OSError) as erro:
        db.rollback()
        if caminho is not None:
            caminho.unlink(missing_ok=True)
        raise HTTPException(status_code=503, detail="armazenamento_indisponivel") from erro
    except Exception:
        db.rollback()
        if caminho is not None:
            caminho.unlink(missing_ok=True)
        raise
    db.commit()
    return {"conversa_id": conversa_id, "mensagem_id": mensagem_id, "situacao": situacao}


@router.post("/reservar-mensagem")
def reservar_mensagem(
    dados: ReservarMensagemRequest,
    identidade: dict = Depends(exigir_usuario_api),
    db: Session = Depends(obter_db_api),
):
    if os.getenv("ORION_CENTRAL_WHATSAPP_ENVIO_ATIVO", "0") != "1":
        raise HTTPException(
            status_code=503,
            detail="envio_central_desativado",
        )

    if dados.encaminhar_conversa_id is not None and (
        dados.responder_mensagem_id is None or dados.encaminhar_conversa_id == dados.conversa_id
    ):
        raise HTTPException(422, "encaminhamento_invalido")

    try:
        mensagem_id, situacao = reservar_mensagem_central(
            db,
            empresa_id=identidade["empresa_id"],
            usuario_id=identidade["usuario_id"],
            conversa_id=dados.conversa_id,
            texto=dados.texto, responder_mensagem_id=dados.responder_mensagem_id,
            encaminhar_conversa_id=dados.encaminhar_conversa_id,
            chave_solicitacao=dados.chave_solicitacao,
        )

        if mensagem_id is None:
            db.rollback()

            codigo = 403 if situacao in (
                "especialista_nao_vinculado",
                "conversa_nao_autorizada",
                "conexao_de_outro_especialista",
            ) else 409

            raise HTTPException(
                status_code=codigo,
                detail=situacao,
            )

        db.commit()

        return {
            "conversa_id": dados.conversa_id,
            "mensagem_id": mensagem_id,
            "situacao": situacao,
        }

    except HTTPException:
        raise
    except Exception:
        db.rollback()
        raise

import os

from app.models.models import Especialista
from app.services.central_whatsapp_preparacao import preparar_envio_central
from app.services.central_whatsapp_execucao import assumir_envio_central
from app.services.central_whatsapp_executor import executar_envio_central
from app.services.followup_transporte_waha import transportar_mensagem_waha


from app.services.central_whatsapp_status import consultar_status_envio_central


@router.get("/pendencias")
def consultar_pendencias_central(
    conversa_id: int,
    identidade: dict = Depends(exigir_usuario_api),
    db: Session = Depends(obter_db_api),
):
    """Consulta pendencias do especialista autenticado."""

    from app.services.central_whatsapp_pendencias import (
        listar_pendencias_envio_central,
    )

    if conversa_id <= 0:
        raise HTTPException(
            status_code=422,
            detail="conversa_invalida",
        )

    especialista = (
        db.query(Especialista)
        .filter(
            Especialista.empresa_id == identidade["empresa_id"],
            Especialista.usuario_id == identidade["usuario_id"],
        )
        .first()
    )

    if especialista is None:
        raise HTTPException(
            status_code=403,
            detail="especialista_nao_vinculado",
        )

    from app.services.central_whatsapp_envio import preparar_destino_central

    destino, situacao = preparar_destino_central(
        db,
        empresa_id=identidade["empresa_id"],
        usuario_id=identidade["usuario_id"],
        conversa_id=conversa_id, permitir_assumir=True,
    )

    if destino is None:
        raise HTTPException(
            status_code=403,
            detail=situacao,
        )

    pendencias = listar_pendencias_envio_central(
        db,
        empresa_id=identidade["empresa_id"],
        conversa_id=conversa_id,
        especialista_id=especialista.id,
    )

    return {"pendencias": pendencias}


@router.get("/status-mensagem")
def consultar_status_mensagem(
    conversa_id: int,
    mensagem_id: int,
    identidade: dict = Depends(exigir_usuario_api),
    db: Session = Depends(obter_db_api),
):
    if conversa_id <= 0 or mensagem_id <= 0:
        raise HTTPException(
            status_code=422,
            detail="identificadores_invalidos",
        )

    especialista = (
        db.query(Especialista)
        .filter(
            Especialista.empresa_id == identidade["empresa_id"],
            Especialista.usuario_id == identidade["usuario_id"],
        )
        .first()
    )

    if especialista is None:
        raise HTTPException(
            status_code=403,
            detail="especialista_nao_vinculado",
        )

    from app.services.central_whatsapp_envio import preparar_destino_central

    destino, situacao = preparar_destino_central(
        db,
        empresa_id=identidade["empresa_id"],
        usuario_id=identidade["usuario_id"],
        conversa_id=conversa_id,
    )

    if destino is None:
        raise HTTPException(
            status_code=403,
            detail=situacao,
        )

    resultado = consultar_status_envio_central(
        db,
        empresa_id=identidade["empresa_id"],
        conversa_id=conversa_id,
        mensagem_id=mensagem_id,
        especialista_id=especialista.id,
    )

    if resultado is None:
        raise HTTPException(
            status_code=404,
            detail="mensagem_nao_encontrada",
        )

    return resultado


class ExecutarMensagemRequest(BaseModel):
    conversa_id: int = Field(gt=0)
    mensagem_id: int = Field(gt=0)


@router.post("/executar-mensagem")
def executar_mensagem(
    dados: ExecutarMensagemRequest,
    identidade: dict = Depends(exigir_usuario_api),
    db: Session = Depends(obter_db_api),
):
    if os.getenv("ORION_CENTRAL_WHATSAPP_ENVIO_ATIVO", "0") != "1":
        raise HTTPException(
            status_code=503,
            detail="envio_central_desativado",
        )

    try:
        especialista = (
            db.query(Especialista)
            .filter(
                Especialista.empresa_id == identidade["empresa_id"],
                Especialista.usuario_id == identidade["usuario_id"],
            )
            .first()
        )

        if especialista is None:
            raise HTTPException(
                status_code=403,
                detail="especialista_nao_vinculado",
            )

        assumido = assumir_envio_central(
            db,
            empresa_id=identidade["empresa_id"],
            conversa_id=dados.conversa_id,
            mensagem_id=dados.mensagem_id,
            especialista_id=especialista.id,
        )

        if not assumido:
            db.rollback()
            raise HTTPException(
                status_code=409,
                detail="mensagem_indisponivel_ou_ja_processada",
            )

        dados_envio, situacao = preparar_envio_central(
            db,
            empresa_id=identidade["empresa_id"],
            usuario_id=identidade["usuario_id"],
            conversa_id=dados.conversa_id,
            mensagem_id=dados.mensagem_id,
        )

        if dados_envio is None:
            db.rollback()
            raise HTTPException(
                status_code=409,
                detail=situacao,
            )

        transportador = transportar_mensagem_waha
        referencia = dados_envio["resposta_waha"]
        if referencia and referencia.startswith("ENC:"):
            transportador = partial(transportador, encaminhar=referencia.removeprefix("ENC:"))
        elif referencia:
            transportador = partial(transportador, reply_to=referencia)
        if dados_envio["midia_tipo"] or dados_envio["midia_url"]:
            if not midia_ativa():
                raise HTTPException(status_code=503, detail="envio_midia_desativado")
            try:
                caminho, nome = caminho_midia(identidade["empresa_id"], dados_envio["midia_url"])
                with caminho.open("rb") as arquivo:
                    conteudo = arquivo.read(LIMITE_MIDIA + 1)
                mime = validar_midia(nome, dados_envio["midia_tipo"] or "", conteudo)
            except (OSError, ValueError) as erro:
                raise HTTPException(status_code=409, detail="anexo_indisponivel") from erro
            transportador = partial(enviar_midia_waha, nome=nome, mime=mime, dados=conteudo)

        db.commit()

        sucesso, resultado = executar_envio_central(
            db,
            empresa_id=identidade["empresa_id"],
            conversa_id=dados.conversa_id,
            mensagem_id=dados.mensagem_id,
            especialista_id=especialista.id,
            sessao=dados_envio["sessao"],
            chat_id=dados_envio["chat_id"],
            transportador=transportador,
        )

        if resultado == "resultado_nao_registrado":
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=resultado,
            )

        db.commit()

        return {
            "mensagem_id": dados.mensagem_id,
            "sucesso": sucesso,
            "situacao": resultado,
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise
