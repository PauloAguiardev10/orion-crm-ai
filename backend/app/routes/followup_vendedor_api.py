from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.services.followup_dependencia_api import (
    exigir_usuario_api,
    obter_db_api,
)
from app.services.followup_confirmacao_envio_humano import (
    confirmar_reserva_envio_humano,
)

from app.services.followup_confirmacao_execucao_humana import (
    confirmar_execucao_envio_humano,
)


import os

from app.services.followup_envio_autorizado import (
    executar_envio_autorizado,
)
from app.services.followup_transporte_waha import (
    transportar_mensagem_waha,
)


router = APIRouter(
    prefix="/api/followup/vendedor",
    tags=["Follow-up Vendedor"],
)


class ReservaMensagemRequest(BaseModel):
    conversa_id: int = Field(gt=0)
    conexao_canal_id: int = Field(gt=0)
    texto: str = Field(min_length=1, max_length=4096)
    chave_solicitacao: str = Field(min_length=1, max_length=128)


@router.post("/reservar-mensagem")
def reservar_mensagem_vendedor(
    dados: ReservaMensagemRequest,
    identidade: dict = Depends(exigir_usuario_api),
    db: Session = Depends(obter_db_api),
):
    resultado = confirmar_reserva_envio_humano(
        db,
        usuario_id=identidade["usuario_id"],
        empresa_id=identidade["empresa_id"],
        conversa_id=dados.conversa_id,
        conexao_canal_id=dados.conexao_canal_id,
        texto=dados.texto,
        chave_solicitacao=dados.chave_solicitacao,
    )

    mensagem_id, situacao = resultado

    if situacao == "reserva_confirmada":
        return JSONResponse(
            status_code=201,
            content={
                "mensagem_id": mensagem_id,
                "situacao": situacao,
            },
        )

    if situacao == "solicitacao_duplicada":
        return {
            "mensagem_id": mensagem_id,
            "situacao": situacao,
        }

    if situacao in (
        "texto_invalido",
        "chave_invalida",
    ):
        codigo = 400
    elif situacao in (
        "usuario_inativo",
        "usuario_nao_autorizado",
        "especialista_nao_vinculado",
    ):
        codigo = 403
    else:
        codigo = 409

    raise HTTPException(
        status_code=codigo,
        detail=situacao,
    )


class ConfirmarExecucaoRequest(BaseModel):
    conversa_id: int = Field(gt=0)
    conexao_canal_id: int = Field(gt=0)
    mensagem_id: int = Field(gt=0)


# Endpoint /assumir-envio desativado: nao realiza transporte WAHA.
def assumir_envio_vendedor(
    dados: ConfirmarExecucaoRequest,
    identidade: dict = Depends(exigir_usuario_api),
    db: Session = Depends(obter_db_api),
):
    confirmado, situacao = confirmar_execucao_envio_humano(
        db,
        usuario_id=identidade["usuario_id"],
        empresa_id=identidade["empresa_id"],
        conversa_id=dados.conversa_id,
        conexao_canal_id=dados.conexao_canal_id,
        mensagem_id=dados.mensagem_id,
    )

    if confirmado and situacao == "execucao_confirmada":
        return {
            "mensagem_id": dados.mensagem_id,
            "situacao": situacao,
        }

    raise HTTPException(
        status_code=409,
        detail=situacao,
    )


@router.post("/executar-mensagem")
def executar_mensagem_vendedor(
    dados: ConfirmarExecucaoRequest,
    identidade: dict = Depends(exigir_usuario_api),
    db: Session = Depends(obter_db_api),
):
    if os.getenv("ORION_ENVIO_HUMANO_ATIVO") != "1":
        raise HTTPException(
            status_code=503,
            detail="Envio humano ainda nao habilitado.",
        )

    confirmado, motivo = confirmar_execucao_envio_humano(
        db,
        usuario_id=identidade["usuario_id"],
        empresa_id=identidade["empresa_id"],
        conversa_id=dados.conversa_id,
        conexao_canal_id=dados.conexao_canal_id,
        mensagem_id=dados.mensagem_id,
    )

    if not confirmado:
        raise HTTPException(
            status_code=409,
            detail=motivo,
        )

    sucesso, situacao = executar_envio_autorizado(
        db,
        usuario_id=identidade["usuario_id"],
        empresa_id=identidade["empresa_id"],
        conversa_id=dados.conversa_id,
        mensagem_id=dados.mensagem_id,
        conexao_canal_id=dados.conexao_canal_id,
        transportador=transportar_mensagem_waha,
    )

    return {
        "mensagem_id": dados.mensagem_id,
        "sucesso": sucesso,
        "situacao": situacao,
    }
