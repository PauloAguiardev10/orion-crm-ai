import streamlit as st


def render_integracoes():

    st.title("🔌 Integrações")

    st.markdown("## Canais planejados")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("""
        <div class="metric-card">
            <h3>📱 WhatsApp</h3>
            <p>Status: aguardando integração</p>
            <p>Canal principal de atendimento.</p>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="metric-card">
            <h3>📸 Instagram Direct</h3>
            <p>Status: aguardando integração</p>
            <p>Leads vindas do Instagram.</p>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown("""
        <div class="metric-card">
            <h3>🔵 Facebook Messenger</h3>
            <p>Status: aguardando integração</p>
            <p>Leads vindas da página do Facebook.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    st.info(
        "Quando o gestor liberar os acessos, conectaremos os canais reais ao CRM SDR."
    )