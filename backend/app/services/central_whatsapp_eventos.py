"""Invalidacoes da Central, calculadas somente sobre dados visiveis ao usuario."""

import asyncio
import json

from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.encoders import jsonable_encoder

from app.database.database import SessionLocal
from app.services.central_whatsapp_consultas import listar_conversas, listar_historico
from app.services.followup_identidade_api import identificar_usuario_api


def snapshot(token, empresa_id, conversa_id, autorizar):
    with SessionLocal() as db:
        identidade, _ = identificar_usuario_api(db, token=token)
        if identidade is None:
            raise HTTPException(401)
        identidade = autorizar(autorizar_leitura=identidade, empresa_id=empresa_id, db=db)
        lista = listar_conversas(db, identidade=identidade, limite=100, deslocamento=0,
                                  conexao_id=None, fixar_conversa_id=conversa_id)
        mensagens = listar_historico(
            db, identidade=identidade, conversa_id=conversa_id, limite=100, deslocamento=0,
        ) if conversa_id is not None else None
        return jsonable_encoder({"conversas": lista, "mensagens": mensagens})


def delta(anterior, atual):
    if atual is None:
        return None
    anterior = anterior or []
    existentes = {item["id"]: item for item in anterior}
    ids = [item["id"] for item in atual]
    conjunto = set(ids)
    return {
        "ordem": ids,
        "alteradas": [item for item in atual if existentes.get(item["id"]) != item],
        "removidas": [item["id"] for item in anterior if item["id"] not in conjunto],
    }


async def transmitir(request, token, empresa_id, conversa_id, autorizar, anterior):
    yield "event: dados\ndata: " + json.dumps({k: delta(None, v) for k, v in anterior.items()}) + "\n\n"
    for _ in range(100):
        await asyncio.sleep(3)
        if await request.is_disconnected():
            return
        try:
            atual = await run_in_threadpool(snapshot, token, empresa_id, conversa_id, autorizar)
        except HTTPException:
            yield "event: sessao\ndata: {}\n\n"
            return
        diferencas = {k: delta(anterior[k], v) for k, v in atual.items() if v != anterior[k]}
        anterior = atual
        if diferencas:
            yield "event: dados\ndata: " + json.dumps(diferencas) + "\n\n"
        else:
            yield ": orion\n\n"
