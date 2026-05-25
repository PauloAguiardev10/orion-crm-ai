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

    produtos = listar_produtos(empresa_id)

    pedidos = listar_pedidos(empresa_id)

    # =========================================
    # NOVO PEDIDO
    # =========================================

    st.markdown("## ➕ Novo pedido")

    if produtos.empty:

        st.warning(
            "Cadastre produtos antes de criar pedidos."
        )

        return

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

    if pedidos.empty:

        st.info(
            "Nenhum pedido cadastrado."
        )

        return

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