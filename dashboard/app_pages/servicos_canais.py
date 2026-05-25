import streamlit as st

from components.graficos import grafico_donut


def render_servicos_canais(leads):

    st.title("📊 Serviços e Canais")

    if leads.empty:
        st.info("Nenhum dado disponível.")
        return

    leads = leads.copy()

    if "produto" not in leads.columns:
        leads["produto"] = "Não informado"

    if "canal" not in leads.columns:
        if "origem" in leads.columns:
            leads["canal"] = leads["origem"]
        else:
            leads["canal"] = "Não informado"

    leads["produto"] = (
        leads["produto"]
        .fillna("Não informado")
        .astype(str)
    )

    leads["canal"] = (
        leads["canal"]
        .fillna("Não informado")
        .astype(str)
    )

    g1, g2 = st.columns(2)

    with g1:
        grafico_donut(
            leads,
            "produto",
            "Serviços Mais Procurados"
        )

    with g2:
        grafico_donut(
            leads,
            "canal",
            "Leads por Canal"
        )

    st.markdown("## 📌 Ranking Detalhado")

    r1, r2 = st.columns(2)

    with r1:
        st.markdown("### Serviços")

        ranking_servicos = (
            leads["produto"]
            .value_counts()
            .reset_index()
        )

        ranking_servicos.columns = [
            "Serviço",
            "Quantidade"
        ]

        st.dataframe(
            ranking_servicos,
            use_container_width=True,
            hide_index=True
        )

    with r2:
        st.markdown("### Canais")

        ranking_canais = (
            leads["canal"]
            .value_counts()
            .reset_index()
        )

        ranking_canais.columns = [
            "Canal",
            "Quantidade"
        ]

        st.dataframe(
            ranking_canais,
            use_container_width=True,
            hide_index=True
        )