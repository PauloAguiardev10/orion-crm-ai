import os

import requests


class SessaoCentralExpirada(Exception):
    pass


def _consultar_central(caminho: str, token: str, *, cache=None, tipo=list, **parametros):
    if not token:
        raise SessaoCentralExpirada

    endereco = os.getenv(
        "ORION_API_INTERNA_URL", "http://127.0.0.1:8000",
    ).rstrip("/")
    headers = {"Authorization": f"Bearer {token}"}
    if cache is not None and "etag" in cache:
        headers["If-None-Match"] = cache["etag"]
    resposta = requests.get(
        f"{endereco}/api/central-whatsapp/{caminho}",
        headers=headers,
        params=parametros,
        timeout=10,
    )
    if resposta.status_code == 304 and cache is not None and "dados" in cache:
        return cache["dados"]
    if resposta.status_code in (401, 403, 404) and cache is not None:
        cache.clear()
    if resposta.status_code == 401:
        raise SessaoCentralExpirada
    resposta.raise_for_status()
    dados = resposta.json()
    if not isinstance(dados, tipo):
        raise ValueError("Resposta inválida da Central.")
    if cache is not None:
        cache.clear()
        if resposta.headers.get("ETag"):
            cache.update(etag=resposta.headers["ETag"], dados=dados)
    return dados


def listar_conversas_whatsapp(
    *, token: str, empresa_id: int | None = None, fixar_conversa_id=None, cache=None,
    busca=None, conexao_id=None, responsavel_id=None, status=None,
) -> list[dict]:
    return _consultar_central(
        "conversas", token, empresa_id=empresa_id, incluir_fila=True,
        fixar_conversa_id=fixar_conversa_id, cache=cache,
        busca=busca, conexao_id=conexao_id, responsavel_id=responsavel_id, status=status,
    )


def listar_mensagens_whatsapp(
    *, token: str, conversa_id: int, empresa_id: int | None = None, cache=None,
    limite=100, antes_id=None,
) -> list[dict]:
    return _consultar_central(
        f"conversas/{int(conversa_id)}/mensagens", token,
        empresa_id=empresa_id, incluir_fila=True, cache=cache,
        limite=limite, antes_id=antes_id,
    )


def listar_atendentes_whatsapp(*, token: str, empresa_id: int | None) -> list[dict]:
    return _consultar_central("atendentes", token, empresa_id=empresa_id)


def consultar_contexto_whatsapp(*, token, empresa_id, conversa_id, cache):
    return _consultar_central(
        f"conversas/{conversa_id}/detalhes", token, tipo=dict, empresa_id=empresa_id, cache=cache,
    )


def listar_filtros_whatsapp(*, token, empresa_id, cache):
    return _consultar_central(
        "filtros-conversas", token, empresa_id=empresa_id, incluir_fila=True, cache=cache,
    )


def marcar_leitura_whatsapp(*, token, empresa_id, conversa_id, mensagem_id):
    endereco = os.getenv("ORION_API_INTERNA_URL", "http://127.0.0.1:8000").rstrip("/")
    resposta = requests.post(
        f"{endereco}/api/central-whatsapp/conversas/{conversa_id}/leitura",
        headers={"Authorization": f"Bearer {token}"}, params={"empresa_id": empresa_id},
        json={"mensagem_id": mensagem_id}, timeout=5, allow_redirects=False,
    )
    resposta.raise_for_status()
    return resposta.json()["ultima_lida_id"]
