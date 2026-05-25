import streamlit as st

from services.leads_service import STATUS_LISTA


def valor_seguro(lead, coluna, padrao="Não informado"):
    try:
        valor = lead[coluna]

        if valor is None or str(valor).lower() in ["none", "nan", ""]:
            return padrao

        return valor

    except Exception:
        return padrao


def render_funil(leads):

    st.title("🔥 Funil Comercial")

    if leads.empty:
        st.info("Nenhuma lead encontrada.")
        return

    leads = leads.copy()

    colunas_padrao = {
        "nome": "Lead sem nome",
        "produto": "Produto não informado",
        "temperatura": "fria",
        "score": 0,
        "responsavel": "Não atribuído",
        "canal": None,
        "origem": "Não informado",
        "status": "Aguardando atendimento",
    }

    for coluna, padrao in colunas_padrao.items():
        if coluna not in leads.columns:
            leads[coluna] = padrao

    if "canal" not in leads.columns or leads["canal"].isna().all():
        leads["canal"] = leads["origem"]

    st.markdown(
        """
        <style>
        .kanban-column {
            background: linear-gradient(135deg, rgba(15,23,42,.96), rgba(30,41,59,.82));
            border: 1px solid rgba(0,229,255,.16);
            border-radius: 18px;
            padding: 16px;
            min-height: 130px;
            margin-bottom: 14px;
            box-shadow: 0 0 18px rgba(0,229,255,.04);
        }

        .kanban-title {
            color: #FFFFFF;
            font-size: 17px;
            font-weight: 800;
            margin-bottom: 10px;
        }

        .kanban-count {
            color: #CBD5E1;
            font-size: 14px;
        }

        .kanban-card {
            background: rgba(30,41,59,.95);
            border: 1px solid rgba(148,163,184,.14);
            border-radius: 16px;
            padding: 14px;
            margin-bottom: 12px;
            color: #E2E8F0;
            font-size: 14px;
        }

        .kanban-card-title {
            color: #FFFFFF;
            font-weight: 800;
            font-size: 15px;
            margin-bottom: 8px;
        }

        .kanban-line {
            margin-bottom: 6px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    cols = st.columns(len(STATUS_LISTA))

    for col, status in zip(cols, STATUS_LISTA):

        with col:

            subset = leads[
                leads["status"]
                .fillna("")
                .astype(str)
                .str.lower()
                .str.contains(status.lower(), na=False)
            ]

            st.markdown(
                f"""
                <div class="kanban-column">
                    <div class="kanban-title">{status}</div>
                    <div class="kanban-count">{len(subset)} lead(s)</div>
                </div>
                """,
                unsafe_allow_html=True
            )

            for _, lead in subset.iterrows():

                temperatura = str(
                    valor_seguro(
                        lead,
                        "temperatura",
                        "fria"
                    )
                ).lower()

                emoji = "🔥"

                if "morna" in temperatura:
                    emoji = "⚡"

                elif "fria" in temperatura:
                    emoji = "❄️"

                nome = valor_seguro(lead, "nome", "Lead sem nome")
                produto = valor_seguro(lead, "produto", "Produto não informado")
                score = valor_seguro(lead, "score", 0)
                responsavel = valor_seguro(lead, "responsavel", "Não atribuído")
                canal = valor_seguro(lead, "canal", "Não informado")

                st.markdown(
                    f"""
                    <div class="kanban-card">
                        <div class="kanban-card-title">{nome}</div>
                        <div class="kanban-line">🧩 {produto}</div>
                        <div class="kanban-line">{emoji} {temperatura}</div>
                        <div class="kanban-line">📊 Score {score}</div>
                        <div class="kanban-line">👨‍💼 {responsavel}</div>
                        <div class="kanban-line">📲 {canal}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )