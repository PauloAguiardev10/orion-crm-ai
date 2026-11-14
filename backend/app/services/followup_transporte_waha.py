import os
import requests

from app.services.followup_ids_waha import (
    extrair_id_resposta_waha,
)


def transportar_mensagem_waha(
    sessao: str,
    chat_id: str,
    texto: str,
) -> tuple[bool, str | None, str | None]:
    """Envia uma unica vez, sem tentativas automaticas."""

    if not sessao or not chat_id or not texto:
        return False, "falha_envio", None

    chave = os.getenv("WAHA_API_KEY", "").strip()

    if not chave:
        return False, "falha_envio", None

    url = os.getenv(
        "WAHA_API_URL",
        "http://localhost:3000",
    ).rstrip("/")

    try:
        resposta = requests.post(
            f"{url}/api/sendText",
            headers={"X-Api-Key": chave},
            json={
                "session": sessao,
                "chatId": chat_id,
                "text": texto,
            },
            timeout=15,
        )

        resposta.raise_for_status()

        try:
            dados = resposta.json()
        except ValueError:
            dados = None

        return (
            True,
            None,
            extrair_id_resposta_waha(dados),
        )

    except requests.exceptions.Timeout:
        return False, "timeout_envio_inconclusivo", None

    except requests.RequestException:
        return False, "falha_envio", None
