import traceback
import time
import random

from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.database import SessionLocal, engine
from app.models.models import Base, Cliente, Conversa, Lead

from app.agents.sdr_agent import (
    conduzir_conversa,
    gerar_resumo_vendedor
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Agente SDR Forway")


class MensagemRequest(BaseModel):
    nome: str | None = None
    telefone: str | None = None
    canal: str
    identificador: str
    mensagem: str


@app.post("/mensagem")
def receber_mensagem(dados: MensagemRequest):

    db: Session = SessionLocal()

    try:

        conversa = db.query(Conversa).filter(
            Conversa.identificador == dados.identificador
        ).first()

        if not conversa:

            conversa = Conversa(
                identificador=dados.identificador,
                canal=dados.canal,
                nome=dados.nome,
                telefone=dados.telefone,
                etapa="inicio",
                historico=""
            )

            db.add(conversa)
            db.commit()
            db.refresh(conversa)

        resposta, analise = conduzir_conversa(
            conversa,
            dados.mensagem
        )

        db.commit()

        resumo = None
        lead_id = None

        if conversa.etapa in ["encaminhar", "aguardando_humano"]:

            lead_existente = None

            if conversa.telefone:
                lead_existente = (
                    db.query(Lead)
                    .join(Cliente, Cliente.id == Lead.cliente_id)
                    .filter(
                        Cliente.telefone == conversa.telefone,
                        Cliente.canal == conversa.canal,
                    )
                    .first()
                )

            if not lead_existente:

                cliente = Cliente(
                    nome=conversa.nome,
                    empresa=conversa.empresa,
                    segmento=conversa.segmento,
                    telefone=conversa.telefone,
                    canal=conversa.canal
                )

                db.add(cliente)
                db.commit()
                db.refresh(cliente)

                resumo = gerar_resumo_vendedor(
                    conversa,
                    analise
                )

                lead = Lead(
                    cliente_id=cliente.id,
                    produto=conversa.servico,
                    temperatura=analise["temperatura"],
                    prioridade=analise["prioridade"],
                    score=analise["score"],
                    origem=conversa.canal,
                    observacoes=conversa.objetivo,
                    resumo_vendedor=resumo,
                    status="Aguardando atendimento"
                )

                db.add(lead)
                db.commit()
                db.refresh(lead)

                lead_id = lead.id

            else:

                resumo = lead_existente.resumo_vendedor
                lead_id = lead_existente.id

        return {
            "canal": conversa.canal,
            "etapa_atual": conversa.etapa,
            "resposta_agente": resposta,
            "produto_identificado": conversa.servico,
            "temperatura": analise["temperatura"],
            "prioridade": analise["prioridade"],
            "score": analise["score"],
            "status": (
                "encaminhado"
                if conversa.etapa in ["encaminhar", "aguardando_humano"]
                else "em_atendimento"
            ),
            "resumo_vendedor": resumo,
            "lead_id": lead_id
        }

    except Exception as erro:
        traceback.print_exc()

        return {
            "erro": str(erro),
            "tipo": type(erro).__name__
        }

    finally:
        db.close()
@app.post("/webhook/waha")
async def webhook_waha(payload: dict):
    import requests

    evento = payload.get("event")
    mensagem = payload.get("payload", {})

    if evento != "message":
        return {"status": "ignorado", "motivo": "evento_diferente_de_message"}

    if mensagem.get("fromMe") is True:
        return {"status": "ignorado", "motivo": "mensagem_enviada_pelo_proprio_numero"}

    texto = mensagem.get("body")
    chat_id = mensagem.get("from")
    nome = mensagem.get("_data", {}).get("notifyName")

    if not texto or not chat_id:
        return {"status": "ignorado", "motivo": "sem_texto_ou_chat_id"}

    dados = MensagemRequest(
        nome=nome,
        telefone=chat_id,
        canal="whatsapp",
        identificador=chat_id,
        mensagem=texto
    )

    resultado = receber_mensagem(dados)
    resposta = resultado.get("resposta_agente")

    if resposta:
        tamanho = len(resposta)

        if tamanho <= 120:
            delay = random.uniform(2, 4)
        elif tamanho <= 350:
            delay = random.uniform(4, 7)
        else:
            delay = random.uniform(7, 12)

        try:
            requests.post(
                "http://localhost:3000/api/startTyping",
                headers={
                    "Content-Type": "application/json",
                    "X-Api-Key": "orionsystems"
                },
                json={
                    "session": "default",
                    "chatId": chat_id
                },
                timeout=10
            )
        except Exception:
            pass

        time.sleep(delay)

        try:
            requests.post(
                "http://localhost:3000/api/stopTyping",
                headers={
                    "Content-Type": "application/json",
                    "X-Api-Key": "orionsystems"
                },
                json={
                    "session": "default",
                    "chatId": chat_id
                },
                timeout=10
            )
        except Exception:
            pass

        requests.post(
            "http://localhost:3000/api/sendText",
            headers={
                "Content-Type": "application/json",
                "X-Api-Key": "orionsystems"
            },
            json={
                "session": "default",
                "chatId": chat_id,
                "text": resposta
            },
            timeout=15
        )

    return {
        "status": "processado",
        "chat_id": chat_id,
        "mensagem": texto,
        "resposta": resposta
    }
