import os
from email.message import Message

import requests


def reservar_anexo_api(*, conversa_id, legenda, arquivo, chave_solicitacao, token, gravacao=False):
    endereco = os.getenv("ORION_API_INTERNA_URL", "http://127.0.0.1:8000").rstrip("/")
    try:
        resposta = requests.post(
            f"{endereco}/api/central-whatsapp/reservar-anexo",
            headers={"Authorization": f"Bearer {token}"},
            data={
                "conversa_id": conversa_id, "legenda": legenda,
                "chave_solicitacao": chave_solicitacao,
                "gravacao": str(gravacao).lower(),
            },
            files={"arquivo": (arquivo.name, arquivo.getvalue(), arquivo.type)},
            timeout=20, allow_redirects=False,
        )
        resultado = resposta.json()
    except (requests.RequestException, ValueError):
        return False, {"situacao": "reserva_inconclusiva"}
    if resposta.status_code == 200:
        return True, resultado
    return False, {"situacao": resultado.get("detail"), "http_status": resposta.status_code}


def obter_anexo_api(*, conversa_id, mensagem_id, empresa_id, token):
    endereco = os.getenv("ORION_API_INTERNA_URL", "http://127.0.0.1:8000").rstrip("/")
    with requests.get(
        f"{endereco}/api/central-whatsapp/conversas/{conversa_id}/mensagens/{mensagem_id}/anexo",
        params={"empresa_id": empresa_id},
        headers={"Authorization": f"Bearer {token}"},
        stream=True, allow_redirects=False, timeout=10,
    ) as resposta:
        if resposta.status_code != 200:
            raise ValueError("anexo_indisponivel")
        dados = bytearray()
        for bloco in resposta.iter_content(chunk_size=65536):
            dados.extend(bloco)
            if len(dados) > 8 * 1024 * 1024:
                raise ValueError("anexo_excede_limite")
        cabecalhos = Message()
        cabecalhos["Content-Disposition"] = resposta.headers.get("Content-Disposition", "")
        nome = cabecalhos.get_filename() or "anexo.pdf"
        return bytes(dados), nome


def gerenciar_atendimento_api(
    *, acao: str, conversa_id: int, token: str, empresa_id: int | None,
    **dados,
) -> tuple[bool, str]:
    endereco = os.getenv(
        "ORION_API_INTERNA_URL",
        "http://127.0.0.1:8000",
    ).rstrip("/")

    if not token:
        return False, "Sessao sem autenticacao da API."

    try:
        resposta = requests.post(
            f"{endereco}/api/central-whatsapp/{acao}-atendimento",
            headers={"Authorization": f"Bearer {token}"},
            params={"empresa_id": empresa_id},
            json={"conversa_id": int(conversa_id), **dados},
            timeout=10,
        )
    except requests.RequestException:
        return False, "Nao foi possivel conectar ao backend."

    if resposta.status_code == 200:
        return True, {
            "assumir": "Atendimento assumido.",
            "transferir": "Atendimento transferido.",
            "encerrar": "Atendimento encerrado.",
        }[acao]

    if resposta.status_code == 401:
        return False, "Autenticacao expirada. Entre novamente no CRM."

    if resposta.status_code == 403:
        return False, "Usuário ou atendente de destino sem permissão para esta ação."

    if resposta.status_code == 409:
        try:
            if resposta.json().get("detail") == "envio_pendente":
                return False, "Verifique os envios pendentes antes de alterar o atendimento."
        except ValueError:
            pass
        return False, "O atendimento mudou ou está indisponível. Atualize a página."

    return False, f"Erro ao alterar atendimento (HTTP {resposta.status_code})."


def assumir_conversa_api(*, conversa_id: int, token: str) -> tuple[bool, str]:
    return gerenciar_atendimento_api(
        acao="assumir", conversa_id=conversa_id, token=token, empresa_id=None,
    )


def reservar_mensagem_api(
    *,
    conversa_id: int,
    texto: str,
    chave_solicitacao: str,
    token: str,
) -> tuple[bool, dict]:
    """Reserva mensagem no backend sem executar envio."""

    if not token:
        return False, {"situacao": "autenticacao_ausente"}

    endereco = os.getenv(
        "ORION_API_INTERNA_URL",
        "http://127.0.0.1:8000",
    ).rstrip("/")

    try:
        resposta = requests.post(
            f"{endereco}/api/central-whatsapp/reservar-mensagem",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "conversa_id": int(conversa_id),
                "texto": texto,
                "chave_solicitacao": chave_solicitacao,
            },
            timeout=15,
        )
    except requests.RequestException:
        return False, {"situacao": "reserva_inconclusiva"}

    try:
        dados = resposta.json()
    except ValueError:
        return False, {"situacao": "resposta_invalida"}

    if resposta.status_code == 200:
        return True, dados

    return False, {
        "situacao": dados.get("detail", "erro_reserva"),
        "http_status": resposta.status_code,
    }


def executar_mensagem_api(
    *,
    conversa_id: int,
    mensagem_id: int,
    token: str,
) -> tuple[bool, dict]:
    """Solicita uma unica execucao da mensagem reservada."""

    if not token:
        return False, {"situacao": "autenticacao_ausente"}

    endereco = os.getenv(
        "ORION_API_INTERNA_URL",
        "http://127.0.0.1:8000",
    ).rstrip("/")

    try:
        resposta = requests.post(
            f"{endereco}/api/central-whatsapp/executar-mensagem",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "conversa_id": int(conversa_id),
                "mensagem_id": int(mensagem_id),
            },
            timeout=25,
        )
    except requests.RequestException:
        return False, {"situacao": "envio_inconclusivo_nao_repetir"}

    try:
        dados = resposta.json()
    except ValueError:
        return False, {"situacao": "resposta_invalida_nao_repetir"}

    if resposta.status_code == 200:
        return dados.get("sucesso") is True, dados

    return False, {
        "situacao": dados.get("detail", "erro_execucao"),
        "http_status": resposta.status_code,
    }



def consultar_status_mensagem_api(
    *,
    conversa_id: int,
    mensagem_id: int,
    token: str,
) -> tuple[bool, dict]:
    """Consulta o resultado de envio sem disparar mensagens."""

    if not token:
        return False, {"situacao": "autenticacao_ausente"}

    endereco = os.getenv(
        "ORION_API_INTERNA_URL",
        "http://127.0.0.1:8000",
    ).rstrip("/")

    try:
        resposta = requests.get(
            f"{endereco}/api/central-whatsapp/status-mensagem",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "conversa_id": int(conversa_id),
                "mensagem_id": int(mensagem_id),
            },
            timeout=10,
        )
    except requests.RequestException:
        return False, {"situacao": "consulta_indisponivel"}

    try:
        dados = resposta.json()
    except ValueError:
        return False, {"situacao": "resposta_invalida"}

    if resposta.status_code == 200:
        return True, dados

    return False, {
        "situacao": dados.get("detail", "erro_consulta"),
        "http_status": resposta.status_code,
    }



def consultar_pendencias_central_api(
    *,
    conversa_id: int,
    token: str,
) -> tuple[bool, dict]:
    """Consulta pendencias no PostgreSQL sem enviar mensagens."""

    if not token:
        return False, {"situacao": "autenticacao_ausente"}

    endereco = os.getenv(
        "ORION_API_INTERNA_URL",
        "http://127.0.0.1:8000",
    ).rstrip("/")

    try:
        resposta = requests.get(
            f"{endereco}/api/central-whatsapp/pendencias",
            headers={"Authorization": f"Bearer {token}"},
            params={"conversa_id": int(conversa_id)},
            timeout=10,
        )
    except requests.RequestException:
        return False, {"situacao": "consulta_indisponivel"}

    try:
        dados = resposta.json()
    except ValueError:
        return False, {"situacao": "resposta_invalida"}

    if resposta.status_code == 200:
        return True, dados

    return False, {
        "situacao": dados.get("detail", "erro_consulta"),
        "http_status": resposta.status_code,
    }
