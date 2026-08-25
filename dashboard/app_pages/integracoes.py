import streamlit as st


def render_integracoes():

    st.title("🔌 Integrações")

    st.markdown(
        """
        <style>
        .integracoes-context-card {
            position: relative;
            overflow: hidden;
            background:
                radial-gradient(circle at 0% 0%, rgba(34,211,238,.09), transparent 38%),
                linear-gradient(145deg, rgba(15,23,42,.97), rgba(3,8,20,.96));
            border: 1px solid rgba(34,211,238,.24);
            border-radius: 18px;
            padding: 16px 18px;
            margin: 8px 0 18px 0;
            box-shadow:
                0 0 26px rgba(34,211,238,.065),
                inset 0 1px 0 rgba(255,255,255,.02);
        }

        .integracoes-context-card::before {
            content: "";
            position: absolute;
            left: 0;
            top: 13px;
            bottom: 13px;
            width: 3px;
            border-radius: 999px;
            background: linear-gradient(180deg, #67E8F9, #22D3EE, #3B82F6);
            box-shadow: 0 0 12px rgba(34,211,238,.78);
        }

        .integracoes-context-title {
            color: #FFFFFF;
            font-size: 15px;
            font-weight: 850;
            margin-left: 5px;
            margin-bottom: 4px;
        }

        .integracoes-context-subtitle {
            color: #94A3B8;
            font-size: 13px;
            margin-left: 5px;
        }

        .integration-card {
            --integration-accent: #22D3EE;
            --integration-border: rgba(34,211,238,.38);
            --integration-glow: rgba(34,211,238,.09);

            position: relative;
            overflow: hidden;

            background:
                radial-gradient(
                    circle at 50% 0%,
                    var(--integration-glow),
                    transparent 48%
                ),
                linear-gradient(
                    145deg,
                    rgba(15,23,42,.98),
                    rgba(3,8,20,.96)
                );

            border:
                1px solid
                var(--integration-border);

            border-radius: 18px;

            padding: 20px;

            min-height: 185px;

            box-shadow:
                0 0 28px
                var(--integration-glow),
                inset 0 1px 0 rgba(255,255,255,.025);

            transition:
                transform .18s ease,
                border-color .18s ease,
                box-shadow .18s ease;
        }

        .integration-card::before {
            content: "";
            position: absolute;
            top: 0;
            left: 16px;
            right: 16px;
            height: 2px;
            border-radius: 999px;

            background:
                linear-gradient(
                    90deg,
                    transparent,
                    var(--integration-accent),
                    transparent
                );

            box-shadow:
                0 0 12px
                var(--integration-accent);

            opacity: .72;
        }

        .integration-card:hover {
            transform: translateY(-2px);
            box-shadow:
                0 0 36px var(--integration-glow),
                0 14px 30px rgba(0,0,0,.20);
        }

        .integration-whatsapp {
            --integration-accent: #22C55E;
            --integration-border: rgba(34,197,94,.40);
            --integration-glow: rgba(34,197,94,.09);
        }

        .integration-instagram {
            --integration-accent: #EC4899;
            --integration-border: rgba(236,72,153,.40);
            --integration-glow: rgba(236,72,153,.09);
        }

        .integration-facebook {
            --integration-accent: #3B82F6;
            --integration-border: rgba(59,130,246,.40);
            --integration-glow: rgba(59,130,246,.09);
        }

        .integration-title {
            color: #FFFFFF;
            font-size: 20px;
            font-weight: 850;
            margin-bottom: 12px;
            letter-spacing: -0.015em;
        }

        .integration-status {
            display: inline-flex;
            align-items: center;
            gap: 7px;

            color: #E2E8F0;

            font-size: 12px;
            font-weight: 700;

            background:
                rgba(15,23,42,.72);

            border:
                1px solid
                rgba(148,163,184,.12);

            border-radius: 999px;

            padding: 6px 9px;

            margin-bottom: 14px;
        }

        .integration-status-dot {
            width: 7px;
            height: 7px;
            border-radius: 999px;
            background: var(--integration-accent);
            box-shadow: 0 0 9px var(--integration-accent);
        }

        .integration-description {
            color: #A7B4C8;
            font-size: 13px;
            line-height: 1.55;
        }

        .integration-note {
            background:
                radial-gradient(circle at 0% 0%, rgba(168,85,247,.08), transparent 40%),
                linear-gradient(145deg, rgba(15,23,42,.96), rgba(3,8,20,.95));
            border: 1px solid rgba(168,85,247,.24);
            border-left: 4px solid #A855F7;
            border-radius: 18px;
            padding: 18px 20px;
            color: #CBD5E1;
            box-shadow: 0 0 24px rgba(168,85,247,.06);
            margin-top: 8px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="integracoes-context-card">
            <div class="integracoes-context-title">Canais conectados ao CRM</div>
            <div class="integracoes-context-subtitle">
                Centralize os principais canais de entrada de leads e atendimento comercial.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("## Canais planejados")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(
            """
            <div class="integration-card integration-whatsapp">
                <div class="integration-title">📱 WhatsApp</div>
                <div class="integration-status">
                    <span class="integration-status-dot"></span>
                    Aguardando integração
                </div>
                <div class="integration-description">
                    Canal principal de atendimento e relacionamento comercial.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            """
            <div class="integration-card integration-instagram">
                <div class="integration-title">📸 Instagram Direct</div>
                <div class="integration-status">
                    <span class="integration-status-dot"></span>
                    Aguardando integração
                </div>
                <div class="integration-description">
                    Leads e conversas originadas pelo Instagram.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            """
            <div class="integration-card integration-facebook">
                <div class="integration-title">🔵 Facebook Messenger</div>
                <div class="integration-status">
                    <span class="integration-status-dot"></span>
                    Aguardando integração
                </div>
                <div class="integration-description">
                    Leads vindas da página e das campanhas no Facebook.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    st.markdown(
        """
        <div class="integration-note">
            Quando o gestor liberar os acessos, conectaremos os canais reais ao CRM SDR.
        </div>
        """,
        unsafe_allow_html=True,
    )