from sqlalchemy import Time
from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)

from app.database.database import Base


# ============================================================
# EMPRESAS / MULTIEMPRESA
# ============================================================


class Empresa(Base):
    """
    Tenant do Orion CRM.

    A tabela empresas também representa a hierarquia comercial:
    Orion Systems (master) -> parceiro -> clientes do parceiro.
    """

    __tablename__ = "empresas"

    id = Column(Integer, primary_key=True, index=True)

    nome = Column(
        String(255),
        nullable=False,
        unique=True,
    )

    plano = Column(
        String(50),
        nullable=True,
        server_default="Lite",
    )

    nicho = Column(String(255), nullable=True)

    timezone = Column(
        String(80),
        nullable=False,
        server_default="America/Fortaleza",
    )

    nome_agente = Column(
        String(100),
        nullable=True,
        server_default="Sofia",
    )

    status = Column(
        String(30),
        nullable=True,
        server_default="ativa",
    )

    whatsapp = Column(
        Boolean,
        nullable=True,
        server_default="true",
    )

    instagram = Column(
        Boolean,
        nullable=True,
        server_default="false",
    )

    facebook = Column(
        Boolean,
        nullable=True,
        server_default="false",
    )

    crm = Column(
        Boolean,
        nullable=True,
        server_default="false",
    )

    funil = Column(
        Boolean,
        nullable=True,
        server_default="false",
    )

    analytics = Column(
        Boolean,
        nullable=True,
        server_default="false",
    )

    vendas_ia = Column(
        Boolean,
        nullable=True,
        server_default="false",
    )

    criado_em = Column(
        DateTime,
        nullable=True,
        server_default=func.now(),
    )

    slug = Column(String(255), nullable=True)

    tipo = Column(String(50), nullable=True)

    logo_path = Column(Text, nullable=True)

    parceiro_nome = Column(String(255), nullable=True)

    data_adesao = Column(Date, nullable=True)

    data_vencimento = Column(Date, nullable=True)

    status_financeiro = Column(String(30), nullable=True)

    bloqueio_automatico = Column(Boolean, nullable=True)

    valor_mensal = Column(
        Numeric(12, 2),
        nullable=True,
    )

    # Campo legado/comercial da assinatura da empresa no Orion.
    # Não confundir com a tabela "servicos", que representa
    # os serviços vendidos pela própria empresa aos seus clientes.
    servicos = Column(Text, nullable=True)

    parceiro_id = Column(
        Integer,
        ForeignKey(
            "empresas.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
        index=True,
    )


class EmpresaAtendimentoConfig(Base):
    """
    Dados institucionais e operacionais fornecidos pela empresa
    para uso da Sofia durante os atendimentos.

    Esta tabela NAO armazena regras comportamentais, prompts,
    qualificacao, score ou logica interna do agente.
    """

    __tablename__ = "empresa_atendimento_config"

    id = Column(Integer, primary_key=True, index=True)

    empresa_id = Column(
        Integer,
        ForeignKey(
            "empresas.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
        index=True,
    )

    descricao_empresa = Column(Text, nullable=True)

    whatsapp_comercial = Column(String(80), nullable=True)
    email_comercial = Column(String(150), nullable=True)

    site = Column(Text, nullable=True)
    instagram_url = Column(Text, nullable=True)
    facebook_url = Column(Text, nullable=True)

    horario_atendimento = Column(Text, nullable=True)
    regiao_atendimento = Column(Text, nullable=True)

    informacoes_comerciais = Column(Text, nullable=True)
    observacoes_atendimento = Column(Text, nullable=True)

    responsavel_leads = Column(String(150), nullable=True)
    whatsapp_notificacao = Column(String(80), nullable=True)
    email_notificacao = Column(String(150), nullable=True)

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


class AgenteConfig(Base):
    """
    Configuração comportamental e operacional do agente de uma empresa.

    Existe no máximo uma configuração por empresa.
    Produtos, serviços e especialistas ficam em tabelas próprias.
    """

    __tablename__ = "agente_config"

    id = Column(Integer, primary_key=True, index=True)

    empresa_id = Column(
        Integer,
        ForeignKey(
            "empresas.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        unique=True,
    )

    nome_agente = Column(
        String(100),
        nullable=True,
        server_default="Sofia",
    )

    tom = Column(
        String(100),
        nullable=True,
        server_default="Humanizado",
    )

    nicho = Column(Text, nullable=True)

    objetivo = Column(Text, nullable=True)

    ia_pode_vender = Column(
        Boolean,
        nullable=True,
        server_default="false",
    )

    ia_envia_pix = Column(
        Boolean,
        nullable=True,
        server_default="false",
    )

    ia_envia_link = Column(
        Boolean,
        nullable=True,
        server_default="false",
    )

    whatsapp = Column(
        Boolean,
        nullable=True,
        server_default="true",
    )

    instagram = Column(
        Boolean,
        nullable=True,
        server_default="false",
    )

    facebook = Column(
        Boolean,
        nullable=True,
        server_default="false",
    )


class Produto(Base):
    """
    Produto físico ou digital comercializado pela empresa.
    """

    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, index=True)

    empresa_id = Column(
        Integer,
        ForeignKey(
            "empresas.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    nome = Column(String(255), nullable=True)

    categoria = Column(String(100), nullable=True)

    descricao = Column(Text, nullable=True)

    preco = Column(
        Numeric(10, 2),
        nullable=True,
        server_default="0",
    )

    ativo = Column(
        Boolean,
        nullable=True,
        server_default="true",
    )

    criado_em = Column(
        DateTime,
        nullable=True,
        server_default=func.now(),
    )


class Servico(Base):
    """
    Serviço comercializado pela empresa aos seus clientes.
    """

    __tablename__ = "servicos"

    __table_args__ = (
        UniqueConstraint(
            "empresa_id",
            "id",
            name="uq_servicos_empresa_id_id",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    empresa_id = Column(
        Integer,
        ForeignKey(
            "empresas.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    nome = Column(
        String(255),
        nullable=False,
    )

    descricao = Column(
        Text,
        nullable=True,
    )

    palavras_chave = Column(
        Text,
        nullable=True,
    )

    ativo = Column(
        Boolean,
        nullable=False,
        server_default="true",
    )


class Especialista(Base):
    """
    Especialista humano que pode receber oportunidades da empresa.
    """

    __tablename__ = "especialistas"

    __table_args__ = (
        UniqueConstraint(
            "empresa_id",
            "id",
            name="uq_especialistas_empresa_id_id",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    empresa_id = Column(
        Integer,
        ForeignKey(
            "empresas.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    nome = Column(
        String(255),
        nullable=False,
    )

    usuario_id = Column(
        Integer,
        nullable=True,
        index=True,
    )


class EspecialistaServico(Base):
    """
    Relaciona especialistas aos serviços que atendem.

    As FKs compostas impedem que um especialista de uma empresa
    seja associado ao serviço pertencente a outro tenant.
    """

    __tablename__ = "especialista_servicos"

    __table_args__ = (
        ForeignKeyConstraint(
            ["empresa_id", "especialista_id"],
            ["especialistas.empresa_id", "especialistas.id"],
            name="fk_especialista_servicos_especialista_empresa",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["empresa_id", "servico_id"],
            ["servicos.empresa_id", "servicos.id"],
            name="fk_especialista_servicos_servico_empresa",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "empresa_id",
            "especialista_id",
            "servico_id",
            name="uq_especialista_servicos_empresa_especialista_servico",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    empresa_id = Column(
        Integer,
        ForeignKey(
            "empresas.id",
            ondelete="RESTRICT",
            name="fk_especialista_servicos_empresa",
        ),
        nullable=False,
        index=True,
    )

    especialista_id = Column(
        Integer,
        nullable=False,
    )

    servico_id = Column(
        Integer,
        nullable=False,
    )


# ============================================================
# OPERAÇÃO COMERCIAL
# ============================================================


class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)

    # O DEFAULT 1 é legado e será removido em uma migration
    # específica após auditarmos todos os fluxos de criação.
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

    __table_args__ = (
        UniqueConstraint(
            "empresa_id",
            "id",
            name="uq_conversas_empresa_id_id",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    # O DEFAULT 1 é legado e será removido depois da auditoria
    # completa dos canais e fluxos de criação de conversas.
    empresa_id = Column(
        Integer,
        nullable=False,
        server_default="1",
        index=True,
    )

    conexao_canal_id = Column(Integer, nullable=True)
    especialista_id = Column(Integer, nullable=True, index=True)

    cliente_id = Column(
        Integer,
        ForeignKey(
            "clientes.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    identificador = Column(
        String(180),
        nullable=False,
        index=True,
    )

    canal = Column(
        String(80),
        nullable=False,
    )

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

    servico_interesse = Column(
        String(150),
        nullable=True,
    )

    historico = Column(Text, nullable=True)

    ultima_mensagem_cliente_em = Column(
        DateTime,
        nullable=True,
    )

    ultima_mensagem_agente_em = Column(
        DateTime,
        nullable=True,
    )

    ultima_mensagem_humano_em = Column(
        DateTime,
        nullable=True,
    )

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

    # Origem comercial pela qual o cliente conheceu a empresa.
    # Exemplos:
    # indicacao
    # referencia_cliente
    # anuncio_instagram
    # anuncio_facebook
    # anuncio
    # organico_instagram
    # organico_facebook
    origem_aquisicao = Column(
        String(80),
        nullable=True,
    )

    # Proveniencia tecnica de anuncio Click-to-WhatsApp.
    # Independente da origem comercial informada pelo cliente.
    anuncio_referral_confirmado = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    anuncio_referral_id = Column(
        String(180),
        nullable=True,
    )

    anuncio_referral_recebido_em = Column(
        DateTime(timezone=True),
        nullable=True,
    )



class Lead(Base):
    __tablename__ = "leads"

    __table_args__ = (
        UniqueConstraint(
            "empresa_id",
            "id",
            name="uq_leads_empresa_id_id",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    # O DEFAULT 1 é legado e será removido após a auditoria
    # completa dos fluxos de criação de leads.
    empresa_id = Column(
        Integer,
        nullable=False,
        server_default="1",
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

    conversa_id = Column(
        Integer,
        ForeignKey(
            "conversas.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    # A associação multiempresa de especialistas será integrada
    # ao fluxo operacional em uma etapa posterior.
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

    entrada_followup_em = Column(
        DateTime(timezone=True),
        nullable=True,
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


# ============================================================
# INTEGRAÇÕES / CANAIS
# ============================================================


class ConexaoCanal(Base):
    """
    Conexão de um canal externo com uma empresa do Orion CRM.

    A mesma estrutura atende Instagram, Facebook/Messenger
    e futuramente WhatsApp Cloud API.
    """

    __tablename__ = "conexoes_canais"

    id = Column(Integer, primary_key=True, index=True)

    empresa_id = Column(
        Integer,
        ForeignKey(
            "empresas.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    provedor = Column(
        String(50),
        nullable=False,
        server_default="meta",
    )

    canal = Column(
        String(50),
        nullable=False,
        index=True,
    )

    # Identificador da conta que recebe os eventos.
    # No Instagram será o ID da conta profissional.
    account_id = Column(
        String(150),
        nullable=True,
        index=True,
    )

    # Utilizado quando a integração envolver uma Página do Facebook.
    page_id = Column(
        String(150),
        nullable=True,
        index=True,
    )

    # Será utilizado posteriormente pela WhatsApp Cloud API.
    phone_number_id = Column(
        String(150),
        nullable=True,
        index=True,
    )

    sessao_waha = Column(String(120), nullable=True)
    especialista_id = Column(Integer, nullable=True)
    nome_conexao = Column(String(100), nullable=True)
    gerenciada_crm = Column(Boolean, nullable=False, server_default="false")
    sofia_ativa = Column(Boolean, nullable=False, server_default="true")
    operacao_suspensa = Column(Boolean, nullable=False, server_default="false")

    # Token da API do provedor.
    # Nunca deve ser exibido em logs ou respostas públicas.
    access_token = Column(
        Text,
        nullable=True,
    )

    ativo = Column(
        Boolean,
        nullable=False,
        server_default="true",
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


class Mensagem(Base):
    __tablename__ = "mensagens"

    __table_args__ = (
        UniqueConstraint(
            "empresa_id",
            "conversa_id",
            "id",
            name="uq_mensagens_empresa_conversa_id",
        ),
    )

    id = Column(Integer, primary_key=True)

    empresa_id = Column(
        Integer,
        ForeignKey("empresas.id", ondelete="CASCADE"),
        nullable=False,
    )

    conversa_id = Column(
        Integer,
        ForeignKey("conversas.id", ondelete="CASCADE"),
        nullable=False,
    )

    cliente_id = Column(
        Integer,
        ForeignKey("clientes.id", ondelete="SET NULL"),
        nullable=True,
    )

    remetente = Column(String(50), nullable=False)
    texto = Column(Text, nullable=True)
    tipo = Column(String(50), nullable=True, server_default="texto")
    midia_url = Column(Text, nullable=True)
    midia_tipo = Column(String(50), nullable=True)
    from_me = Column(Boolean, nullable=True, server_default="false")
    conexao_canal_id = Column(Integer, nullable=True)
    especialista_id = Column(Integer, nullable=True)
    mensagem_id_externo = Column(String(180), nullable=True)
    mensagem_id_waha = Column(String(180), nullable=True)
    sessao_waha = Column(String(120), nullable=True)
    criado_em = Column(DateTime, nullable=True, server_default=func.now())
    status_processamento = Column(String(30), nullable=True)
    processado_em = Column(DateTime, nullable=True)
    status_envio = Column(String(40), nullable=True)


# ============================================================
# FOLLOW-UP AUTOMATICO
# ============================================================


class FollowupAgendamento(Base):
    __tablename__ = "followup_agendamentos"

    __table_args__ = (
        ForeignKeyConstraint(
            ["empresa_id", "lead_id"],
            ["leads.empresa_id", "leads.id"],
            name="fk_followup_lead_empresa",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["empresa_id", "conversa_id"],
            ["conversas.empresa_id", "conversas.id"],
            name="fk_followup_conversa_empresa",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["empresa_id", "conversa_id", "mensagem_id"],
            [
                "mensagens.empresa_id",
                "mensagens.conversa_id",
                "mensagens.id",
            ],
            name="fk_followup_mensagem",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "mensagem_id IS NULL OR conversa_id IS NOT NULL",
            name="ck_followup_mensagem_exige_conversa",
        ),
        CheckConstraint(
            "numero_tentativa >= 1",
            name="ck_followup_numero_tentativa",
        ),
        CheckConstraint(
            "tentativas_envio >= 0",
            name="ck_followup_tentativas_envio",
        ),
        CheckConstraint(
            "status IN ("
            "'pendente', 'processando', 'enviado', "
            "'cancelado', 'falha', 'inconclusivo')",
            name="ck_followup_status",
        ),
        UniqueConstraint(
            "empresa_id",
            "lead_id",
            "numero_tentativa",
            name="uq_followup_empresa_lead_tentativa",
        ),
    )

    id = Column(BigInteger, primary_key=True)

    empresa_id = Column(
        Integer,
        ForeignKey("empresas.id", ondelete="RESTRICT"),
        nullable=False,
    )

    lead_id = Column(Integer, nullable=False)
    conversa_id = Column(Integer, nullable=True)

    numero_tentativa = Column(
        Integer,
        nullable=False,
        server_default="1",
    )

    entrada_lead_em = Column(DateTime(timezone=True), nullable=False)
    agendado_para = Column(DateTime(timezone=True), nullable=False)

    status = Column(
        String(30),
        nullable=False,
        server_default="pendente",
    )

    tentativas_envio = Column(
        Integer,
        nullable=False,
        server_default="0",
    )

    mensagem_id = Column(Integer, nullable=True)
    mensagem_id_externo = Column(String(180), nullable=True)
    erro_envio = Column(Text, nullable=True)

    reservado_em = Column(DateTime(timezone=True), nullable=True)
    reserva_token = Column(String(100), nullable=True)
    reserva_expira_em = Column(DateTime(timezone=True), nullable=True)
    envio_iniciado_em = Column(DateTime(timezone=True), nullable=True)

    criado_em = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    atualizado_em = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    enviado_em = Column(DateTime(timezone=True), nullable=True)
    cancelado_em = Column(DateTime(timezone=True), nullable=True)

class FollowupConfiguracao(Base):
    __tablename__ = "followup_configuracoes"

    __table_args__ = (
        CheckConstraint(
            "modo IN ('padrao_orion', 'personalizado')",
            name="ck_followup_modo",
        ),
        CheckConstraint(
            "quantidade_tentativas BETWEEN 1 AND 10",
            name="ck_followup_quantidade",
        ),
        CheckConstraint(
            "segunda_sexta_inicio < segunda_sexta_fim",
            name="ck_followup_semana_horarios",
        ),
        CheckConstraint(
            "sabado_inicio < sabado_fim",
            name="ck_followup_sabado_horarios",
        ),
    )

    id = Column(BigInteger, primary_key=True)
    empresa_id = Column(
        Integer,
        ForeignKey("empresas.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )

    ativo = Column(Boolean, nullable=False, server_default="false")
    modo = Column(String(20), nullable=False, server_default="padrao_orion")
    quantidade_tentativas = Column(Integer, nullable=False, server_default="3")
    fuso_horario = Column(
        String(80),
        nullable=False,
        server_default="America/Sao_Paulo",
    )

    segunda_sexta_inicio = Column(Time, nullable=False, server_default="08:00")
    segunda_sexta_fim = Column(Time, nullable=False, server_default="18:00")
    sabado_ativo = Column(Boolean, nullable=False, server_default="true")
    sabado_inicio = Column(Time, nullable=False, server_default="08:00")
    sabado_fim = Column(Time, nullable=False, server_default="12:00")
    domingo_ativo = Column(Boolean, nullable=False, server_default="false")

    criado_em = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    atualizado_em = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class FollowupModeloMensagem(Base):
    __tablename__ = "followup_modelos_mensagem"

    __table_args__ = (
        UniqueConstraint(
            "empresa_id",
            "numero_tentativa",
            name="uq_followup_modelo_empresa_tentativa",
        ),
        CheckConstraint(
            "numero_tentativa BETWEEN 1 AND 10",
            name="ck_followup_modelo_tentativa",
        ),
        CheckConstraint(
            "intervalo_minutos BETWEEN 1 AND 43200",
            name="ck_followup_modelo_intervalo",
        ),
        CheckConstraint(
            "length(trim(texto)) BETWEEN 1 AND 4000",
            name="ck_followup_modelo_texto",
        ),
    )

    id = Column(BigInteger, primary_key=True)
    empresa_id = Column(
        Integer,
        ForeignKey("empresas.id", ondelete="RESTRICT"),
        nullable=False,
    )
    numero_tentativa = Column(Integer, nullable=False)
    intervalo_minutos = Column(Integer, nullable=False)
    texto = Column(Text, nullable=False)
    ativo = Column(Boolean, nullable=False, server_default="true")

    criado_em = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    atualizado_em = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
