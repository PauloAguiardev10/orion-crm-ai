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

    st.markdown(
        """
        <style>
        .produtos-section-card {
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

        .produtos-section-card::before {
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

        .produtos-section-title {
            color: #FFFFFF;
            font-size: 15px;
            font-weight: 850;
            margin-left: 5px;
            margin-bottom: 4px;
        }

        .produtos-section-subtitle {
            color: #94A3B8;
            font-size: 13px;
            margin-left: 5px;
        }

        .produtos-empty-card {
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

        .produtos-empty-card strong {
            color: #FFFFFF;
        }

        .produto-management-empty {
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

    st.markdown("## ➕ Cadastrar produto")

    st.markdown(
        """
        <div class="produtos-section-card">
            <div class="produtos-section-title">Novo produto</div>
            <div class="produtos-section-subtitle">
                Cadastre informações comerciais, preço, estoque e imagem do produto.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

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

    st.markdown(
        """
        <div class="produtos-section-card">
            <div class="produtos-section-title">Catálogo da empresa</div>
            <div class="produtos-section-subtitle">
                Consulte os produtos disponíveis, estoque, preço e situação atual.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if produtos.empty:

        st.markdown(
            """
            <div class="produtos-empty-card">
                <strong>Nenhum produto cadastrado ainda.</strong><br>
                O catálogo aparecerá aqui assim que o primeiro produto for criado.
            </div>
            """,
            unsafe_allow_html=True,
        )

    else:

        st.dataframe(
            produtos,
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("---")

    st.markdown("## ⚙️ Gerenciar produto")

    st.markdown(
        """
        <div class="produtos-section-card">
            <div class="produtos-section-title">Gestão do produto</div>
            <div class="produtos-section-subtitle">
                Atualize dados, estoque, status e informações comerciais do item selecionado.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if produtos.empty:

        st.markdown(
            """
            <div class="produto-management-empty">
                Nenhum produto disponível para edição no momento.<br>
                Quando um produto for cadastrado, os controles de gerenciamento aparecerão nesta área.
            </div>
            """,
            unsafe_allow_html=True,
        )

        return

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