import streamlit as st

from styles.theme import carregar_tema
from components.sidebar import render_sidebar
from services.leads_service import carregar_leads

from services.auth_service import (
    validar_login,
    obter_empresa_usuario,
    obter_empresa_id_usuario,
    obter_nivel_usuario,
)

from utils.bloqueio import (
    empresa_bloqueada,
    tela_bloqueio,
)

from app_pages.visao_geral import render_visao_geral
from app_pages.leads import render_leads
from app_pages.produtos import render_produtos
from app_pages.pedidos import render_pedidos
from app_pages.conversas import render_conversas
from app_pages.especialistas import render_especialistas
from app_pages.funil_comercial import render_funil
from app_pages.servicos_canais import render_servicos_canais
from app_pages.resultados import render_resultados
from app_pages.integracoes import render_integracoes
from app_pages.configuracoes import render_configuracoes
from app_pages.empresas import render_empresas


st.set_page_config(
    page_title="Orion Systems",
    page_icon="🚀",
    layout="wide",
)

carregar_tema()


if "logado" not in st.session_state:
    st.session_state.logado = False

if "usuario" not in st.session_state:
    st.session_state.usuario = None

if "empresa" not in st.session_state:
    st.session_state.empresa = None

if "empresa_id" not in st.session_state:
    st.session_state.empresa_id = None

if "nivel" not in st.session_state:
    st.session_state.nivel = None

if "empresa_login_id" not in st.session_state:
    st.session_state.empresa_login_id = None

if "empresa_login_nome" not in st.session_state:
    st.session_state.empresa_login_nome = None

if "empresa_ativa_id" not in st.session_state:
    st.session_state.empresa_ativa_id = None

if "empresa_ativa_nome" not in st.session_state:
    st.session_state.empresa_ativa_nome = None


TITULOS_PAGINAS = {
    "📈 Leads": "📋 Leads",
    "🛒 Produtos": "🛒 Produtos",
    "🧾 Pedidos": "🧾 Pedidos / Vendas",
    "💬 Conversas": "💬 Conversas",
    "👨‍💼 Especialistas": "👨‍💼 Painel Especialistas",
    "🔥 Funil Comercial": "🔥 Funil Comercial",
    "📊 Serviços e Canais": "📊 Serviços e Canais",
    "📌 Resultados": "📌 Resultados Comerciais",
    "🔌 Integrações": "🔌 Integrações",
    "⚙️ Configurações": "⚙️ Configurações Operacionais",
    "🏢 Empresas": "🏢 Empresas",
}


def render_titulo_pagina(pagina):
    """
    Renderiza o título fora das páginas individuais.

    Isso evita que o Streamlit reutilize visualmente o primeiro st.title()
    mostrado durante a navegação.
    """
    titulo = TITULOS_PAGINAS.get(pagina)

    if not titulo:
        return

    st.markdown(
        f"""
        <div class="orion-page-title">
            {titulo}
        </div>
        """,
        unsafe_allow_html=True,
    )


def tela_login():
    st.markdown(
        """
        <style>
        .main .block-container {
            max-width: 100%;
            padding-top: 6vh;
        }

        div[data-testid="stTextInput"] input {
            background-color: #111827;
            border: 1px solid rgba(0,229,255,.18);
            border-radius: 14px;
            color: white;
            height: 52px;
        }

        div[data-testid="stTextInput"] label {
            color: #E2E8F0 !important;
            font-weight: 600;
        }

        div.stButton {
            margin-top: 18px;
        }

        div.stButton > button {
            background: linear-gradient(90deg, #06B6D4, #7C3AED);
            border: none;
            color: white;
            font-weight: 700;
            border-radius: 14px;
            height: 56px;
            font-size: 18px;
            transition: .3s;
        }

        div.stButton > button:hover {
            transform: scale(1.02);
            box-shadow: 0 0 18px rgba(0,229,255,.22);
        }

        .titulo-orion {
            text-align: center;
            font-size: 58px;
            font-weight: 900;
            letter-spacing: 2px;
            color: white;
            margin-top: -10px;
            margin-bottom: 4px;
        }

        .subtitulo-orion {
            text-align: center;
            color: #00E5FF;
            font-size: 18px;
            letter-spacing: 1px;
            margin-bottom: 4px;
        }

        .powered-orion {
            text-align: center;
            color: #64748B;
            font-size: 12px;
            margin-bottom: 38px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 1.1, 1])

    with col2:
        logo1, logo2, logo3 = st.columns([1, 0.8, 1])

        with logo2:
            try:
                st.image(
                    "assets/logo_orion_symbol.png",
                    width=240,
                )
            except Exception:
                pass

        st.markdown(
            """
            <div class="titulo-orion">
                ORION SYSTEMS
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="subtitulo-orion">
                Inteligência Comercial Automatizada
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="powered-orion">
                Powered by Orion Intelligence
            </div>
            """,
            unsafe_allow_html=True,
        )

        usuario = st.text_input(
            "Usuário",
            key="login_usuario",
        )

        senha = st.text_input(
            "Senha",
            type="password",
            key="login_senha",
        )

        if st.button(
            "Entrar",
            use_container_width=True,
        ):
            if validar_login(usuario, senha):
                empresa = obter_empresa_usuario(usuario)
                empresa_id = obter_empresa_id_usuario(usuario)
                nivel = obter_nivel_usuario(usuario)

                st.session_state.logado = True
                st.session_state.usuario = usuario
                st.session_state.empresa = empresa
                st.session_state.empresa_id = empresa_id
                st.session_state.nivel = nivel

                st.session_state.empresa_login_id = empresa_id
                st.session_state.empresa_login_nome = empresa
                st.session_state.empresa_ativa_id = empresa_id
                st.session_state.empresa_ativa_nome = empresa

                st.rerun()

            else:
                st.error("Usuário ou senha inválidos.")


if not st.session_state.logado:
    tela_login()
    st.stop()


pagina = render_sidebar()

if empresa_bloqueada():
    tela_bloqueio()


leads = carregar_leads(
    st.session_state.empresa_id
)


with st.sidebar:
    st.markdown("---")

    st.caption(
        f"Conta: {st.session_state.get('empresa_login_nome')}"
    )
    st.caption(
        f"Empresa ativa: {st.session_state.get('empresa_ativa_nome')}"
    )
    st.caption(
        f"ID ativo: {st.session_state.get('empresa_ativa_id')}"
    )
    st.caption(f"Usuário: {st.session_state.usuario}")
    st.caption(f"Nível: {st.session_state.nivel}")

    if st.button("Sair"):
        st.session_state.logado = False
        st.session_state.usuario = None
        st.session_state.empresa = None
        st.session_state.empresa_id = None
        st.session_state.nivel = None
        st.session_state.empresa_login_id = None
        st.session_state.empresa_login_nome = None
        st.session_state.empresa_ativa_id = None
        st.session_state.empresa_ativa_nome = None

        st.rerun()


# A Visão Geral já possui um cabeçalho próprio.
if pagina != "🏠 Visão Geral":
    render_titulo_pagina(pagina)


if pagina == "🏠 Visão Geral":
    render_visao_geral(leads)

elif pagina == "📈 Leads":
    render_leads(leads)

elif pagina == "🛒 Produtos":
    render_produtos()

elif pagina == "🧾 Pedidos":
    render_pedidos()

elif pagina == "💬 Conversas":
    render_conversas(leads)

elif pagina == "👨‍💼 Especialistas":
    render_especialistas(leads)

elif pagina == "🔥 Funil Comercial":
    render_funil(leads)

elif pagina == "📊 Serviços e Canais":
    render_servicos_canais(leads)

elif pagina == "📌 Resultados":
    render_resultados(leads)

elif pagina == "🔌 Integrações":
    render_integracoes()

elif pagina == "⚙️ Configurações":
    render_configuracoes()

elif pagina == "🏢 Empresas":
    if st.session_state.nivel in ["orion_admin", "parceiro_admin"]:
        render_empresas()
    else:
        st.error("Acesso restrito.")