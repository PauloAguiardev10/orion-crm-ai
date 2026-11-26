"""Validacao de vinculos e destinatario WAHA do follow-up."""


def chat_id_whatsapp_valido(chat_id: str) -> bool:
    if not isinstance(chat_id, str) or chat_id.count("@") != 1:
        return False
    numero, dominio = chat_id.split("@", 1)
    return numero.isascii() and numero.isdigit() and dominio in ("c.us", "lid")


def validar_destinatario_followup(
    *,
    empresa_id: int,
    empresa_agendamento_id: int,
    empresa_lead_id: int,
    empresa_conversa_id: int,
    conversa_id_agendamento: int | None,
    conversa_id_lead: int | None,
    conversa_id: int,
    canal: str,
    chat_id: str,
) -> tuple[str | None, str]:
    """Recusa destinatarios e vinculos inconsistentes."""

    ids_empresa = (
        empresa_id,
        empresa_agendamento_id,
        empresa_lead_id,
        empresa_conversa_id,
    )

    if any(type(valor) is not int or valor < 1 for valor in ids_empresa):
        return None, "empresa_invalida"

    if len(set(ids_empresa)) != 1:
        return None, "empresa_divergente"

    if type(conversa_id) is not int or conversa_id < 1:
        return None, "conversa_invalida"

    if (
        type(conversa_id_agendamento) is not int
        or type(conversa_id_lead) is not int
        or conversa_id_agendamento != conversa_id
        or conversa_id_lead != conversa_id
    ):
        return None, "conversa_divergente"

    if canal != "whatsapp":
        return None, "canal_nao_suportado"

    if not chat_id_whatsapp_valido(chat_id):
        return None, "chat_id_invalido"

    return chat_id, "destinatario_validado"
