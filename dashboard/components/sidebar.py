import streamlit as st

from database.db import conectar


def obter_logo_empresa(empresa_id):
    try:
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(empresas)")
        colunas = [col[1] for col in cursor.fetchall()]

        if "logo_path" not in colunas:
            cursor.execute("ALTER TABLE empresas ADD COLUMN logo_path TEXT")
            conn.commit()

        cursor.execute(
            "SELECT logo_path FROM empresas WHERE id = ?",
            (empresa_id,)
        )

        resultado = cursor.fetchone()
        conn.close()

        if resultado and resultado[0]:
            return resultado[0]

    except Exception:
        pass

    return "assets/logo_orion.png"


def render_sidebar():
    nivel = st.session_state.get("nivel", "usuario")
    empresa_id = st.session_state.get("empresa_id")
    empresa = st.session_state.get("empresa", "")

    with st.sidebar:
        st.markdown("<br>", unsafe_allow_html=True)

        if nivel == "parceiro_admin" and empresa == "Forway":
            logo_path = "assets/logo_forway.png"
            titulo_crm = "FORWAY CRM"
        else:
            logo_path = obter_logo_empresa(empresa_id)
            titulo_crm = "ORION SYSTEMS CRM"

        try:
            st.image(logo_path, width=180)
        except Exception:
            st.markdown(f"## {titulo_crm}")

        st.markdown(f"### {titulo_crm}")

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

        pagina = st.radio("Menu", menu)

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