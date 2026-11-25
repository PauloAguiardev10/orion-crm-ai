import os
from pathlib import Path

from dotenv import load_dotenv
from itsdangerous import URLSafeTimedSerializer

RAIZ_PROJETO = Path(__file__).resolve().parents[2]
load_dotenv(RAIZ_PROJETO / ".env", override=False)


def gerar_token_central(*, usuario_id: int, empresa_id: int) -> str:
    """Gera token compativel com a autenticacao da API."""

    usuario_id = int(usuario_id)
    empresa_id = int(empresa_id)

    if usuario_id <= 0 or empresa_id <= 0:
        raise ValueError("Identidade invalida.")

    segredo = os.getenv("ORION_API_AUTH_SECRET", "")

    if len(segredo) < 32:
        raise RuntimeError(
            "ORION_API_AUTH_SECRET nao configurado corretamente."
        )

    serializador = URLSafeTimedSerializer(
        segredo,
        salt="orion-api-vendedores-v1",
    )

    return serializador.dumps({
        "usuario_id": usuario_id,
        "empresa_id": empresa_id,
    })
