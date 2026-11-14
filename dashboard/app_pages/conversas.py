import streamlit as st



from services.central_whatsapp_service import (
    listar_conversas_whatsapp,
    listar_mensagens_whatsapp,
)


def render_central_whatsapp():
    st.subheader("Central de Atendimento WhatsApp")
    st.caption("Conversas reais vinculadas ao usuario e a empresa.")

    usuario_id = st.session_state.get("usuario_id")
    empresa_id = st.session_state.get("empresa_id")
    nivel = st.session_state.get("nivel")

    if not usuario_id or not empresa_id:
        st.warning("Identificacao do usuario indisponivel.")
        return

    try:
        conversas = listar_conversas_whatsapp(
            empresa_id=int(empresa_id),
            usuario_id=int(usuario_id),
            nivel=str(nivel),
        )
    except Exception:
        st.error("Nao foi possivel consultar as conversas WhatsApp.")
        return

    if not conversas:
        st.info("Nenhuma conversa WhatsApp disponivel para este usuario.")
        return

    st.metric("Conversas disponiveis", len(conversas))

    for conversa in conversas:
        nome = conversa.get("nome") or conversa.get("identificador") or "Contato"
        vendedor = conversa.get("vendedor_nome") or "Nao atribuido"
        status = conversa.get("status_atendimento") or "Sem status"
        ultima = conversa.get("ultima_mensagem") or "Sem mensagens"

        with st.expander(f"{nome} | {status}"):
            st.write(f"**Vendedor:** {vendedor}")
            st.write(f"**WhatsApp:** {conversa.get('identificador') or 'Nao informado'}")
            st.write(f"**Ultima mensagem:** {ultima}")

            try:
                mensagens = listar_mensagens_whatsapp(
                    empresa_id=int(empresa_id),
                    usuario_id=int(usuario_id),
                    nivel=str(nivel),
                    conversa_id=int(conversa["id"]),
                )
            except Exception:
                st.error("Nao foi possivel carregar o historico.")
                continue

            st.markdown("**Historico de mensagens**")

            if not mensagens:
                st.info("Nenhuma mensagem registrada.")
                continue

            for mensagem in mensagens:
                remetente = (
                    "assistant"
                    if mensagem.get("from_me")
                    else "user"
                )

                texto = mensagem.get("texto") or ""

                with st.chat_message(remetente):
                    st.write(texto)

                    data = mensagem.get("criado_em")
                    if data:
                        st.caption(
                            data.strftime("%d/%m/%Y %H:%M")
                        )


def render_conversas(leads):
    render_central_whatsapp()


    st.title("💬 Conversas")

    st.markdown(
        """
        <style>
        .conversas-shell {
            background:
                radial-gradient(circle at 0% 0%, rgba(34,211,238,.08), transparent 36%),
                linear-gradient(145deg, rgba(15,23,42,.96), rgba(3,8,20,.95));
            border: 1px solid rgba(34,211,238,.22);
            border-radius: 18px;
            padding: 16px 18px;
            margin: 8px 0 18px 0;
            box-shadow: 0 0 26px rgba(34,211,238,.06);
        }

        .conversas-shell-title {
            color: #FFFFFF;
            font-size: 15px;
            font-weight: 800;
            margin-bottom: 4px;
        }

        .conversas-shell-subtitle {
            color: #94A3B8;
            font-size: 13px;
        }

        .conversa-empty {
            background:
                radial-gradient(circle at 50% 0%, rgba(99,102,241,.09), transparent 44%),
                linear-gradient(145deg, rgba(15,23,42,.96), rgba(3,8,20,.95));
            border: 1px dashed rgba(99,102,241,.38);
            border-radius: 18px;
            padding: 28px 20px;
            text-align: center;
            color: #CBD5E1;
            margin: 10px 0 18px 0;
            box-shadow: 0 0 24px rgba(99,102,241,.06);
        }

        .conversa-empty strong {
            color: #FFFFFF;
        }

        .conversa-info-card {
            background:
                linear-gradient(145deg, rgba(15,23,42,.97), rgba(3,8,20,.96));
            border: 1px solid rgba(34,211,238,.20);
            border-radius: 18px;
            padding: 18px;
            margin: 10px 0 18px 0;
            box-shadow: 0 0 24px rgba(34,211,238,.055);
        }

        .conversa-meta-line {
            color: #CBD5E1;
            font-size: 14px;
            margin-bottom: 7px;
        }

        .conversa-meta-line strong {
            color: #FFFFFF;
        }

        .conversa-resumo-card {
            background:
                radial-gradient(circle at 0% 0%, rgba(168,85,247,.10), transparent 38%),
                linear-gradient(145deg, rgba(15,23,42,.97), rgba(3,8,20,.96));
            border: 1px solid rgba(168,85,247,.26);
            border-left: 4px solid #A855F7;
            border-radius: 18px;
            padding: 18px 20px;
            margin: 8px 0 16px 0;
            box-shadow: 0 0 26px rgba(168,85,247,.07);
            color: #E2E8F0;
            line-height: 1.65;
        }

        .conversa-historico-card {
            background:
                radial-gradient(circle at 0% 0%, rgba(34,211,238,.08), transparent 38%),
                linear-gradient(145deg, rgba(15,23,42,.97), rgba(3,8,20,.96));
            border: 1px solid rgba(34,211,238,.24);
            border-left: 4px solid #22D3EE;
            border-radius: 18px;
            padding: 18px 20px;
            margin: 8px 0 16px 0;
            box-shadow: 0 0 26px rgba(34,211,238,.065);
            color: #E2E8F0;
            line-height: 1.6;
            white-space: pre-wrap;
        }

        [data-testid="stMetric"] {
            background:
                linear-gradient(145deg, rgba(15,23,42,.97), rgba(3,8,20,.96));
            border: 1px solid rgba(34,211,238,.24);
            border-radius: 18px;
            padding: 14px 16px;
            box-shadow: 0 0 24px rgba(34,211,238,.055);
        }

        [data-testid="stSelectbox"] > div > div {
            border-radius: 12px !important;
        }

        [data-testid="stSelectbox"] > div > div:focus-within {
            border-color: rgba(34,211,238,.68) !important;
            box-shadow:
                0 0 0 1px rgba(34,211,238,.16),
                0 0 18px rgba(34,211,238,.09) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="conversas-shell">
            <div class="conversas-shell-title">Central de conversas comerciais</div>
            <div class="conversas-shell-subtitle">
                Consulte o contexto da lead, indicadores, resumo comercial e histórico completo.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if leads.empty:
        st.markdown(
            """
            <div class="conversa-empty">
                <strong>Nenhuma conversa encontrada ainda.</strong><br>
                Quando uma lead iniciar atendimento, os dados aparecerão nesta estrutura.
            </div>
            """,
            unsafe_allow_html=True,
        )

        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric("Canal", "—")

        with c2:
            st.metric("Score", "0")

        with c3:
            st.metric("Temperatura", "—")

        st.markdown(
            """
            <div class="conversa-info-card">
                <div class="conversa-meta-line"><strong>Responsável:</strong> Não atribuído</div>
                <div class="conversa-meta-line"><strong>Status:</strong> Aguardando atendimento</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("## 🧠 Resumo Comercial")

        st.markdown(
            """
            <div class="conversa-resumo-card">
                Resumo ainda não disponível para esta conversa.
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("## 💬 Histórico da Conversa")

        st.markdown(
            """
            <div class="conversa-historico-card">
                Histórico real ainda não disponível.
            </div>
            """,
            unsafe_allow_html=True,
        )

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

    st.markdown(
        f"""
        <div class="conversa-info-card">
            <div class="conversa-meta-line">
                <strong>Responsável:</strong> {lead['responsavel']}
            </div>
            <div class="conversa-meta-line">
                <strong>Status:</strong> {lead['status']}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    st.markdown("## 🧠 Resumo Comercial")

    resumo = str(lead["resumo_vendedor"]).strip()

    if resumo and resumo.lower() not in ["none", "nan"]:
        st.markdown(
            f"""
            <div class="conversa-resumo-card">
                {resumo}
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="conversa-resumo-card">
                Resumo ainda não disponível para esta conversa.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    st.markdown("## 💬 Histórico da Conversa")

    historico = str(lead["historico"]).strip()

    if historico and historico.lower() not in ["none", "nan"]:
        st.markdown(
            f"""
            <div class="conversa-historico-card">
                {historico}
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="conversa-historico-card">
                Histórico real ainda não disponível para esta lead.
            </div>
            """,
            unsafe_allow_html=True,
        )
