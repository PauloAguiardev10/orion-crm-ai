import streamlit as st

from services.leads_service import (
    atualizar_lead,
    STATUS_LISTA
)

from services.configuracoes_service import (
    carregar_especialistas
)


MOTIVOS_PERDA = [
    "Sem orçamento",
    "Sem interesse",
    "Fechou com concorrente",
    "Não respondeu",
    "Momento errado",
    "Outro motivo"
]


def valor_seguro(lead, coluna, padrao="Não informado"):
    try:
        valor = lead[coluna]
        if valor is None or str(valor).lower() in ["none", "nan", ""]:
            return padrao
        return valor
    except Exception:
        return padrao


def normalizar_status(status):
    status = str(status).strip().lower()

    if "aguardando" in status:
        return "Aguardando atendimento"

    if status == "em" or "em atendimento" in status:
        return "Em atendimento"

    if "proposta" in status:
        return "Proposta enviada"

    if "não fechado" in status or "nao fechado" in status:
        return "Não fechado"

    if "fechado" in status:
        return "Negócio fechado"

    return "Aguardando atendimento"


def render_leads(leads):

    st.title("📋 Leads")

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

    leads["status"] = leads["status"].apply(normalizar_status)

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

    st.markdown(
        """
        <style>
        .leads-context-card {
            background:
                radial-gradient(circle at 0% 0%, rgba(34,211,238,.09), transparent 38%),
                linear-gradient(145deg, rgba(15,23,42,.97), rgba(3,8,20,.96));
            border: 1px solid rgba(34,211,238,.24);
            border-radius: 18px;
            padding: 16px 18px;
            margin: 8px 0 18px 0;
            box-shadow: 0 0 26px rgba(34,211,238,.065);
        }

        .leads-context-title {
            color: #FFFFFF;
            font-size: 15px;
            font-weight: 800;
            margin-bottom: 4px;
        }

        .leads-context-subtitle {
            color: #94A3B8;
            font-size: 13px;
        }

        .leads-empty-card {
            background:
                radial-gradient(circle at 50% 0%, rgba(99,102,241,.09), transparent 44%),
                linear-gradient(145deg, rgba(15,23,42,.96), rgba(3,8,20,.95));
            border: 1px dashed rgba(99,102,241,.40);
            border-radius: 18px;
            padding: 28px 20px;
            margin: 12px 0 18px 0;
            text-align: center;
            color: #CBD5E1;
            box-shadow: 0 0 24px rgba(99,102,241,.06);
        }

        .leads-empty-card strong {
            color: #FFFFFF;
        }

        .lead-card {
            position: relative;
            overflow: hidden;
            background:
                radial-gradient(circle at 0% 0%, rgba(34,211,238,.08), transparent 40%),
                radial-gradient(circle at 100% 100%, rgba(168,85,247,.055), transparent 38%),
                linear-gradient(145deg, rgba(15,23,42,.98), rgba(3,8,20,.96));
            border: 1px solid rgba(34,211,238,.27);
            border-radius: 18px;
            padding: 20px 20px 20px 22px;
            margin-bottom: 16px;
            box-shadow:
                0 0 28px rgba(34,211,238,.07),
                0 12px 28px rgba(0,0,0,.16);
            transition: transform .18s ease, border-color .18s ease, box-shadow .18s ease;
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

        .lead-card:hover {
            transform: translateY(-2px);
            border-color: rgba(34,211,238,.48);
            box-shadow:
                0 0 36px rgba(34,211,238,.12),
                0 14px 32px rgba(0,0,0,.20);
        }

        .lead-title {
            color: #FFFFFF;
            font-size: 22px;
            font-weight: 850;
            margin-bottom: 10px;
            letter-spacing: -0.015em;
            text-shadow: 0 0 18px rgba(34,211,238,.08);
        }

        .lead-line {
            color: #CBD5E1;
            font-size: 14px;
            margin-bottom: 6px;
        }

        [data-testid="stSelectbox"] > div > div,
        [data-testid="stTextInput"] > div > div,
        [data-testid="stNumberInput"] > div > div,
        [data-testid="stTextArea"] textarea {
            border-radius: 12px !important;
        }

        [data-testid="stSelectbox"] > div > div:focus-within,
        [data-testid="stTextInput"] > div > div:focus-within,
        [data-testid="stNumberInput"] > div > div:focus-within,
        [data-testid="stTextArea"] textarea:focus {
            border-color: rgba(34,211,238,.68) !important;
            box-shadow:
                0 0 0 1px rgba(34,211,238,.15),
                0 0 18px rgba(34,211,238,.09) !important;
        }

        [data-testid="stExpander"] {
            border-color: rgba(34,211,238,.20) !important;
            box-shadow: 0 0 22px rgba(34,211,238,.045);
        }

        div[data-testid="stButton"] > button {
            border-radius: 12px !important;
            transition: transform .18s ease, border-color .18s ease, box-shadow .18s ease;
        }

        div[data-testid="stButton"] > button:hover {
            transform: translateY(-1px);
            border-color: rgba(34,211,238,.62) !important;
            box-shadow: 0 0 18px rgba(34,211,238,.12) !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="leads-context-card">
            <div class="leads-context-title">Gestão comercial de leads</div>
            <div class="leads-context-subtitle">
                Filtre oportunidades, acompanhe score e temperatura e atualize o andamento comercial.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if leads_filtradas.empty:
        mensagem_vazia = (
            "Nenhuma lead registrada ainda."
            if leads.empty
            else "Nenhuma lead encontrada com os filtros selecionados."
        )

        st.markdown(
            f"""
            <div class="leads-empty-card">
                <strong>{mensagem_vazia}</strong><br>
                A estrutura da gestão permanece disponível e será preenchida automaticamente quando houver oportunidades.
            </div>
            """,
            unsafe_allow_html=True,
        )
        return


    for _, lead in leads_filtradas.iterrows():

        lead_id = valor_seguro(lead, "id", "0")
        nome = valor_seguro(lead, "nome", "Lead sem nome")
        empresa = valor_seguro(lead, "empresa", "Empresa não informada")
        telefone = valor_seguro(lead, "telefone", "Não informado")
        canal = valor_seguro(lead, "canal", "Não informado")
        produto = valor_seguro(lead, "produto", "Não identificado")
        temperatura = valor_seguro(lead, "temperatura", "fria")
        score = valor_seguro(lead, "score", 0)

        status_atual = normalizar_status(
            valor_seguro(
                lead,
                "status",
                "Aguardando atendimento"
            )
        )

        responsavel_atual = valor_seguro(
            lead,
            "responsavel",
            "Não atribuído"
        )

        valor_atual = valor_seguro(
            lead,
            "valor_negocio",
            0
        )

        mensalidade_atual = valor_seguro(
            lead,
            "mensalidade",
            0
        )

        motivo_perda_atual = valor_seguro(
            lead,
            "motivo_perda",
            ""
        )

        observacao_atual = valor_seguro(
            lead,
            "observacao_comercial",
            ""
        )

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

        valor_negocio = float(valor_atual or 0)
        mensalidade = float(mensalidade_atual or 0)
        motivo_perda = str(motivo_perda_atual or "")
        observacao_comercial = str(observacao_atual or "")

        if novo_status == "Negócio fechado":

            st.markdown("### 💰 Dados do negócio fechado")

            n1, n2 = st.columns(2)

            with n1:
                valor_negocio = st.number_input(
                    f"Valor do contrato Lead #{lead_id}",
                    min_value=0.0,
                    value=float(valor_atual or 0),
                    step=100.0,
                    key=f"valor_negocio_{lead_id}"
                )

            with n2:
                mensalidade = st.number_input(
                    f"Mensalidade Lead #{lead_id}",
                    min_value=0.0,
                    value=float(mensalidade_atual or 0),
                    step=100.0,
                    key=f"mensalidade_{lead_id}"
                )

            motivo_perda = ""

        elif novo_status == "Não fechado":

            st.markdown("### ❌ Motivo da perda")

            index_motivo = (
                MOTIVOS_PERDA.index(motivo_perda_atual)
                if motivo_perda_atual in MOTIVOS_PERDA
                else 0
            )

            motivo_perda = st.selectbox(
                f"Motivo da perda Lead #{lead_id}",
                MOTIVOS_PERDA,
                index=index_motivo,
                key=f"motivo_perda_{lead_id}"
            )

            observacao_comercial = st.text_area(
                f"Observação comercial Lead #{lead_id}",
                value=str(observacao_atual or ""),
                key=f"observacao_comercial_{lead_id}"
            )

            valor_negocio = 0
            mensalidade = 0

        else:
            motivo_perda = ""
            valor_negocio = float(valor_atual or 0)
            mensalidade = float(mensalidade_atual or 0)
            observacao_comercial = str(observacao_atual or "")

        if st.button(
            f"Salvar Lead #{lead_id}",
            key=f"salvar_{lead_id}"
        ):
            atualizar_lead(
                lead_id,
                normalizar_status(novo_status),
                responsavel,
                valor_negocio,
                mensalidade,
                motivo_perda,
                observacao_comercial
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