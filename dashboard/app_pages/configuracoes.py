import streamlit as st

from database.db import conectar

from services.configuracoes_service import (
    carregar_especialistas,
    carregar_servicos,
    cadastrar_especialista,
    cadastrar_servico,
)

from services.usuarios_service import (
    listar_usuarios,
    criar_usuario,
    alterar_senha,
)


def excluir_usuario(usuario):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM usuarios
        WHERE usuario = ?
    """, (usuario,))

    conn.commit()

    removido = cursor.rowcount > 0

    conn.close()

    return removido


def render_configuracoes():
    empresa_id = st.session_state.empresa_id

    st.title("⚙️ Configurações Operacionais")

    st.markdown("## 👤 Usuários da Empresa")

    usuarios = listar_usuarios()

    usuarios_empresa = []

    if not usuarios.empty:
        usuarios_empresa = usuarios[
            usuarios["empresa"] == st.session_state.empresa
        ]

        st.dataframe(
            usuarios_empresa,
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("### ➕ Criar funcionário")

    u1, u2 = st.columns(2)

    with u1:
        novo_usuario = st.text_input("Usuário novo")

    with u2:
        nova_senha = st.text_input(
            "Senha do novo usuário",
            type="password",
        )

        nivel = st.selectbox(
            "Nível de acesso",
            [
                "admin_empresa",
                "usuario",
            ],
        )

    if st.button("Criar usuário"):
        if criar_usuario(
            novo_usuario,
            nova_senha,
            st.session_state.empresa,
            nivel,
        ):
            st.success("Usuário criado com sucesso.")
            st.rerun()
        else:
            st.error("Não foi possível criar o usuário.")

    st.markdown("### 🔑 Alterar senha")

    usuarios_lista = []

    if not usuarios.empty:
        usuarios_lista = usuarios[
            usuarios["empresa"] == st.session_state.empresa
        ]["usuario"].tolist()

    usuario_alterar = st.selectbox(
        "Selecionar usuário",
        usuarios_lista,
        key="usuario_alterar_senha",
    )

    nova_senha_alterar = st.text_input(
        "Nova senha",
        type="password",
    )

    if st.button("Alterar senha"):
        if alterar_senha(
            usuario_alterar,
            nova_senha_alterar,
        ):
            st.success("Senha alterada com sucesso.")
        else:
            st.error("Não foi possível alterar a senha.")

    st.markdown("### 🗑️ Excluir usuário")

    usuario_excluir = st.selectbox(
        "Selecionar usuário para excluir",
        usuarios_lista,
        key="usuario_excluir",
    )

    confirmar_exclusao = st.checkbox(
        "Confirmo que desejo excluir este usuário"
    )

    if st.button("Excluir usuário"):
        if not confirmar_exclusao:
            st.warning("Marque a confirmação antes de excluir.")
        elif usuario_excluir == st.session_state.usuario:
            st.error("Você não pode excluir o usuário que está logado.")
        else:
            if excluir_usuario(usuario_excluir):
                st.success("Usuário excluído com sucesso.")
                st.rerun()
            else:
                st.error("Não foi possível excluir o usuário.")

    st.markdown("---")

    st.markdown("## 🧩 Serviços / Especialidades")

    novo_servico = st.text_input("Novo serviço ou especialidade")

    if st.button("Cadastrar Serviço"):
        cadastrar_servico(
            novo_servico,
            empresa_id,
        )

        st.success("Serviço cadastrado.")
        st.rerun()

    servicos = carregar_servicos(empresa_id)

    if not servicos.empty:
        st.dataframe(
            servicos,
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("---")

    st.markdown("## 👨‍💼 Especialistas")

    especialistas = carregar_especialistas(empresa_id)

    nome_especialista = st.text_input("Nome do especialista")

    opcoes_servicos = {
        row["nome"]: row["id"]
        for _, row in servicos.iterrows()
    }

    especialidades = st.multiselect(
        "Especialidades que esse especialista atende",
        list(opcoes_servicos.keys()),
    )

    servicos_ids = [
        opcoes_servicos[nome]
        for nome in especialidades
    ]

    if st.button("Cadastrar / Atualizar Especialista"):
        cadastrar_especialista(
            nome_especialista,
            servicos_ids,
            empresa_id,
        )

        st.success("Especialista cadastrado.")
        st.rerun()

    if not especialistas.empty:
        st.dataframe(
            especialistas,
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("---")

    st.success("Configurações operacionais salvas por empresa.")