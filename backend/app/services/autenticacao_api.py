import os

from itsdangerous import (
    URLSafeTimedSerializer,
    BadSignature,
    SignatureExpired,
)


TEMPO_MAXIMO_TOKEN = 3600


def _serializador():
    segredo = os.getenv("ORION_API_AUTH_SECRET", "")

    if len(segredo) < 32:
        raise RuntimeError(
            "ORION_API_AUTH_SECRET nao configurado corretamente."
        )

    return URLSafeTimedSerializer(
        segredo,
        salt="orion-api-vendedores-v1",
    )


def gerar_token_api(*, usuario_id: int, empresa_id: int) -> str:
    if (
        type(usuario_id) is not int
        or type(empresa_id) is not int
        or usuario_id <= 0
        or empresa_id <= 0
    ):
        raise ValueError("Identidade invalida.")

    return _serializador().dumps({
        "usuario_id": usuario_id,
        "empresa_id": empresa_id,
    })


def validar_token_api(token: str) -> dict | None:
    if not isinstance(token, str) or not token:
        return None

    try:
        dados = _serializador().loads(
            token,
            max_age=TEMPO_MAXIMO_TOKEN,
        )
    except (BadSignature, SignatureExpired):
        return None

    if not isinstance(dados, dict):
        return None

    usuario_id = dados.get("usuario_id")
    empresa_id = dados.get("empresa_id")

    if (
        type(usuario_id) is not int
        or type(empresa_id) is not int
        or usuario_id <= 0
        or empresa_id <= 0
    ):
        return None

    return {
        "usuario_id": usuario_id,
        "empresa_id": empresa_id,
    }
