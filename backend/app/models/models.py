from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from app.database.database import Base


class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)

    nome = Column(String)
    empresa = Column(String)
    segmento = Column(String)

    telefone = Column(String)

    canal = Column(String)

    criado_em = Column(
        DateTime,
        default=datetime.utcnow
    )


class Conversa(Base):
    __tablename__ = "conversas"

    id = Column(Integer, primary_key=True, index=True)

    identificador = Column(String)

    nome = Column(String)

    empresa = Column(String)

    segmento = Column(String)

    telefone = Column(String)

    canal = Column(String)

    etapa = Column(String)

    objetivo = Column(Text)

    servico = Column(String)

    historico = Column(Text)

    criado_em = Column(
        DateTime,
        default=datetime.utcnow
    )


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)

    cliente_id = Column(Integer)

    produto = Column(String)

    temperatura = Column(String)

    prioridade = Column(String)

    score = Column(Integer)

    origem = Column(String)

    observacoes = Column(Text)

    resumo_vendedor = Column(Text)

    status = Column(
        String,
        default="Aguardando atendimento"
    )

    criado_em = Column(
        DateTime,
        default=datetime.utcnow
    )