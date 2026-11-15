
from sqlalchemy.orm import Session

from app.models.models import ConexaoCanal


def localizar_conexao_waha(
    db: Session,
    sessao: str,
) -> tuple[ConexaoCanal | None, str]:

    if not isinstance(sessao, str) or not sessao.strip():
        return None, "sessao_invalida"

    conexoes = (
        db.query(ConexaoCanal)
        .filter(
            ConexaoCanal.sessao_waha == sessao.strip(),
            ConexaoCanal.provedor == "waha",
            ConexaoCanal.canal == "whatsapp",
            ConexaoCanal.ativo.is_(True),
        )
        .limit(2)
        .all()
    )

    if not conexoes:
        return None, "conexao_nao_cadastrada"

    if len(conexoes) != 1:
        return None, "conexao_ambigua"

    conexao = conexoes[0]

    # Conexoes institucionais podem operar sem vendedor fixo.
    # A validacao da empresa ocorre no fluxo de entrada WAHA.
    # Permissoes de acesso dos vendedores sao verificadas
    # separadamente nos servicos de atendimento.
    return conexao, "conexao_identificada"
