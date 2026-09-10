from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


TIMEZONE_PADRAO = "America/Fortaleza"


def obter_timezone(
    nome_timezone: str | None = None,
) -> ZoneInfo:
    """
    Retorna um timezone IANA válido.
    """

    nome = (
        nome_timezone
        or TIMEZONE_PADRAO
    ).strip()

    try:
        return ZoneInfo(nome)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(
            f"Timezone inválido: {nome}"
        ) from exc


def agora_utc() -> datetime:
    """
    Retorna o instante atual em UTC.
    """

    return datetime.now(timezone.utc)


def agora_empresa(
    nome_timezone: str | None = None,
) -> datetime:
    """
    Retorna o instante atual no timezone da empresa.
    """

    return agora_utc().astimezone(
        obter_timezone(nome_timezone)
    )


def utc_sem_fuso_para_empresa(
    valor: datetime,
    nome_timezone: str | None = None,
) -> datetime:
    """
    Converte timestamps legados armazenados no PostgreSQL
    como UTC em TIMESTAMP WITHOUT TIME ZONE para o horário
    local da empresa.
    """

    if valor.tzinfo is None:
        valor = valor.replace(
            tzinfo=timezone.utc
        )
    else:
        valor = valor.astimezone(
            timezone.utc
        )

    return valor.astimezone(
        obter_timezone(nome_timezone)
    )


def horas_desde_timestamp_utc(
    valor: datetime,
) -> float:
    """
    Calcula horas transcorridas desde um timestamp UTC.

    Aceita o formato legado do banco:
    TIMESTAMP WITHOUT TIME ZONE representando UTC.
    """

    if valor.tzinfo is None:
        valor = valor.replace(
            tzinfo=timezone.utc
        )
    else:
        valor = valor.astimezone(
            timezone.utc
        )

    diferenca = (
        agora_utc() - valor
    ).total_seconds() / 3600

    return round(
        max(diferenca, 0),
        1,
    )
