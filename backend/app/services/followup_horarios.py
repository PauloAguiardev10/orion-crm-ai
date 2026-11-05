"""Calcula o horario do primeiro follow-up automatico."""

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo


FUSO_BRASILIA = ZoneInfo("America/Sao_Paulo")
ESPERA_PRIMEIRO_FOLLOWUP = timedelta(hours=3)

ABERTURA = time(8, 0)
FECHAMENTO_SEMANA = time(18, 0)
FECHAMENTO_SABADO = time(12, 0)


def calcular_primeiro_followup(entrada_lead: datetime) -> datetime:
    """
    Calcula o primeiro horario permitido para follow-up.

    A entrada precisa conter fuso horario.
    O resultado utiliza o horario de Brasilia.
    """
    if entrada_lead.tzinfo is None or entrada_lead.utcoffset() is None:
        raise ValueError(
            "A data de entrada da lead deve conter fuso horario."
        )

    candidato = (
        entrada_lead.astimezone(FUSO_BRASILIA)
        + ESPERA_PRIMEIRO_FOLLOWUP
    )

    while True:
        dia_semana = candidato.weekday()

        if dia_semana == 6:
            candidato = datetime.combine(
                candidato.date() + timedelta(days=1),
                ABERTURA,
                tzinfo=FUSO_BRASILIA,
            )
            continue

        fechamento = (
            FECHAMENTO_SABADO
            if dia_semana == 5
            else FECHAMENTO_SEMANA
        )

        horario = candidato.time()

        if horario < ABERTURA:
            return candidato.replace(
                hour=8, minute=0, second=0, microsecond=0
            )

        if horario <= fechamento:
            return candidato

        candidato = datetime.combine(
            candidato.date() + timedelta(days=1),
            ABERTURA,
            tzinfo=FUSO_BRASILIA,
        )
