"""Extracao conservadora do identificador retornado pelo WAHA."""


def extrair_id_resposta_waha(
    resposta: object,
) -> str | None:
    """Extrai ID somente de formatos explicitamente reconhecidos."""

    if not isinstance(resposta, dict):
        return None

    candidatos = []

    for campo in ("id", "messageId", "message_id"):
        valor = resposta.get(campo)

        if isinstance(valor, dict):
            valor = valor.get("_serialized")

        if isinstance(valor, str) and valor.strip():
            candidatos.append(valor.strip())

    dados = resposta.get("_data")

    if isinstance(dados, dict):
        for campo in ("id", "messageId", "message_id"):
            valor = dados.get(campo)

            if isinstance(valor, dict):
                valor = valor.get("_serialized")

            if isinstance(valor, str) and valor.strip():
                candidatos.append(valor.strip())

    if not candidatos:
        return None

    if len(set(candidatos)) != 1:
        return None

    return candidatos[0]
