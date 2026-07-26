from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)

from app.database.database import Base


class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    nome = Column(
        String(150),
        nullable=True,
        index=True,
    )

    empresa = Column(
        String(150),
        nullable=True,
        index=True,
    )

    segmento = Column(
        String(120),
        nullable=True,
        index=True,
    )

    telefone = Column(
        String(30),
        nullable=True,
        index=True,
    )

    canal = Column(
        String(30),
        nullable=True,
        index=True,
    )

    criado_em = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )


class Conversa(Base):
    __tablename__ = "conversas"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    identificador = Column(
        String(150),
        nullable=False,
        index=True,
    )

    nome = Column(
        String(150),
        nullable=True,
        index=True,
    )

    empresa = Column(
        String(150),
        nullable=True,
        index=True,
    )

    segmento = Column(
        String(120),
        nullable=True,
        index=True,
    )

    telefone = Column(
        String(30),
        nullable=True,
        index=True,
    )

    canal = Column(
        String(30),
        nullable=False,
        index=True,
    )

    etapa = Column(
        String(50),
        default="inicio",
        nullable=False,
        index=True,
    )

    objetivo = Column(
        Text,
        nullable=True,
    )

    servico = Column(
        String(150),
        nullable=True,
        index=True,
    )

    historico = Column(
        Text,
        nullable=True,
    )

    criado_em = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )


class Lead(Base):
    __tablename__ = "leads"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    cliente_id = Column(
        Integer,
        ForeignKey(
            "clientes.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    produto = Column(
        String(150),
        nullable=True,
        index=True,
    )

    temperatura = Column(
        String(30),
        nullable=True,
        index=True,
    )

    prioridade = Column(
        String(30),
        nullable=True,
        index=True,
    )

    score = Column(
        Integer,
        default=0,
        nullable=False,
        index=True,
    )

    origem = Column(
        String(50),
        nullable=True,
        index=True,
    )

    observacoes = Column(
        Text,
        nullable=True,
    )

    resumo_vendedor = Column(
        Text,
        nullable=True,
    )

    status = Column(
        String(50),
        default="Aguardando atendimento",
        nullable=False,
        index=True,
    )

    criado_em = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )