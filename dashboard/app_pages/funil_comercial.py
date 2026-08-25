import html
from textwrap import dedent

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


def texto_html(valor):
    return html.escape(str(valor))


def render_funil(leads):

    st.title("🔥 Funil Comercial")

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
        dedent(
            """
            <style>
            .orion-funil-wrap {
                margin-top: 6px;
            }

            .kanban-column {
                --stage-accent: #22D3EE;
                --stage-border: rgba(34,211,238,.42);
                --stage-glow: rgba(34,211,238,.10);

                position: relative;
                overflow: hidden;

                background:
                    radial-gradient(
                        circle at 50% 0%,
                        var(--stage-glow),
                        transparent 44%
                    ),
                    linear-gradient(
                        180deg,
                        rgba(10,18,36,.98),
                        rgba(3,8,20,.96)
                    );

                border:
                    1px solid
                    var(--stage-border);

                border-radius: 18px;
                padding: 17px 16px 15px 16px;
                min-height: 132px;
                margin-bottom: 14px;

                box-shadow:
                    0 0 26px var(--stage-glow),
                    inset 0 1px 0 rgba(255,255,255,.025);

                transition:
                    transform .20s ease,
                    box-shadow .20s ease,
                    border-color .20s ease;
            }

            .kanban-column::before {
                content: "";
                position: absolute;
                top: 0;
                left: 14px;
                right: 14px;
                height: 2px;
                border-radius: 999px;

                background:
                    linear-gradient(
                        90deg,
                        transparent,
                        var(--stage-accent),
                        transparent
                    );

                box-shadow:
                    0 0 12px var(--stage-accent);

                opacity: .75;
            }

            .kanban-column:hover {
                transform: translateY(-2px);
                box-shadow:
                    0 0 34px var(--stage-glow),
                    0 12px 28px rgba(0,0,0,.20);
            }

            .stage-waiting {
                --stage-accent: #22D3EE;
                --stage-border: rgba(34,211,238,.44);
                --stage-glow: rgba(34,211,238,.11);
            }

            .stage-service {
                --stage-accent: #6366F1;
                --stage-border: rgba(99,102,241,.44);
                --stage-glow: rgba(99,102,241,.11);
            }

            .stage-proposal {
                --stage-accent: #D946EF;
                --stage-border: rgba(217,70,239,.42);
                --stage-glow: rgba(217,70,239,.10);
            }

            .stage-won {
                --stage-accent: #22C55E;
                --stage-border: rgba(34,197,94,.42);
                --stage-glow: rgba(34,197,94,.10);
            }

            .stage-lost {
                --stage-accent: #EF4444;
                --stage-border: rgba(239,68,68,.40);
                --stage-glow: rgba(239,68,68,.09);
            }

            .kanban-title {
                position: relative;
                z-index: 1;
                color: #FFFFFF;
                font-size: 16px;
                line-height: 1.2;
                font-weight: 850;
                margin-bottom: 11px;
                letter-spacing: -0.01em;
                text-shadow: 0 0 16px var(--stage-glow);
            }

            .kanban-count {
                position: relative;
                z-index: 1;
                display: inline-flex;
                align-items: center;
                gap: 6px;
                color: #CBD5E1;
                font-size: 13px;
                font-weight: 650;
                background: rgba(15,23,42,.72);
                border: 1px solid rgba(148,163,184,.11);
                border-radius: 999px;
                padding: 5px 9px;
            }

            .kanban-count-dot {
                width: 7px;
                height: 7px;
                border-radius: 999px;
                background: var(--stage-accent);
                box-shadow: 0 0 9px var(--stage-accent);
            }

            .kanban-card {
                --card-accent: #22D3EE;
                --card-border: rgba(34,211,238,.24);
                --card-glow: rgba(34,211,238,.065);

                position: relative;
                overflow: hidden;

                background:
                    radial-gradient(
                        circle at 0% 0%,
                        var(--card-glow),
                        transparent 42%
                    ),
                    linear-gradient(
                        145deg,
                        rgba(15,23,42,.98),
                        rgba(4,9,22,.96)
                    );

                border: 1px solid var(--card-border);
                border-radius: 16px;
                padding: 15px;
                margin-bottom: 12px;
                color: #E2E8F0;
                font-size: 13px;

                box-shadow:
                    0 0 22px var(--card-glow),
                    0 10px 24px rgba(0,0,0,.16);

                transition:
                    transform .18s ease,
                    border-color .18s ease,
                    box-shadow .18s ease;
            }

            .kanban-card::before {
                content: "";
                position: absolute;
                left: 0;
                top: 13px;
                bottom: 13px;
                width: 3px;
                border-radius: 999px;
                background: var(--card-accent);
                box-shadow: 0 0 10px var(--card-accent);
            }

            .kanban-card:hover {
                transform: translateY(-2px);
                border-color: var(--card-accent);
                box-shadow:
                    0 0 28px var(--card-glow),
                    0 12px 28px rgba(0,0,0,.22);
            }

            .card-waiting {
                --card-accent: #22D3EE;
                --card-border: rgba(34,211,238,.26);
                --card-glow: rgba(34,211,238,.07);
            }

            .card-service {
                --card-accent: #6366F1;
                --card-border: rgba(99,102,241,.26);
                --card-glow: rgba(99,102,241,.07);
            }

            .card-proposal {
                --card-accent: #D946EF;
                --card-border: rgba(217,70,239,.25);
                --card-glow: rgba(217,70,239,.065);
            }

            .card-won {
                --card-accent: #22C55E;
                --card-border: rgba(34,197,94,.25);
                --card-glow: rgba(34,197,94,.065);
            }

            .card-lost {
                --card-accent: #EF4444;
                --card-border: rgba(239,68,68,.24);
                --card-glow: rgba(239,68,68,.06);
            }

            .kanban-card-title {
                color: #FFFFFF;
                font-weight: 850;
                font-size: 15px;
                margin: 0 0 10px 3px;
                letter-spacing: -0.01em;
            }

            .kanban-line {
                color: #C8D3E2;
                margin: 0 0 7px 3px;
                padding: 0;
                line-height: 1.35;
            }

            .kanban-line:last-child {
                margin-bottom: 0;
            }

            .kanban-temperature {
                display: inline-flex;
                align-items: center;
                gap: 6px;
                color: #E2E8F0;
                background: rgba(15,23,42,.62);
                border: 1px solid rgba(148,163,184,.10);
                border-radius: 999px;
                padding: 4px 8px;
                margin: 2px 0 8px 3px;
            }

            @media (prefers-reduced-motion: reduce) {
                .kanban-column,
                .kanban-card {
                    transition: none !important;
                }
            }
            </style>
            """
        ),
        unsafe_allow_html=True
    )

    status_visuais = {
        "Aguardando atendimento": {
            "stage": "stage-waiting",
            "card": "card-waiting",
        },
        "Em atendimento": {
            "stage": "stage-service",
            "card": "card-service",
        },
        "Proposta enviada": {
            "stage": "stage-proposal",
            "card": "card-proposal",
        },
        "Negócio fechado": {
            "stage": "stage-won",
            "card": "card-won",
        },
        "Não fechado": {
            "stage": "stage-lost",
            "card": "card-lost",
        },
    }

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

            visual = status_visuais.get(
                status,
                {
                    "stage": "stage-waiting",
                    "card": "card-waiting",
                },
            )

            status_html = texto_html(status)

            st.markdown(
                dedent(
                    f"""
                    <div class="kanban-column {visual["stage"]}">
                        <div class="kanban-title">{status_html}</div>
                        <div class="kanban-count">
                            <span class="kanban-count-dot"></span>
                            {len(subset)} lead(s)
                        </div>
                    </div>
                    """
                ),
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

                nome = texto_html(
                    valor_seguro(
                        lead,
                        "nome",
                        "Lead sem nome"
                    )
                )

                produto = texto_html(
                    valor_seguro(
                        lead,
                        "produto",
                        "Produto não informado"
                    )
                )

                score = texto_html(
                    valor_seguro(
                        lead,
                        "score",
                        0
                    )
                )

                responsavel = texto_html(
                    valor_seguro(
                        lead,
                        "responsavel",
                        "Não atribuído"
                    )
                )

                canal = texto_html(
                    valor_seguro(
                        lead,
                        "canal",
                        "Não informado"
                    )
                )

                temperatura_html = texto_html(temperatura)

                st.markdown(
                    dedent(
                        f"""
                        <div class="kanban-card {visual["card"]}">
                            <div class="kanban-card-title">{nome}</div>
                            <p class="kanban-line">🧩 {produto}</p>
                            <div class="kanban-temperature">{emoji} {temperatura_html}</div>
                            <p class="kanban-line">📊 Score {score}</p>
                            <p class="kanban-line">👨‍💼 {responsavel}</p>
                            <p class="kanban-line">📲 {canal}</p>
                        </div>
                        """
                    ),
                    unsafe_allow_html=True
                )