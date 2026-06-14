import traceback

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