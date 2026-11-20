"""Calcula horarios permitidos para o follow-up automatico."""

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo


FUSO_BRASILIA = ZoneInfo("America/Sao_Paulo")


def calcular_primeiro_followup(
    entrada_lead: datetime,
    *,
    intervalo_minutos: int = 180,
    fuso_horario: str = "America/Sao_Paulo",
    segunda_sexta_inicio: time = time(8, 0),
    segunda_sexta_fim: time = time(18, 0),
    sabado_ativo: bool = True,
    sabado_inicio: time = time(8, 0),
    sabado_fim: time = time(12, 0),
    domingo_ativo: bool = False,
) -> datetime:
    """Calcula o primeiro horario permitido para follow-up."""

    if entrada_lead.tzinfo is None or entrada_lead.utcoffset() is None:
        raise ValueError("A entrada da lead precisa conter fuso horario.")

    if not 1 <= intervalo_minutos <= 43200:
        raise ValueError("Intervalo de follow-up invalido.")

    fuso = ZoneInfo(fuso_horario)

    candidato = (
        entrada_lead.astimezone(fuso)
        + timedelta(minutes=intervalo_minutos)
    )

    for _ in range(35):
        dia = candidato.weekday()

        if dia == 6 and not domingo_ativo:
            candidato = datetime.combine(
                candidato.date() + timedelta(days=1),
                segunda_sexta_inicio,
                tzinfo=fuso,
            )
            continue

        if dia == 5:
            if not sabado_ativo:
                candidato = datetime.combine(
                    candidato.date() + timedelta(days=2),
                    segunda_sexta_inicio,
                    tzinfo=fuso,
                )
                continue

            abertura = sabado_inicio
            fechamento = sabado_fim

        elif dia == 6:
            abertura = segunda_sexta_inicio
            fechamento = segunda_sexta_fim

        else:
            abertura = segunda_sexta_inicio
            fechamento = segunda_sexta_fim

        horario = candidato.time().replace(tzinfo=None)

        if horario < abertura:
            return datetime.combine(
                candidato.date(),
                abertura,
                tzinfo=fuso,
            )

        if horario <= fechamento:
            return candidato

        candidato = datetime.combine(
            candidato.date() + timedelta(days=1),
            time(0, 0),
            tzinfo=fuso,
        )

    raise ValueError("Nao foi possivel calcular horario permitido.")


def horario_followup_permitido(
    agora: datetime,
    *,
    fuso_horario: str = "America/Sao_Paulo",
    segunda_sexta_inicio: time = time(8, 0),
    segunda_sexta_fim: time = time(18, 0),
    sabado_ativo: bool = True,
    sabado_inicio: time = time(8, 0),
    sabado_fim: time = time(12, 0),
    domingo_ativo: bool = False,
) -> bool:
    """Verifica se o instante atual esta dentro do horario permitido."""

    if agora.tzinfo is None or agora.utcoffset() is None:
        raise ValueError("A data precisa conter fuso horario.")

    horario_local = agora.astimezone(ZoneInfo(fuso_horario))
    dia = horario_local.weekday()
    horario = horario_local.time().replace(tzinfo=None)

    if dia == 5:
        if not sabado_ativo:
            return False
        return sabado_inicio <= horario <= sabado_fim

    if dia == 6:
        if not domingo_ativo:
            return False
        return segunda_sexta_inicio <= horario <= segunda_sexta_fim

    return segunda_sexta_inicio <= horario <= segunda_sexta_fim
