import streamlit as st

from components.graficos import grafico_donut


def melhor_valor(df, coluna):
    if df.empty:
        return "N/A"

    if coluna not in df.columns:
        return "N/A"

    serie = (
        df[coluna]
        .dropna()
        .astype(str)
    )

    serie = serie[
        serie.str.strip() != ""
    ]

    if serie.empty:
        return "N/A"

    contagem = serie.value_counts()

    if contagem.empty:
        return "N/A"

    return contagem.idxmax()


def render_resultados(leads):

    st.title("📌 Resultados Comerciais")

    if leads.empty:
        st.info("Nenhum dado disponível.")
        return

    leads = leads.copy()

    if "status" not in leads.columns:
        leads["status"] = "Aguardando atendimento"

    if "produto" not in leads.columns:
        leads["produto"] = "Não informado"

    if "responsavel" not in leads.columns:
        leads["responsavel"] = "Não atribuído"

    if "canal" not in leads.columns:
        if "origem" in leads.columns:
            leads["canal"] = leads["origem"]
        else:
            leads["canal"] = "Não informado"

    status_normalizado = (
        leads["status"]
        .fillna("")
        .astype(str)
        .str.lower()
    )

    fechados_df = leads[
        status_normalizado.str.contains("fechado", na=False)
        & ~status_normalizado.str.contains("não fechado|nao fechado", na=False)
    ]

    nao_fechados_df = leads[
        status_normalizado.str.contains("não fechado|nao fechado", na=False)
    ]

    total = len(leads)

    taxa = round(
        (len(fechados_df) / total) * 100,
        1
    ) if total > 0 else 0

    melhor_canal = melhor_valor(
        fechados_df,
        "canal"
    )

    melhor_servico = melhor_valor(
        fechados_df,
        "produto"
    )

    melhor_especialista = melhor_valor(
        fechados_df,
        "responsavel"
    )

    st.markdown(
        """
        <style>
        .metric-card {
            background: linear-gradient(135deg, rgba(15,23,42,.96), rgba(30,41,59,.88));
            border: 1px solid rgba(0,229,255,.16);
            border-radius: 18px;
            padding: 18px 20px;
            min-height: 105px;
            box-shadow: 0 0 18px rgba(0,229,255,.04);
        }

        .metric-title {
            color: #94A3B8;
            font-size: 13px;
            margin-bottom: 8px;
        }

        .metric-value {
            color: #FFFFFF;
            font-size: 28px;
            font-weight: 800;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    c1, c2, c3, c4 = st.columns(4)

    metricas = [
        ("✅ Fechados", len(fechados_df)),
        ("⚪ Não fechados", len(nao_fechados_df)),
        ("📈 Conversão", f"{taxa}%"),
        ("🏆 Melhor canal", melhor_canal),
    ]

    for col, (titulo, valor) in zip([c1, c2, c3, c4], metricas):
        with col:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-title">{titulo}</div>
                    <div class="metric-value">{valor}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown("## 🧠 Insights Comerciais")

    i1, i2 = st.columns(2)

    with i1:
        st.success(f"🏆 Serviço campeão: {melhor_servico}")

    with i2:
        st.info(f"👨‍💼 Especialista destaque: {melhor_especialista}")

    st.markdown("## 📊 Conversão")

    if not fechados_df.empty:

        g1, g2 = st.columns(2)

        with g1:
            grafico_donut(
                fechados_df,
                "canal",
                "Canais que mais convertem"
            )

        with g2:
            grafico_donut(
                fechados_df,
                "produto",
                "Serviços mais vendidos"
            )

        st.markdown("## 👨‍💼 Ranking Especialistas")

        ranking = (
            fechados_df["responsavel"]
            .fillna("Não atribuído")
            .astype(str)
            .value_counts()
            .reset_index()
        )

        ranking.columns = [
            "Especialista",
            "Fechamentos"
        ]

        st.dataframe(
            ranking,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.warning("Ainda não existem negócios fechados.")