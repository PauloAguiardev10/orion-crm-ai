from sqlalchemy.orm import Session

from app.models.models import Conversa, ConexaoCanal
from app.services.mensagem_service import registrar_mensagem


def registrar_mensagem_humana_waha(
    db: Session,
    *,
    empresa_id: int,
    conversa_id: int,
    conexao_canal_id: int,
    especialista_id: int,
    texto: str,
    mensagem_id_externo: str,
):
    if not isinstance(texto, str) or not texto.strip():
        return None, "texto_invalido"

    if not isinstance(mensagem_id_externo, str) or not mensagem_id_externo.strip():
        return None, "id_externo_invalido"

    conexao = (
        db.query(ConexaoCanal)
        .filter(
            ConexaoCanal.id == conexao_canal_id,
            ConexaoCanal.empresa_id == empresa_id,
            ConexaoCanal.especialista_id == especialista_id,
            ConexaoCanal.canal == "whatsapp",
            ConexaoCanal.provedor == "waha",
            ConexaoCanal.ativo.is_(True),
        )
        .first()
    )

    if conexao is None:
        return None, "conexao_vendedor_invalida"

    conversa = (
        db.query(Conversa)
        .filter(
            Conversa.id == conversa_id,
            Conversa.empresa_id == empresa_id,
            Conversa.conexao_canal_id == conexao_canal_id,
            Conversa.canal == "whatsapp",
        )
        .first()
    )

    if conversa is None:
        return None, "conversa_conexao_invalida"

    registro, criado = registrar_mensagem(
        db,
        empresa_id=empresa_id,
        conversa_id=conversa_id,
        cliente_id=conversa.cliente_id,
        remetente="humano",
        texto=texto.strip(),
        from_me=True,
        mensagem_id_externo=mensagem_id_externo.strip(),
    )

    if not criado:
        return registro, "mensagem_duplicada"

    return registro, "mensagem_humana_registrada"
