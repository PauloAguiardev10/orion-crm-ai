from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


TIMEZONE_PADRAO = "America/Fortaleza"


def obter_timezone(
    nome_timezone: str | None = None,
) -> ZoneInfo:
    """
    Retorna um timezone IANA válido.

    Quando nenhum timezone é informado, utiliza o padrão
    operacional atual do Orion CRM.
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
    Retorna o instante atual em UTC com informação de timezone.
    """

    return datetime.now(timezone.utc)


def agora_empresa(
    nome_timezone: str | None = None,
) -> datetime:
    """
    Retorna o instante atual convertido para o timezone da empresa.
    """

    return agora_utc().astimezone(
        obter_timezone(nome_timezone)
    )


def utc_para_empresa(
    valor: datetime,
    nome_timezone: str | None = None,
) -> datetime:
    """
    Converte um datetime UTC para o timezone da empresa.

    Datetimes sem timezone são interpretados explicitamente como UTC.
    Essa convenção será usada somente para registros cuja semântica
    UTC tenha sido confirmada.
    """

    if valor.tzinfo is None:
        valor = valor.replace(
            tzinfo=timezone.utc
        )

    return valor.astimezone(
        obter_timezone(nome_timezone)
    )
