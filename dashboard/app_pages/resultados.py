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


def card(titulo, valor):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">{titulo}</div>
            <div class="metric-value">{valor}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_resultados(leads):

    st.title("📌 Resultados Comerciais")

    if leads.empty:
        st.info("Nenhum dado disponível.")
        return

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

    with c1:
        card("✅ Fechados", len(fechados_df))
    with c2:
        card("⚪ Não fechados", len(nao_fechados_df))
    with c3:
        card("📈 Conversão", f"{taxa}%")
    with c4:
        card("🏆 Melhor canal", melhor_canal)

    st.markdown("<br>", unsafe_allow_html=True)

    f1, f2 = st.columns(2)

    with f1:
        card("💰 Valor Fechado", formatar_moeda(valor_fechado))

    with f2:
        card("🔁 Receita Mensal", formatar_moeda(mensalidade_total))

    st.markdown("## 🧠 Insights Comerciais")

    i1, i2 = st.columns(2)

    with i1:
        st.success(f"🏆 Serviço campeão: {melhor_servico}")

    with i2:
        st.info(f"👨‍💼 Especialista destaque: {melhor_especialista}")

    if not nao_fechados_df.empty and "motivo_perda" in nao_fechados_df.columns:

        motivos = (
            nao_fechados_df["motivo_perda"]
            .fillna("")
            .astype(str)
        )

        motivos = motivos[motivos.str.strip() != ""]

        if not motivos.empty:
            st.markdown("## ❌ Motivos de Perda")

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