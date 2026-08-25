import streamlit as st

from services.pedidos_service import (
    listar_pedidos,
    cadastrar_pedido,
    atualizar_pedido,
    excluir_pedido,
    STATUS_PAGAMENTO,
    STATUS_PEDIDO,
    FORMAS_PAGAMENTO,
)

from services.produtos_service import (
    listar_produtos,
)


def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def render_pedidos():

    empresa_id = st.session_state.empresa_id

    st.title("🧾 Pedidos / Vendas")

    st.markdown(
        """
        <style>
        .pedidos-section-card {
            position: relative;
            overflow: hidden;
            background:
                radial-gradient(circle at 0% 0%, rgba(34,211,238,.09), transparent 38%),
                linear-gradient(145deg, rgba(15,23,42,.97), rgba(3,8,20,.96));
            border: 1px solid rgba(34,211,238,.24);
            border-radius: 18px;
            padding: 16px 18px;
            margin: 8px 0 16px 0;
            box-shadow:
                0 0 26px rgba(34,211,238,.065),
                inset 0 1px 0 rgba(255,255,255,.02);
        }

        .pedidos-section-card::before {
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

        .pedidos-section-title {
            color: #FFFFFF;
            font-size: 15px;
            font-weight: 850;
            margin-left: 5px;
            margin-bottom: 4px;
        }

        .pedidos-section-subtitle {
            color: #94A3B8;
            font-size: 13px;
            margin-left: 5px;
        }

        .pedidos-empty-card {
            background:
                radial-gradient(circle at 50% 0%, rgba(99,102,241,.09), transparent 44%),
                linear-gradient(145deg, rgba(15,23,42,.96), rgba(3,8,20,.95));
            border: 1px dashed rgba(99,102,241,.40);
            border-radius: 18px;
            padding: 28px 20px;
            margin: 10px 0 18px 0;
            text-align: center;
            color: #CBD5E1;
            box-shadow: 0 0 24px rgba(99,102,241,.06);
        }

        .pedidos-empty-card strong {
            color: #FFFFFF;
        }

        .pedidos-warning-card {
            background:
                radial-gradient(circle at 0% 0%, rgba(245,158,11,.09), transparent 40%),
                linear-gradient(145deg, rgba(15,23,42,.96), rgba(3,8,20,.95));
            border: 1px solid rgba(245,158,11,.30);
            border-left: 4px solid #F59E0B;
            border-radius: 18px;
            padding: 20px;
            color: #E2E8F0;
            box-shadow: 0 0 24px rgba(245,158,11,.065);
            margin-bottom: 14px;
        }

        .pedido-management-empty {
            background:
                radial-gradient(circle at 0% 0%, rgba(168,85,247,.08), transparent 40%),
                linear-gradient(145deg, rgba(15,23,42,.96), rgba(3,8,20,.95));
            border: 1px solid rgba(168,85,247,.24);
            border-left: 4px solid #A855F7;
            border-radius: 18px;
            padding: 22px 20px;
            color: #CBD5E1;
            box-shadow: 0 0 24px rgba(168,85,247,.06);
            margin-bottom: 12px;
        }

        [data-testid="stMetric"] {
            background:
                radial-gradient(circle at 12% 0%, rgba(34,211,238,.12), transparent 42%),
                linear-gradient(145deg, rgba(15,23,42,.97), rgba(3,8,20,.96));
            border: 1px solid rgba(34,211,238,.32);
            border-radius: 18px;
            padding: 16px 18px;
            box-shadow: 0 0 25px rgba(34,211,238,.09);
        }

        [data-testid="stDataFrame"] {
            border: 1px solid rgba(34,211,238,.26);
            border-radius: 18px;
            overflow: hidden;
            box-shadow:
                0 0 30px rgba(34,211,238,.07),
                0 14px 34px rgba(0,0,0,.18);
        }

        [data-testid="stTextInput"] > div > div,
        [data-testid="stNumberInput"] > div > div,
        [data-testid="stSelectbox"] > div > div,
        [data-testid="stTextArea"] textarea {
            border-radius: 12px !important;
        }

        [data-testid="stTextInput"] > div > div:focus-within,
        [data-testid="stNumberInput"] > div > div:focus-within,
        [data-testid="stSelectbox"] > div > div:focus-within,
        [data-testid="stTextArea"] textarea:focus {
            border-color: rgba(34,211,238,.68) !important;
            box-shadow:
                0 0 0 1px rgba(34,211,238,.15),
                0 0 18px rgba(34,211,238,.09) !important;
        }

        div[data-testid="stButton"] > button {
            border-radius: 12px !important;
            transition:
                transform .18s ease,
                border-color .18s ease,
                box-shadow .18s ease;
        }

        div[data-testid="stButton"] > button:hover {
            transform: translateY(-1px);
            border-color: rgba(34,211,238,.62) !important;
            box-shadow: 0 0 18px rgba(34,211,238,.12) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    produtos = listar_produtos(empresa_id)
    pedidos = listar_pedidos(empresa_id)

    # =========================================
    # NOVO PEDIDO
    # =========================================

    st.markdown("## ➕ Novo pedido")

    st.markdown(
        """
        <div class="pedidos-section-card">
            <div class="pedidos-section-title">Nova venda</div>
            <div class="pedidos-section-subtitle">
                Registre cliente, produto, quantidade, origem e forma de pagamento.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if produtos.empty:

        st.markdown(
            """
            <div class="pedidos-warning-card">
                <strong>Cadastre produtos antes de criar pedidos.</strong><br>
                A estrutura de vendas permanece visível e será liberada automaticamente quando houver produtos ativos.
            </div>
            """,
            unsafe_allow_html=True,
        )

    else:

        produtos_dict = {

            f"{row['nome']} - {formatar_moeda(float(row['preco']))}":
            row

            for _, row in produtos.iterrows()
        }

        pedido_produto = st.selectbox(
            "Produto",
            list(produtos_dict.keys())
        )

        produto = produtos_dict[pedido_produto]

        c1, c2 = st.columns(2)

        with c1:

            cliente_nome = st.text_input(
                "Nome cliente"
            )

            cliente_telefone = st.text_input(
                "Telefone cliente"
            )

            quantidade = st.number_input(
                "Quantidade",
                min_value=1,
                value=1
            )

        with c2:

            forma_pagamento = st.selectbox(
                "Forma pagamento",
                FORMAS_PAGAMENTO
            )

            origem = st.selectbox(
                "Origem venda",
                [
                    "WhatsApp",
                    "Instagram",
                    "Facebook",
                    "Manual"
                ]
            )

            vendido_por = st.selectbox(
                "Vendido por",
                [
                    "IA",
                    "Humano"
                ]
            )

        observacoes = st.text_area(
            "Observações"
        )

        valor_total = (
            float(produto["preco"])
            * quantidade
        )

        st.metric(
            "Valor total",
            formatar_moeda(valor_total)
        )

        if st.button(
            "Cadastrar pedido",
            use_container_width=True
        ):

            cadastrar_pedido(

                empresa_id,

                cliente_nome,

                cliente_telefone,

                produto["id"],

                produto["nome"],

                quantidade,

                valor_total,

                forma_pagamento,

                "Aguardando pagamento",

                "Novo pedido",

                origem,

                vendido_por,

                observacoes
            )

            st.success(
                "Pedido cadastrado."
            )

            st.rerun()

    st.markdown("---")

    # =========================================
    # LISTAGEM
    # =========================================

    st.markdown(
        "## 📋 Pedidos cadastrados"
    )

    st.markdown(
        """
        <div class="pedidos-section-card">
            <div class="pedidos-section-title">Histórico de pedidos</div>
            <div class="pedidos-section-subtitle">
                Acompanhe cliente, produto, valores, pagamento e andamento da venda.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if pedidos.empty:

        st.markdown(
            """
            <div class="pedidos-empty-card">
                <strong>Nenhum pedido cadastrado ainda.</strong><br>
                Os pedidos aparecerão aqui assim que a primeira venda for registrada.
            </div>
            """,
            unsafe_allow_html=True,
        )

    else:

        st.dataframe(
            pedidos,
            use_container_width=True,
            hide_index=True
        )

    st.markdown("---")

    # =========================================
    # GERENCIAR
    # =========================================

    st.markdown(
        "## ⚙️ Gerenciar pedido"
    )

    st.markdown(
        """
        <div class="pedidos-section-card">
            <div class="pedidos-section-title">Gestão do pedido</div>
            <div class="pedidos-section-subtitle">
                Atualize pagamento, andamento e observações da venda selecionada.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if pedidos.empty:

        st.markdown(
            """
            <div class="pedido-management-empty">
                Nenhum pedido disponível para gerenciamento no momento.<br>
                Quando uma venda for cadastrada, os controles aparecerão nesta área.
            </div>
            """,
            unsafe_allow_html=True,
        )

        return

    pedidos_dict = {

        f"Pedido #{row['id']} - {row['cliente_nome']}":
        row

        for _, row in pedidos.iterrows()
    }

    pedido_escolhido = st.selectbox(
        "Selecionar pedido",
        list(pedidos_dict.keys())
    )

    pedido = pedidos_dict[pedido_escolhido]

    g1, g2 = st.columns(2)

    with g1:

        novo_status_pagamento = st.selectbox(
            "Status pagamento",
            STATUS_PAGAMENTO,
            index=STATUS_PAGAMENTO.index(
                pedido["status_pagamento"]
            )
            if pedido["status_pagamento"] in STATUS_PAGAMENTO
            else 0
        )

    with g2:

        novo_status_pedido = st.selectbox(
            "Status pedido",
            STATUS_PEDIDO,
            index=STATUS_PEDIDO.index(
                pedido["status_pedido"]
            )
            if pedido["status_pedido"] in STATUS_PEDIDO
            else 0
        )

    nova_observacao = st.text_area(
        "Observações atualizadas",
        value=pedido["observacoes"]
        if pedido["observacoes"]
        else ""
    )

    b1, b2 = st.columns(2)

    with b1:

        if st.button(
            "Salvar alterações pedido",
            use_container_width=True
        ):

            atualizar_pedido(

                pedido["id"],

                novo_status_pagamento,

                novo_status_pedido,

                nova_observacao
            )

            st.success(
                "Pedido atualizado."
            )

            st.rerun()

    with b2:

        if st.button(
            "Excluir pedido",
            use_container_width=True
        ):

            excluir_pedido(
                pedido["id"]
            )

            st.warning(
                "Pedido excluído."
            )

            st.rerun()