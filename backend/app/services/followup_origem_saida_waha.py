from sqlalchemy.orm import Session
from app.models.models import Mensagem


def verificar_saida_automatica_registrada(
    db: Session,
    empresa_id: int,
    sessao_waha: str,
    mensagem_id_waha: str | None,
) -> tuple[bool, str]:

    if not mensagem_id_waha:
        return False, "id_waha_ausente"

    if not sessao_waha or not sessao_waha.strip():
        return False, "sessao_invalida"

    mensagem = (
        db.query(Mensagem)
        .filter(
            Mensagem.empresa_id == empresa_id,
            Mensagem.sessao_waha == sessao_waha.strip(),
            Mensagem.mensagem_id_waha == mensagem_id_waha,
            Mensagem.from_me.is_(True),
        )
        .first()
    )

    if mensagem is None:
        return False, "origem_ainda_nao_comprovada"

    return True, "saida_automatica_registrada"
