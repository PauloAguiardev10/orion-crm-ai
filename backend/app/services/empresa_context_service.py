from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.models.models import (
    AgenteConfig,
    ConexaoCanal,
    Empresa,
    Especialista,
    EspecialistaServico,
    Produto,
    Servico,
)


# ============================================================
# OBJETOS DE CONTEXTO
# ============================================================


@dataclass(frozen=True)
class ConfiguracaoAgenteContexto:
    nome_agente: str
    tom: str
    nicho: Optional[str]
    objetivo: Optional[str]

    ia_pode_vender: bool
    ia_envia_pix: bool
    ia_envia_link: bool

    whatsapp: bool
    instagram: bool
    facebook: bool


@dataclass(frozen=True)
class ServicoContexto:
    id: int
    nome: str
    descricao: Optional[str] = None
    palavras_chave: Optional[str] = None
    ativo: bool = True


@dataclass(frozen=True)
class ProdutoContexto:
    id: int
    nome: str
    categoria: Optional[str]
    descricao: Optional[str]
    preco: Optional[Decimal]
    ativo: bool


@dataclass(frozen=True)
class EspecialistaContexto:
    id: int
    nome: str
    servicos_ids: tuple[int, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class CanalContexto:
    id: int
    provedor: str
    canal: str
    ativo: bool

    account_id: Optional[str] = None
    page_id: Optional[str] = None
    phone_number_id: Optional[str] = None


@dataclass(frozen=True)
class ContextoEmpresa:
    empresa_id: int
    nome_empresa: str

    slug: Optional[str]
    tipo: Optional[str]
    parceiro_id: Optional[int]

    nicho_empresa: Optional[str]
    status_empresa: Optional[str]

    agente: ConfiguracaoAgenteContexto

    servicos: tuple[ServicoContexto, ...]
    produtos: tuple[ProdutoContexto, ...]
    especialistas: tuple[EspecialistaContexto, ...]
    canais: tuple[CanalContexto, ...]

    @property
    def empresa_ativa(self) -> bool:
        return (self.status_empresa or "").strip().lower() == "ativa"

    @property
    def possui_servicos(self) -> bool:
        return bool(self.servicos)

    @property
    def possui_produtos(self) -> bool:
        return bool(self.produtos)


# ============================================================
# EXCEÇÕES
# ============================================================


class ContextoEmpresaErro(Exception):
    """Erro base da camada de contexto multiempresa."""


class EmpresaNaoEncontradaErro(ContextoEmpresaErro):
    """Empresa solicitada não existe."""


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================


def _bool_seguro(valor, padrao: bool = False) -> bool:
    if valor is None:
        return padrao

    return bool(valor)


def _texto_ou_padrao(
    valor: Optional[str],
    padrao: str,
) -> str:
    if valor is None:
        return padrao

    texto = str(valor).strip()

    if not texto:
        return padrao

    return texto


def _montar_configuracao_agente(
    empresa: Empresa,
    config: Optional[AgenteConfig],
) -> ConfiguracaoAgenteContexto:
    """
    Monta a configuração efetiva do agente.

    Se ainda não existir agente_config para a empresa,
    utiliza apenas defaults seguros vindos do cadastro
    da própria empresa.

    Nunca busca configuração de outra empresa como fallback.
    """

    if config is None:
        return ConfiguracaoAgenteContexto(
            nome_agente=_texto_ou_padrao(
                empresa.nome_agente,
                "Sofia",
            ),
            tom="Humanizado",
            nicho=empresa.nicho,
            objetivo=None,
            ia_pode_vender=False,
            ia_envia_pix=False,
            ia_envia_link=False,
            whatsapp=_bool_seguro(
                empresa.whatsapp,
                True,
            ),
            instagram=_bool_seguro(
                empresa.instagram,
                False,
            ),
            facebook=_bool_seguro(
                empresa.facebook,
                False,
            ),
        )

    return ConfiguracaoAgenteContexto(
        nome_agente=_texto_ou_padrao(
            config.nome_agente,
            _texto_ou_padrao(
                empresa.nome_agente,
                "Sofia",
            ),
        ),
        tom=_texto_ou_padrao(
            config.tom,
            "Humanizado",
        ),
        nicho=config.nicho or empresa.nicho,
        objetivo=config.objetivo,
        ia_pode_vender=_bool_seguro(
            config.ia_pode_vender,
            False,
        ),
        ia_envia_pix=_bool_seguro(
            config.ia_envia_pix,
            False,
        ),
        ia_envia_link=_bool_seguro(
            config.ia_envia_link,
            False,
        ),
        whatsapp=_bool_seguro(
            config.whatsapp,
            _bool_seguro(empresa.whatsapp, True),
        ),
        instagram=_bool_seguro(
            config.instagram,
            _bool_seguro(empresa.instagram, False),
        ),
        facebook=_bool_seguro(
            config.facebook,
            _bool_seguro(empresa.facebook, False),
        ),
    )


def _carregar_servicos(
    db: Session,
    empresa_id: int,
) -> tuple[ServicoContexto, ...]:
    registros = (
        db.query(Servico)
        .filter(
            Servico.empresa_id == empresa_id,
            Servico.ativo.is_(True),
        )
        .order_by(
            Servico.nome.asc(),
            Servico.id.asc(),
        )
        .all()
    )

    return tuple(
        ServicoContexto(
            id=registro.id,
            nome=registro.nome,
            descricao=registro.descricao,
            palavras_chave=registro.palavras_chave,
            ativo=bool(registro.ativo),
        )
        for registro in registros
    )


def _carregar_produtos(
    db: Session,
    empresa_id: int,
) -> tuple[ProdutoContexto, ...]:
    registros = (
        db.query(Produto)
        .filter(
            Produto.empresa_id == empresa_id,
            Produto.ativo.is_(True),
        )
        .order_by(
            Produto.nome.asc(),
            Produto.id.asc(),
        )
        .all()
    )

    return tuple(
        ProdutoContexto(
            id=registro.id,
            nome=registro.nome or "",
            categoria=registro.categoria,
            descricao=registro.descricao,
            preco=registro.preco,
            ativo=_bool_seguro(
                registro.ativo,
                True,
            ),
        )
        for registro in registros
    )


def _carregar_especialistas(
    db: Session,
    empresa_id: int,
) -> tuple[EspecialistaContexto, ...]:
    especialistas = (
        db.query(Especialista)
        .filter(
            Especialista.empresa_id == empresa_id,
        )
        .order_by(
            Especialista.nome.asc(),
            Especialista.id.asc(),
        )
        .all()
    )

    if not especialistas:
        return ()

    vinculos = (
        db.query(EspecialistaServico)
        .filter(
            EspecialistaServico.empresa_id == empresa_id,
        )
        .all()
    )

    servicos_por_especialista: dict[int, list[int]] = {}

    for vinculo in vinculos:
        servicos_por_especialista.setdefault(
            vinculo.especialista_id,
            [],
        ).append(
            vinculo.servico_id,
        )

    resultado = []

    for especialista in especialistas:
        servicos_ids = tuple(
            sorted(
                set(
                    servicos_por_especialista.get(
                        especialista.id,
                        [],
                    )
                )
            )
        )

        resultado.append(
            EspecialistaContexto(
                id=especialista.id,
                nome=especialista.nome,
                servicos_ids=servicos_ids,
            )
        )

    return tuple(resultado)


def _carregar_canais(
    db: Session,
    empresa_id: int,
) -> tuple[CanalContexto, ...]:
    """
    Carrega apenas metadados necessários para o contexto.

    access_token propositalmente NÃO é exposto.
    """

    registros = (
        db.query(ConexaoCanal)
        .filter(
            ConexaoCanal.empresa_id == empresa_id,
            ConexaoCanal.ativo.is_(True),
        )
        .order_by(
            ConexaoCanal.canal.asc(),
            ConexaoCanal.id.asc(),
        )
        .all()
    )

    return tuple(
        CanalContexto(
            id=registro.id,
            provedor=registro.provedor,
            canal=registro.canal,
            ativo=_bool_seguro(
                registro.ativo,
                True,
            ),
            account_id=registro.account_id,
            page_id=registro.page_id,
            phone_number_id=registro.phone_number_id,
        )
        for registro in registros
    )


# ============================================================
# API PRINCIPAL
# ============================================================


def carregar_contexto_empresa(
    db: Session,
    empresa_id: int,
) -> ContextoEmpresa:
    """
    Carrega o contexto operacional de exatamente uma empresa.

    Todas as consultas dependentes são explicitamente filtradas
    pelo mesmo empresa_id recebido.

    Nenhuma informação pertencente a outro tenant é utilizada
    como fallback.
    """

    if not isinstance(empresa_id, int) or empresa_id <= 0:
        raise ValueError(
            "empresa_id deve ser um inteiro positivo."
        )

    empresa = (
        db.query(Empresa)
        .filter(
            Empresa.id == empresa_id,
        )
        .one_or_none()
    )

    if empresa is None:
        raise EmpresaNaoEncontradaErro(
            f"Empresa não encontrada: empresa_id={empresa_id}"
        )

    config = (
        db.query(AgenteConfig)
        .filter(
            AgenteConfig.empresa_id == empresa_id,
        )
        .one_or_none()
    )

    agente = _montar_configuracao_agente(
        empresa=empresa,
        config=config,
    )

    servicos = _carregar_servicos(
        db=db,
        empresa_id=empresa_id,
    )

    produtos = _carregar_produtos(
        db=db,
        empresa_id=empresa_id,
    )

    especialistas = _carregar_especialistas(
        db=db,
        empresa_id=empresa_id,
    )

    canais = _carregar_canais(
        db=db,
        empresa_id=empresa_id,
    )

    return ContextoEmpresa(
        empresa_id=empresa.id,
        nome_empresa=empresa.nome,
        slug=empresa.slug,
        tipo=empresa.tipo,
        parceiro_id=empresa.parceiro_id,
        nicho_empresa=empresa.nicho,
        status_empresa=empresa.status,
        agente=agente,
        servicos=servicos,
        produtos=produtos,
        especialistas=especialistas,
        canais=canais,
    )