from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)

from app.database.database import Base


class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)

    # A chave estrangeira existe no PostgreSQL.
    # Mantemos Integer no ORM porque a tabela empresas não é mapeada
    # neste módulo e o banco já garante a integridade referencial.
    empresa_id = Column(
        Integer,
        nullable=False,
        server_default="1",
        index=True,
    )

    nome = Column(String(150), nullable=True)
    empresa_cliente = Column(String(150), nullable=True)
    segmento = Column(String(120), nullable=True)
    telefone = Column(String(80), nullable=True)
    email = Column(String(150), nullable=True)
    canal_origem = Column(String(80), nullable=True)

    status = Column(
        String(30),
        nullable=True,
        server_default="ativo",
    )

    criado_em = Column(
        DateTime,
        nullable=True,
        server_default=func.now(),
    )

    atualizado_em = Column(
        DateTime,
        nullable=True,
        server_default=func.now(),
        onupdate=func.now(),
    )

    empresa = Column(String(150), nullable=True)
    canal = Column(String(80), nullable=True)


class Conversa(Base):
    __tablename__ = "conversas"

    id = Column(Integer, primary_key=True, index=True)

    # FK garantida pelo PostgreSQL.
    empresa_id = Column(
        Integer,
        nullable=False,
        server_default="1",
        index=True,
    )

    cliente_id = Column(
        Integer,
        ForeignKey("clientes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    identificador = Column(
        String(180),
        nullable=False,
        index=True,
    )

    canal = Column(String(80), nullable=False)

    etapa = Column(
        String(80),
        nullable=True,
        server_default="inicio",
    )

    status_atendimento = Column(
        String(80),
        nullable=True,
        server_default="em_atendimento_ia",
    )

    humano_assumiu = Column(
        Boolean,
        nullable=True,
        server_default="false",
    )

    objetivo = Column(Text, nullable=True)
    servico_interesse = Column(String(150), nullable=True)
    historico = Column(Text, nullable=True)

    ultima_mensagem_cliente_em = Column(DateTime, nullable=True)
    ultima_mensagem_agente_em = Column(DateTime, nullable=True)
    ultima_mensagem_humano_em = Column(DateTime, nullable=True)

    lembrete_20min_enviado = Column(
        Boolean,
        nullable=True,
        server_default="false",
    )

    criado_em = Column(
        DateTime,
        nullable=True,
        server_default=func.now(),
    )

    atualizado_em = Column(
        DateTime,
        nullable=True,
        server_default=func.now(),
        onupdate=func.now(),
    )

    nome = Column(String(150), nullable=True)
    empresa = Column(String(150), nullable=True)
    segmento = Column(String(120), nullable=True)
    telefone = Column(String(80), nullable=True)
    servico = Column(String(150), nullable=True)


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)

    # FK garantida pelo PostgreSQL.
    empresa_id = Column(
        Integer,
        nullable=False,
        server_default="1",
        index=True,
    )

    cliente_id = Column(
        Integer,
        ForeignKey("clientes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    conversa_id = Column(
        Integer,
        ForeignKey("conversas.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # A FK para especialistas continua sendo validada pelo PostgreSQL.
    especialista_id = Column(
        Integer,
        nullable=True,
        index=True,
    )

    produto = Column(String(150), nullable=True)
    temperatura = Column(String(30), nullable=True)
    prioridade = Column(String(30), nullable=True)

    score = Column(
        Integer,
        nullable=True,
        server_default="0",
    )

    origem = Column(String(80), nullable=True)
    observacoes = Column(Text, nullable=True)
    resumo_vendedor = Column(Text, nullable=True)

    status = Column(
        String(80),
        nullable=True,
        server_default="Aguardando atendimento",
    )

    responsavel = Column(
        String(150),
        nullable=True,
        server_default="Não atribuído",
    )

    valor_negocio = Column(
        Numeric,
        nullable=True,
        server_default="0",
    )

    mensalidade = Column(
        Numeric,
        nullable=True,
        server_default="0",
    )

    motivo_perda = Column(Text, nullable=True)
    observacao_comercial = Column(Text, nullable=True)

    criado_em = Column(
        DateTime,
        nullable=True,
        server_default=func.now(),
    )

    atualizado_em = Column(
        DateTime,
        nullable=True,
        server_default=func.now(),
        onupdate=func.now(),
    )