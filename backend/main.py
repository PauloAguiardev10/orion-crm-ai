import json
import os
import random
import time
import traceback

import requests
from fastapi import FastAPI
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.agents.sdr_agent import (
    conduzir_conversa,
    gerar_resumo_vendedor,
)
from app.database.database import SessionLocal, engine
from app.models.models import Base, Cliente, Conversa, Lead


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
) -> str:
    """
    Tenta resolver o telefone real antes de salvar no CRM.

    Ordem:
    1. @c.us;
    2. cache em memória;
    3. agenda do WAHA;
    4. histórico do PostgreSQL;
    5. preserva o LID se não houver resolução.
    """

    if not chat_id:
        return chat_id

    if chat_id.endswith("@c.us"):
        telefone = chat_id.replace("@c.us", "").strip()
        return telefone or chat_id

    if not chat_id.endswith("@lid"):
        return chat_id

    telefone_cache = TELEFONES_LID_CACHE.get(chat_id)

    if telefone_cache:
        return telefone_cache

    lid_numero = chat_id.replace("@lid", "").strip()

    headers = {
        "X-Api-Key": os.getenv(
            "WAHA_API_KEY",
            "orionsystems",
        ),
    }

    try:
        resposta = requests.get(
            "http://localhost:3000/api/contacts/all",
            headers=headers,
            params={
                "session": sessao,
            },
            timeout=20,
        )

        resposta.raise_for_status()

        contatos = resposta.json()

        if isinstance(contatos, list):
            for contato in contatos:
                if not isinstance(contato, dict):
                    continue

                numero = str(
                    contato.get("number") or ""
                ).strip()

                if numero != lid_numero:
                    continue

                contato_id = contato.get("id")

                if isinstance(contato_id, dict):
                    contato_id = (
                        contato_id.get("_serialized")
                        or (
                            f"{contato_id.get('user')}@{contato_id.get('server')}"
                            if contato_id.get("user")
                            and contato_id.get("server")
                            else None
                        )
                    )

                if (
                    isinstance(contato_id, str)
                    and contato_id.endswith("@c.us")
                ):
                    telefone_real = (
                        contato_id
                        .replace("@c.us", "")
                        .strip()
                    )

                    if telefone_real:
                        TELEFONES_LID_CACHE[
                            chat_id
                        ] = telefone_real

                        return telefone_real

    except (
        requests.RequestException,
        ValueError,
        TypeError,
    ):
        pass

    telefone_banco = buscar_telefone_real_no_banco(
        chat_id,
        empresa_id,
    )

    if telefone_banco:
        TELEFONES_LID_CACHE[
            chat_id
        ] = telefone_banco

        return telefone_banco

    return chat_id


@app.post("/mensagem")
def receber_mensagem(dados: MensagemRequest):
    db: Session = SessionLocal()

    try:
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
                telefone=dados.telefone,
                etapa="inicio",
                historico="",
            )

            db.add(conversa)
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

        resposta, analise = conduzir_conversa(
            conversa,
            dados.mensagem,
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
            lead_existente = None

            if conversa.telefone:
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
                cliente = Cliente(
                    empresa_id=dados.empresa_id,
                    nome=conversa.nome,
                    empresa=conversa.empresa,
                    empresa_cliente=conversa.empresa,
                    segmento=conversa.segmento,
                    telefone=conversa.telefone,
                    canal=conversa.canal,
                    canal_origem=conversa.canal,
                )

                db.add(cliente)
                db.commit()
                db.refresh(cliente)

                conversa.cliente_id = cliente.id

                resumo = gerar_resumo_vendedor(
                    conversa,
                    analise,
                )

                lead = Lead(
                    empresa_id=dados.empresa_id,
                    cliente_id=cliente.id,
                    conversa_id=conversa.id,
                    produto=conversa.servico,
                    temperatura=analise["temperatura"],
                    prioridade=analise["prioridade"],
                    score=analise["score"],
                    origem=conversa.canal,
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


@app.post("/webhook/waha")
async def webhook_waha(payload: dict):
    evento = payload.get("event")
    mensagem = payload.get("payload", {})

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

    if resposta:
        tamanho = len(resposta)

        if tamanho <= 120:
            delay = random.uniform(2, 4)
        elif tamanho <= 350:
            delay = random.uniform(4, 7)
        else:
            delay = random.uniform(7, 12)

        headers = {
            "Content-Type": "application/json",
            "X-Api-Key": os.getenv(
                "WAHA_API_KEY",
                "orionsystems",
            ),
        }

        try:
            requests.post(
                "http://localhost:3000/api/startTyping",
                headers=headers,
                json={
                    "session": sessao,
                    "chatId": chat_id,
                },
                timeout=10,
            )
        except requests.RequestException:
            pass

        time.sleep(delay)

        try:
            requests.post(
                "http://localhost:3000/api/stopTyping",
                headers=headers,
                json={
                    "session": sessao,
                    "chatId": chat_id,
                },
                timeout=10,
            )
        except requests.RequestException:
            pass

        envio = requests.post(
            "http://localhost:3000/api/sendText",
            headers=headers,
            json={
                "session": sessao,
                "chatId": chat_id,
                "text": resposta,
            },
            timeout=15,
        )

        envio.raise_for_status()

    return {
        "status": "processado",
        "empresa_id": empresa_id,
        "sessao": sessao,
        "chat_id": chat_id,
        "mensagem": texto,
        "resposta": resposta,
    }