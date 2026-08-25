import pandas as pd
import streamlit as st

from components.graficos import grafico_donut


def render_servicos_canais(leads):

    st.title("📊 Serviços e Canais")

    st.markdown(
        """
        <style>
        .servicos-context-card {
            position: relative;
            overflow: hidden;
            background:
                radial-gradient(circle at 0% 0%, rgba(34,211,238,.09), transparent 38%),
                linear-gradient(145deg, rgba(15,23,42,.97), rgba(3,8,20,.96));
            border: 1px solid rgba(34,211,238,.24);
            border-radius: 18px;
            padding: 16px 18px;
            margin: 8px 0 18px 0;
            box-shadow:
                0 0 26px rgba(34,211,238,.065),
                inset 0 1px 0 rgba(255,255,255,.02);
        }

        .servicos-context-card::before {
            content: "";
            position: absolute;
            left: 0;
            top: 13px;
            bottom: 13px;
            width: 3px;
            border-radius: 999px;
            background: linear-gradient(180deg, #67E8F9, #22D3EE, #3B82F6);
            box-shadow: 0 0 12px rgba(34,211,238,.78);
        }

        .servicos-context-title {
            color: #FFFFFF;
            font-size: 15px;
            font-weight: 850;
            margin-left: 5px;
            margin-bottom: 4px;
        }

        .servicos-context-subtitle {
            color: #94A3B8;
            font-size: 13px;
            margin-left: 5px;
        }

        .servicos-empty-card {
            background:
                radial-gradient(circle at 50% 0%, rgba(99,102,241,.09), transparent 44%),
                linear-gradient(145deg, rgba(15,23,42,.96), rgba(3,8,20,.95));
            border: 1px dashed rgba(99,102,241,.40);
            border-radius: 18px;
            padding: 26px 20px;
            margin: 10px 0 18px 0;
            text-align: center;
            color: #CBD5E1;
            box-shadow: 0 0 24px rgba(99,102,241,.06);
        }

        .servicos-empty-card strong {
            color: #FFFFFF;
        }

        .ranking-card {
            background:
                radial-gradient(circle at 0% 0%, rgba(34,211,238,.06), transparent 40%),
                linear-gradient(145deg, rgba(15,23,42,.96), rgba(3,8,20,.95));
            border: 1px solid rgba(34,211,238,.18);
            border-radius: 18px;
            padding: 14px 16px;
            margin: 4px 0 12px 0;
            box-shadow: 0 0 22px rgba(34,211,238,.045);
        }

        .ranking-title {
            color: #FFFFFF;
            font-size: 14px;
            font-weight: 800;
            margin-bottom: 3px;
        }

        .ranking-subtitle {
            color: #94A3B8;
            font-size: 12px;
        }

        [data-testid="stPlotlyChart"] {
            border: 1px solid rgba(34,211,238,.18) !important;
            border-radius: 18px !important;
            box-shadow:
                0 0 28px rgba(34,211,238,.05),
                inset 0 1px 0 rgba(255,255,255,.018) !important;
        }

        [data-testid="stDataFrame"] {
            border: 1px solid rgba(34,211,238,.24);
            border-radius: 18px;
            overflow: hidden;
            box-shadow:
                0 0 28px rgba(34,211,238,.055),
                0 12px 30px rgba(0,0,0,.16);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="servicos-context-card">
            <div class="servicos-context-title">Inteligência comercial por serviço e canal</div>
            <div class="servicos-context-subtitle">
                Identifique os serviços mais procurados e os canais que mais geram oportunidades.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

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

    st.markdown("## 📈 Visão Analítica")

    if leads.empty:
        st.markdown(
            """
            <div class="servicos-empty-card">
                <strong>Nenhum dado disponível ainda.</strong><br>
                Os gráficos de serviços e canais aparecerão nesta área assim que houver leads registradas.
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
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
        st.markdown(
            """
            <div class="ranking-card">
                <div class="ranking-title">Serviços</div>
                <div class="ranking-subtitle">
                    Volume de interesse por serviço.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if leads.empty:
            ranking_servicos = pd.DataFrame(
                columns=[
                    "Serviço",
                    "Quantidade",
                ]
            )
        else:
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
        st.markdown(
            """
            <div class="ranking-card">
                <div class="ranking-title">Canais</div>
                <div class="ranking-subtitle">
                    Distribuição das oportunidades por origem.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if leads.empty:
            ranking_canais = pd.DataFrame(
                columns=[
                    "Canal",
                    "Quantidade",
                ]
            )
        else:
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