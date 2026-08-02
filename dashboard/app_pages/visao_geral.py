import streamlit as st
import pandas as pd

from database.db import conectar
from components.graficos import grafico_donut


def buscar_dados_empresa(empresa_id):
    conn = conectar()
    try:
        leads = pd.read_sql_query(
            "SELECT * FROM leads WHERE empresa_id = %s ORDER BY id DESC",
            conn,
            params=(empresa_id,),
        )
        pedidos = pd.read_sql_query(
            "SELECT * FROM pedidos WHERE empresa_id = %s ORDER BY id DESC",
            conn,
            params=(empresa_id,),
        )
        produtos = pd.read_sql_query(
            "SELECT * FROM produtos WHERE empresa_id = %s ORDER BY id DESC",
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
        .top-card {background: linear-gradient(135deg, rgba(15,23,42,.96), rgba(2,6,23,.96)); border: 1px solid rgba(0,229,255,.20); border-radius: 22px; padding: 28px 32px; margin-bottom: 24px; box-shadow: 0 0 30px rgba(0,229,255,.05);}
        .top-title {font-size: 42px; font-weight: 900; color: #FFFFFF; margin-bottom: 6px;}
        .top-subtitle {color: #94A3B8; font-size: 15px;}
        .metric-card {background: linear-gradient(135deg, rgba(15,23,42,.96), rgba(30,41,59,.82)); border: 1px solid rgba(0,229,255,.16); border-radius: 18px; padding: 18px 20px; min-height: 105px; box-shadow: 0 0 18px rgba(0,229,255,.04);}
        .metric-label {color: #94A3B8; font-size: 13px; margin-bottom: 8px;}
        .metric-value {color: #FFFFFF; font-size: 30px; font-weight: 800;}
        .section-title {font-size: 30px; font-weight: 850; margin-top: 28px; margin-bottom: 16px; color: #FFFFFF;}
        .diagnostico-card {background: linear-gradient(135deg, rgba(30,41,59,.95), rgba(2,6,23,.96)); border-left: 5px solid #06B6D4; border-radius: 16px; padding: 22px; color: #E2E8F0; margin-top: 12px; line-height: 1.7;}
        </style>
    """, unsafe_allow_html=True)


def card(label, value):
    st.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>', unsafe_allow_html=True)


def topo(titulo, subtitulo):
    st.markdown(f'<div class="top-card"><div class="top-title">{titulo}</div><div class="top-subtitle">{subtitulo}</div></div>', unsafe_allow_html=True)


def calcular_metricas(leads, pedidos, produtos):
    total = len(leads)
    quentes = em_atendimento = aguardando = fechados = nao_fechados = 0

    if not leads.empty:
        if "temperatura" in leads.columns:
            quentes = len(leads[leads["temperatura"].astype(str).str.lower().str.contains("quente", na=False)])
        if "status" in leads.columns:
            status = leads["status"].astype(str).str.lower()
            em_atendimento = len(status[status.str.contains("em atendimento", na=False)])
            aguardando = len(status[status.str.contains("aguardando", na=False)])
            fechados = len(status[status.str.contains("fechado", na=False) & ~status.str.contains("não fechado|nao fechado", na=False)])
            nao_fechados = len(status[status.str.contains("não fechado|nao fechado", na=False)])

    valor_pedidos = 0
    if not pedidos.empty and "valor_total" in pedidos.columns:
        valor_pedidos = pedidos["valor_total"].fillna(0).sum()

    return {"total": total, "quentes": quentes, "em_atendimento": em_atendimento, "aguardando": aguardando, "fechados": fechados, "nao_fechados": nao_fechados, "pedidos": len(pedidos), "produtos": len(produtos), "valor_pedidos": valor_pedidos}


def render_graficos_leads(leads):
    if leads.empty:
        st.info("Nenhuma lead registrada ainda.")
        return
    g1, g2 = st.columns(2)
    with g1:
        if "status" in leads.columns:
            grafico_donut(leads, "status", "Status das Leads")
    with g2:
        if "temperatura" in leads.columns:
            grafico_donut(leads, "temperatura", "Temperatura das Leads")


def render_empresa_ativa():
    aplicar_css()

    empresa_id = st.session_state.get("empresa_ativa_id", st.session_state.get("empresa_id"))
    empresa_nome = st.session_state.get("empresa_ativa_nome", st.session_state.get("empresa"))

    leads, pedidos, produtos = buscar_dados_empresa(empresa_id)
    m = calcular_metricas(leads, pedidos, produtos)

    topo(
        f"🏠 Visão Geral — {empresa_nome}",
        "Painel operacional da empresa ativa, com indicadores de atendimento, leads e resultados comerciais.",
    )

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1: card("Total Leads", m["total"])
    with c2: card("🔥 Quentes", m["quentes"])
    with c3: card("🕘 Atendimento", m["em_atendimento"])
    with c4: card("⏳ Aguardando", m["aguardando"])
    with c5: card("✅ Fechados", m["fechados"])
    with c6: card("⚪ Não fechados", m["nao_fechados"])

    st.markdown('<div class="section-title">🔎 Diagnóstico Comercial</div>', unsafe_allow_html=True)

    if leads.empty:
        st.markdown('<div class="diagnostico-card">Ainda não existem dados suficientes para diagnóstico desta empresa.</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="diagnostico-card">A operação possui <strong>{m["total"]}</strong> leads registradas. Empresa analisada: <strong>{empresa_nome}</strong>.</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">📊 Analytics Comercial</div>', unsafe_allow_html=True)
    render_graficos_leads(leads)

    st.markdown('<div class="section-title">📈 Últimas Leads</div>', unsafe_allow_html=True)
    if leads.empty:
        st.info("Nenhuma lead cadastrada.")
    else:
        st.dataframe(leads.head(10), use_container_width=True, hide_index=True)


def render_visao_geral(leads_param=None):
    render_empresa_ativa()