"""Resolucao segura de sessao WAHA para follow-ups."""

from collections.abc import Mapping


def resolver_sessao_waha_empresa(
    empresa_id: int,
    mapa_sessoes: Mapping[str, int],
) -> tuple[str | None, str]:
    """Exige exatamente uma sessao explicitamente vinculada a empresa."""

    if type(empresa_id) is not int or empresa_id < 1:
        return None, "empresa_invalida"

    if not isinstance(mapa_sessoes, Mapping):
        return None, "mapa_sessoes_invalido"

    sessoes = []

    for sessao, empresa_vinculada in mapa_sessoes.items():
        if (
            isinstance(sessao, str)
            and sessao.strip()
            and type(empresa_vinculada) is int
            and empresa_vinculada == empresa_id
        ):
            sessoes.append(sessao)

    if not sessoes:
        return None, "sessao_nao_configurada"

    if len(sessoes) != 1:
        return None, "multiplas_sessoes_empresa"

    return sessoes[0], "sessao_resolvida"
