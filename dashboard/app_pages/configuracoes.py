import streamlit as st

from database.db import conectar

from services.configuracoes_service import (
    carregar_especialistas,
    carregar_servicos,
    cadastrar_especialista,
    cadastrar_servico,
    carregar_ids_servicos_especialista,
    excluir_especialista_por_nome,
    excluir_servico,
)

from services.usuarios_service import (
    listar_usuarios,
    criar_usuario,
    alterar_senha,
)


def limpar_formularios():
    st.session_state["reset_config"] = (
        st.session_state.get("reset_config", 0) + 1
    )


def excluir_usuario(usuario_id, usuario_nome, empresa_id):
    excluir_especialista_por_nome(
        usuario_nome,
        empresa_id,
    )

    conn = conectar()

    try:

        with conn.cursor() as cursor:

            cursor.execute("""
                DELETE FROM usuarios
                WHERE id = %s
            """, (
                int(usuario_id),
            ))

        conn.commit()

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()


def render_configuracoes():

    empresa_id = st.session_state.empresa_id
    reset_key = st.session_state.get("reset_config", 0)

    st.title("⚙️ Configurações Operacionais")

    st.markdown(
        """
        <style>
        .config-section-card {
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

        .config-section-card::before {
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

        .config-section-title {
            color: #FFFFFF;
            font-size: 15px;
            font-weight: 850;
            margin-left: 5px;
            margin-bottom: 4px;
        }

        .config-section-subtitle {
            color: #94A3B8;
            font-size: 13px;
            margin-left: 5px;
        }

        .config-empty-card {
            background:
                radial-gradient(circle at 50% 0%, rgba(99,102,241,.09), transparent 44%),
                linear-gradient(145deg, rgba(15,23,42,.96), rgba(3,8,20,.95));
            border: 1px dashed rgba(99,102,241,.40);
            border-radius: 18px;
            padding: 24px 20px;
            margin: 10px 0 16px 0;
            color: #CBD5E1;
            text-align: center;
            box-shadow: 0 0 24px rgba(99,102,241,.06);
        }

        .config-empty-card strong {
            color: #FFFFFF;
        }

        .config-info-card {
            background:
                radial-gradient(circle at 0% 0%, rgba(168,85,247,.08), transparent 40%),
                linear-gradient(145deg, rgba(15,23,42,.96), rgba(3,8,20,.95));
            border: 1px solid rgba(168,85,247,.24);
            border-left: 4px solid #A855F7;
            border-radius: 18px;
            padding: 18px 20px;
            color: #CBD5E1;
            box-shadow: 0 0 24px rgba(168,85,247,.06);
            margin: 8px 0 14px 0;
        }

        [data-testid="stDataFrame"] {
            border: 1px solid rgba(34,211,238,.24);
            border-radius: 18px;
            overflow: hidden;
            box-shadow:
                0 0 28px rgba(34,211,238,.055),
                0 12px 30px rgba(0,0,0,.16);
        }

        [data-testid="stTextInput"] > div > div,
        [data-testid="stSelectbox"] > div > div,
        [data-testid="stMultiSelect"] > div > div {
            border-radius: 12px !important;
        }

        [data-testid="stTextInput"] > div > div:focus-within,
        [data-testid="stSelectbox"] > div > div:focus-within,
        [data-testid="stMultiSelect"] > div > div:focus-within {
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

    st.markdown(
        """
        <div class="config-section-card">
            <div class="config-section-title">Gestão operacional da empresa</div>
            <div class="config-section-subtitle">
                Centralize usuários, acessos, especialidades e responsáveis comerciais.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("## 👤 Usuários / Especialistas da Empresa")

    usuarios = listar_usuarios()
    usuarios_empresa = usuarios

    if not usuarios.empty:
        usuarios_empresa = usuarios[
            usuarios["empresa"] == st.session_state.empresa
        ]

        st.dataframe(
            usuarios_empresa,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.markdown(
            """
            <div class="config-empty-card">
                <strong>Nenhum usuário cadastrado ainda.</strong><br>
                A estrutura de gestão permanece disponível para o primeiro cadastro.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### ➕ Criar funcionário")

    st.markdown(
        """
        <div class="config-section-card">
            <div class="config-section-title">Novo funcionário</div>
            <div class="config-section-subtitle">
                Crie um acesso para administrador da empresa ou usuário operacional.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    u1, u2 = st.columns(2)

    with u1:
        novo_usuario = st.text_input(
            "Usuário novo",
            key=f"novo_usuario_{reset_key}"
        )

    with u2:
        nova_senha = st.text_input(
            "Senha do novo usuário",
            type="password",
            key=f"nova_senha_{reset_key}"
        )

        nivel = st.selectbox(
            "Nível de acesso",
            ["admin_empresa", "usuario"],
            index=None,
            placeholder="Selecione o nível de acesso",
            key=f"nivel_{reset_key}"
        )

    if st.button("Criar usuário"):

        if not novo_usuario.strip():
            st.warning("Informe o nome do usuário.")

        elif not nova_senha.strip():
            st.warning("Informe a senha do usuário.")

        elif not nivel:
            st.warning("Selecione o nível de acesso.")

        elif criar_usuario(
            novo_usuario,
            nova_senha,
            st.session_state.empresa,
            nivel,
            empresa_id,
        ):
            st.success("Usuário criado com sucesso.")
            limpar_formularios()
            st.rerun()

        else:
            st.error("Não foi possível criar o usuário.")

    st.markdown("### 🗑️ Excluir funcionário")

    usuarios_lista_excluir = []

    if not usuarios_empresa.empty:
        usuarios_lista_excluir = [
            f"{row['id']} - {row['usuario']}"
            for _, row in usuarios_empresa.iterrows()
        ]

    if usuarios_lista_excluir:

        usuario_excluir = st.selectbox(
            "Selecionar funcionário para excluir",
            usuarios_lista_excluir,
            index=None,
            placeholder="Selecione um funcionário",
            key=f"usuario_excluir_{reset_key}"
        )

        if st.button("Excluir usuário"):

            if not usuario_excluir:
                st.warning("Selecione um funcionário para excluir.")

            else:
                usuario_id = usuario_excluir.split(" - ")[0]
                usuario_nome = usuario_excluir.split(" - ", 1)[1]

                excluir_usuario(
                    usuario_id,
                    usuario_nome,
                    empresa_id,
                )

                st.success("Usuário excluído com sucesso.")
                limpar_formularios()
                st.rerun()

    else:
        st.markdown(
            """
            <div class="config-empty-card">
                Nenhum usuário disponível para exclusão.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### 🔑 Alterar senha")

    usuarios_lista = []

    if not usuarios_empresa.empty:
        usuarios_lista = usuarios_empresa["usuario"].tolist()

    if usuarios_lista:

        usuario_alterar = st.selectbox(
            "Selecionar usuário",
            usuarios_lista,
            index=None,
            placeholder="Selecione um usuário",
            key=f"usuario_alterar_{reset_key}"
        )

        nova_senha_alterar = st.text_input(
            "Nova senha",
            type="password",
            key=f"nova_senha_alterar_{reset_key}"
        )

        if st.button("Alterar senha"):

            if not usuario_alterar:
                st.warning("Selecione um usuário.")

            elif not nova_senha_alterar.strip():
                st.warning("Informe a nova senha.")

            elif alterar_senha(
                usuario_alterar,
                nova_senha_alterar,
            ):
                st.success("Senha alterada com sucesso.")
                limpar_formularios()
                st.rerun()

            else:
                st.error("Não foi possível alterar a senha.")

    else:
        st.markdown(
            """
            <div class="config-empty-card">
                Nenhum usuário disponível para alterar senha.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    st.markdown("## 🧩 Serviços / Especialidades")

    st.markdown(
        """
        <div class="config-section-card">
            <div class="config-section-title">Serviços e especialidades</div>
            <div class="config-section-subtitle">
                Cadastre os serviços atendidos pela equipe e vincule-os aos especialistas.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    novo_servico = st.text_input(
        "Novo serviço ou especialidade",
        key=f"novo_servico_{reset_key}"
    )

    if st.button("Cadastrar Serviço"):

        if novo_servico.strip():
            cadastrar_servico(
                novo_servico,
                empresa_id,
            )

            st.success("Serviço cadastrado.")
            limpar_formularios()
            st.rerun()

        else:
            st.warning("Informe o nome do serviço.")

    servicos = carregar_servicos(empresa_id)

    if not servicos.empty:

        st.dataframe(
            servicos,
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("### 🗑️ Excluir especialidade")

        servico_excluir = st.selectbox(
            "Selecionar especialidade",
            [
                f"{row['id']} - {row['nome']}"
                for _, row in servicos.iterrows()
            ],
            index=None,
            placeholder="Selecione uma especialidade",
            key=f"servico_excluir_{reset_key}"
        )

        if st.button("Excluir especialidade"):

            if not servico_excluir:
                st.warning("Selecione uma especialidade para excluir.")

            else:
                servico_id = servico_excluir.split(" - ")[0]

                excluir_servico(
                    servico_id,
                    empresa_id,
                )

                st.success("Especialidade excluída com sucesso.")
                limpar_formularios()
                st.rerun()

    else:
        st.markdown(
            """
            <div class="config-empty-card">
                Nenhum serviço ou especialidade cadastrado ainda.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    st.markdown("## 👨‍💼 Especialistas / Atendentes")

    st.markdown(
        """
        <div class="config-info-card">
            Os especialistas são os próprios usuários cadastrados da empresa.
            Selecione um funcionário e vincule as especialidades que ele atende.
        </div>
        """,
        unsafe_allow_html=True,
    )

    especialistas = carregar_especialistas(empresa_id)

    funcionarios = []

    if not usuarios_empresa.empty:
        funcionarios = usuarios_empresa["usuario"].tolist()

    if not funcionarios:

        st.markdown(
            """
            <div class="config-empty-card">
                <strong>Cadastre um funcionário antes de vincular especialidades.</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )

    else:

        funcionario_selecionado = st.selectbox(
            "Selecionar funcionário",
            funcionarios,
            index=None,
            placeholder="Selecione um funcionário",
            key=f"funcionario_especialista_{reset_key}"
        )

        if funcionario_selecionado:

            opcoes_servicos = {
                row["nome"]: row["id"]
                for _, row in servicos.iterrows()
            } if not servicos.empty else {}

            ids_atuais = carregar_ids_servicos_especialista(
                funcionario_selecionado,
                empresa_id,
            )

            nomes_atuais = [
                nome
                for nome, servico_id in opcoes_servicos.items()
                if servico_id in ids_atuais
            ]

            especialidades = st.multiselect(
                "Especialidades que esse funcionário atende",
                list(opcoes_servicos.keys()),
                default=nomes_atuais,
                key=f"especialidades_{funcionario_selecionado}_{reset_key}"
            )

            servicos_ids = [
                opcoes_servicos[nome]
                for nome in especialidades
            ]

            if st.button("Salvar especialidades do funcionário"):

                cadastrar_especialista(
                    funcionario_selecionado,
                    servicos_ids,
                    empresa_id,
                )

                st.success("Especialidades atualizadas com sucesso.")
                limpar_formularios()
                st.rerun()

        else:
            st.markdown(
                """
                <div class="config-empty-card">
                    Selecione um funcionário para configurar as especialidades.
                </div>
                """,
                unsafe_allow_html=True,
            )

    if not especialistas.empty:

        st.dataframe(
            especialistas,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.markdown(
            """
            <div class="config-empty-card">
                Nenhum especialista configurado ainda.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    st.success("Configurações operacionais salvas por empresa.")