import streamlit as st


def render_alertas_operacionais(leads):

    st.markdown("## 🚨 Alertas Inteligentes")

    if leads.empty:
        st.info("Nenhuma lead para analisar.")
        return

    leads_quentes_aguardando = leads[
        (leads["temperatura"] == "quente") &
        (leads["status"] == "Aguardando atendimento")
    ]

    leads_em_atendimento = leads[
        leads["status"] == "Em atendimento"
    ]

    negocios_fechados = leads[
        leads["status"] == "Negócio fechado"
    ]

    canal_top = (
        leads["canal"].value_counts().idxmax()
        if not leads.empty
        else "Não identificado"
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        if len(leads_quentes_aguardando) > 0:

            lead_critica = leads_quentes_aguardando.iloc[0]

            st.error(
                f"""
                🔥 Lead quente parada há
                {lead_critica['horas_desde_entrada']}h
                """
            )

        else:

            st.success(
                "✅ Nenhuma lead quente parada."
            )

    with c2:

        st.warning(
            f"""
            🕒 {len(leads_em_atendimento)}
            lead(s) em atendimento
            """
        )

    with c3:

        st.success(
            f"""
            ✅ {len(negocios_fechados)}
            negócio(s) fechado(s)
            """
        )

    with c4:

        st.info(
            f"""
            📲 Canal dominante:
            {canal_top}
            """
        )

    st.markdown("---")

    st.markdown("### 📌 Leads Prioritárias")

    prioritarias = leads[
        leads["temperatura"] == "quente"
    ]

    if prioritarias.empty:

        st.info(
            "Nenhuma lead prioritária."
        )

    else:

        for _, lead in prioritarias.iterrows():

            st.warning(f"""
            🔥 {lead['nome']} •
            {lead['produto']} •
            {lead['status']} •
            {lead['horas_desde_entrada']}h
            """)