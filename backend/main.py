import json
import os
import random
import time
import traceback
from urllib.parse import quote

import requests
from fastapi import FastAPI
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.agents.sdr_agent import (
    conduzir_conversa,
    gerar_resumo_vendedor,
)
from app.database.database import SessionLocal, engine
from app.services.empresa_context_service import carregar_contexto_empresa
from app.models.models import (
    Base,
    Cliente,
    ConexaoCanal,
    Conversa,
    Lead,
)


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Agente SDR Forway")


def carregar_mapa_sessoes() -> dict[str, int]:
    """
    Carrega o vínculo entre sessão WAHA e empresa.

    Exemplo no ambiente:
    WAHA_SESSION_EMPRESA_MAP={"default": 1, "nike": 3}

    Enquanto essa variável não existir, a sessão default continua
    vinculada à empresa 1 (Forway), preservando o funcionamento atual.
    """
    valor = os.getenv(
        "WAHA_SESSION_EMPRESA_MAP",
        '{"default": 1}',
    )

    try:
        mapa = json.loads(valor)

        return {
            str(sessao): int(empresa_id)
            for sessao, empresa_id in mapa.items()
        }

    except (TypeError, ValueError, json.JSONDecodeError):
        return {"default": 1}


SESSAO_EMPRESA = carregar_mapa_sessoes()

# Cache de mapeamentos LID -> telefone já resolvidos.
TELEFONES_LID_CACHE: dict[str, str] = {}

MENSAGENS_WAHA_PROCESSADAS: dict[str, float] = {}
TTL_MENSAGEM_WAHA_SEGUNDOS = 10 * 60


def limpar_cache_mensagens_waha() -> None:
    agora = time.monotonic()
    expiradas = [
        mensagem_id
        for mensagem_id, instante in MENSAGENS_WAHA_PROCESSADAS.items()
        if agora - instante > TTL_MENSAGEM_WAHA_SEGUNDOS
    ]

    for mensagem_id in expiradas:
        MENSAGENS_WAHA_PROCESSADAS.pop(mensagem_id, None)


def obter_id_mensagem_waha(mensagem: dict) -> str | None:
    candidatos = [
        mensagem.get("id"),
        mensagem.get("messageId"),
        mensagem.get("message_id"),
    ]

    dados = mensagem.get("_data", {})
    if isinstance(dados, dict):
        candidatos.extend([
            dados.get("id"),
            dados.get("messageId"),
            dados.get("message_id"),
        ])

    for candidato in candidatos:
        if isinstance(candidato, str) and candidato.strip():
            return candidato.strip()

        if isinstance(candidato, dict):
            for chave in ["_serialized", "serialized", "id"]:
                valor = candidato.get(chave)
                if isinstance(valor, str) and valor.strip():
                    return valor.strip()

    return None


def mensagem_waha_ja_processada(mensagem_id: str | None) -> bool:
    if not mensagem_id:
        return False

    limpar_cache_mensagens_waha()

    if mensagem_id in MENSAGENS_WAHA_PROCESSADAS:
        return True

    MENSAGENS_WAHA_PROCESSADAS[mensagem_id] = time.monotonic()
    return False


def liberar_mensagem_waha(mensagem_id: str | None) -> None:
    if mensagem_id:
        MENSAGENS_WAHA_PROCESSADAS.pop(mensagem_id, None)


def normalizar_telefone_crm(telefone: str | None) -> str | None:
    if telefone is None:
        return None

    valor = str(telefone).strip()

    if not valor or valor.endswith("@lid"):
        return None

    if valor.endswith("@c.us"):
        valor = valor[:-5]

    numero = "".join(c for c in valor if c.isdigit())
    return numero or None


class MensagemRequest(BaseModel):
    empresa_id: int = Field(default=1, ge=1)
    nome: str | None = None
    telefone: str | None = None
    canal: str
    identificador: str
    mensagem: str


def obter_empresa_id_por_sessao(sessao: str) -> int | None:
    return SESSAO_EMPRESA.get(sessao)


def obter_sessao_waha(payload: dict, mensagem: dict) -> str:
    sessao = (
        payload.get("session")
        or mensagem.get("session")
        or mensagem.get("_data", {}).get("session")
        or "default"
    )

    if isinstance(sessao, dict):
        sessao = (
            sessao.get("name")
            or sessao.get("id")
            or "default"
        )

    return str(sessao)


def obter_chat_id_whatsapp(telefone: str | None) -> str | None:
    """
    Normaliza um telefone configurado no ambiente para o formato
    de chat usado pelo WAHA.

    Exemplo:
    5585999999999 -> 5585999999999@c.us
    """
    if not telefone:
        return None

    valor = str(telefone).strip()

    if not valor:
        return None

    if valor.endswith("@c.us") or valor.endswith("@lid"):
        return valor

    numero = "".join(
        caractere
        for caractere in valor
        if caractere.isdigit()
    )

    if not numero:
        return None

    return f"{numero}@c.us"


def obter_lid_luciano() -> str | None:
    """
    Retorna o identificador LID do WhatsApp interno do Luciano.

    O LID fica configurado fora do código por variável de ambiente:
    LUCIANO_WHATSAPP_LID=222805740281887@lid
    """
    valor = os.getenv("LUCIANO_WHATSAPP_LID")

    if not valor:
        return None

    valor = str(valor).strip()

    if not valor:
        return None

    if not valor.endswith("@lid"):
        return None

    return valor


def buscar_telefone_real_no_banco(
    chat_id: str,
    empresa_id: int | None,
) -> str | None:
    """
    Procura um telefone real já associado ao mesmo LID
    em conversas anteriores da empresa.
    """
    if not chat_id or not empresa_id:
        return None

    db: Session = SessionLocal()

    try:
        conversa_anterior = (
            db.query(Conversa)
            .filter(
                Conversa.empresa_id == empresa_id,
                Conversa.identificador == chat_id,
                Conversa.telefone.isnot(None),
                ~Conversa.telefone.like("%@lid"),
                ~Conversa.telefone.like("%@c.us"),
            )
            .order_by(Conversa.id.desc())
            .first()
        )

        if not conversa_anterior:
            return None

        telefone = str(
            conversa_anterior.telefone or ""
        ).strip()

        if telefone and telefone.isdigit():
            return telefone

        return None

    finally:
        db.close()


def obter_telefone_real_waha(
    chat_id: str,
    sessao: str,
    empresa_id: int | None = None,
) -> str | None:
    if not chat_id:
        return None

    if chat_id.endswith("@c.us"):
        return normalizar_telefone_crm(chat_id)

    if not chat_id.endswith("@lid"):
        return normalizar_telefone_crm(chat_id)

    telefone_cache = TELEFONES_LID_CACHE.get(chat_id)
    if telefone_cache:
        return telefone_cache

    headers = {
        "X-Api-Key": os.getenv("WAHA_API_KEY", "orionsystems"),
    }

    sessao_url = quote(str(sessao), safe="")
    lid_numero = chat_id.replace("@lid", "").strip()
    lid_url = quote(lid_numero, safe="")

    try:
        resposta = requests.get(
            f"http://localhost:3000/api/{sessao_url}/lids/{lid_url}",
            headers=headers,
            timeout=4,
        )
        resposta.raise_for_status()
        dados_lid = resposta.json()

        if isinstance(dados_lid, dict):
            telefone_real = normalizar_telefone_crm(
                dados_lid.get("pn")
                or dados_lid.get("phoneNumber")
                or dados_lid.get("phone")
            )
            if telefone_real:
                TELEFONES_LID_CACHE[chat_id] = telefone_real
                return telefone_real
    except (requests.RequestException, ValueError, TypeError) as erro:
        print("[WAHA LID] falha na resolução direta:", repr(erro), flush=True)

    try:
        resposta = requests.get(
            "http://localhost:3000/api/contacts",
            headers=headers,
            params={"contactId": chat_id, "session": sessao},
            timeout=4,
        )
        resposta.raise_for_status()
        contato = resposta.json()

        if isinstance(contato, list):
            contato = contato[0] if contato else None

        if isinstance(contato, dict):
            candidatos = [
                contato.get("pn"),
                contato.get("phoneNumber"),
                contato.get("phone"),
                contato.get("number"),
                contato.get("id"),
            ]

            for candidato in candidatos:
                if isinstance(candidato, dict):
                    candidato = (
                        candidato.get("_serialized")
                        or candidato.get("user")
                    )

                telefone_real = normalizar_telefone_crm(candidato)
                if telefone_real:
                    TELEFONES_LID_CACHE[chat_id] = telefone_real
                    return telefone_real
    except (requests.RequestException, ValueError, TypeError) as erro:
        print("[WAHA CONTATO] falha na consulta individual:", repr(erro), flush=True)

    telefone_banco = buscar_telefone_real_no_banco(chat_id, empresa_id)
    if telefone_banco:
        TELEFONES_LID_CACHE[chat_id] = telefone_banco
        return telefone_banco

    print(
        f"[WAHA LID] telefone não resolvido; mantendo identificador técnico {chat_id}",
        flush=True,
    )
    return None
def buscar_conexao_canal_meta(
    db: Session,
    canal: str,
    *,
    account_id: str | None = None,
    page_id: str | None = None,
    phone_number_id: str | None = None,
) -> ConexaoCanal | None:
    """
    Localiza a conexão Meta ativa responsável pelo evento recebido.

    A resolução é multiempresa: a conta externa identifica qual
    empresa do Orion CRM deve receber a mensagem.
    """
    query = db.query(ConexaoCanal).filter(
        ConexaoCanal.provedor == "meta",
        ConexaoCanal.canal == canal,
        ConexaoCanal.ativo.is_(True),
    )

    if account_id:
        query = query.filter(
            ConexaoCanal.account_id == str(account_id)
        )

    elif page_id:
        query = query.filter(
            ConexaoCanal.page_id == str(page_id)
        )

    elif phone_number_id:
        query = query.filter(
            ConexaoCanal.phone_number_id == str(phone_number_id)
        )

    else:
        return None

    return query.first()

@app.post("/mensagem")
def receber_mensagem(dados: MensagemRequest):
    db: Session = SessionLocal()

    try:
        telefone_normalizado = normalizar_telefone_crm(dados.telefone)

        conversa = (
            db.query(Conversa)
            .filter(
                Conversa.empresa_id == dados.empresa_id,
                Conversa.identificador == dados.identificador,
            )
            .order_by(Conversa.id.desc())
            .first()
        )

        if not conversa:
            conversa = Conversa(
                empresa_id=dados.empresa_id,
                identificador=dados.identificador,
                canal=dados.canal,
                nome=dados.nome,
                telefone=telefone_normalizado,
                etapa="inicio",
                historico="",
            )

            db.add(conversa)
            db.commit()
            db.refresh(conversa)

        elif telefone_normalizado and conversa.telefone != telefone_normalizado:
            conversa.telefone = telefone_normalizado

            if conversa.cliente_id:
                cliente_vinculado = (
                    db.query(Cliente)
                    .filter(
                        Cliente.id == conversa.cliente_id,
                        Cliente.empresa_id == dados.empresa_id,
                    )
                    .first()
                )
                if cliente_vinculado:
                    cliente_vinculado.telefone = telefone_normalizado

            db.commit()
            db.refresh(conversa)

        # Se o especialista já assumiu esta conversa no CRM,
        # a Sofia permanece em silêncio e não executa o fluxo da IA.
        if conversa.humano_assumiu is True:
            return {
                "empresa_id": dados.empresa_id,
                "canal": conversa.canal,
                "etapa_atual": conversa.etapa,
                "resposta_agente": None,
                "produto_identificado": conversa.servico,
                "temperatura": None,
                "prioridade": None,
                "score": None,
                "status": "em_atendimento_humano",
                "resumo_vendedor": None,
                "lead_id": None,
                "humano_assumiu": True,
            }

        contexto_empresa = carregar_contexto_empresa(
            db,
            conversa.empresa_id,
        )

        resposta, analise = conduzir_conversa(
            conversa,
            dados.mensagem,
            contexto_empresa=contexto_empresa,
        )
        

        db.commit()

        resumo = None
        lead_id = None
        nova_lead = False
        notificacao_luciano = None

        if conversa.etapa in [
            "encaminhar",
            "aguardando_humano",
        ]:
            lead_existente = (
                db.query(Lead)
                .filter(
                    Lead.empresa_id == dados.empresa_id,
                    Lead.conversa_id == conversa.id,
                )
                .order_by(Lead.id.desc())
                .first()
            )

            if not lead_existente and conversa.telefone:
                lead_existente = (
                    db.query(Lead)
                    .join(
                        Cliente,
                        Cliente.id == Lead.cliente_id,
                    )
                    .filter(
                        Lead.empresa_id == dados.empresa_id,
                        Cliente.empresa_id == dados.empresa_id,
                        Cliente.telefone == conversa.telefone,
                        Cliente.canal == conversa.canal,
                    )
                    .order_by(Lead.id.desc())
                    .first()
                )

            if not lead_existente:
                origem_aquisicao = (
                    conversa.origem_aquisicao
                    or conversa.canal
                )

                cliente = Cliente(
                    empresa_id=dados.empresa_id,
                    nome=conversa.nome,
                    empresa=conversa.empresa,
                    empresa_cliente=conversa.empresa,
                    segmento=conversa.segmento,
                    telefone=conversa.telefone,
                    canal=conversa.canal,
                    canal_origem=origem_aquisicao,
                )

                db.add(cliente)
                db.commit()
                db.refresh(cliente)

                conversa.cliente_id = cliente.id

                resumo = gerar_resumo_vendedor(
                    conversa,
                    analise,
                    contexto_empresa=contexto_empresa,
                )

                lead = Lead(
                    empresa_id=dados.empresa_id,
                    cliente_id=cliente.id,
                    conversa_id=conversa.id,
                    produto=conversa.servico,
                    temperatura=analise["temperatura"],
                    prioridade=analise["prioridade"],
                    score=analise["score"],
                    origem=origem_aquisicao,
                    observacoes=conversa.objetivo,
                    resumo_vendedor=resumo,
                    status="Aguardando atendimento",
                )

                db.add(lead)
                db.commit()
                db.refresh(lead)

                lead_id = lead.id
                nova_lead = True

                notificacao_luciano = (
                    "🔥 Nova lead qualificada — Forway\n\n"
                    f"Nome: {conversa.nome or 'Não informado'}\n"
                    f"Empresa: {conversa.empresa or 'Não informada'}\n"
                    f"Segmento: {conversa.segmento or 'Não informado'}\n"
                    f"WhatsApp: {conversa.telefone or 'Não informado'}\n"
                    f"Serviço: {conversa.servico or 'Não identificado'}\n"
                    f"Temperatura: {analise['temperatura'].capitalize()}\n"
                    f"Prioridade: {analise['prioridade'].capitalize()}\n"
                    f"Score: {analise['score']}\n\n"
                    "Lead aguardando atendimento no CRM."
                )

            else:
                resumo = lead_existente.resumo_vendedor
                lead_id = lead_existente.id

                if not conversa.cliente_id:
                    conversa.cliente_id = lead_existente.cliente_id
                    db.commit()

        return {
            "empresa_id": dados.empresa_id,
            "canal": conversa.canal,
            "etapa_atual": conversa.etapa,
            "resposta_agente": resposta,
            "produto_identificado": conversa.servico,
            "temperatura": analise["temperatura"],
            "prioridade": analise["prioridade"],
            "score": analise["score"],
            "status": (
                "encaminhado"
                if conversa.etapa in [
                    "encaminhar",
                    "aguardando_humano",
                ]
                else "em_atendimento"
            ),
            "resumo_vendedor": resumo,
            "lead_id": lead_id,
            "nova_lead": nova_lead,
            "notificacao_luciano": notificacao_luciano,
        }

    except Exception as erro:
        db.rollback()
        traceback.print_exc()

        return {
            "erro": str(erro),
            "tipo": type(erro).__name__,
        }

    finally:
        db.close()


def calcular_delay_resposta(resposta: str) -> float:
    tamanho = len(resposta or "")

    if tamanho <= 120:
        return random.uniform(3.5, 5.0)
    if tamanho <= 350:
        return random.uniform(5.0, 8.0)
    return random.uniform(8.0, 12.0)


def definir_presenca_digitacao(
    sessao: str,
    chat_id: str,
    digitando: bool,
    headers: dict,
) -> bool:
    presenca = "typing" if digitando else "paused"

    try:
        resposta = requests.post(
            f"http://localhost:3000/api/{quote(str(sessao), safe='')}/presence",
            headers=headers,
            json={"chatId": chat_id, "presence": presenca},
            timeout=5,
        )
        resposta.raise_for_status()
        return True
    except requests.RequestException as erro:
        print(f"[WAHA PRESENCE] falha em {presenca}: {repr(erro)}", flush=True)

    endpoint = "startTyping" if digitando else "stopTyping"

    try:
        resposta = requests.post(
            f"http://localhost:3000/api/{endpoint}",
            headers=headers,
            json={"session": sessao, "chatId": chat_id},
            timeout=5,
        )
        resposta.raise_for_status()
        return True
    except requests.RequestException as erro:
        print(f"[WAHA TYPING] falha no fallback {endpoint}: {repr(erro)}", flush=True)
        return False


def enviar_texto_waha(
    sessao: str,
    chat_id: str,
    texto: str,
    headers: dict,
) -> tuple[bool, str | None]:
    try:
        envio = requests.post(
            "http://localhost:3000/api/sendText",
            headers=headers,
            json={"session": sessao, "chatId": chat_id, "text": texto},
            timeout=15,
        )
        envio.raise_for_status()
        return True, None

    except requests.exceptions.ReadTimeout as erro:
        print(
            "[WAHA SEND] timeout; envio pode ter sido concluído. "
            f"Sem reenvio automático. Erro: {repr(erro)}",
            flush=True,
        )
        return False, "timeout_envio_inconclusivo"

    except requests.RequestException as erro:
        print(f"[WAHA SEND] falha no envio: {repr(erro)}", flush=True)
        return False, "falha_envio"


@app.post("/webhook/waha")
async def webhook_waha(payload: dict):
    evento = payload.get("event")
    mensagem = payload.get("payload", {})
    mensagem_id = obter_id_mensagem_waha(mensagem)
    dados_internos = mensagem.get("_data", {})

    print(
        "[WAHA WEBHOOK]",
        {
            "event": evento,
            "message_id": mensagem_id,
            "from": mensagem.get("from"),
            "fromMe": mensagem.get("fromMe"),
            "_data_id": (
                dados_internos.get("id")
                if isinstance(dados_internos, dict)
                else None
            ),
        },
        flush=True,
    )

    if evento != "message":
        return {
            "status": "ignorado",
            "motivo": "evento_diferente_de_message",
        }

    if mensagem.get("fromMe") is True:
        return {
            "status": "ignorado",
            "motivo": "mensagem_enviada_pelo_proprio_numero",
        }

    texto = mensagem.get("body")
    chat_id = mensagem.get("from")
    nome = mensagem.get("_data", {}).get("notifyName")

    if chat_id == "status@broadcast":
        return {
            "status": "ignorado",
            "motivo": "status_broadcast",
        }

    sessao = obter_sessao_waha(
        payload,
        mensagem,
    )

    empresa_id = obter_empresa_id_por_sessao(
        sessao,
    )

    if empresa_id is None:
        return {
            "status": "ignorado",
            "motivo": "sessao_sem_empresa_vinculada",
            "sessao": sessao,
        }

    if not texto or not chat_id:
        return {
            "status": "ignorado",
            "motivo": "sem_texto_ou_chat_id",
        }

    lid_luciano = obter_lid_luciano()

    if (
        lid_luciano
        and chat_id == lid_luciano
    ):
        return {
            "status": "ignorado",
            "motivo": "contato_interno_luciano",
            "empresa_id": empresa_id,
            "sessao": sessao,
            "chat_id": chat_id,
        }

    if mensagem_waha_ja_processada(mensagem_id):
        print(
            f"[WAHA WEBHOOK] mensagem duplicada ignorada: {mensagem_id}",
            flush=True,
        )
        return {
            "status": "ignorado",
            "motivo": "mensagem_duplicada",
            "message_id": mensagem_id,
            "empresa_id": empresa_id,
            "sessao": sessao,
            "chat_id": chat_id,
        }

    telefone_real = obter_telefone_real_waha(
        chat_id,
        sessao,
        empresa_id,
    )

    dados = MensagemRequest(
        empresa_id=empresa_id,
        nome=nome,
        telefone=telefone_real,
        canal="whatsapp",
        identificador=chat_id,
        mensagem=texto,
    )

    resultado = receber_mensagem(dados)

    if resultado.get("erro"):
        liberar_mensagem_waha(mensagem_id)
        return {
            "status": "erro",
            "empresa_id": empresa_id,
            "sessao": sessao,
            **resultado,
        }

    resposta = resultado.get("resposta_agente")

    if (
        resultado.get("nova_lead") is True
        and resultado.get("notificacao_luciano")
    ):
        chat_id_luciano = obter_lid_luciano()

        if chat_id_luciano:
            headers_notificacao = {
                "Content-Type": "application/json",
                "X-Api-Key": os.getenv(
                    "WAHA_API_KEY",
                    "orionsystems",
                ),
            }

            try:
                envio_notificacao = requests.post(
                    "http://localhost:3000/api/sendText",
                    headers=headers_notificacao,
                    json={
                        "session": sessao,
                        "chatId": chat_id_luciano,
                        "text": resultado["notificacao_luciano"],
                    },
                    timeout=15,
                )

                envio_notificacao.raise_for_status()

            except requests.RequestException:
                traceback.print_exc()

    status_envio = None

    if resposta:
        delay = calcular_delay_resposta(resposta)

        headers = {
            "Content-Type": "application/json",
            "X-Api-Key": os.getenv("WAHA_API_KEY", "orionsystems"),
        }

        definir_presenca_digitacao(
            sessao,
            chat_id,
            True,
            headers,
        )

        time.sleep(delay)

        definir_presenca_digitacao(
            sessao,
            chat_id,
            False,
            headers,
        )

        envio_ok, status_envio = enviar_texto_waha(
            sessao,
            chat_id,
            resposta,
            headers,
        )

        if not envio_ok:
            print(
                "[WAHA WEBHOOK] resposta não confirmada por HTTP; "
                f"status={status_envio}; message_id={mensagem_id}",
                flush=True,
            )

    return {
        "status": "processado",
        "empresa_id": empresa_id,
        "sessao": sessao,
        "chat_id": chat_id,
        "mensagem": texto,
        "message_id": mensagem_id,
        "resposta": resposta,
        "status_envio": status_envio,
    }
