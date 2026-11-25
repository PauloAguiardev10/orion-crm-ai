from uuid import uuid4
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.models.models import ConexaoCanal, Conversa, Empresa
from app.services.central_whatsapp_atendimento import atendentes_autorizados
from app.services.waha_gestao_transporte import ErroGestaoWaha


def plano_conexoes(db, empresa_id, *, bloquear=False):
    consulta = db.query(Empresa.plano).filter_by(id=empresa_id, status="ativa")
    if bloquear:
        consulta = consulta.with_for_update()
    empresa = consulta.one_or_none()
    if empresa is None:
        raise ErroGestaoWaha("empresa_nao_autorizada", 403)
    plano = (empresa.plano or "").strip().upper()
    return plano, _limite_configurado(db, plano, "conexoes")


def _limite_configurado(db, plano, recurso):
    return db.execute(text("SELECT orion_limite_plano(:plano, :recurso)"), {
        "plano": plano, "recurso": recurso,
    }).scalar_one()


def capacidade_usuarios(db, empresa_id, plano):
    contabilizados = db.execute(text("""
        SELECT COUNT(*) FROM usuarios WHERE empresa_id = :empresa
            AND lower(btrim(coalesce(nivel, ''))) <> 'orion_admin'
    """), {"empresa": empresa_id}).scalar_one()
    return {"usuarios_contabilizados": contabilizados,
            "limite_usuarios": _limite_configurado(db, plano, "usuarios")}


def _conexoes(db, empresa_id):
    return db.query(ConexaoCanal).filter_by(empresa_id=empresa_id, canal="whatsapp", provedor="waha")


def listar_conexoes(db, identidade):
    consulta = _conexoes(db, identidade["empresa_id"])
    if not identidade.get("empresa_propria", True):
        consulta = consulta.filter(ConexaoCanal.especialista_id.is_(None))
    return consulta.order_by(ConexaoCanal.id).all()


def obter_conexao(db, identidade, conexao_id, *, bloquear=False):
    consulta = _conexoes(db, identidade["empresa_id"]).filter_by(id=conexao_id)
    if not identidade.get("empresa_propria", True):
        consulta = consulta.filter(ConexaoCanal.especialista_id.is_(None))
    if bloquear:
        consulta = consulta.with_for_update()
    conexao = consulta.one_or_none()
    if conexao is None:
        raise ErroGestaoWaha("conexao_indisponivel", 404)
    return conexao


def _validar_titular(db, identidade, especialista_id):
    if especialista_id is not None and (
        not identidade.get("empresa_propria", True)
        or not any(item.id == especialista_id for item in atendentes_autorizados(db, identidade["empresa_id"]))
    ):
        raise ErroGestaoWaha("atendente_nao_autorizado", 403)


def cadastrar_conexao(db, identidade, dados):
    empresa_id = identidade["empresa_id"]
    _, limite = plano_conexoes(db, empresa_id, bloquear=True)
    if limite is None:
        raise ErroGestaoWaha("limite_plano_nao_configurado", 409)
    _validar_titular(db, identidade, dados["especialista_id"])
    conexao = ConexaoCanal(
        empresa_id=empresa_id, canal="whatsapp", provedor="waha", ativo=True,
        gerenciada_crm=True, operacao_suspensa=True,
        sessao_waha=f"orion-{empresa_id}-{uuid4().hex}", **dados,
    )
    db.add(conexao)
    try:
        db.flush()
    except IntegrityError as erro:
        if getattr(getattr(erro.orig, "diag", None), "constraint_name", None) == "orion_limite_conexoes":
            raise ErroGestaoWaha("limite_plano_atingido", 409) from None
        raise
    return conexao


def exigir_gerenciada(conexao):
    if (
        not conexao.ativo or not conexao.gerenciada_crm or not conexao.sessao_waha
        or not conexao.sessao_waha.startswith(f"orion-{conexao.empresa_id}-")
    ):
        raise ErroGestaoWaha("conexao_legada_protegida", 409)


def atualizar_conexao(db, identidade, conexao, dados):
    exigir_gerenciada(conexao)
    _validar_titular(db, identidade, dados["especialista_id"])
    if dados["especialista_id"] != conexao.especialista_id and db.query(Conversa.id).filter_by(
        empresa_id=conexao.empresa_id, conexao_canal_id=conexao.id,
    ).first():
        raise ErroGestaoWaha("vinculo_com_conversas_existentes", 409)
    for campo, valor in dados.items():
        setattr(conexao, campo, valor)
