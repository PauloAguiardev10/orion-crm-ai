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

    st.markdown(
        """
        <style>
        .especialistas-context-card {
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

        .especialistas-context-card::before {
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

        .especialistas-context-title {
            color: #FFFFFF;
            font-size: 15px;
            font-weight: 850;
            margin-left: 5px;
            margin-bottom: 4px;
        }

        .especialistas-context-subtitle {
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
            font-size: 29px;
            font-weight: 850;
        }

        .metric-cyan {
            --metric-accent: #22D3EE;
            --metric-border: rgba(34,211,238,.42);
            --metric-glow: rgba(34,211,238,.10);
        }

        .metric-purple {
            --metric-accent: #6366F1;
            --metric-border: rgba(99,102,241,.42);
            --metric-glow: rgba(99,102,241,.10);
        }

        .metric-pink {
            --metric-accent: #D946EF;
            --metric-border: rgba(217,70,239,.40);
            --metric-glow: rgba(217,70,239,.095);
        }

        .metric-green {
            --metric-accent: #22C55E;
            --metric-border: rgba(34,197,94,.40);
            --metric-glow: rgba(34,197,94,.095);
        }

        .especialista-empty-card {
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

        .especialista-empty-card strong {
            color: #FFFFFF;
        }

        .lead-card {
            position: relative;
            overflow: hidden;
            background:
                radial-gradient(circle at 0% 0%, rgba(34,211,238,.08), transparent 40%),
                linear-gradient(145deg, rgba(15,23,42,.98), rgba(3,8,20,.96));
            border: 1px solid rgba(34,211,238,.26);
            border-radius: 18px;
            padding: 20px 20px 20px 22px;
            margin-bottom: 16px;
            box-shadow:
                0 0 28px rgba(34,211,238,.07),
                0 12px 28px rgba(0,0,0,.16);
        }

        .lead-card::before {
            content: "";
            position: absolute;
            left: 0;
            top: 14px;
            bottom: 14px;
            width: 3px;
            border-radius: 999px;
            background: linear-gradient(180deg, #67E8F9, #22D3EE, #6366F1);
            box-shadow: 0 0 12px rgba(34,211,238,.78);
        }

        .lead-title {
            color: #FFFFFF;
            font-size: 21px;
            font-weight: 850;
            margin-bottom: 9px;
            letter-spacing: -0.01em;
        }

        .lead-line {
            color: #CBD5E1;
            font-size: 14px;
            margin-bottom: 6px;
        }

        [data-testid="stSelectbox"] > div > div {
            border-radius: 12px !important;
        }

        [data-testid="stSelectbox"] > div > div:focus-within {
            border-color: rgba(34,211,238,.68) !important;
            box-shadow:
                0 0 0 1px rgba(34,211,238,.15),
                0 0 18px rgba(34,211,238,.09) !important;
        }

        [data-testid="stPlotlyChart"] {
            border-color: rgba(34,211,238,.17) !important;
            box-shadow:
                0 0 28px rgba(34,211,238,.045),
                inset 0 1px 0 rgba(255,255,255,.018) !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="especialistas-context-card">
            <div class="especialistas-context-title">Performance da equipe comercial</div>
            <div class="especialistas-context-subtitle">
                Acompanhe volume de leads, atendimentos, propostas e negócios por responsável.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

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

    if leads.empty:
        responsaveis = ["Não atribuído"]
    else:
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

    c1, c2, c3, c4 = st.columns(4)

    metricas = [
        ("Total Leads", total, "cyan"),
        ("🕒 Em atendimento", atendimento, "purple"),
        ("📨 Propostas", propostas, "pink"),
        ("✅ Fechados", fechados, "green")
    ]

    for col, (titulo, valor, variante) in zip([c1, c2, c3, c4], metricas):
        with col:
            st.markdown(
                f"""
                <div class="metric-card metric-{variante}">
                    <div class="metric-title">{titulo}</div>
                    <div class="metric-value">{valor}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown("## 📊 Performance")

    if leads_resp.empty:
        st.markdown(
            """
            <div class="especialista-empty-card">
                <strong>Nenhuma lead atribuída para este especialista.</strong><br>
                Os gráficos permanecerão disponíveis assim que houver movimentação comercial.
            </div>
            """,
            unsafe_allow_html=True,
        )
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
        st.markdown(
            """
            <div class="especialista-empty-card">
                <strong>Nenhuma lead encontrada para este especialista.</strong><br>
                Os cards de oportunidades aparecerão nesta área quando houver atribuições.
            </div>
            """,
            unsafe_allow_html=True,
        )
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