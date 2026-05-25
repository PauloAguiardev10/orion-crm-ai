import plotly.express as px
import streamlit as st


NEON_COLORS = [
    "#00E5FF",
    "#7C3AED",
    "#2563EB",
    "#06B6D4",
    "#9333EA",
    "#22C55E",
    "#F97316"
]


def grafico_donut(df, coluna, titulo):

    if df is None or df.empty:
        st.info("Sem dados para gerar gráfico.")
        return

    if coluna not in df.columns:
        st.warning(f"Coluna '{coluna}' não encontrada.")
        return

    dados = (
        df[coluna]
        .fillna("Não informado")
        .astype(str)
        .replace("", "Não informado")
        .value_counts()
        .reset_index()
    )

    if dados.empty:
        st.info("Sem dados suficientes para gráfico.")
        return

    dados.columns = [
        "Categoria",
        "Quantidade"
    ]

    fig = px.pie(
        dados,
        names="Categoria",
        values="Quantidade",
        hole=0.68,
        title=titulo,
        color_discrete_sequence=NEON_COLORS
    )

    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        marker=dict(
            line=dict(
                color="#020617",
                width=2
            )
        ),
        pull=[0.04 for _ in range(len(dados))]
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",

        font=dict(
            color="white",
            size=14
        ),

        title_font=dict(
            size=20,
            color="#E0F2FE"
        ),

        legend=dict(
            orientation="h",
            y=-0.20,
            x=0.5,
            xanchor="center",
            font=dict(
                size=12,
                color="white"
            )
        ),

        margin=dict(
            t=60,
            b=70,
            l=20,
            r=20
        ),

        height=420
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )