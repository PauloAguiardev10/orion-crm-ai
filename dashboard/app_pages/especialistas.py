import streamlit as st

from components.graficos import grafico_donut


def valor_seguro(lead, coluna, padrao="Não informado"):
    try:
        valor = lead[coluna]

        if valor is None or str(valor).lower() in ["none", "nan", ""]:
            return padrao

        return valor

    except Exception:
        return padrao


def render_especialistas(leads):

    st.title("👨‍💼 Painel Especialistas")

    if leads.empty:
        st.info("Nenhuma lead encontrada.")
        return

    leads = leads.copy()

    colunas_padrao = {
        "nome": "Lead sem nome",
        "empresa": "Empresa não informada",
        "produto": "Produto não informado",
        "score": 0,
        "temperatura": "fria",
        "canal": None,
        "origem": "Não informado",
        "status": "Aguardando atendimento",
        "responsavel": "Não atribuído",
    }

    for coluna, padrao in colunas_padrao.items():
        if coluna not in leads.columns:
            leads[coluna] = padrao

    if "canal" not in leads.columns or leads["canal"].isna().all():
        leads["canal"] = leads["origem"]

    leads["responsavel"] = (
        leads["responsavel"]
        .fillna("Não atribuído")
        .astype(str)
    )

    responsaveis = sorted(
        leads["responsavel"]
        .unique()
        .tolist()
    )

    especialista = st.selectbox(
        "Selecione especialista:",
        responsaveis
    )

    leads_resp = leads[
        leads["responsavel"] == especialista
    ]

    total = len(leads_resp)

    status_normalizado = (
        leads_resp["status"]
        .fillna("")
        .astype(str)
        .str.lower()
    )

    atendimento = len(
        status_normalizado[
            status_normalizado.str.contains(
                "em atendimento",
                na=False
            )
        ]
    )

    propostas = len(
        status_normalizado[
            status_normalizado.str.contains(
                "proposta",
                na=False
            )
        ]
    )

    fechados = len(
        status_normalizado[
            status_normalizado.str.contains(
                "fechado",
                na=False
            )
        ]
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

        .lead-card {
            background: linear-gradient(135deg, rgba(15,23,42,.96), rgba(30,41,59,.88));
            border: 1px solid rgba(0,229,255,.16);
            border-radius: 18px;
            padding: 20px;
            margin-bottom: 16px;
            box-shadow: 0 0 18px rgba(0,229,255,.04);
        }

        .lead-title {
            color: #FFFFFF;
            font-size: 22px;
            font-weight: 800;
            margin-bottom: 8px;
        }

        .lead-line {
            color: #CBD5E1;
            font-size: 15px;
            margin-bottom: 5px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    c1, c2, c3, c4 = st.columns(4)

    metricas = [
        ("Total Leads", total),
        ("🕒 Em atendimento", atendimento),
        ("📨 Propostas", propostas),
        ("✅ Fechados", fechados)
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

    st.markdown("## 📊 Performance")

    if leads_resp.empty:
        st.info("Nenhuma lead atribuída para este especialista.")
    else:
        g1, g2 = st.columns(2)

        with g1:
            grafico_donut(
                leads_resp,
                "status",
                "Pipeline Especialista"
            )

        with g2:
            grafico_donut(
                leads_resp,
                "produto",
                "Serviços Atendidos"
            )

    st.markdown("## 📋 Leads")

    if leads_resp.empty:
        st.info("Nenhuma lead encontrada para este especialista.")
        return

    for _, lead in leads_resp.iterrows():

        nome = valor_seguro(lead, "nome", "Lead sem nome")
        empresa = valor_seguro(lead, "empresa", "Empresa não informada")
        produto = valor_seguro(lead, "produto", "Produto não informado")
        score = valor_seguro(lead, "score", 0)
        temperatura = valor_seguro(lead, "temperatura", "fria")
        canal = valor_seguro(lead, "canal", "Não informado")
        status = valor_seguro(lead, "status", "Aguardando atendimento")

        st.markdown(
            f"""
            <div class="lead-card">
                <div class="lead-title">{nome}</div>
                <div class="lead-line">🏢 {empresa}</div>
                <div class="lead-line">🧩 {produto}</div>
                <div class="lead-line">📊 Score {score}</div>
                <div class="lead-line">🔥 {temperatura}</div>
                <div class="lead-line">📲 {canal}</div>
                <div class="lead-line">📌 {status}</div>
            </div>
            """,
            unsafe_allow_html=True
        )