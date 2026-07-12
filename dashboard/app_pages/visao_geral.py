import streamlit as st
import pandas as pd

from database.db import conectar
from components.graficos import grafico_donut


def buscar_empresas_permitidas():
    nivel = st.session_state.get("nivel")
    empresa_id = st.session_state.get("empresa_id")

    conn = conectar()

    try:
        if nivel == "orion_admin":
            empresas = pd.read_sql_query(
                """
                SELECT *
                FROM empresas
                ORDER BY id DESC
                """,
                conn,
            )

        elif nivel == "parceiro_admin":
            # Temporariamente mostra empresas ativas.
            # A coluna parceiro_nome ainda não existe no PostgreSQL.
            empresas = pd.read_sql_query(
                """
                SELECT *
                FROM empresas
                WHERE status = 'ativa'
                ORDER BY id DESC
                """,
                conn,
            )

        else:
            empresas = pd.read_sql_query(
                """
                SELECT *
                FROM empresas
                WHERE id = %s
                """,
                conn,
                params=(empresa_id,),
            )

        return empresas

    finally:
        conn.close()


def buscar_dados_empresa(empresa_id):
    conn = conectar()

    try:
        leads = pd.read_sql_query(
            """
            SELECT *
            FROM leads
            WHERE empresa_id = %s
            ORDER BY id DESC
            """,
            conn,
            params=(empresa_id,),
        )

        pedidos = pd.read_sql_query(
            """
            SELECT *
            FROM pedidos
            WHERE empresa_id = %s
            ORDER BY id DESC
            """,
            conn,
            params=(empresa_id,),
        )

        produtos = pd.read_sql_query(
            """
            SELECT *
            FROM produtos
            WHERE empresa_id = %s
            ORDER BY id DESC
            """,
            conn,
            params=(empresa_id,),
        )

        return leads, pedidos, produtos

    finally:
        conn.close()


def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def aplicar_css():
    st.markdown("""
        <style>
        .top-card {
            background: linear-gradient(135deg, rgba(15,23,42,.96), rgba(2,6,23,.96));
            border: 1px solid rgba(0,229,255,.20);
            border-radius: 22px;
            padding: 28px 32px;
            margin-bottom: 24px;
            box-shadow: 0 0 30px rgba(0,229,255,.05);
        }

        .top-title {
            font-size: 42px;
            font-weight: 900;
            color: #FFFFFF;
            margin-bottom: 6px;
        }

        .top-subtitle {
            color: #94A3B8;
            font-size: 15px;
        }

        .metric-card {
            background: linear-gradient(135deg, rgba(15,23,42,.96), rgba(30,41,59,.82));
            border: 1px solid rgba(0,229,255,.16);
            border-radius: 18px;
            padding: 18px 20px;
            min-height: 105px;
            box-shadow: 0 0 18px rgba(0,229,255,.04);
        }

        .metric-label {
            color: #94A3B8;
            font-size: 13px;
            margin-bottom: 8px;
        }

        .metric-value {
            color: #FFFFFF;
            font-size: 30px;
            font-weight: 800;
        }

        .section-title {
            font-size: 30px;
            font-weight: 850;
            margin-top: 28px;
            margin-bottom: 16px;
            color: #FFFFFF;
        }

        .insight-card {
            background: rgba(8,47,73,.55);
            border: 1px solid rgba(14,165,233,.22);
            border-radius: 16px;
            padding: 18px;
            margin-bottom: 12px;
            color: #E2E8F0;
        }

        .diagnostico-card {
            background: linear-gradient(135deg, rgba(30,41,59,.95), rgba(2,6,23,.96));
            border-left: 5px solid #06B6D4;
            border-radius: 16px;
            padding: 22px;
            color: #E2E8F0;
            margin-top: 12px;
            line-height: 1.7;
        }
        </style>
    """, unsafe_allow_html=True)


def card(label, value):
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
        </div>
    """, unsafe_allow_html=True)


def topo(titulo, subtitulo):
    st.markdown(f"""
        <div class="top-card">
            <div class="top-title">{titulo}</div>
            <div class="top-subtitle">{subtitulo}</div>
        </div>
    """, unsafe_allow_html=True)


def calcular_metricas(leads, pedidos, produtos):
    total = len(leads)
    quentes = 0
    em_atendimento = 0
    aguardando = 0
    fechados = 0
    nao_fechados = 0

    if not leads.empty:
        if "temperatura" in leads.columns:
            quentes = len(
                leads[
                    leads["temperatura"]
                    .astype(str)
                    .str.lower()
                    .str.contains("quente", na=False)
                ]
            )

        if "status" in leads.columns:
            status = leads["status"].astype(str).str.lower()

            em_atendimento = len(
                status[status.str.contains("em atendimento", na=False)]
            )

            aguardando = len(
                status[status.str.contains("aguardando", na=False)]
            )

            fechados = len(
                status[
                    status.str.contains("fechado", na=False)
                    & ~status.str.contains("não fechado|nao fechado", na=False)
                ]
            )

            nao_fechados = len(
                status[
                    status.str.contains("não fechado|nao fechado", na=False)
                ]
            )

    valor_pedidos = 0

    if not pedidos.empty and "valor_total" in pedidos.columns:
        valor_pedidos = pedidos["valor_total"].fillna(0).sum()

    return {
        "total": total,
        "quentes": quentes,
        "em_atendimento": em_atendimento,
        "aguardando": aguardando,
        "fechados": fechados,
        "nao_fechados": nao_fechados,
        "pedidos": len(pedidos),
        "produtos": len(produtos),
        "valor_pedidos": valor_pedidos,
    }


def render_graficos_leads(leads):
    if leads.empty:
        st.info("Nenhuma lead registrada ainda.")
        return

    g1, g2 = st.columns(2)

    with g1:
        if "status" in leads.columns:
            grafico_donut(
                leads,
                "status",
                "Status das Leads"
            )

    with g2:
        if "temperatura" in leads.columns:
            grafico_donut(
                leads,
                "temperatura",
                "Temperatura das Leads"
            )


def texto_diagnostico(m):
    palavra_lead = "lead" if m["aguardando"] == 1 else "leads"
    verbo = "está" if m["aguardando"] == 1 else "estão"

    return f"""
        <strong>A IA gerou {m["quentes"]} leads quentes.</strong><br><br>
        Porém, <strong>{m["aguardando"]} {palavra_lead}</strong> {verbo} aguardando atendimento humano.<br><br>
        <strong>Conclusão:</strong> existem oportunidades sendo geradas, mas parte delas pode estar sendo perdida por demora no atendimento.<br><br>
        <strong>Recomendação:</strong> oferecer upgrade para IA Vendas/Premium.
    """


def render_cliente():
    aplicar_css()

    empresa_id = st.session_state.get("empresa_id")
    empresa_nome = st.session_state.get("empresa")

    leads, pedidos, produtos = buscar_dados_empresa(empresa_id)
    m = calcular_metricas(leads, pedidos, produtos)

    topo(
        f"🏠 Visão Geral - {empresa_nome}",
        "Painel operacional com indicadores de atendimento, leads e resultados comerciais."
    )

    c1, c2, c3, c4, c5, c6 = st.columns(6)

    with c1:
        card("Total Leads", m["total"])
    with c2:
        card("🔥 Quentes", m["quentes"])
    with c3:
        card("🕘 Atendimento", m["em_atendimento"])
    with c4:
        card("⏳ Aguardando", m["aguardando"])
    with c5:
        card("✅ Fechados", m["fechados"])
    with c6:
        card("⚪ Não fechados", m["nao_fechados"])

    st.markdown(
        '<div class="section-title">🧠 Insights da Operação</div>',
        unsafe_allow_html=True
    )

    if leads.empty:
        st.markdown("""
            <div class="insight-card">
                Nenhuma lead registrada ainda. Assim que a Sofia começar os atendimentos,
                os dados aparecerão aqui automaticamente.
            </div>
        """, unsafe_allow_html=True)
    else:
        if m["aguardando"] > 0:
            st.markdown(f"""
                <div class="insight-card">
                    🚨 Existem <strong>{m["aguardando"]}</strong> leads aguardando atendimento humano.
                    Isso pode representar perda de oportunidades.
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class="insight-card">
                    ✅ Nenhum gargalo crítico identificado no atendimento humano.
                </div>
            """, unsafe_allow_html=True)

    st.markdown(
        '<div class="section-title">📊 Analytics Comercial</div>',
        unsafe_allow_html=True
    )

    render_graficos_leads(leads)

    st.markdown(
        '<div class="section-title">📈 Últimas Leads</div>',
        unsafe_allow_html=True
    )

    if leads.empty:
        st.info("Nenhuma lead cadastrada.")
    else:
        st.dataframe(
            leads.head(10),
            use_container_width=True,
            hide_index=True
        )


def render_admin_ou_parceiro():
    aplicar_css()

    nivel = st.session_state.get("nivel")

    titulo = (
        "🏠 Painel Master Orion"
        if nivel == "orion_admin"
        else "🏠 Painel Parceiro Forway"
    )

    topo(
        titulo,
        "Acompanhe clientes, indicadores, diagnósticos comerciais e oportunidades de upgrade."
    )

    empresas = buscar_empresas_permitidas()

    if empresas.empty:
        st.info("Nenhuma empresa encontrada.")
        return

    total_empresas = len(empresas)

    empresas_ativas = (
        len(empresas[empresas["status"] == "ativa"])
        if "status" in empresas
        else 0
    )

    empresas_vencidas = (
        len(empresas[empresas["status_financeiro"].isin(["vencido", "inadimplente"])])
        if "status_financeiro" in empresas
        else 0
    )

    receita_mensal = (
        empresas["valor_mensal"].fillna(0).sum()
        if "valor_mensal" in empresas
        else 0
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        card("Empresas", total_empresas)
    with c2:
        card("Ativas", empresas_ativas)
    with c3:
        card("Vencidas", empresas_vencidas)
    with c4:
        card("Receita Mensal", formatar_moeda(receita_mensal))

    st.markdown(
        '<div class="section-title">🏢 Diagnóstico por Cliente</div>',
        unsafe_allow_html=True
    )

    opcoes = {
        f"{row['id']} - {row['nome']}": row["id"]
        for _, row in empresas.iterrows()
    }

    opcoes_lista = list(opcoes.keys())

    empresa_salva_id = st.session_state.get("empresa_diagnostico_id")

    indice_atual = 0

    if empresa_salva_id:
        for i, opcao in enumerate(opcoes_lista):
            if int(opcoes[opcao]) == int(empresa_salva_id):
                indice_atual = i
                break

    empresa_escolhida = st.selectbox(
        "Selecionar cliente",
        opcoes_lista,
        index=indice_atual,
        key="diagnostico_cliente"
    )

    empresa_id = int(opcoes[empresa_escolhida])

    st.session_state["empresa_diagnostico_id"] = empresa_id

    empresa = empresas[
        empresas["id"] == empresa_id
    ].iloc[0]

    st.markdown(f"### Cliente selecionado: {empresa['nome']}")

    leads, pedidos, produtos = buscar_dados_empresa(empresa_id)
    m = calcular_metricas(leads, pedidos, produtos)

    d1, d2, d3, d4, d5, d6 = st.columns(6)

    with d1:
        card("Leads", m["total"])
    with d2:
        card("🔥 Quentes", m["quentes"])
    with d3:
        card("⏳ Aguardando", m["aguardando"])
    with d4:
        card("✅ Fechados", m["fechados"])
    with d5:
        card("⚪ Não fechados", m["nao_fechados"])
    with d6:
        card("Valor", formatar_moeda(m["valor_pedidos"]))

    st.markdown(
        '<div class="section-title">🔎 Diagnóstico Comercial</div>',
        unsafe_allow_html=True
    )

    if leads.empty:
        st.markdown("""
            <div class="diagnostico-card">
                Ainda não existem dados suficientes para diagnóstico deste cliente.
            </div>
        """, unsafe_allow_html=True)
    else:
        if m["aguardando"] > 0:
            st.markdown(
                (
                    '<div class="diagnostico-card">'
                    f'{texto_diagnostico(m)}'
                    '</div>'
                ),
                unsafe_allow_html=True
            )
        else:
            st.markdown(f"""
                <div class="diagnostico-card">
                    A operação possui <strong>{m["total"]}</strong> leads registradas.
                    Nenhum gargalo crítico de atendimento humano foi identificado no momento.
                </div>
            """, unsafe_allow_html=True)

    st.markdown(
        '<div class="section-title">📊 Gráficos do Cliente</div>',
        unsafe_allow_html=True
    )

    render_graficos_leads(leads)

    st.markdown(
        '<div class="section-title">📈 Leads do Cliente</div>',
        unsafe_allow_html=True
    )

    if leads.empty:
        st.info("Nenhum lead encontrado.")
    else:
        st.dataframe(
            leads,
            use_container_width=True,
            hide_index=True
        )


def render_visao_geral(leads_param=None):
    nivel = st.session_state.get("nivel")

    if nivel in ["orion_admin", "parceiro_admin"]:
        render_admin_ou_parceiro()
    else:
        render_cliente()