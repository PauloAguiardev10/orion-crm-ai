import base64
import os

import requests
import streamlit as st
from streamlit.components.v1 import html

from services.central_whatsapp_service import SessaoCentralExpirada, listar_atendentes_whatsapp


ERROS = {
    "limite_plano_nao_configurado": "O limite de conexões deste plano ainda não foi configurado.",
    "limite_plano_atingido": "O limite de conexões deste plano foi atingido.",
    "limite_sessoes_provedor": "A instalação da WAHA recusou outra sessão.",
    "gestao_waha_desativada": "Gestão da WAHA desativada neste ambiente.",
    "conexao_legada_protegida": "A conexão legada está protegida contra alterações pelo CRM.",
    "vinculo_com_conversas_existentes": "A conexão já tem histórico e seu vínculo está protegido.",
    "qr_nao_disponivel": "A sessão ainda não oferece um QR Code.",
}
ESTADOS = {
    "WORKING": "Conectada", "STOPPED": "Desconectada", "FAILED": "Falha na sessão",
    "SCAN_QR_CODE": "Aguardando leitura do QR Code", "STARTING": "Iniciando",
    "NAO_PROVISIONADA": "Aguardando conexão", "DESCONHECIDO": "Estado desconhecido",
    "PASSKEY_REQUIRED": "WAHA exige chave de acesso",
    "PASSKEY_CONFIRMATION_REQUIRED": "WAHA exige confirmação de chave de acesso",
}


def _api(metodo, caminho, *, corpo=None, imagem=False):
    origem = os.getenv("ORION_API_INTERNA_URL", "http://127.0.0.1:8000").rstrip("/")
    try:
        resposta = requests.request(
            metodo, f"{origem}/api/central-whatsapp/{caminho}",
            params={"empresa_id": st.session_state.get("empresa_ativa_id")},
            headers={"Authorization": f"Bearer {st.session_state.get('token_central', '')}"},
            json=corpo, timeout=25, allow_redirects=False,
        )
        if resposta.ok and resposta.status_code < 300:
            return resposta.content if imagem else resposta.json()
        motivo = resposta.json().get("detail")
        mensagem = ERROS.get(motivo) if isinstance(motivo, str) else None
        st.warning(mensagem or "Operação indisponível para esta conexão.")
    except (ValueError, requests.RequestException):
        st.warning("Não foi possível consultar o serviço de conexões.")
    return None


@st.fragment(run_every=5)
def _estado_conexao(conexao):
    caminho = f"conexoes/{conexao['id']}"
    estado = _api("GET", caminho + "/estado")
    if estado is None:
        return
    codigo = estado["estado"]
    st.write(f"**Situação operacional:** {ESTADOS.get(codigo, 'Estado desconhecido')}")
    if estado.get("numero"):
        st.write(f"**Número:** +{estado['numero']}")
    if codigo == "SCAN_QR_CODE" and conexao["gerenciada"] and not conexao["suspensa"]:
        qr = _api("GET", caminho + "/qr", imagem=True)
        if qr:
            dados = base64.b64encode(qr).decode("ascii")
            html(f'<img alt="QR Code do WhatsApp" width="260" height="260" src="data:image/png;base64,{dados}">',
                 height=270)


def _formulario(chave, atendentes, conexao=None):
    atual = conexao or {}
    opcoes = [None, *atendentes]
    titular = atual.get("especialista_id")
    if titular is not None and titular not in atendentes:
        opcoes.append(titular)
    with st.form(chave):
        nome = st.text_input("Identificação da conexão", value=atual.get("nome", ""), max_chars=100)
        especialista_id = st.selectbox(
            "Vendedor ou atendente", opcoes, index=opcoes.index(titular),
            format_func=lambda item: "Conexão corporativa" if item is None else atendentes.get(item, "Vínculo atual"),
        )
        sofia = st.checkbox("Usar Sofia nesta conexão", value=atual.get("sofia_ativa", True))
        if st.form_submit_button("Salvar alterações" if conexao else "Cadastrar conexão"):
            return {"nome_conexao": nome, "especialista_id": especialista_id, "sofia_ativa": sofia}
    return None


def render_conexoes_whatsapp():
    if st.session_state.get("nivel") not in ("orion_admin", "parceiro_admin", "admin_empresa"):
        return
    if not st.toggle("Gerenciar conexões WhatsApp"):
        return
    dados = _api("GET", "conexoes")
    if dados is None:
        return
    empresa_id = st.session_state.get("empresa_ativa_id")
    propria = empresa_id in (None, st.session_state.get("empresa_login_id"))
    atendentes = {}
    if propria:
        try:
            atendentes = {
                a["id"]: a["nome"] for a in listar_atendentes_whatsapp(
                    token=st.session_state.get("token_central", ""), empresa_id=empresa_id,
                )
            }
        except (SessaoCentralExpirada, ValueError, requests.RequestException):
            st.warning("Lista de atendentes indisponível.")

    plano, limite = dados["plano"], dados["limite"]
    st.caption(f"Plano {plano} · " + (f"{limite} conexões" if limite is not None else "Limite não configurado"))
    if dados.get("limite_usuarios") is not None:
        st.caption(f"Usuários na franquia: {dados['usuarios_contabilizados']} · Limite: {dados['limite_usuarios']}")
    if limite is not None:
        with st.expander("Cadastrar conexão"):
            formulario = _formulario(f"cadastrar_waha_{empresa_id}", atendentes)
            if formulario is not None and _api("POST", "conexoes", corpo=formulario):
                st.rerun()
    conexoes = {item["id"]: item for item in dados["conexoes"]}
    if not conexoes:
        st.info("Nenhuma conexão WhatsApp cadastrada.")
        return
    escolhida = st.selectbox(
        "Conexão WhatsApp", list(conexoes), format_func=lambda key: f"#{key} · {conexoes[key]['nome']}",
        key=f"gestao_conexao_{empresa_id}",
    )
    conexao = conexoes[escolhida]
    _estado_conexao(conexao)
    if not conexao["gerenciada"]:
        st.caption("Conexão legada protegida. Você pode consultar seu estado.")
        return
    caminho = f"conexoes/{escolhida}"
    if st.button("Conectar ou reconectar", key=f"conectar_waha_{escolhida}"):
        if _api("POST", caminho + "/conectar"):
            st.rerun()
    with st.expander("Editar conexão"):
        alteracoes = _formulario(f"editar_waha_{escolhida}", atendentes, conexao)
        if alteracoes is not None and _api("PUT", caminho, corpo=alteracoes):
            st.rerun()
    with st.expander("Desconectar sessão"):
        st.caption("A sessão será pausada e o pareamento será mantido para reconexão.")
        confirmar = st.checkbox("Confirmo a desconexão desta sessão", key=f"confirmar_waha_{escolhida}")
        if st.button("Desconectar", disabled=not confirmar, key=f"desconectar_waha_{escolhida}"):
            if _api("POST", caminho + "/desconectar", corpo={"confirmar": confirmar}):
                st.rerun()
