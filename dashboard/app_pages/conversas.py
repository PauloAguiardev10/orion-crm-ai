import streamlit as st


def render_conversas(leads):

    st.title("💬 Conversas")

    if leads.empty:
        st.info("Nenhuma conversa encontrada.")
        return

    leads = leads.copy()

    colunas_padrao = {
        "id": 0,
        "produto": "Produto não informado",
        "origem": "WhatsApp",
        "canal": None,
        "responsavel": "Não atribuído",
        "score": 0,
        "temperatura": "Não informada",
        "status": "Aguardando atendimento",
        "historico": "",
        "resumo_vendedor": "",
    }

    for coluna, padrao in colunas_padrao.items():
        if coluna not in leads.columns:
            leads[coluna] = padrao

    if "canal" not in leads.columns or leads["canal"].isna().all():
        leads["canal"] = leads["origem"]

    leads["opcao_conversa"] = leads.apply(
        lambda row: f"#{row['id']} | {row['produto']} | {row['canal']}",
        axis=1
    )

    conversa_escolhida = st.selectbox(
        "Selecione uma conversa:",
        leads["opcao_conversa"].tolist()
    )

    lead = leads[
        leads["opcao_conversa"] == conversa_escolhida
    ].iloc[0]

    st.subheader(f"🧩 {lead['produto']}")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("Canal", lead["canal"])

    with c2:
        st.metric("Score", lead["score"])

    with c3:
        st.metric("Temperatura", lead["temperatura"])

    st.write(f"**Responsável:** {lead['responsavel']}")
    st.write(f"**Status:** {lead['status']}")

    st.markdown("---")

    st.markdown("## 🧠 Resumo Comercial")

    resumo = str(lead["resumo_vendedor"]).strip()

    if resumo and resumo.lower() not in ["none", "nan"]:
        st.info(resumo)
    else:
        st.info("Resumo ainda não disponível para esta conversa.")

    st.markdown("---")

    st.markdown("## 💬 Histórico da Conversa")

    historico = str(lead["historico"]).strip()

    if historico and historico.lower() not in ["none", "nan"]:
        st.text(historico)
    else:
        st.warning("Histórico real ainda não disponível para esta lead.")