from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

from styles.theme import carregar_tema
from components.sidebar import render_sidebar
from services.leads_service import carregar_leads

from services.auth_service import (
    validar_login,
    obter_usuario_id,
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


def proteger_interface_contra_traducao():
    """
    Marca o Orion CRM como interface pt-BR
    e solicita que tradutores automaticos nao alterem a pagina.
    """

    components.html(
        """
        <script>
        (function () {
            try {
                const doc = window.parent.document;

                doc.documentElement.lang = "pt-BR";
                doc.documentElement.setAttribute(
                    "translate",
                    "no"
                );

                doc.documentElement.classList.add(
                    "notranslate"
                );

                if (doc.body) {
                    doc.body.setAttribute(
                        "translate",
                        "no"
                    );

                    doc.body.classList.add(
                        "notranslate"
                    );
                }

                let metaGoogle = doc.head.querySelector(
                    'meta[name="google"]'
                );

                if (!metaGoogle) {
                    metaGoogle = doc.createElement(
                        "meta"
                    );

                    metaGoogle.setAttribute(
                        "name",
                        "google"
                    );

                    doc.head.appendChild(
                        metaGoogle
                    );
                }

                metaGoogle.setAttribute(
                    "content",
                    "notranslate"
                );

                let metaLanguage = doc.head.querySelector(
                    'meta[http-equiv="Content-Language"]'
                );

                if (!metaLanguage) {
                    metaLanguage = doc.createElement(
                        "meta"
                    );

                    metaLanguage.setAttribute(
                        "http-equiv",
                        "Content-Language"
                    );

                    doc.head.appendChild(
                        metaLanguage
                    );
                }

                metaLanguage.setAttribute(
                    "content",
                    "pt-BR"
                );

            } catch (erro) {
                console.warn(
                    "Orion CRM notranslate:",
                    erro
                );
            }
        })();
        </script>
        """,
        height=0,
    )


st.set_page_config(
    page_title="Orion Systems",
    page_icon="🚀",
    layout="wide",
)

proteger_interface_contra_traducao()

carregar_tema()


if "logado" not in st.session_state:
    st.session_state.logado = False

if "usuario" not in st.session_state:
    st.session_state.usuario = None

if "usuario_id" not in st.session_state:
    st.session_state.usuario_id = None

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
    """
    Login principal do Orion CRM AI.

    A imagem estática apresenta:
    - Identidade Orion Systems
    - IA robótica
    - Planeta Terra e redes neurais
    - Dashboard demonstrativo da Forway

    Os campos e o botão são reais.
    A autenticação multiempresa é preservada.
    """

    css_path = (
        Path(__file__).resolve().parent
        / "assets"
        / "login"
        / "login.css"
    )

    if css_path.is_file():
        css_login = css_path.read_text(
            encoding="utf-8-sig"
        )

        st.markdown(
            f"<style>{css_login}</style>",
            unsafe_allow_html=True,
        )

    # A imagem aprovada já contém:
    # logo, títulos, painel Forway e elementos decorativos.
    #
    # Não renderizamos novamente esses elementos.
    # Apenas os controles funcionais do login.

    esquerda, direita = st.columns(
        [1, 2],
        gap="small",
    )

    with esquerda:

        st.markdown(
            '<div class="orion-login-marker"></div>',
            unsafe_allow_html=True,
        )

        usuario = st.text_input(
            "Usuário ou empresa",
            placeholder="Usuário ou empresa",
            label_visibility="collapsed",
            key="login_usuario",
        )

        senha = st.text_input(
            "Senha",
            placeholder="Senha",
            type="password",
            label_visibility="collapsed",
            key="login_senha",
        )

        if st.button(
            "Entrar  →",
            use_container_width=True,
        ):

            if validar_login(usuario, senha):

                usuario_id = obter_usuario_id(usuario)

                empresa = obter_empresa_usuario(usuario)

                empresa_id = obter_empresa_id_usuario(
                    usuario
                )

                nivel = obter_nivel_usuario(usuario)

                # Estado de autenticação

                st.session_state.logado = True

                st.session_state.usuario = usuario

                st.session_state.usuario_id = usuario_id

                st.session_state.empresa = empresa

                st.session_state.empresa_id = empresa_id

                st.session_state.nivel = nivel

                # Empresa vinculada ao login

                st.session_state.empresa_login_id = (
                    empresa_id
                )

                st.session_state.empresa_login_nome = (
                    empresa
                )

                # Empresa ativa no CRM

                st.session_state.empresa_ativa_id = (
                    empresa_id
                )

                st.session_state.empresa_ativa_nome = (
                    empresa
                )

                st.rerun()

            else:

                st.error(
                    "Usuário ou senha inválidos."
                )


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
        st.session_state.usuario_id = None
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
