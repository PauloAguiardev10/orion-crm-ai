import streamlit as st

from services.leads_service import (
    atualizar_lead,
    STATUS_LISTA
)

from services.configuracoes_service import (
    carregar_especialistas
)


def valor_seguro(lead, coluna, padrao="Não informado"):
    try:
        valor = lead[coluna]
        if valor is None or str(valor).lower() in ["none", "nan", ""]:
            return padrao
        return valor
    except Exception:
        return padrao


def render_leads(leads):

    st.title("📋 Leads")

    if leads.empty:
        st.info("Nenhuma lead encontrada.")
        return

    leads = leads.copy()

    colunas_padrao = {
        "nome": "Lead sem nome",
        "empresa": "Empresa não informada",
        "telefone": "Não informado",
        "canal": None,
        "origem": "Não informado",
        "produto": "Não identificado",
        "temperatura": "fria",
        "score": 0,
        "status": "Aguardando atendimento",
        "responsavel": "Não atribuído",
        "resumo_vendedor": "",
        "historico": "",
    }

    for coluna, padrao in colunas_padrao.items():
        if coluna not in leads.columns:
            leads[coluna] = padrao

    if "canal" not in leads.columns or leads["canal"].isna().all():
        leads["canal"] = leads["origem"]

    leads["status_normalizado"] = (
        leads["status"]
        .fillna("Aguardando atendimento")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    especialistas_df = carregar_especialistas(
        st.session_state.get("empresa_id", 1)
    )

    responsaveis = (
        especialistas_df["nome"].tolist()
        if not especialistas_df.empty and "nome" in especialistas_df.columns
        else ["Não atribuído"]
    )

    if "Não atribuído" not in responsaveis:
        responsaveis.insert(0, "Não atribuído")

    st.markdown("## 🔎 Filtros")

    f1, f2, f3, f4 = st.columns(4)

    with f1:
        filtro_status = st.selectbox(
            "Status",
            ["Todos"] + STATUS_LISTA
        )

    with f2:
        canais = sorted(
            leads["canal"]
            .fillna("Não informado")
            .astype(str)
            .unique()
            .tolist()
        )

        filtro_canal = st.selectbox(
            "Canal",
            ["Todos"] + canais
        )

    with f3:
        filtro_responsavel = st.selectbox(
            "Responsável",
            ["Todos"] + responsaveis
        )

    with f4:
        busca = st.text_input("Buscar nome/empresa/produto")

    leads_filtradas = leads.copy()

    if filtro_status != "Todos":
        filtro_status_normalizado = filtro_status.strip().lower()

        leads_filtradas = leads_filtradas[
            leads_filtradas["status_normalizado"].str.contains(
                filtro_status_normalizado,
                na=False
            )
        ]

    if filtro_canal != "Todos":
        leads_filtradas = leads_filtradas[
            leads_filtradas["canal"].astype(str) == filtro_canal
        ]

    if filtro_responsavel != "Todos":
        leads_filtradas = leads_filtradas[
            leads_filtradas["responsavel"].astype(str) == filtro_responsavel
        ]

    if busca:
        busca = busca.lower()

        leads_filtradas = leads_filtradas[
            leads_filtradas["nome"].fillna("").astype(str).str.lower().str.contains(busca, na=False)
            |
            leads_filtradas["empresa"].fillna("").astype(str).str.lower().str.contains(busca, na=False)
            |
            leads_filtradas["produto"].fillna("").astype(str).str.lower().str.contains(busca, na=False)
        ]

    st.markdown("---")

    if leads_filtradas.empty:
        st.warning("Nenhuma lead encontrada nos filtros.")
        return

    st.markdown(
        """
        <style>
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

    for _, lead in leads_filtradas.iterrows():

        lead_id = valor_seguro(lead, "id", "0")
        nome = valor_seguro(lead, "nome", "Lead sem nome")
        empresa = valor_seguro(lead, "empresa", "Empresa não informada")
        telefone = valor_seguro(lead, "telefone", "Não informado")
        canal = valor_seguro(lead, "canal", "Não informado")
        produto = valor_seguro(lead, "produto", "Não identificado")
        temperatura = valor_seguro(lead, "temperatura", "fria")
        score = valor_seguro(lead, "score", 0)
        status_atual = valor_seguro(lead, "status", "Aguardando atendimento")
        responsavel_atual = valor_seguro(lead, "responsavel", "Não atribuído")

        st.markdown(
            f"""
            <div class="lead-card">
                <div class="lead-title">#{lead_id} - {nome}</div>
                <div class="lead-line">🏢 {empresa}</div>
                <div class="lead-line">📲 {telefone}</div>
                <div class="lead-line">📡 {canal}</div>
                <div class="lead-line">🧩 {produto}</div>
                <div class="lead-line">🔥 {temperatura} • Score {score}</div>
                <div class="lead-line">📌 {status_atual}</div>
                <div class="lead-line">👨‍💼 {responsavel_atual}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        c1, c2 = st.columns(2)

        with c1:
            novo_status = st.selectbox(
                f"Status Lead #{lead_id}",
                STATUS_LISTA,
                index=STATUS_LISTA.index(status_atual)
                if status_atual in STATUS_LISTA
                else 0,
                key=f"status_{lead_id}"
            )

        with c2:
            responsavel = st.selectbox(
                f"Responsável Lead #{lead_id}",
                responsaveis,
                index=responsaveis.index(responsavel_atual)
                if responsavel_atual in responsaveis
                else 0,
                key=f"responsavel_{lead_id}"
            )

        if st.button(
            f"Salvar Lead #{lead_id}",
            key=f"salvar_{lead_id}"
        ):
            atualizar_lead(
                lead_id,
                novo_status,
                responsavel
            )

            st.success("Lead atualizada com sucesso.")
            st.rerun()

        resumo = valor_seguro(lead, "resumo_vendedor", "")

        with st.expander("🧠 Resumo Comercial"):
            if resumo:
                st.text(resumo)
            else:
                st.info("Resumo não disponível.")

        historico = valor_seguro(lead, "historico", "")

        if historico:
            with st.expander("💬 Conversa da Sofia"):
                st.text(historico)

        st.markdown("<br>", unsafe_allow_html=True)