"""Validacao preliminar de referencias de anuncios WhatsApp."""


def analisar_referencia_anuncio(referencia: dict | None) -> dict:
    """Analisa metadados sem consultar ou modificar o banco."""

    resultado = {
        "referencia_valida": False,
        "anuncio_id": None,
        "motivo": "referencia_ausente",
    }

    if not isinstance(referencia, dict) or not referencia:
        return resultado

    anuncio_id = (
        referencia.get("source_id")
        or referencia.get("sourceId")
        or referencia.get("ad_id")
    )

    origem = (
        referencia.get("source_type")
        or referencia.get("sourceType")
        or ""
    )

    if not isinstance(anuncio_id, (str, int)):
        resultado["motivo"] = "identificador_anuncio_ausente"
        return resultado

    anuncio_id = str(anuncio_id).strip()

    if not anuncio_id or len(anuncio_id) > 180:
        resultado["motivo"] = "identificador_anuncio_invalido"
        return resultado

    if not isinstance(origem, str):
        resultado["motivo"] = "tipo_origem_invalido"
        return resultado

    if origem.strip().lower() not in {"ad", "ads"}:
        resultado["motivo"] = "origem_publicitaria_nao_comprovada"
        return resultado

    resultado["referencia_valida"] = True
    resultado["anuncio_id"] = anuncio_id
    resultado["motivo"] = "referencia_publicitaria_identificada"

    return resultado
