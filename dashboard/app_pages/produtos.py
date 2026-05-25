import streamlit as st

from services.produtos_service import (
    listar_produtos,
    cadastrar_produto,
    atualizar_produto,
    excluir_produto,
)

from utils.permissoes import (
    verificar_permissao,
    tela_upgrade,
)


def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def render_produtos():

    empresa_id = st.session_state.empresa_id

    # =========================================
    # BLOQUEIO PREMIUM
    # =========================================

    if not verificar_permissao("Premium"):

        tela_upgrade(
            "Produtos",
            "Premium"
        )

        return

    st.title("🛒 Produtos")

    produtos = listar_produtos(empresa_id)

    st.markdown("## ➕ Cadastrar produto")

    c1, c2 = st.columns(2)

    with c1:
        nome = st.text_input("Nome do produto")
        categoria = st.text_input("Categoria")
        preco = st.number_input("Preço", min_value=0.0, value=0.0)

    with c2:
        estoque = st.number_input("Estoque", min_value=0, value=0)
        status = st.selectbox("Status", ["ativo", "inativo"])
        imagem_url = st.text_input("Link da imagem")

    descricao = st.text_area("Descrição do produto")

    if st.button("Cadastrar produto", use_container_width=True):

        if cadastrar_produto(
            empresa_id,
            nome,
            categoria,
            descricao,
            preco,
            estoque,
            imagem_url,
            status,
        ):

            st.success("Produto cadastrado com sucesso.")
            st.rerun()

        else:

            st.warning("Informe o nome do produto.")

    st.markdown("---")

    st.markdown("## 📦 Produtos cadastrados")

    if produtos.empty:

        st.info("Nenhum produto cadastrado.")
        return

    st.dataframe(
        produtos,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("---")

    st.markdown("## ⚙️ Gerenciar produto")

    produto_opcoes = {

        f"{row['id']} - {row['nome']}":
        row["id"]

        for _, row in produtos.iterrows()
    }

    produto_escolhido = st.selectbox(
        "Selecionar produto",
        list(produto_opcoes.keys()),
    )

    produto_id = produto_opcoes[
        produto_escolhido
    ]

    produto = produtos[
        produtos["id"] == produto_id
    ].iloc[0]

    g1, g2 = st.columns(2)

    with g1:

        novo_nome = st.text_input(
            "Nome atualizado",
            value=produto["nome"],
        )

        nova_categoria = st.text_input(
            "Categoria atualizada",
            value=produto["categoria"]
            if produto["categoria"]
            else "",
        )

        novo_preco = st.number_input(
            "Preço atualizado",
            min_value=0.0,
            value=float(produto["preco"]),
        )

    with g2:

        novo_estoque = st.number_input(
            "Estoque atualizado",
            min_value=0,
            value=int(produto["estoque"]),
        )

        novo_status = st.selectbox(
            "Status atualizado",
            ["ativo", "inativo"],
            index=["ativo", "inativo"].index(
                produto["status"]
            )
            if produto["status"] in ["ativo", "inativo"]
            else 0,
        )

        nova_imagem = st.text_input(
            "Link imagem atualizado",
            value=produto["imagem_url"]
            if produto["imagem_url"]
            else "",
        )

    nova_descricao = st.text_area(
        "Descrição atualizada",
        value=produto["descricao"]
        if produto["descricao"]
        else "",
    )

    b1, b2 = st.columns(2)

    with b1:

        if st.button(
            "Salvar alterações",
            use_container_width=True
        ):

            atualizar_produto(
                produto_id,
                novo_nome,
                nova_categoria,
                nova_descricao,
                novo_preco,
                novo_estoque,
                nova_imagem,
                novo_status,
            )

            st.success("Produto atualizado.")
            st.rerun()

    with b2:

        if st.button(
            "Excluir produto",
            use_container_width=True
        ):

            excluir_produto(produto_id)

            st.warning("Produto excluído.")
            st.rerun()