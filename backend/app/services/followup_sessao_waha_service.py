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


def resolver_sessao_waha_conversa(
    db,
    *,
    empresa_id: int,
    conexao_canal_id: int,
) -> tuple[str | None, str]:
    """Resolve a sessao WAHA pela conexao especifica da conversa."""

    from app.models.models import ConexaoCanal

    if (
        type(empresa_id) is not int
        or empresa_id < 1
        or type(conexao_canal_id) is not int
        or conexao_canal_id < 1
    ):
        return None, "identificadores_invalidos"

    conexao = (
        db.query(ConexaoCanal)
        .filter(
            ConexaoCanal.id == conexao_canal_id,
            ConexaoCanal.empresa_id == empresa_id,
            ConexaoCanal.provedor == "waha",
            ConexaoCanal.canal == "whatsapp",
            ConexaoCanal.ativo.is_(True),
        )
        .first()
    )

    if conexao is None:
        return None, "conexao_waha_nao_encontrada"

    if conexao.operacao_suspensa:
        return None, "conexao_waha_suspensa"

    if conexao.especialista_id is None:
        return None, "vendedor_nao_vinculado"

    if not conexao.sessao_waha or not conexao.sessao_waha.strip():
        return None, "sessao_waha_nao_configurada"

    return conexao.sessao_waha.strip(), "sessao_resolvida"
