import streamlit as st
import pandas as pd

from textwrap import dedent

from database.db import conectar

from components.graficos import (
    grafico_donut,
)

from components.sidebar import (
    render_seletor_empresa,
)


def buscar_dados_empresa(
    empresa_id,
):
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
            params=(
                empresa_id,
            ),
        )

        pedidos = pd.read_sql_query(
            """
            SELECT *
            FROM pedidos
            WHERE empresa_id = %s
            ORDER BY id DESC
            """,
            conn,
            params=(
                empresa_id,
            ),
        )

        produtos = pd.read_sql_query(
            """
            SELECT *
            FROM produtos
            WHERE empresa_id = %s
            ORDER BY id DESC
            """,
            conn,
            params=(
                empresa_id,
            ),
        )

        return (
            leads,
            pedidos,
            produtos,
        )

    finally:

        conn.close()


def formatar_moeda(valor):
    return (
        f"R$ {valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def aplicar_css():
    st.markdown(
        dedent(
            """
            <style>

            .top-card {
                position: relative;
                overflow: hidden;

                background:
                    radial-gradient(circle at 4% 0%, rgba(34,211,238,.15), transparent 34%),
                    radial-gradient(circle at 96% 5%, rgba(168,85,247,.12), transparent 34%),
                    linear-gradient(135deg, rgba(10,20,40,.98), rgba(3,8,22,.97));

                border: 1px solid rgba(34,211,238,.28);
                border-radius: 22px;
                padding: 28px 32px;
                margin-bottom: 20px;

                box-shadow:
                    0 0 0 1px rgba(255,255,255,.02) inset,
                    0 0 38px rgba(34,211,238,.09),
                    0 18px 52px rgba(0,0,0,.26);
            }

            .top-card::after {
                content: "";
                position: absolute;
                inset: 0;
                pointer-events: none;
                background:
                    linear-gradient(
                        90deg,
                        rgba(34,211,238,.06),
                        transparent 22%,
                        transparent 78%,
                        rgba(168,85,247,.05)
                    );
            }

            .top-title {
                position: relative;
                z-index: 1;
                font-size: 42px;
                font-weight: 900;
                color: #FFFFFF;
                margin-bottom: 6px;
                letter-spacing: -0.025em;
                text-shadow: 0 0 28px rgba(34,211,238,.12);
            }

            .top-subtitle {
                position: relative;
                z-index: 1;
                color: #9FB0C8;
                font-size: 15px;
            }

            .metric-card {
                position: relative;
                overflow: hidden;

                background:
                    radial-gradient(
                        circle at 50% 100%,
                        var(--metric-glow, rgba(34,211,238,.08)),
                        transparent 66%
                    ),
                    linear-gradient(145deg, rgba(12,21,40,.98), rgba(3,8,20,.96));

                border: 1px solid var(--metric-border, rgba(34,211,238,.30));
                border-radius: 18px;
                padding: 17px 18px 18px 18px;
                min-height: 112px;

                box-shadow:
                    0 0 26px var(--metric-shadow, rgba(34,211,238,.07)),
                    inset 0 1px 0 rgba(255,255,255,.025);

                transition:
                    transform .2s ease,
                    border-color .2s ease,
                    box-shadow .2s ease;
            }

            .metric-card::before {
                content: "";
                position: absolute;
                top: 0;
                left: 16px;
                right: 16px;
                height: 1px;
                background:
                    linear-gradient(
                        90deg,
                        transparent,
                        var(--metric-accent, #22D3EE),
                        transparent
                    );
                opacity: .62;
            }

            .metric-card:hover {
                transform: translateY(-2px);
                box-shadow:
                    0 0 34px var(--metric-shadow-hover, rgba(34,211,238,.13)),
                    0 12px 28px rgba(0,0,0,.22);
            }

            .metric-label {
                position: relative;
                z-index: 1;
                color: #A7B4C8;
                font-size: 13px;
                font-weight: 650;
                margin-bottom: 7px;
                white-space: nowrap;
            }

            .metric-value {
                position: relative;
                z-index: 1;
                color: #FFFFFF;
                font-size: 31px;
                line-height: 1.1;
                font-weight: 850;
                text-shadow: 0 0 18px var(--metric-text-glow, rgba(255,255,255,.03));
            }

            .metric-cyan {
                --metric-accent: #22D3EE;
                --metric-border: rgba(34,211,238,.42);
                --metric-glow: rgba(34,211,238,.10);
                --metric-shadow: rgba(34,211,238,.08);
                --metric-shadow-hover: rgba(34,211,238,.16);
                --metric-text-glow: rgba(34,211,238,.10);
            }

            .metric-pink {
                --metric-accent: #EC4899;
                --metric-border: rgba(236,72,153,.42);
                --metric-glow: rgba(236,72,153,.10);
                --metric-shadow: rgba(236,72,153,.07);
                --metric-shadow-hover: rgba(236,72,153,.15);
                --metric-text-glow: rgba(236,72,153,.10);
            }

            .metric-purple {
                --metric-accent: #A855F7;
                --metric-border: rgba(168,85,247,.42);
                --metric-glow: rgba(168,85,247,.10);
                --metric-shadow: rgba(168,85,247,.07);
                --metric-shadow-hover: rgba(168,85,247,.15);
                --metric-text-glow: rgba(168,85,247,.10);
            }

            .metric-amber {
                --metric-accent: #F59E0B;
                --metric-border: rgba(245,158,11,.40);
                --metric-glow: rgba(245,158,11,.09);
                --metric-shadow: rgba(245,158,11,.06);
                --metric-shadow-hover: rgba(245,158,11,.14);
                --metric-text-glow: rgba(245,158,11,.10);
            }

            .metric-green {
                --metric-accent: #22C55E;
                --metric-border: rgba(34,197,94,.40);
                --metric-glow: rgba(34,197,94,.09);
                --metric-shadow: rgba(34,197,94,.06);
                --metric-shadow-hover: rgba(34,197,94,.14);
                --metric-text-glow: rgba(34,197,94,.10);
            }

            .metric-red {
                --metric-accent: #EF4444;
                --metric-border: rgba(239,68,68,.38);
                --metric-glow: rgba(239,68,68,.08);
                --metric-shadow: rgba(239,68,68,.055);
                --metric-shadow-hover: rgba(239,68,68,.13);
                --metric-text-glow: rgba(239,68,68,.09);
            }

            .section-title {
                font-size: 28px;
                font-weight: 850;
                margin-top: 30px;
                margin-bottom: 16px;
                color: #FFFFFF;
                letter-spacing: -0.018em;
                text-shadow: 0 0 22px rgba(34,211,238,.07);
            }

            .diagnostico-card {
                position: relative;
                overflow: hidden;
                background:
                    radial-gradient(circle at 0% 50%, rgba(34,211,238,.10), transparent 36%),
                    linear-gradient(135deg, rgba(15,28,49,.97), rgba(3,8,22,.97));
                border: 1px solid rgba(34,211,238,.18);
                border-left: 5px solid #22D3EE;
                border-radius: 16px;
                padding: 22px 24px;
                color: #E2E8F0;
                margin-top: 12px;
                line-height: 1.72;
                box-shadow:
                    0 0 30px rgba(34,211,238,.06),
                    inset 0 1px 0 rgba(255,255,255,.02);
            }

            .diagnostico-card strong {
                color: #FFFFFF;
                font-weight: 800;
                text-shadow: 0 0 16px rgba(34,211,238,.09);
            }

            .empresa-contexto-card {
                background:
                    linear-gradient(
                        135deg,
                        rgba(15,23,42,.96),
                        rgba(30,41,59,.78)
                    );
                border: 1px solid rgba(34,211,238,.14);
                border-radius: 18px;
                padding: 16px 20px;
                margin-bottom: 22px;
                box-shadow: 0 0 16px rgba(34,211,238,.03);
            }

            [data-testid="stPlotlyChart"] {
                border-color: rgba(34,211,238,.16) !important;
                box-shadow:
                    0 0 28px rgba(34,211,238,.045),
                    inset 0 1px 0 rgba(255,255,255,.018) !important;
            }

            [data-testid="stDataFrame"] {
                border-color: rgba(34,211,238,.24) !important;
                box-shadow:
                    0 0 34px rgba(34,211,238,.055),
                    0 14px 36px rgba(0,0,0,.20) !important;
            }

            </style>
            """
        ),
        unsafe_allow_html=True,
    )


def card(
    label,
    value,
    variante="cyan",
):
    st.markdown(
        dedent(
            f"""
            <div class="metric-card metric-{variante}">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{value}</div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )


def topo(
    titulo,
    subtitulo,
):
    st.markdown(
        dedent(
            f"""
            <div class="top-card">
                <div class="top-title">{titulo}</div>
                <div class="top-subtitle">{subtitulo}</div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )


def calcular_metricas(
    leads,
    pedidos,
    produtos,
):
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
            status = (
                leads["status"]
                .fillna("")
                .astype(str)
                .str.lower()
            )

            em_atendimento = len(
                status[
                    status.str.contains(
                        "em atendimento",
                        na=False,
                    )
                ]
            )

            aguardando = len(
                status[
                    status.str.contains(
                        "aguardando",
                        na=False,
                    )
                ]
            )

            fechados = len(
                status[
                    status.str.contains(
                        "fechado",
                        na=False,
                    )
                    & ~status.str.contains(
                        "não fechado|nao fechado",
                        na=False,
                    )
                ]
            )

            nao_fechados = len(
                status[
                    status.str.contains(
                        "não fechado|nao fechado",
                        na=False,
                    )
                ]
            )

    valor_pedidos = 0

    if (
        not pedidos.empty
        and "valor_total" in pedidos.columns
    ):
        valor_pedidos = (
            pedidos["valor_total"]
            .fillna(0)
            .sum()
        )

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


def render_graficos_leads(
    leads,
):
    if leads.empty:
        st.info("Nenhuma lead registrada ainda.")
        return

    g1, g2 = st.columns(2)

    with g1:
        if "status" in leads.columns:
            grafico_donut(
                leads,
                "status",
                "Status das Leads",
            )

    with g2:
        if "temperatura" in leads.columns:
            grafico_donut(
                leads,
                "temperatura",
                "Temperatura das Leads",
            )


@st.fragment(run_every="10s")
def render_dados_atualizados():
    """
    Atualiza automaticamente os dados comerciais sem
    recarregar a aplicação inteira e sem destruir a sessão
    atual do usuário.
    """

    empresa_id = st.session_state.get(
        "empresa_ativa_id",
        st.session_state.get(
            "empresa_id",
        ),
    )

    empresa_nome = st.session_state.get(
        "empresa_ativa_nome",
        st.session_state.get(
            "empresa",
        ),
    )

    if not empresa_id:
        st.warning(
            "Nenhuma empresa ativa selecionada."
        )
        return

    leads, pedidos, produtos = (
        buscar_dados_empresa(
            empresa_id
        )
    )

    m = calcular_metricas(
        leads,
        pedidos,
        produtos,
    )

    c1, c2, c3, c4, c5, c6 = st.columns(6)

    with c1:
        card(
            "Total Leads",
            m["total"],
            "cyan",
        )

    with c2:
        card(
            "🔥 Quentes",
            m["quentes"],
            "pink",
        )

    with c3:
        card(
            "🕘 Atendimento",
            m["em_atendimento"],
            "purple",
        )

    with c4:
        card(
            "⏳ Aguardando",
            m["aguardando"],
            "amber",
        )

    with c5:
        card(
            "✅ Fechados",
            m["fechados"],
            "green",
        )

    with c6:
        card(
            "⚪ Não fechados",
            m["nao_fechados"],
            "red",
        )

    st.markdown(
        dedent(
            """
            <div class="section-title">
                🔎 Diagnóstico Comercial
            </div>
            """
        ),
        unsafe_allow_html=True,
    )

    if leads.empty:
        st.markdown(
            dedent(
                """
                <div class="diagnostico-card">
                    Ainda não existem dados suficientes
                    para diagnóstico desta empresa.
                </div>
                """
            ),
            unsafe_allow_html=True,
        )

    else:
        total_leads = m["total"]
        quentes = m["quentes"]
        aguardando = m["aguardando"]

        texto = (
            f"A operação possui "
            f"<strong>{total_leads}</strong> "
            f"{'lead registrada' if total_leads == 1 else 'leads registradas'}."
            f"<br><br>"
            f"A IA gerou "
            f"<strong>{quentes}</strong> "
            f"{'lead quente' if quentes == 1 else 'leads quentes'}."
        )

        if aguardando > 0:
            texto += (
                f"<br><br>"
                f"<strong>{aguardando}</strong> "
                f"{'lead está aguardando atendimento humano' if aguardando == 1 else 'leads estão aguardando atendimento humano'}."
            )

        texto += (
            f"<br><br>"
            f"Empresa analisada: "
            f"<strong>{empresa_nome}</strong>."
        )

        st.markdown(
            dedent(
                f"""
                <div class="diagnostico-card">
                    {texto}
                </div>
                """
            ),
            unsafe_allow_html=True,
        )

    st.markdown(
        dedent(
            """
            <div class="section-title">
                📊 Analytics Comercial
            </div>
            """
        ),
        unsafe_allow_html=True,
    )

    render_graficos_leads(
        leads
    )

    st.markdown(
        dedent(
            """
            <div class="section-title">
                📈 Últimas Leads
            </div>
            """
        ),
        unsafe_allow_html=True,
    )

    if leads.empty:
        st.info(
            "Nenhuma lead cadastrada."
        )

    else:
        st.dataframe(
            leads.head(10),
            width="stretch",
            hide_index=True,
        )


def render_empresa_ativa():

    aplicar_css()

    empresa_nome_atual = (
        st.session_state.get(
            "empresa_ativa_nome",
            st.session_state.get(
                "empresa",
                "",
            ),
        )
    )

    topo(
        f"🏠 Visão Geral — {empresa_nome_atual}",
        (
            "Painel operacional da empresa ativa, "
            "com indicadores de atendimento, "
            "leads e resultados comerciais."
        ),
    )

    render_seletor_empresa()

    st.markdown("---")

    # Apenas esta área é atualizada automaticamente.
    render_dados_atualizados()


def render_visao_geral(
    leads_param=None,
):
    render_empresa_ativa()