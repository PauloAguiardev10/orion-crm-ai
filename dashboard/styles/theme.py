import streamlit as st


def carregar_tema():
    st.markdown("""
    <style>
    :root {
        --orion-bg-0: #020617;
        --orion-bg-1: #050816;
        --orion-bg-2: #0B1224;
        --orion-panel: rgba(10, 18, 36, .94);
        --orion-panel-2: rgba(15, 23, 42, .92);
        --orion-border: rgba(103, 232, 249, .18);
        --orion-cyan: #22D3EE;
        --orion-blue: #3B82F6;
        --orion-purple: #A855F7;
        --orion-pink: #EC4899;
        --orion-green: #22C55E;
        --orion-amber: #F59E0B;
        --orion-red: #EF4444;
        --orion-text: #F8FAFC;
        --orion-muted: #94A3B8;
    }

    html, body, [class*="css"] {
        background:
            radial-gradient(circle at 8% 0%, rgba(34,211,238,.08), transparent 28%),
            radial-gradient(circle at 92% 8%, rgba(168,85,247,.07), transparent 30%),
            linear-gradient(180deg, #07101F 0%, #040916 45%, #020617 100%);
        color: var(--orion-text);
    }

    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(circle at 20% 5%, rgba(59,130,246,.05), transparent 28%),
            radial-gradient(circle at 82% 12%, rgba(168,85,247,.04), transparent 24%),
            linear-gradient(180deg, #07101F 0%, #030817 48%, #020617 100%);
    }

    [data-testid="stHeader"] {
        background: rgba(2,6,23,.72);
        backdrop-filter: blur(12px);
    }

    .block-container {
        padding-top: 2.2rem !important;
        padding-bottom: 3rem;
        max-width: 1560px;
    }

    [data-testid="stSidebar"] {
        background:
            radial-gradient(circle at 50% 0%, rgba(34,211,238,.06), transparent 28%),
            linear-gradient(180deg, #020617 0%, #07101F 52%, #030817 100%);
        border-right: 1px solid rgba(34,211,238,.13);
        box-shadow: 12px 0 40px rgba(0,0,0,.26);
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        color: #E2E8F0;
    }

    [data-testid="stSidebar"] button,
    [data-testid="stSidebar"] [role="button"] {
        transition: all .2s ease;
    }

    [data-testid="stAppViewContainer"] h1 {
        display: none !important;
    }

    .orion-page-title {
        color: #FFFFFF;
        font-size: 2.55rem;
        line-height: 1.35;
        font-weight: 850;
        margin: 0.5rem 0 1.4rem 0;
        padding-top: 0.4rem;
        padding-bottom: 0.2rem;
        letter-spacing: -0.025em;
        overflow: visible;
        text-shadow: 0 0 24px rgba(34,211,238,.10);
    }

    .hero {
        position: relative;
        overflow: hidden;
        background:
            radial-gradient(circle at 0% 0%, rgba(34,211,238,.16), transparent 34%),
            radial-gradient(circle at 100% 0%, rgba(168,85,247,.14), transparent 35%),
            linear-gradient(135deg, rgba(12,22,43,.98), rgba(5,10,25,.96));
        border: 1px solid rgba(34,211,238,.28);
        padding: 28px;
        border-radius: 24px;
        box-shadow:
            0 0 0 1px rgba(255,255,255,.02) inset,
            0 0 38px rgba(34,211,238,.10),
            0 18px 60px rgba(0,0,0,.30);
        margin-bottom: 22px;
    }

    .hero h1 {
        font-size: 42px;
        margin-bottom: 5px;
    }

    .hero p {
        color: #CBD5E1;
        font-size: 16px;
    }

    .metric-card {
        background: linear-gradient(145deg, rgba(15,23,42,.96), rgba(2,6,23,.94));
        border: 1px solid rgba(34,211,238,.22);
        border-radius: 20px;
        padding: 20px;
        box-shadow:
            0 0 28px rgba(34,211,238,.07),
            inset 0 0 18px rgba(124,58,237,.04);
        transition: transform .2s ease, border-color .2s ease, box-shadow .2s ease;
    }

    .metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(34,211,238,.45);
        box-shadow:
            0 0 34px rgba(34,211,238,.13),
            0 12px 28px rgba(0,0,0,.22);
    }

    .metric-title {
        color: #94A3B8;
        font-size: 14px;
    }

    .metric-value {
        font-size: 34px;
        font-weight: 800;
        color: white;
    }

    .lead-card {
        background:
            radial-gradient(circle at 0% 0%, rgba(34,211,238,.05), transparent 30%),
            linear-gradient(145deg, rgba(15,23,42,.97), rgba(8,15,30,.94));
        border: 1px solid rgba(148,163,184,.16);
        border-radius: 20px;
        padding: 22px;
        margin-bottom: 18px;
        box-shadow: 0 0 24px rgba(0,0,0,.26), inset 0 0 16px rgba(34,211,238,.02);
        transition: all .22s ease;
    }

    .lead-card:hover {
        border-color: rgba(34,211,238,.35);
        box-shadow: 0 0 32px rgba(34,211,238,.10), 0 14px 32px rgba(0,0,0,.24);
    }

    .kanban-card {
        background: linear-gradient(145deg, rgba(17,24,39,.98), rgba(2,6,23,.97));
        border: 1px solid rgba(34,211,238,.18);
        border-radius: 18px;
        padding: 15px;
        margin-bottom: 12px;
        box-shadow: 0 0 18px rgba(34,211,238,.06);
    }

    .kanban-column {
        background: linear-gradient(180deg, rgba(9,16,31,.94), rgba(2,6,23,.90));
        border: 1px solid rgba(34,211,238,.14);
        border-radius: 20px;
        padding: 15px;
        min-height: 260px;
        box-shadow: 0 0 24px rgba(34,211,238,.04), inset 0 1px 0 rgba(255,255,255,.02);
    }

    .client-msg {
        background: linear-gradient(135deg, #1E293B, #111827);
        border: 1px solid rgba(148,163,184,.12);
        padding: 12px;
        border-radius: 14px;
        margin-bottom: 10px;
    }

    .agent-msg {
        background: linear-gradient(135deg, #1D4ED8, #6D28D9);
        border: 1px solid rgba(129,140,248,.34);
        box-shadow: 0 0 22px rgba(99,102,241,.12);
        padding: 12px;
        border-radius: 14px;
        margin-bottom: 10px;
    }

    [data-testid="stSelectbox"] > div > div,
    [data-testid="stTextInput"] > div > div,
    [data-testid="stNumberInput"] > div > div,
    [data-testid="stTextArea"] textarea {
        background: rgba(7,13,27,.96) !important;
        border-color: rgba(71,85,105,.55) !important;
        border-radius: 12px !important;
    }

    [data-testid="stSelectbox"] > div > div:focus-within,
    [data-testid="stTextInput"] > div > div:focus-within,
    [data-testid="stNumberInput"] > div > div:focus-within,
    [data-testid="stTextArea"] textarea:focus {
        border-color: rgba(34,211,238,.70) !important;
        box-shadow: 0 0 0 1px rgba(34,211,238,.18), 0 0 18px rgba(34,211,238,.08) !important;
    }

    .stButton > button,
    [data-testid="stBaseButton-secondary"],
    [data-testid="stBaseButton-primary"] {
        border-radius: 12px !important;
        transition: all .2s ease !important;
    }

    .stButton > button:hover {
        border-color: rgba(34,211,238,.65) !important;
        box-shadow: 0 0 18px rgba(34,211,238,.10) !important;
    }

    [data-testid="stDataFrame"] {
        border: 1px solid rgba(34,211,238,.20);
        border-radius: 18px;
        overflow: hidden;
        box-shadow: 0 0 28px rgba(34,211,238,.05), 0 14px 36px rgba(0,0,0,.20);
        background: rgba(4,10,23,.88);
    }

    [data-testid="stPlotlyChart"] {
        background:
            radial-gradient(circle at 50% 20%, rgba(34,211,238,.035), transparent 45%),
            linear-gradient(145deg, rgba(8,15,30,.96), rgba(2,6,23,.92));
        border: 1px solid rgba(34,211,238,.13);
        border-radius: 18px;
        padding: 8px;
        box-shadow: 0 0 24px rgba(34,211,238,.04), inset 0 1px 0 rgba(255,255,255,.02);
    }

    [data-testid="stExpander"] {
        border: 1px solid rgba(34,211,238,.14) !important;
        border-radius: 16px !important;
        background: rgba(7,13,27,.72) !important;
        overflow: hidden;
    }

    hr {
        border-color: rgba(71,85,105,.30) !important;
    }

    * {
        scrollbar-width: thin;
        scrollbar-color: rgba(34,211,238,.28) rgba(2,6,23,.6);
    }

    *::-webkit-scrollbar {
        width: 9px;
        height: 9px;
    }

    *::-webkit-scrollbar-track {
        background: rgba(2,6,23,.62);
    }

    *::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, rgba(34,211,238,.36), rgba(168,85,247,.30));
        border-radius: 999px;
    }

    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after {
            transition: none !important;
            animation: none !important;
        }
    }
    /* =========================================
   MENU LATERAL - NEON COMPACTO
   ========================================= */

[data-testid="stSidebar"] div[role="radiogroup"] {
    gap: 0.08rem !important;
}

[data-testid="stSidebar"] div[role="radiogroup"] label {
    position: relative;

    border-radius: 9px;

    padding:
        2px 6px !important;

    margin:
        0 !important;

    min-height:
        30px !important;

    border:
        1px solid transparent;

    background:
        transparent;

    transition:
        background .16s ease,
        border-color .16s ease,
        box-shadow .16s ease;
}

/* Mantém texto compacto */
[data-testid="stSidebar"] div[role="radiogroup"] label p {
    margin:
        0 !important;

    line-height:
        1.15 !important;

    font-size:
        14px !important;
}

/* Hover discreto */
[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    background:
        rgba(15,23,42,.62);

    border-color:
        rgba(34,211,238,.16);

    box-shadow:
        0 0 12px
        rgba(34,211,238,.04);
}

/* OPÇÃO SELECIONADA */
[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
    background:
        linear-gradient(
            90deg,
            rgba(8,47,73,.58),
            rgba(15,23,42,.66)
        );

    border-color:
        rgba(34,211,238,.48);

    box-shadow:
        0 0 0 1px
        rgba(34,211,238,.05)
        inset,

        0 0 13px
        rgba(34,211,238,.13);
}

/* Linha neon lateral */
[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked)::before {
    content: "";

    position:
        absolute;

    left:
        -1px;

    top:
        18%;

    bottom:
        18%;

    width:
        2px;

    border-radius:
        999px;

    background:
        linear-gradient(
            180deg,
            #67E8F9,
            #22D3EE,
            #3B82F6
        );

    box-shadow:
        0 0 8px
        rgba(34,211,238,.68);
}

[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p {
    color:
        #F8FAFC !important;

    font-weight:
        700 !important;

    text-shadow:
        0 0 8px
        rgba(34,211,238,.14);
}
    </style>
    """, unsafe_allow_html=True)