
STATUS_RECEBIDA = "recebida"
STATUS_PROCESSANDO = "processando"
STATUS_CONCLUIDA = "concluida"
STATUS_FALHA = "falha"

ESTADOS_PROCESSAMENTO = frozenset({
    STATUS_RECEBIDA,
    STATUS_PROCESSANDO,
    STATUS_CONCLUIDA,
    STATUS_FALHA,
})

STATUS_ENVIO_CONFIRMADO_HTTP = "aceito_waha"
STATUS_ENVIO_FALHA = "falha_envio"
STATUS_ENVIO_INCONCLUSIVO = "timeout_envio_inconclusivo"
STATUS_ENVIO_NAO_APLICAVEL = "nao_aplicavel"


TRANSICOES_PERMITIDAS = {
    STATUS_RECEBIDA: frozenset({
        STATUS_PROCESSANDO,
        STATUS_FALHA,
    }),
    STATUS_PROCESSANDO: frozenset({
        STATUS_CONCLUIDA,
        STATUS_FALHA,
    }),
    STATUS_FALHA: frozenset({
        STATUS_PROCESSANDO,
    }),
    STATUS_CONCLUIDA: frozenset(),
}


def transicao_permitida(atual: str, novo: str) -> bool:
    """Valida transicoes sem alterar o banco."""
    return novo in TRANSICOES_PERMITIDAS.get(atual, frozenset())


def classificar_resultado_envio(
    envio_ok: bool,
    status_envio: str | None,
) -> str:
    """Classifica o retorno HTTP do WAHA sem reenviar mensagens."""

    if envio_ok:
        return STATUS_ENVIO_CONFIRMADO_HTTP

    if status_envio == "timeout_envio_inconclusivo":
        return STATUS_ENVIO_INCONCLUSIVO

    return STATUS_ENVIO_FALHA


def avaliar_persistencia_entrada(
    mensagem_id_externo: str | None,
    resultado_persistencia: str,
) -> str:
    """Avalia a persistencia sem assumir que houve processamento."""

    if resultado_persistencia not in {
        "criada", "duplicada", "erro"
    }:
        raise ValueError("Resultado de persistencia invalido.")

    if not mensagem_id_externo:
        return "sem_id_externo"

    if resultado_persistencia == "criada":
        return "pendente_processamento"

    if resultado_persistencia == "duplicada":
        return "verificar_estado_existente"

    return "falha_persistencia"


def decidir_reprocessamento_mensagem(
    estado_processamento: str | None,
) -> str:
    """Classifica mensagens existentes sem autorizar reenvio automatico."""

    if estado_processamento == STATUS_CONCLUIDA:
        return "ignorar_concluida"

    if estado_processamento == STATUS_PROCESSANDO:
        return "aguardar_processamento"

    if estado_processamento == STATUS_RECEBIDA:
        return "avaliar_reserva_atomica"

    if estado_processamento == STATUS_FALHA:
        return "reter_para_analise"

    return "estado_desconhecido"
