import requests

from app.services.waha_destino import ConfiguracaoWahaInvalida, resolver_waha
from app.services.followup_ids_waha import (
    extrair_id_resposta_waha,
)


def transportar_mensagem_waha(
    sessao: str,
    chat_id: str,
    texto: str,
    *, reply_to: str | None = None, encaminhar: str | None = None,
) -> tuple[bool, str | None, str | None]:
    """Envia uma unica vez, sem tentativas automaticas."""

    if not sessao or not chat_id or not texto:
        return False, "falha_envio", None

    try:
        destino = resolver_waha(sessao)
        if not destino.chave_api:
            return False, "falha_envio", None
        endpoint = "forwardMessage" if encaminhar else "sendText"
        resposta = requests.post(
            f"{destino.origem}/api/{endpoint}",
            headers=destino.headers, allow_redirects=False,
            json={
                "session": destino.sessao,
                "chatId": chat_id,
                **({"messageId": encaminhar} if encaminhar else {"text": texto}),
                **({"reply_to": reply_to} if reply_to else {}),
            },
            timeout=15,
        )

        if 300 <= resposta.status_code < 400:
            return False, "timeout_envio_inconclusivo", None
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

    except requests.exceptions.ConnectionError:
        # A conexao pode cair depois de o WAHA receber a mensagem.
        # Nao permitir repeticao automatica de um envio incerto.
        return False, "timeout_envio_inconclusivo", None

    except (requests.RequestException, ConfiguracaoWahaInvalida):
        return False, "falha_envio", None
