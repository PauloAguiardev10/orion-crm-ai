import streamlit as st
import pandas as pd

from components.graficos import grafico_donut


def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def melhor_valor(df, coluna):
    if df.empty or coluna not in df.columns:
        return "N/A"

    serie = df[coluna].dropna().astype(str)
    serie = serie[serie.str.strip() != ""]

    if serie.empty:
        return "N/A"

    contagem = serie.value_counts()

    if contagem.empty:
        return "N/A"

    return contagem.idxmax()


def card(titulo, valor, variante="cyan"):
    st.markdown(
        f"""
        <div class="metric-card metric-{variante}">
            <div class="metric-title">{titulo}</div>
            <div class="metric-value">{valor}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_resultados(leads):

    st.title("📌 Resultados Comerciais")

    st.markdown(
        """
        <style>
        .resultados-context-card {
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

        .resultados-context-card::before {
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

        .resultados-context-title {
            color: #FFFFFF;
            font-size: 15px;
            font-weight: 850;
            margin-left: 5px;
            margin-bottom: 4px;
        }

        .resultados-context-subtitle {
            color: #94A3B8;
            font-size: 13px;
            margin-left: 5px;
        }

        .metric-card {
            position: relative;
            overflow: hidden;
            background:
                radial-gradient(circle at 50% 100%, var(--metric-glow), transparent 64%),
                linear-gradient(145deg, rgba(15,23,42,.98), rgba(3,8,20,.96));
            border: 1px solid var(--metric-border);
            border-radius: 18px;
            padding: 18px 20px;
            min-height: 108px;
            box-shadow:
                0 0 26px var(--metric-glow),
                inset 0 1px 0 rgba(255,255,255,.02);
        }

        .metric-card::before {
            content: "";
            position: absolute;
            top: 0;
            left: 14px;
            right: 14px;
            height: 2px;
            border-radius: 999px;
            background: linear-gradient(90deg, transparent, var(--metric-accent), transparent);
            box-shadow: 0 0 10px var(--metric-accent);
            opacity: .72;
        }

        .metric-title {
            color: #A7B4C8;
            font-size: 13px;
            font-weight: 650;
            margin-bottom: 8px;
        }

        .metric-value {
            color: #FFFFFF;
            font-size: 28px;
            font-weight: 850;
        }

        .metric-cyan {
            --metric-accent: #22D3EE;
            --metric-border: rgba(34,211,238,.42);
            --metric-glow: rgba(34,211,238,.10);
        }

        .metric-red {
            --metric-accent: #EF4444;
            --metric-border: rgba(239,68,68,.40);
            --metric-glow: rgba(239,68,68,.09);
        }

        .metric-purple {
            --metric-accent: #A855F7;
            --metric-border: rgba(168,85,247,.42);
            --metric-glow: rgba(168,85,247,.10);
        }

        .metric-green {
            --metric-accent: #22C55E;
            --metric-border: rgba(34,197,94,.40);
            --metric-glow: rgba(34,197,94,.095);
        }

        .metric-amber {
            --metric-accent: #F59E0B;
            --metric-border: rgba(245,158,11,.40);
            --metric-glow: rgba(245,158,11,.09);
        }

        .metric-pink {
            --metric-accent: #EC4899;
            --metric-border: rgba(236,72,153,.40);
            --metric-glow: rgba(236,72,153,.09);
        }

        .insight-card {
            position: relative;
            overflow: hidden;
            background:
                radial-gradient(circle at 0% 0%, var(--insight-glow), transparent 42%),
                linear-gradient(145deg, rgba(15,23,42,.97), rgba(3,8,20,.96));
            border: 1px solid var(--insight-border);
            border-left: 4px solid var(--insight-accent);
            border-radius: 18px;
            padding: 18px 20px;
            color: #E2E8F0;
            box-shadow: 0 0 24px var(--insight-glow);
            min-height: 74px;
        }

        .insight-title {
            color: #FFFFFF;
            font-size: 14px;
            font-weight: 800;
            margin-bottom: 5px;
        }

        .insight-value {
            color: #CBD5E1;
            font-size: 14px;
        }

        .insight-green {
            --insight-accent: #22C55E;
            --insight-border: rgba(34,197,94,.28);
            --insight-glow: rgba(34,197,94,.07);
        }

        .insight-purple {
            --insight-accent: #A855F7;
            --insight-border: rgba(168,85,247,.28);
            --insight-glow: rgba(168,85,247,.07);
        }

        .resultados-empty-card {
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

        .resultados-empty-card strong {
            color: #FFFFFF;
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
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="resultados-context-card">
            <div class="resultados-context-title">Performance comercial consolidada</div>
            <div class="resultados-context-subtitle">
                Acompanhe conversão, receita, canais, serviços e desempenho da equipe.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    leads = leads.copy()

    colunas_padrao = {
        "status": "Aguardando atendimento",
        "produto": "Não informado",
        "responsavel": "Não atribuído",
        "canal": "Não informado",
        "origem": "Não informado",
        "valor_negocio": 0,
        "mensalidade": 0,
        "motivo_perda": "",
        "observacao_comercial": "",
    }

    for coluna, padrao in colunas_padrao.items():
        if coluna not in leads.columns:
            leads[coluna] = padrao

    if "canal" not in leads.columns or leads["canal"].isna().all():
        leads["canal"] = leads["origem"]

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

    valor_fechado = 0
    mensalidade_total = 0

    if "valor_negocio" in fechados_df.columns:
        valor_fechado = (
            pd.to_numeric(
                fechados_df["valor_negocio"],
                errors="coerce"
            )
            .fillna(0)
            .sum()
        )

    if "mensalidade" in fechados_df.columns:
        mensalidade_total = (
            pd.to_numeric(
                fechados_df["mensalidade"],
                errors="coerce"
            )
            .fillna(0)
            .sum()
        )

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

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        card("✅ Fechados", len(fechados_df), "green")

    with c2:
        card("⚪ Não fechados", len(nao_fechados_df), "red")

    with c3:
        card("📈 Conversão", f"{taxa}%", "purple")

    with c4:
        card("🏆 Melhor canal", melhor_canal, "cyan")

    st.markdown("<br>", unsafe_allow_html=True)

    f1, f2 = st.columns(2)

    with f1:
        card("💰 Valor Fechado", formatar_moeda(valor_fechado), "amber")

    with f2:
        card("🔁 Receita Mensal", formatar_moeda(mensalidade_total), "pink")

    st.markdown("## 🧠 Insights Comerciais")

    i1, i2 = st.columns(2)

    with i1:
        st.markdown(
            f"""
            <div class="insight-card insight-green">
                <div class="insight-title">🏆 Serviço campeão</div>
                <div class="insight-value">{melhor_servico}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with i2:
        st.markdown(
            f"""
            <div class="insight-card insight-purple">
                <div class="insight-title">👨‍💼 Especialista destaque</div>
                <div class="insight-value">{melhor_especialista}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("## ❌ Motivos de Perda")

    if not nao_fechados_df.empty and "motivo_perda" in nao_fechados_df.columns:

        motivos = (
            nao_fechados_df["motivo_perda"]
            .fillna("")
            .astype(str)
        )

        motivos = motivos[motivos.str.strip() != ""]

        if not motivos.empty:

            motivos_df = (
                motivos
                .value_counts()
                .reset_index()
            )

            motivos_df.columns = [
                "Motivo",
                "Quantidade"
            ]

            st.dataframe(
                motivos_df,
                use_container_width=True,
                hide_index=True
            )

        else:
            st.markdown(
                """
                <div class="resultados-empty-card">
                    Nenhum motivo de perda registrado até o momento.
                </div>
                """,
                unsafe_allow_html=True,
            )

    else:
        st.markdown(
            """
            <div class="resultados-empty-card">
                Nenhum motivo de perda registrado até o momento.
            </div>
            """,
            unsafe_allow_html=True,
        )

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

    else:
        st.markdown(
            """
            <div class="resultados-empty-card">
                <strong>Ainda não existem negócios fechados.</strong><br>
                Os gráficos de conversão aparecerão nesta área quando houver vendas concluídas.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("## 👨‍💼 Ranking Especialistas")

    if not fechados_df.empty:

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

    else:
        ranking = pd.DataFrame(
            columns=[
                "Especialista",
                "Fechamentos",
            ]
        )

    st.dataframe(
        ranking,
        use_container_width=True,
        hide_index=True
    )