import streamlit as st

from database.db import conectar
from services.empresa_contexto_service import listar_empresas_permitidas


def obter_logo_empresa(empresa_id):
    conn = None
    try:
        conn = conectar()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT logo_path FROM empresas WHERE id = %s",
                (int(empresa_id),),
            )
            resultado = cursor.fetchone()
        if resultado and resultado[0]:
            return resultado[0]
    except Exception:
        pass
    finally:
        if conn:
            conn.close()
    return "assets/logo_orion.png"


def inicializar_contexto_empresa():
    if "empresa_login_id" not in st.session_state:
        st.session_state.empresa_login_id = st.session_state.get("empresa_id")
    if "empresa_login_nome" not in st.session_state:
        st.session_state.empresa_login_nome = st.session_state.get("empresa")
    if "empresa_ativa_id" not in st.session_state:
        st.session_state.empresa_ativa_id = st.session_state.get("empresa_id")
    if "empresa_ativa_nome" not in st.session_state:
        st.session_state.empresa_ativa_nome = st.session_state.get("empresa")


def aplicar_empresa_ativa(empresa_id, empresa_nome):
    st.session_state.empresa_ativa_id = int(empresa_id)
    st.session_state.empresa_ativa_nome = empresa_nome
    st.session_state.empresa_id = int(empresa_id)
    st.session_state.empresa = empresa_nome


def render_seletor_empresa():
    nivel = st.session_state.get("nivel", "usuario")
    empresa_login_id = st.session_state.get("empresa_login_id")

    if nivel not in ["orion_admin", "parceiro_admin"] or not empresa_login_id:
        return

    empresas = listar_empresas_permitidas(nivel, int(empresa_login_id))
    if empresas.empty:
        st.info("Nenhuma empresa disponível.")
        return

    opcoes = {}
    for _, row in empresas.iterrows():
        empresa_id = int(row["id"])
        nome = str(row["nome"])
        tipo = str(row["tipo"] or "cliente")
        if empresa_id == int(empresa_login_id):
            label = f"🏢 {nome} — painel principal"
        elif tipo == "cliente":
            label = f"👤 {nome}"
        elif tipo == "parceiro":
            label = f"🤝 {nome}"
        else:
            label = f"🏢 {nome}"
        opcoes[label] = {"id": empresa_id, "nome": nome}

    labels = list(opcoes.keys())
    empresa_ativa_id = int(st.session_state.get("empresa_ativa_id", empresa_login_id))
    indice = 0
    for i, label in enumerate(labels):
        if int(opcoes[label]["id"]) == empresa_ativa_id:
            indice = i
            break

    st.markdown("#### Empresa ativa")
    selecionada = st.selectbox(
        "Selecionar empresa ativa",
        labels,
        index=indice,
        key="seletor_empresa_ativa",
        label_visibility="collapsed",
    )

    contexto = opcoes[selecionada]
    if int(contexto["id"]) != empresa_ativa_id:
        aplicar_empresa_ativa(contexto["id"], contexto["nome"])
        st.rerun()

    st.caption(f"Contexto atual: {st.session_state.get('empresa_ativa_nome')}")


def render_sidebar():
    inicializar_contexto_empresa()

    nivel = st.session_state.get("nivel", "usuario")
    empresa_login_nome = st.session_state.get("empresa_login_nome", "")
    empresa_ativa_id = st.session_state.get("empresa_ativa_id")

    with st.sidebar:
        st.markdown("<br>", unsafe_allow_html=True)

        if nivel == "parceiro_admin" and empresa_login_nome == "Forway":
            logo_path = "assets/logo_forway.png"
            titulo_crm = "FORWAY CRM"
        else:
            logo_path = obter_logo_empresa(empresa_ativa_id)
            titulo_crm = "ORION SYSTEMS CRM"

        try:
            st.image(logo_path, width=180)
        except Exception:
            st.markdown(f"## {titulo_crm}")

        st.markdown(f"### {titulo_crm}")

        if nivel in ["orion_admin", "parceiro_admin"]:
            st.markdown("---")
            render_seletor_empresa()
            st.markdown("---")

        menu = [
            "🏠 Visão Geral",
            "📈 Leads",
            "🛒 Produtos",
            "🧾 Pedidos",
            "💬 Conversas",
            "👨‍💼 Especialistas",
            "🔥 Funil Comercial",
            "📊 Serviços e Canais",
            "📌 Resultados",
            "🔌 Integrações",
            "⚙️ Configurações",
        ]
        if nivel in ["orion_admin", "parceiro_admin"]:
            menu.append("🏢 Empresas")

        pagina = st.radio("Menu", menu, key="menu_principal")

        st.markdown("---")
        st.success("🟢 Agente IA Online")
        st.caption("WhatsApp • Instagram Direct • Facebook Messenger")
        st.markdown("---")

        try:
            st.image("assets/logo_orion.png", width=130)
        except Exception:
            st.markdown("**ORION SYSTEMS**")

        st.caption("Powered by Orion Systems")
        return pagina