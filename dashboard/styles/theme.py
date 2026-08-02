import streamlit as st


def carregar_tema():
    st.markdown("""
    <style>
    html, body, [class*="css"] {
        background: radial-gradient(circle at top left, #111827 0%, #050816 45%, #020617 100%);
        color: #f8fafc;
    }

    .block-container {
        padding-top: 2.5rem !important;
        padding-bottom: 2rem;

    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #020617, #0f172a);
        border-right: 1px solid #1e293b;
    }

    /*
    Os títulos nativos criados com st.title() dentro das páginas são
    ocultados. O app.py renderiza um único título dinâmico e confiável.
    */
    [data-testid="stAppViewContainer"] h1 {
        display: none !important;
    }

    .orion-page-title {
        color: #FFFFFF;
        font-size: 2.55rem;
        line-height: 1.35;
        font-weight: 800;
        margin: 0.5rem 0 1.4rem 0;
        padding-top: 0.4rem;
        padding-bottom: 0.2rem;
        letter-spacing: -0.02em;
        overflow: visible;
    }

    .hero {
        background: linear-gradient(135deg, rgba(0,229,255,.20), rgba(124,58,237,.24));
        border: 1px solid rgba(0,229,255,.28);
        padding: 28px;
        border-radius: 24px;
        box-shadow: 0 0 45px rgba(0,229,255,.18);
        margin-bottom: 22px;
    }

    .hero h1 {
        font-size: 42px;
        margin-bottom: 5px;
    }

    .hero p {
        color: #cbd5e1;
        font-size: 16px;
    }

    .metric-card {
        background: linear-gradient(145deg, rgba(15,23,42,.95), rgba(2,6,23,.92));
        border: 1px solid rgba(0,229,255,.22);
        border-radius: 22px;
        padding: 22px;
        box-shadow:
            0 0 30px rgba(0,229,255,.10),
            inset 0 0 18px rgba(124,58,237,.06);
        transition: all .25s ease;
    }

    .metric-card:hover {
        transform: translateY(-3px);
        border-color: rgba(0,229,255,.45);
        box-shadow:
            0 0 45px rgba(0,229,255,.18),
            0 0 25px rgba(124,58,237,.12);
    }

    .metric-title {
        color: #94a3b8;
        font-size: 14px;
    }

    .metric-value {
        font-size: 34px;
        font-weight: 800;
        color: white;
    }

    .lead-card {
        background: linear-gradient(145deg, rgba(15,23,42,.96), rgba(17,24,39,.9));
        border: 1px solid rgba(148,163,184,.18);
        border-radius: 22px;
        padding: 22px;
        margin-bottom: 18px;
        box-shadow: 0 0 30px rgba(0,0,0,.30);
    }

    .lead-card:hover {
        border-color: rgba(0,229,255,.35);
        box-shadow: 0 0 35px rgba(0,229,255,.12);
    }

    .kanban-card {
        background: linear-gradient(145deg, #111827, #020617);
        border: 1px solid rgba(0,229,255,.18);
        border-radius: 18px;
        padding: 15px;
        margin-bottom: 12px;
        box-shadow: 0 0 18px rgba(0,229,255,.07);
    }

    .kanban-column {
        background: rgba(2, 6, 23, .72);
        border: 1px solid rgba(0,229,255,.18);
        border-radius: 20px;
        padding: 15px;
        min-height: 260px;
        box-shadow: 0 0 22px rgba(0,229,255,.06);
    }

    .client-msg {
        background: #1e293b;
        padding: 12px;
        border-radius: 14px;
        margin-bottom: 10px;
    }

    .agent-msg {
        background: linear-gradient(135deg, #2563eb, #7c3aed);
        padding: 12px;
        border-radius: 14px;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)