import json
import os
import random
import time
import threading
import traceback
import unicodedata
from urllib.parse import quote

import requests
from fastapi import Depends, FastAPI, HTTPException, Request
from pydantic import BaseModel, Field, PrivateAttr
from sqlalchemy.orm import Session

from app.agents.sdr_agent import (
    conduzir_conversa,
    gerar_resumo_vendedor,
    obter_especialista_responsavel,
)
from app.database.database import SessionLocal, engine
from app.services.empresa_context_service import carregar_contexto_empresa
from app.services.waha_destino import (
    PREFIXO, ConfiguracaoWahaInvalida, alias_waha, resolver_waha,
)
from app.services.waha_health_service import consultar_saude_sessao
from app.models.models import (
    Base,
    Cliente,
    ConexaoCanal,
    Conversa,
    Lead,
)


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Agente SDR Forway")

from app.routes.followup_vendedor_api import router as followup_vendedor_router
app.include_router(followup_vendedor_router)

from app.routes.central_whatsapp_api import router as central_whatsapp_router
app.include_router(central_whatsapp_router)


@app.get("/status/waha")
def status_waha():
    resultado = consultar_saude_sessao("default")

    return {
        "status": resultado.status,
        "conectado": resultado.saudavel,
        "requer_intervencao": resultado.requer_intervencao,
        "engine_state": resultado.engine_state,
    }


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
TELEFONES_LID_CACHE: dict[tuple[int, str, str], str] = {}

MENSAGENS_WAHA_PROCESSADAS: dict[tuple[int, str, str], float] = {}
LOCK_MENSAGENS_WAHA = threading.RLock()
TTL_MENSAGEM_WAHA_SEGUNDOS = 10 * 60


def limpar_cache_mensagens_waha() -> None:
    with LOCK_MENSAGENS_WAHA:
        agora = time.monotonic()
        expiradas = [
            mensagem_id
            for mensagem_id, instante in MENSAGENS_WAHA_PROCESSADAS.items()
            if agora - instante > TTL_MENSAGEM_WAHA_SEGUNDOS
        ]

        for mensagem_id in expiradas:
            MENSAGENS_WAHA_PROCESSADAS.pop(mensagem_id, None)


def obter_id_mensagem_waha(mensagem: dict) -> str | None:
    from app.services.followup_ids_waha import extrair_id_resposta_waha
    return extrair_id_resposta_waha(mensagem)


def mensagem_waha_ja_processada(
    mensagem_id: str | None,
    empresa_id: int,
    sessao: str = "",
) -> bool:
    if not mensagem_id:
        return False

    chave_cache = (empresa_id, sessao, mensagem_id)

    with LOCK_MENSAGENS_WAHA:
        limpar_cache_mensagens_waha()

        if chave_cache in MENSAGENS_WAHA_PROCESSADAS:
            return True

        MENSAGENS_WAHA_PROCESSADAS[chave_cache] = time.monotonic()
        return False


def liberar_mensagem_waha(
    mensagem_id: str | None,
    empresa_id: int,
    sessao: str = "",
) -> None:
    if mensagem_id:
        chave_cache = (empresa_id, sessao, mensagem_id)

        with LOCK_MENSAGENS_WAHA:
            MENSAGENS_WAHA_PROCESSADAS.pop(chave_cache, None)


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
    _conexao_waha_id: int | None = PrivateAttr(default=None)
    empresa_id: int = Field(default=1, ge=1)
    nome: str | None = None
    telefone: str | None = None
    canal: str
    identificador: str
    mensagem: str
    mensagem_id_externo: str | None = None
    referencia_anuncio: dict | None = None


from app.agents.detector_atendimento_humano import detectar_pedido_atendimento_humano


def obter_empresa_id_por_sessao(sessao: str) -> int | None:
    return SESSAO_EMPRESA.get(sessao)


def obter_sessao_waha(payload: dict, mensagem: dict) -> str:
    dados = mensagem.get("_data")
    sessao = (
        payload.get("session")
        or mensagem.get("session")
        or (dados.get("session") if isinstance(dados, dict) else None)
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




def montar_alerta_atendimento_humano(conversa, nome_empresa):
    """
    Monta o alerta interno quando o cliente solicita
    atendimento humano antes de concluir a qualificacao.
    """
    def campo(valor, padrao="Nao informado"):
        valor = str(valor).strip() if valor is not None else ""
        return valor or padrao

    return (
        f"Solicitacao de atendimento humano - {nome_empresa}\n\n"
        f"Nome: {campo(conversa.nome)}\n"
        f"Empresa: {campo(conversa.empresa, 'Nao informada')}\n"
        f"Segmento: {campo(conversa.segmento)}\n"
        f"Canal: {campo(conversa.canal)}\n"
        f"Contato: {campo(conversa.telefone)}\n\n"
        "Motivo: Cliente solicitou atendimento humano.\n"
        "Proxima acao: Assumir a conversa no CRM."
    )




def montar_alerta_lead_comercial(conversa, analise, nome_empresa):
    """Monta notificacao comercial com contato validado."""
    import re

    contato = str(conversa.telefone or "").strip()
    numero = re.sub(r"\D", "", contato)

    link = ""
    if (
        contato
        and "@" not in contato
        and numero == contato.lstrip("+")
        and 10 <= len(numero) <= 15
    ):
        link = f"Abrir conversa: https://wa.me/{numero}\n"

    def campo(valor, padrao="Nao informado"):
        return str(valor).strip() if valor else padrao

    return (
        f"Nova lead qualificada - {nome_empresa}\n\n"
        f"Nome: {campo(conversa.nome)}\n"
        f"Empresa: {campo(conversa.empresa, 'Nao informada')}\n"
        f"Segmento: {campo(conversa.segmento)}\n"
        f"WhatsApp: {campo(conversa.telefone)}\n"
        f"{link}"
        f"Servi\u00e7o: {campo(conversa.servico, 'Nao identificado')}\n"
        f"Temperatura: {analise['temperatura'].capitalize()}\n"
        f"Prioridade: {analise['prioridade'].capitalize()}\n"
        f"Score: {analise['score']}\n\n"
        "Lead aguardando atendimento no CRM."
    )



def obter_destinatario_notificacao(db, empresa_id):
    """
    Retorna o destinatario interno da empresa.
    Preserva o LID existente da Forway e isola tenants.
    """
    if empresa_id == 1:
        lid_forway = obter_lid_luciano()
        if lid_forway:
            return lid_forway

    from app.models.models import EmpresaAtendimentoConfig

    config = (
        db.query(EmpresaAtendimentoConfig)
        .filter(
            EmpresaAtendimentoConfig.empresa_id == empresa_id
        )
        .one_or_none()
    )

    if config is None or not config.whatsapp_notificacao:
        return None

    return obter_chat_id_whatsapp(
        config.whatsapp_notificacao
    )



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
    if (
        type(empresa_id) is not int
        or empresa_id < 1
        or not isinstance(sessao, str)
        or not sessao.strip()
    ):
        return None

    if not chat_id:
        return None

    if chat_id.endswith("@c.us"):
        return normalizar_telefone_crm(chat_id)

    if not chat_id.endswith("@lid"):
        return normalizar_telefone_crm(chat_id)

    chave_cache = (empresa_id, str(sessao), chat_id)
    telefone_cache = TELEFONES_LID_CACHE.get(chave_cache)
    if telefone_cache:
        return telefone_cache

    try:
        rota = resolver_waha(sessao)
    except ConfiguracaoWahaInvalida:
        return None
    headers = rota.headers
    sessao_url = quote(rota.sessao, safe="")
    lid_numero = chat_id.replace("@lid", "").strip()
    lid_url = quote(lid_numero, safe="")

    try:
        resposta = requests.get(
            f"{rota.origem}/api/{sessao_url}/lids/{lid_url}",
            headers=headers,
            timeout=4, allow_redirects=False,
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
                TELEFONES_LID_CACHE[chave_cache] = telefone_real
                return telefone_real
    except (requests.RequestException, ValueError, TypeError) as erro:
        print("[WAHA LID] falha na resolução direta:", repr(erro), flush=True)

    try:
        resposta = requests.get(
            f"{rota.origem}/api/contacts",
            headers=headers,
            params={"contactId": chat_id, "session": rota.sessao},
            timeout=4, allow_redirects=False,
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
                    TELEFONES_LID_CACHE[chave_cache] = telefone_real
                    return telefone_real
    except (requests.RequestException, ValueError, TypeError) as erro:
        print("[WAHA CONTATO] falha na consulta individual:", repr(erro), flush=True)

    telefone_banco = buscar_telefone_real_no_banco(chat_id, empresa_id)
    if telefone_banco:
        TELEFONES_LID_CACHE[chave_cache] = telefone_banco
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

        conversas = db.query(Conversa).filter(
            Conversa.empresa_id == dados.empresa_id,
            Conversa.identificador == dados.identificador,
        )
        sofia_habilitada = True
        if dados._conexao_waha_id is not None:
            from app.services.followup_vinculo_conversa_waha import localizar_conversa_entrada_waha

            conexao = db.query(ConexaoCanal).filter_by(
                id=dados._conexao_waha_id, empresa_id=dados.empresa_id,
                canal="whatsapp", provedor="waha", ativo=True,
            ).with_for_update().one_or_none()
            if conexao is None:
                return {"erro": "conexao_indisponivel"}
            sofia_habilitada = conexao.sofia_ativa and not conexao.operacao_suspensa
            conversa = localizar_conversa_entrada_waha(
                db, empresa_id=dados.empresa_id, conexao_id=conexao.id, chat_id=dados.identificador,
            )
        else:
            conversa = conversas.order_by(Conversa.id.desc()).first()

        if not conversa:
            conversa = Conversa(
                empresa_id=dados.empresa_id,
                identificador=dados.identificador,
                canal=dados.canal,
                conexao_canal_id=dados._conexao_waha_id,
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

        elif dados._conexao_waha_id is not None:
            db.commit()

        # Follow-up: registra referencia publicitaria preliminar.
        # Referencia recebida nao equivale a campanha comprovada.
        if dados.referencia_anuncio:
            from datetime import datetime, timezone
            from app.services.followup_origem_anuncio import (
                analisar_referencia_anuncio,
            )

            analise_referral = analisar_referencia_anuncio(
                dados.referencia_anuncio
            )

            if (
                analise_referral["referencia_valida"]
                and not conversa.anuncio_referral_id
            ):
                conversa.anuncio_referral_id = (
                    analise_referral["anuncio_id"]
                )
                conversa.anuncio_referral_recebido_em = (
                    datetime.now(timezone.utc)
                )
                # Nunca confirmar campanha apenas com metadados.
                conversa.anuncio_referral_confirmado = False
                db.commit()

        # Se o especialista já assumiu esta conversa no CRM,
        # a Sofia permanece em silêncio e não executa o fluxo da IA.

        from app.services.mensagem_service import (
            persistir_mensagem_segura,
        )

        resultado_persistencia, mensagem_interna_id = persistir_mensagem_segura(
            empresa_id=dados.empresa_id,
            conversa_id=conversa.id,
            cliente_id=conversa.cliente_id,
            remetente="cliente",
            texto=dados.mensagem,
            from_me=False,
            mensagem_id_externo=dados.mensagem_id_externo,
            retornar_id=True,
        )

        if resultado_persistencia == "erro":
            raise RuntimeError(
                "Falha ao registrar mensagem recebida no CRM."
            )

        if resultado_persistencia == "criada":
            from app.services.mensagem_service import (
                assumir_processamento_mensagem,
            )

            reservado = assumir_processamento_mensagem(
                db,
                empresa_id=dados.empresa_id,
                conversa_id=conversa.id,
                mensagem_id=mensagem_interna_id,
            )

            if not reservado:
                raise RuntimeError(
                    "Nao foi possivel reservar a mensagem."
                )

            db.commit()


        if (
            dados.mensagem_id_externo
            and resultado_persistencia == "duplicada"
        ):
            from app.services.mensagem_service import (
                consultar_estado_mensagem,
            )
            from app.models.models import Mensagem

            estado_mensagem = consultar_estado_mensagem(
                db,
                empresa_id=dados.empresa_id,
                conversa_id=conversa.id,
                mensagem_id_externo=dados.mensagem_id_externo,
            )

            mensagem_cliente = (
                db.query(Mensagem)
                .filter(
                    Mensagem.id == mensagem_interna_id,
                    Mensagem.empresa_id == dados.empresa_id,
                    Mensagem.conversa_id == conversa.id,
                    Mensagem.mensagem_id_externo
                    == dados.mensagem_id_externo,
                    Mensagem.from_me.is_(False),
                    Mensagem.remetente == "cliente",
                )
                .first()
            )

            if mensagem_cliente is not None:
                from app.services.followup_processamento_service import (
                    processar_resposta_cliente_followup,
                )

                processar_resposta_cliente_followup(db, mensagem=mensagem_cliente)

                db.commit()

            return {
                "conversa_id": conversa.id,
                "cliente_id": conversa.cliente_id,
                "empresa_id": dados.empresa_id,
                "resposta_agente": None,
                "nova_lead": False,
                "alerta_atendimento_humano": False,
                "notificacao_luciano": None,
                "status": "mensagem_duplicada",
                "estado_processamento": estado_mensagem,
            }

        entrada_lead_followup_em = None
        if sofia_habilitada and conversa.humano_assumiu is not True:
            contexto_empresa = carregar_contexto_empresa(db, conversa.empresa_id)
            etapa_anterior = conversa.etapa
            resposta, analise = conduzir_conversa(
                conversa,
                dados.mensagem,
                contexto_empresa=contexto_empresa,
            )

            # A Sofia pode ter preparado a resposta durante uma tomada humana.
            # Revalida antes de gravar a etapa, o status e o histórico da IA.
            with db.no_autoflush:
                humano_assumiu = (
                    db.query(Conversa.humano_assumiu)
                    .filter(Conversa.id == conversa.id, Conversa.empresa_id == dados.empresa_id)
                    .with_for_update()
                    .scalar()
                )
                if humano_assumiu is True:
                    db.refresh(conversa)

        if conversa.humano_assumiu is True or not sofia_habilitada:
            from app.services.mensagem_service import (
                concluir_processamento_mensagem,
            )

            if not sofia_habilitada:
                conversa = db.query(Conversa).filter_by(
                    id=conversa.id, empresa_id=dados.empresa_id,
                ).with_for_update().populate_existing().one()
                if conversa.humano_assumiu is not True and conversa.status_atendimento != "finalizado":
                    conversa.status_atendimento = "aguardando_humano"

            concluido = concluir_processamento_mensagem(
                db,
                empresa_id=dados.empresa_id,
                conversa_id=conversa.id,
                mensagem_id=mensagem_interna_id,
            )

            if not concluido:
                raise RuntimeError(
                    "Falha ao concluir mensagem em atendimento humano."
                )

            db.commit()

            return {
                "conversa_id": conversa.id,
                "cliente_id": conversa.cliente_id,
                "empresa_id": dados.empresa_id,
                "canal": conversa.canal,
                "etapa_atual": conversa.etapa,
                "resposta_agente": None,
                "produto_identificado": conversa.servico,
                "temperatura": None,
                "prioridade": None,
                "score": None,
                "status": (
                    "finalizado" if conversa.status_atendimento == "finalizado"
                    else "em_atendimento_humano" if conversa.humano_assumiu is True
                    else "aguardando_humano"
                ),
                "resumo_vendedor": None,
                "lead_id": None,
                "humano_assumiu": conversa.humano_assumiu is True,
            }

        # ENCERRAMENTO POS-ENCAMINHAMENTO
        # Mensagens posteriores ao encaminhamento nao devem
        # reprocessar leads nem disparar notificacoes comerciais.
        if etapa_anterior == "aguardando_humano":
            from app.services.mensagem_service import (
                concluir_processamento_mensagem,
            )

            concluido = concluir_processamento_mensagem(
                db,
                empresa_id=dados.empresa_id,
                conversa_id=conversa.id,
                mensagem_id=mensagem_interna_id,
            )

            if not concluido:
                raise RuntimeError(
                    "Falha ao concluir mensagem apos encaminhamento."
                )

            db.commit()

            return {
                "conversa_id": conversa.id,
                "cliente_id": conversa.cliente_id,
                "empresa_id": dados.empresa_id,
                "canal": conversa.canal,
                "etapa_atual": conversa.etapa,
                "resposta_agente": resposta,
                "produto_identificado": conversa.servico,
                "temperatura": analise["temperatura"],
                "prioridade": analise["prioridade"],
                "score": analise["score"],
                "status": "encaminhado",
                "resumo_vendedor": None,
                "lead_id": None,
                "nova_lead": False,
                "notificacao_luciano": None,
                "alerta_atendimento_humano": False,
            }

        primeiro_encaminhamento_humano = (
            etapa_anterior != 'aguardando_humano'
            and conversa.etapa == 'aguardando_humano'
        )

        pedido_humano_explicito = (
            primeiro_encaminhamento_humano
            and detectar_pedido_atendimento_humano(dados.mensagem)
        )
        

        db.commit()

        resumo = None
        lead_id = None
        nova_lead = False
        notificacao_luciano = None

        if pedido_humano_explicito:
            notificacao_luciano = montar_alerta_atendimento_humano(
                conversa,
                contexto_empresa.nome_empresa,
            )

        # Registra no CRM contatos comerciais que ainda não concluíram
        # a qualificação. A lead provisória não dispara notificação
        # e será enriquecida quando a Sofia concluir o atendimento.
        lead_provisoria = (
            db.query(Lead)
            .filter(
                Lead.empresa_id == dados.empresa_id,
                Lead.conversa_id == conversa.id,
            )
            .order_by(Lead.id.desc())
            .first()
        )

        texto_inicial_normalizado = (
            unicodedata.normalize(
                "NFKD",
                (dados.mensagem or "").strip().lower(),
            )
            .encode("ascii", "ignore")
            .decode("ascii")
        )

        identificador_valido = (
            bool(dados.identificador)
            and dados.identificador != "0@c.us"
            and (
                dados.identificador.endswith("@c.us")
                or dados.identificador.endswith("@lid")
            )
        )

        sinais_interesse_comercial = [
            "mais informacoes",
            "saber mais",
            "gostaria de saber",
            "tenho interesse",
            "quero contratar",
            "quero saber",
            "sobre os servicos",
            "sobre isso",
            "trafego pago",
            "social media",
            "design",
            "web design",
            "automacao",
            "estrutura completa",
            "treinamento comercial",
        ]

        tem_interesse_comercial = any(
            sinal in texto_inicial_normalizado
            for sinal in sinais_interesse_comercial
        )

        mensagem_comercial_valida = (
            identificador_valido
            and bool(conversa.telefone)
            and 1 <= len(texto_inicial_normalizado) <= 1000
            and "codigo de confirmacao do facebook"
                not in texto_inicial_normalizado
            and not texto_inicial_normalizado.startswith("/9j/")
        )

        if (
            lead_provisoria is None
            and conversa.etapa not in [
                "encaminhar",
                "aguardando_humano",
            ]
            and mensagem_comercial_valida
        ):
            origem_aquisicao = (
                conversa.origem_aquisicao
                or conversa.canal
            )

            cliente_provisorio = Cliente(
                empresa_id=dados.empresa_id,
                nome=conversa.nome,
                empresa=conversa.empresa,
                empresa_cliente=conversa.empresa,
                segmento=conversa.segmento,
                telefone=conversa.telefone,
                canal=conversa.canal,
                canal_origem=origem_aquisicao,
            )

            db.add(cliente_provisorio)
            db.flush()

            conversa.cliente_id = cliente_provisorio.id

            lead_provisoria = Lead(
                empresa_id=dados.empresa_id,
                cliente_id=cliente_provisorio.id,
                conversa_id=conversa.id,
                especialista_id=None,
                responsavel="Não atribuído",
                produto=conversa.servico,
                temperatura="fria",
                prioridade="baixa",
                score=0,
                origem=origem_aquisicao,
                observacoes=conversa.objetivo,
                resumo_vendedor=None,
                status="Em atendimento",
                entrada_followup_em=None,
            )

            db.add(lead_provisoria)
            db.commit()
            db.refresh(lead_provisoria)

            lead_id = lead_provisoria.id

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
                        Lead.status.in_(("Aguardando resposta", "Em atendimento")),
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

                especialista_responsavel = obter_especialista_responsavel(
                    contexto_empresa,
                    nome_servico=conversa.servico,
                )

                resumo = gerar_resumo_vendedor(
                    conversa,
                    analise,
                    contexto_empresa=contexto_empresa,
                )

                lead = Lead(
                    empresa_id=dados.empresa_id,
                    cliente_id=cliente.id,
                    conversa_id=conversa.id,
                    especialista_id=(
                        especialista_responsavel.id
                        if especialista_responsavel is not None
                        else None
                    ),
                    responsavel=(
                        especialista_responsavel.nome
                        if especialista_responsavel is not None
                        else "Não atribuído"
                    ),
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

                if not pedido_humano_explicito:
                    notificacao_luciano = montar_alerta_lead_comercial(
                        conversa,
                        analise,
                        contexto_empresa.nome_empresa,
                    )

            else:
                era_lead_provisoria = (
                    not lead_existente.resumo_vendedor
                    and lead_existente.status in (
                        "Aguardando atendimento",
                        "Aguardando resposta",
                        "Em atendimento",
                        "Em qualificação",
                    )
                )

                if not era_lead_provisoria:
                    resumo = lead_existente.resumo_vendedor
                    lead_id = lead_existente.id

                    if (
                        not conversa.cliente_id
                        and lead_existente.cliente_id
                    ):
                        conversa.cliente_id = lead_existente.cliente_id
                        db.commit()

                else:
                    cliente_existente = None
                    if lead_existente.cliente_id:
                        cliente_existente = (
                            db.query(Cliente)
                            .filter(
                                Cliente.id == lead_existente.cliente_id,
                                Cliente.empresa_id == dados.empresa_id,
                            )
                            .first()
                        )

                    origem_aquisicao = (
                        conversa.origem_aquisicao
                        or conversa.canal
                    )

                    if cliente_existente:
                        cliente_existente.nome = conversa.nome
                        cliente_existente.empresa = conversa.empresa
                        cliente_existente.empresa_cliente = conversa.empresa
                        cliente_existente.segmento = conversa.segmento
                        cliente_existente.telefone = conversa.telefone
                        cliente_existente.canal = conversa.canal
                        cliente_existente.canal_origem = origem_aquisicao

                    if not conversa.cliente_id:
                        conversa.cliente_id = lead_existente.cliente_id

                    especialista_responsavel = (
                        obter_especialista_responsavel(
                            contexto_empresa,
                            nome_servico=conversa.servico,
                        )
                    )

                    resumo = gerar_resumo_vendedor(
                        conversa,
                        analise,
                        contexto_empresa=contexto_empresa,
                    )

                    lead_existente.especialista_id = (
                        especialista_responsavel.id
                        if especialista_responsavel is not None
                        else None
                    )
                    lead_existente.responsavel = (
                        especialista_responsavel.nome
                        if especialista_responsavel is not None
                        else "Não atribuído"
                    )
                    lead_existente.produto = conversa.servico
                    lead_existente.temperatura = analise["temperatura"]
                    lead_existente.prioridade = analise["prioridade"]
                    lead_existente.score = analise["score"]
                    lead_existente.origem = origem_aquisicao
                    lead_existente.observacoes = conversa.objetivo
                    lead_existente.resumo_vendedor = resumo
                    lead_existente.status = "Aguardando atendimento"

                    db.commit()
                    db.refresh(lead_existente)

                    lead_id = lead_existente.id
                    nova_lead = True

                    if not pedido_humano_explicito:
                        notificacao_luciano = montar_alerta_lead_comercial(
                            conversa,
                            analise,
                            contexto_empresa.nome_empresa,
                        )

        from app.services.mensagem_service import (
            concluir_processamento_mensagem,
        )

        concluido = concluir_processamento_mensagem(
            db,
            empresa_id=dados.empresa_id,
            conversa_id=conversa.id,
            mensagem_id=mensagem_interna_id,
        )

        if not concluido:
            raise RuntimeError(
                "Falha ao concluir processamento da mensagem."
            )

        db.commit()

        if lead_id and entrada_lead_followup_em is None:
            lead_para_followup = (
                db.query(Lead)
                .filter(
                    Lead.id == lead_id,
                    Lead.empresa_id == dados.empresa_id,
                )
                .first()
            )

            if lead_para_followup is not None:
                entrada_lead_followup_em = (
                    lead_para_followup.entrada_followup_em
                )

        return {
            "conversa_id": conversa.id,
            "cliente_id": conversa.cliente_id,
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
            "entrada_lead_followup_em": entrada_lead_followup_em,
            "nova_lead": nova_lead,
            "notificacao_luciano": notificacao_luciano,
            "alerta_atendimento_humano": pedido_humano_explicito,
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
    try:
        rota = resolver_waha(sessao)
    except ConfiguracaoWahaInvalida:
        return False
    headers = rota.headers
    presenca = "typing" if digitando else "paused"

    try:
        resposta = requests.post(
            f"{rota.origem}/api/{quote(rota.sessao, safe='')}/presence",
            headers=headers,
            json={"chatId": chat_id, "presence": presenca},
            timeout=5, allow_redirects=False,
        )
        resposta.raise_for_status()
        return True
    except requests.RequestException as erro:
        print(f"[WAHA PRESENCE] falha em {presenca}: {repr(erro)}", flush=True)

    endpoint = "startTyping" if digitando else "stopTyping"

    try:
        resposta = requests.post(
            f"{rota.origem}/api/{endpoint}",
            headers=headers,
            json={"session": rota.sessao, "chatId": chat_id},
            timeout=5, allow_redirects=False,
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
) -> tuple[bool, str | None, str | None]:
    try:
        rota = resolver_waha(sessao)
        envio = requests.post(
            f"{rota.origem}/api/sendText",
            headers=rota.headers,
            json={"session": rota.sessao, "chatId": chat_id, "text": texto},
            timeout=15, allow_redirects=False,
        )
        if 300 <= envio.status_code < 400:
            return False, "timeout_envio_inconclusivo", None
        envio.raise_for_status()

        from app.services.followup_ids_waha import (
            extrair_id_resposta_waha,
        )

        try:
            dados_resposta = envio.json()
        except ValueError:
            dados_resposta = None

        id_waha = extrair_id_resposta_waha(dados_resposta)

        return True, None, id_waha

    except requests.exceptions.ReadTimeout as erro:
        print(
            "[WAHA SEND] timeout; envio pode ter sido concluído. "
            f"Sem reenvio automático. Erro: {repr(erro)}",
            flush=True,
        )
        return False, "timeout_envio_inconclusivo", None

    except (requests.RequestException, ConfiguracaoWahaInvalida) as erro:
        print(f"[WAHA SEND] falha no envio: {repr(erro)}", flush=True)
        return False, "falha_envio", None


@app.post("/webhook/waha/{instancia}")
async def webhook_waha_instancia(instancia: str, request: Request, payload: dict):
    from starlette.concurrency import run_in_threadpool
    from app.services.followup_eventos_waha import assinatura_waha_valida

    try:
        sessao = alias_waha(instancia, payload.get("session"))
        rota = resolver_waha(sessao)
    except ConfiguracaoWahaInvalida:
        raise HTTPException(401, "Origem WAHA invalida") from None
    if (
        request.headers.get("X-Webhook-Hmac-Algorithm") != "sha512"
        or not assinatura_waha_valida(
            await request.body(), rota.chave_hmac, request.headers.get("X-Webhook-Hmac", ""),
        )
    ):
        raise HTTPException(401, "Assinatura WAHA invalida")
    return await run_in_threadpool(
        processar_webhook_waha, {**payload, "session": sessao}, True,
    )


async def autenticar_webhook_waha(request: Request) -> bool:
    from app.services.followup_eventos_waha import assinatura_waha_valida

    chave = os.getenv("WAHA_WEBHOOK_HMAC_KEY")
    if not chave:
        return False
    if (
        request.headers.get("X-Webhook-Hmac-Algorithm") != "sha512"
        or not assinatura_waha_valida(
            await request.body(), chave, request.headers.get("X-Webhook-Hmac", ""),
        )
    ):
        raise HTTPException(status_code=401, detail="Assinatura WAHA inválida")
    return True


@app.post("/webhook/waha")
def webhook_waha(payload: dict, autenticado: bool = Depends(autenticar_webhook_waha)):
    mensagem = payload.get("payload")
    sessao = obter_sessao_waha(payload, mensagem if isinstance(mensagem, dict) else {})
    if sessao.strip().startswith(PREFIXO):
        raise HTTPException(401, "Origem WAHA invalida")
    return processar_webhook_waha(payload, autenticado)


def processar_webhook_waha(payload: dict, autenticado: bool):
    evento = payload.get("event")
    if evento == "message.ack":
        if autenticado is not True:
            return {"status": "ignorado", "motivo": "ack_sem_assinatura"}
        from app.services.central_whatsapp_ack import registrar_ack_waha

        with SessionLocal() as db_ack, db_ack.begin():
            motivo = registrar_ack_waha(db_ack, payload)
        return {"status": "processado" if motivo in ("ack_registrado", "ack_pendente") else "ignorado",
                "motivo": motivo}
    if evento not in ("message", "message.any", "message.reaction"):
        return {"status": "ignorado", "motivo": "evento_diferente_de_message"}

    mensagem = payload.get("payload")
    if not isinstance(mensagem, dict):
        return {"status": "ignorado", "motivo": "payload_invalido"}

    mensagem_id = obter_id_mensagem_waha(mensagem)
    dados_internos = mensagem.get("_data")
    if not isinstance(dados_internos, dict):
        dados_internos = {}

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

    if evento == "message.reaction" and mensagem.get("fromMe") is not False:
        return {"status": "ignorado", "motivo": "evento_sem_resposta_do_cliente"}

    if mensagem.get("fromMe") is True:
        from app.services.followup_eventos_waha import identificar_saida_waha
        from app.services.followup_conexoes_waha import localizar_conexao_waha
        from app.services.followup_origem_saida_waha import (
            proteger_followup_de_saida_manual,
            verificar_saida_automatica_registrada,
        )

        dados_saida, motivo_saida = identificar_saida_waha(payload)

        if dados_saida is None:
            return {"status": "ignorado", "motivo": motivo_saida}

        db_saida = SessionLocal()

        try:
            conexao, motivo_conexao = localizar_conexao_waha(
                db_saida,
                dados_saida["sessao"],
            )

            if conexao is None:
                return {"status": "ignorado", "motivo": motivo_conexao}

            automatica, motivo_origem = verificar_saida_automatica_registrada(
                db_saida,
                conexao.empresa_id,
                dados_saida["sessao"],
                mensagem_id,
            )

            if automatica:
                return {
                    "status": "ignorado",
                    "motivo": "saida_automatica_registrada",
                }

            if (
                autenticado is True and evento == "message.any"
                and mensagem.get("source") == "app"
                and mensagem_id and len(mensagem_id) <= 180
                and proteger_followup_de_saida_manual(
                    db_saida, conexao=conexao,
                    destinatario=dados_saida["destinatario"], mensagem_id=mensagem_id,
                )
            ):
                db_saida.commit()
                return {"status": "processado", "motivo": "followup_bloqueado_saida_manual"}

            return {
                "status": "ignorado",
                "motivo": "saida_sem_origem_comprovada",
                "detalhe": motivo_origem,
            }

        finally:
            db_saida.close()

    if evento != "message" and mensagem.get("fromMe") is not False:
        return {"status": "ignorado", "motivo": "evento_sem_resposta_do_cliente"}

    texto = mensagem.get("body") if evento != "message.reaction" else None
    chat_id = mensagem.get("from")
    nome = dados_internos.get("notifyName")

    if chat_id == "status@broadcast":
        return {
            "status": "ignorado",
            "motivo": "status_broadcast",
        }

    sessao = obter_sessao_waha(
        payload,
        mensagem,
    )

    empresa_id = None if sessao.startswith(PREFIXO) else obter_empresa_id_por_sessao(sessao)
    if empresa_id is None and autenticado is True:
        from app.services.followup_conexoes_waha import localizar_conexao_waha

        with SessionLocal() as db_sessao:
            cadastrada, _ = localizar_conexao_waha(db_sessao, sessao)
            if cadastrada is not None and cadastrada.gerenciada_crm:
                empresa_id = cadastrada.empresa_id

    if empresa_id is None:
        return {
            "status": "ignorado",
            "motivo": "sessao_sem_empresa_vinculada",
            "sessao": sessao,
        }

    if autenticado is True:
        from app.services.followup_entrada_conexao_waha import (
            validar_conexao_entrada_waha,
        )

        with SessionLocal() as db_entrada:
            conexao_id, motivo = validar_conexao_entrada_waha(db_entrada, sessao, empresa_id)
        if conexao_id is None:
            return {"status": "ignorado", "motivo": motivo}

    if not isinstance(chat_id, str) or not chat_id.strip():
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

    from app.services.central_whatsapp_midia import midia_ativa

    if (
        midia_ativa() and autenticado is True and evento in ("message", "message.any")
        and mensagem.get("hasMedia") is True and mensagem.get("fromMe") is False
        and isinstance(mensagem_id, str) and 0 < len(mensagem_id) <= 180
        and chat_id.endswith(("@c.us", "@lid")) and chat_id.split("@", 1)[0].isdigit()
    ):
        from app.services.central_whatsapp_midia_entrada import registrar_midia_recebida

        with SessionLocal() as db_midia:
            situacao = registrar_midia_recebida(
                db_midia, empresa_id=empresa_id, conexao_id=conexao_id, sessao=sessao,
                chat_id=chat_id, mensagem_id=mensagem_id, payload=mensagem,
            )
        return {"status": "processado", "motivo": situacao}

    if not isinstance(texto, str) or not texto.strip():
        from app.services.followup_eventos_waha import identificar_resposta_sem_texto

        tipo_resposta = identificar_resposta_sem_texto(evento, mensagem)
        if tipo_resposta and mensagem_id and chat_id.endswith(("@c.us", "@lid")):
            from app.services.followup_entrada_conexao_waha import validar_conexao_entrada_waha
            from app.services.mensagem_service import registrar_mensagem

            with SessionLocal() as db_resposta:
                conexao_id, _ = validar_conexao_entrada_waha(
                    db_resposta, sessao, empresa_id,
                )
                if conexao_id is not None:
                    conversa = (
                        db_resposta.query(Conversa)
                        .join(
                            Lead,
                            (Lead.conversa_id == Conversa.id)
                            & (Lead.empresa_id == Conversa.empresa_id),
                        )
                        .filter(
                            Conversa.empresa_id == empresa_id,
                            Conversa.conexao_canal_id == conexao_id,
                            Conversa.canal == "whatsapp",
                            Conversa.identificador == chat_id,
                            Lead.status.in_(("Em atendimento", "Aguardando resposta")),
                        )
                        .order_by(Conversa.id.desc())
                        .first()
                    )
                    if conversa is not None:
                        registro, criada = registrar_mensagem(
                            db_resposta,
                            empresa_id=empresa_id,
                            conversa_id=conversa.id,
                            cliente_id=conversa.cliente_id,
                            remetente="cliente",
                            texto="",
                            from_me=False,
                            mensagem_id_externo=mensagem_id,
                        )
                        if criada:
                            registro.tipo = tipo_resposta
                        db_resposta.commit()
                        return {"status": "processado", "motivo": "resposta_sem_texto"}
        return {"status": "ignorado", "motivo": "sem_texto_ou_chat_id"}

    if mensagem_waha_ja_processada(mensagem_id, empresa_id, sessao):
        if mensagem_id:
            from app.models.models import Mensagem
            from app.services.followup_processamento_service import (
                processar_resposta_cliente_followup,
            )

            db_recuperacao = SessionLocal()
            try:
                mensagem_cliente = (
                    db_recuperacao.query(Mensagem)
                    .join(
                        Conversa,
                        Conversa.id == Mensagem.conversa_id,
                    )
                    .filter(
                        Mensagem.empresa_id == empresa_id,
                        Conversa.empresa_id == empresa_id,
                        Conversa.identificador == chat_id,
                        Mensagem.mensagem_id_externo == mensagem_id,
                        Mensagem.from_me.is_(False),
                        Mensagem.remetente == "cliente",
                        *(
                            (Conversa.conexao_canal_id == conexao_id,)
                            if autenticado is True else ()
                        ),
                    )
                    .order_by(Mensagem.id.desc())
                    .first()
                )

                if mensagem_cliente is not None:
                    processar_resposta_cliente_followup(
                        db_recuperacao, mensagem=mensagem_cliente,
                    )

                    db_recuperacao.commit()

            except Exception:
                db_recuperacao.rollback()
                traceback.print_exc()
                return {
                    "status": "erro",
                    "motivo": "falha_recuperacao_duplicada",
                    "empresa_id": empresa_id,
                    "message_id": mensagem_id,
                }
            finally:
                db_recuperacao.close()

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

    # Metadados de anuncio, quando fornecidos pelo WAHA.
    # Ainda nao representam campanha comprovada.
    referencia_anuncio = None
    if isinstance(dados_internos, dict):
        referencia_anuncio = dados_internos.get("referral")
    if referencia_anuncio is None:
        referencia_anuncio = mensagem.get("referral")
    if not isinstance(referencia_anuncio, dict):
        referencia_anuncio = None

    dados = MensagemRequest(
        empresa_id=empresa_id,
        nome=nome,
        telefone=telefone_real,
        canal="whatsapp",
        identificador=chat_id,
        mensagem=texto,
        mensagem_id_externo=mensagem_id,
        referencia_anuncio=referencia_anuncio,
    )
    if autenticado is True:
        dados._conexao_waha_id = conexao_id

    resultado = receber_mensagem(dados)

    if resultado.get("erro"):
        liberar_mensagem_waha(mensagem_id, empresa_id, sessao)
        return {
            "status": "erro",
            "empresa_id": empresa_id,
            "sessao": sessao,
            **resultado,
        }

    if resultado.get("status") == "mensagem_duplicada":
        return {
            "status": "ignorado",
            "motivo": "mensagem_duplicada",
            "estado_processamento": resultado.get(
                "estado_processamento"
            ),
            "empresa_id": empresa_id,
            "message_id": mensagem_id,
        }

    # Vinculo seguro da conversa com a conexao WAHA.
    # Falhas nesta integracao nao interrompem a Sofia.
    if resultado.get("conversa_id"):
        db_vinculo = SessionLocal()
        try:
            from app.services.followup_entrada_conexao_waha import (
                validar_conexao_entrada_waha,
            )
            from app.services.followup_vinculo_conversa_waha import (
                vincular_conversa_conexao_waha,
            )

            conexao_id, motivo_conexao = validar_conexao_entrada_waha(
                db_vinculo,
                sessao,
                empresa_id,
            )

            if conexao_id is not None:
                vinculado, motivo_vinculo = vincular_conversa_conexao_waha(
                    db_vinculo,
                    empresa_id,
                    resultado["conversa_id"],
                    conexao_id,
                )

                if vinculado:
                    db_vinculo.commit()
                else:
                    db_vinculo.rollback()
                    print(
                        f"[FOLLOWUP] vinculo recusado: {motivo_vinculo}",
                        flush=True,
                    )
            else:
                print(
                    f"[FOLLOWUP] conexao nao validada: {motivo_conexao}",
                    flush=True,
                )

        except Exception as erro_vinculo:
            db_vinculo.rollback()
            print(
                f"[FOLLOWUP] falha no vinculo: {erro_vinculo}",
                flush=True,
            )
        finally:
            db_vinculo.close()

    resposta = resultado.get("resposta_agente")

    if (
        (
            resultado.get("nova_lead") is True
            or resultado.get("alerta_atendimento_humano") is True
        )
        and resultado.get("notificacao_luciano")
    ):
        chat_id_destinatario = None
        db_notificacao = None
        try:
            db_notificacao = SessionLocal()
            chat_id_destinatario = obter_destinatario_notificacao(
                db_notificacao,
                empresa_id,
            )
        except Exception as erro_notificacao:
            print(
                f"Falha ao consultar destinatario de notificacao "
                f"da empresa {empresa_id}: {erro_notificacao}"
            )
        finally:
            if db_notificacao is not None:
                db_notificacao.close()

        if chat_id_destinatario:
            enviar_texto_waha(sessao, chat_id_destinatario, resultado["notificacao_luciano"], {})
        else:
            print(f"ALERTA: destinatario de notificacao nao configurado para empresa {empresa_id}.")

    status_envio = None
    resposta_mensagem_id = None

    if resposta:
        from app.services.mensagem_service import (
            registrar_resposta_agente,
        )

        db_resposta = SessionLocal()
        try:
            id_resposta_externo = (
                "sofia:" + mensagem_id
                if mensagem_id and len(mensagem_id) <= 174
                else None
            )

            registro_resposta = registrar_resposta_agente(
                db_resposta,
                empresa_id=empresa_id,
                conversa_id=resultado["conversa_id"],
                cliente_id=resultado.get("cliente_id"),
                texto=resposta,
                mensagem_id_externo=id_resposta_externo,
            )

            resposta_mensagem_id = registro_resposta.id
            db_resposta.commit()
        except Exception:
            db_resposta.rollback()
            raise
        finally:
            db_resposta.close()

        delay = calcular_delay_resposta(resposta)

        headers = {}

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

        agradecimento_pos_encaminhamento = (
            resultado.get("etapa_atual") == "aguardando_humano"
            and resultado.get("nova_lead") is False
            and resposta.startswith(
                "Eu que agrade\u00e7o pelo contato e pela confian\u00e7a na "
            )
        )
        # Serializa o inicio do envio da Sofia com a tomada do atendimento.
        with SessionLocal() as db_verificacao:
            conversa_envio = (
                db_verificacao.query(Conversa.humano_assumiu)
                .filter(
                    Conversa.id == resultado["conversa_id"],
                    Conversa.empresa_id == empresa_id,
                )
                .with_for_update()
                .one_or_none()
            )
            sofia_desativada = False
            if autenticado is True:
                conexao_envio = db_verificacao.query(
                    ConexaoCanal.sofia_ativa, ConexaoCanal.operacao_suspensa,
                ).filter_by(id=conexao_id, empresa_id=empresa_id, ativo=True).one_or_none()
                sofia_desativada = (
                    conexao_envio is None or not conexao_envio.sofia_ativa
                    or conexao_envio.operacao_suspensa
                )
            envio_bloqueado = (
                conversa_envio is None
                or sofia_desativada
                or conversa_envio.humano_assumiu is True
                or (agradecimento_pos_encaminhamento and conversa_envio.humano_assumiu is None)
            )
            if not envio_bloqueado:
                envio_ok, status_envio, id_waha = enviar_texto_waha(
                    sessao, chat_id, resposta, headers,
                )

        if envio_bloqueado:
            from app.services.mensagem_service import (
                registrar_resultado_envio,
            )
            from app.services.estados_mensagem import (
                STATUS_ENVIO_NAO_APLICAVEL,
            )

            db_cancelamento = SessionLocal()
            try:
                atualizado = registrar_resultado_envio(
                    db_cancelamento,
                    empresa_id=empresa_id,
                    conversa_id=resultado["conversa_id"],
                    mensagem_id=resposta_mensagem_id,
                    status_envio=STATUS_ENVIO_NAO_APLICAVEL,
                )
                if not atualizado:
                    raise RuntimeError(
                        "Falha ao registrar cancelamento do envio."
                    )
                # LIMPEZA SEGURA DO HISTORICO CANCELADO
                # Remove somente a ultima ocorrencia exata da
                # resposta cancelada, preservando mensagens posteriores.
                sufixo_cancelado = "\nAgente: " + resposta

                conversa_cancelamento = (
                    db_cancelamento.query(Conversa)
                    .filter(
                        Conversa.id == resultado["conversa_id"],
                        Conversa.empresa_id == empresa_id,
                    )
                    .with_for_update()
                    .one_or_none()
                )

                if conversa_cancelamento is None:
                    raise RuntimeError(
                        "Conversa nao encontrada no cancelamento."
                    )

                historico_atual = (
                    conversa_cancelamento.historico or ""
                )

                posicao = historico_atual.rfind(
                    sufixo_cancelado
                )

                if posicao >= 0:
                    fim_resposta = (
                        posicao + len(sufixo_cancelado)
                    )

                    trecho_posterior = (
                        historico_atual[fim_resposta:]
                    )

                    if (
                        not trecho_posterior
                        or trecho_posterior.startswith("\n")
                    ):
                        conversa_cancelamento.historico = (
                            historico_atual[:posicao]
                            + trecho_posterior
                        )
                    else:
                        print(
                            "[WAHA WEBHOOK] historico preservado: "
                            "ocorrencia ambigua da resposta cancelada.",
                            flush=True,
                        )
                else:
                    print(
                        "[WAHA WEBHOOK] resposta cancelada "
                        "nao encontrado no historico.",
                        flush=True,
                    )

                db_cancelamento.commit()
            except Exception:
                db_cancelamento.rollback()
                raise
            finally:
                db_cancelamento.close()

            return {
                "status": "processado",
                "empresa_id": empresa_id,
                "sessao": sessao,
                "chat_id": chat_id,
                "message_id": mensagem_id,
                "resposta": None,
                "status_envio": STATUS_ENVIO_NAO_APLICAVEL,
                "motivo": "sofia_desativada_na_conexao" if sofia_desativada
                else "atendimento_humano_assumido",
            }

        from app.services.mensagem_service import (
            registrar_resultado_envio,
        )
        from app.services.estados_mensagem import (
            classificar_resultado_envio,
        )

        db_envio = SessionLocal()
        try:
            atualizado = registrar_resultado_envio(
                db_envio,
                empresa_id=empresa_id,
                conversa_id=resultado["conversa_id"],
                mensagem_id=resposta_mensagem_id,
                status_envio=classificar_resultado_envio(
                    envio_ok,
                    status_envio,
                ),
                mensagem_id_waha=id_waha if envio_ok else None,
                sessao_waha=sessao if envio_ok and id_waha else None,
            )

            if not atualizado:
                raise RuntimeError(
                    "Nao foi possivel registrar resultado do WAHA."
                )

            db_envio.commit()
        except Exception as erro_registro_envio:
            db_envio.rollback()
            print(
                "[WAHA WEBHOOK] falha ao registrar resultado "
                f"do envio: {erro_registro_envio}",
                flush=True,
            )
            status_envio = (
                status_envio
                or "registro_resultado_pendente"
            )
        finally:
            db_envio.close()

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
