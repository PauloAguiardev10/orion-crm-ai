import streamlit as st

from services.followup_configuracoes_service import (
    carregar_configuracoes_followup,
    salvar_configuracoes_followup,
    salvar_modelo_mensagem_followup,
    listar_agendamentos_followup,
)


def render_followup():
    """Interface administrativa do Follow-up Automatico."""


    nivel = st.session_state.get("nivel")
    empresa_id = st.session_state.get(
        "empresa_ativa_id",
        st.session_state.get("empresa_id"),
)

    if nivel not in {
        "orion_admin",
        "parceiro_admin",
        "admin_empresa",
    }:
        st.error("Acesso restrito.")
        return

    if not empresa_id:
        st.warning("Selecione uma empresa para continuar.")
        return

    st.title("Follow-up Autom\u00e1tico")

    st.info(
        "M\u00f3dulo em configura\u00e7\u00e3o. "
        "Os disparos autom\u00e1ticos permanecem desativados."
    )

    try:
        dados = carregar_configuracoes_followup(
            empresa_id,
            nivel=nivel,
            empresa_login_id=st.session_state.get(
                "empresa_login_id"
            ),
        )

    except PermissionError:
        st.error("Empresa n\u00e3o autorizada para este usuário.")
        return

    except Exception as erro:
        st.error(f"Erro ao carregar configura\u00e7\u00f5es: {erro}")
        return

    configuracao = dados["configuracao"]
    mensagens = dados["mensagens"]

    if configuracao is None:
        st.warning(
            "Esta empresa ainda n\u00e3o possui configura\u00e7\u00e3o de Follow-up."
        )
        return

    st.subheader("Editar configura\u00e7\u00f5es")

    with st.form("form_followup_configuracoes"):

        quantidade = st.number_input(
            "Quantidade de tentativas",
            min_value=1,
            max_value=10,
            value=int(configuracao["quantidade_tentativas"]),
            step=1,
        )

        st.markdown("**Segunda a sexta-feira**")

        col1, col2 = st.columns(2)

        with col1:
            semana_inicio = st.time_input(
                "Início",
                value=configuracao["segunda_sexta_inicio"],
                key="followup_semana_inicio",
            )

        with col2:
            semana_fim = st.time_input(
                "Fim",
                value=configuracao["segunda_sexta_fim"],
                key="followup_semana_fim",
            )

        sabado_ativo = st.checkbox(
            "Permitir disparos aos sábados",
            value=bool(configuracao["sabado_ativo"]),
        )

        col3, col4 = st.columns(2)

        with col3:
            sabado_inicio = st.time_input(
                "Início no sábado",
                value=configuracao["sabado_inicio"],
            )

        with col4:
            sabado_fim = st.time_input(
                "Fim no sábado",
                value=configuracao["sabado_fim"],
            )

        domingo_ativo = st.checkbox(
            "Permitir disparos aos domingos",
            value=bool(configuracao["domingo_ativo"]),
        )

        salvar = st.form_submit_button(
            "Salvar configura\u00e7\u00f5es",
            type="primary",
        )

    if salvar:
        try:
            salvar_configuracoes_followup(
                empresa_id,
                nivel=nivel,
                empresa_login_id=st.session_state.get(
                    "empresa_login_id"
                ),
                quantidade_tentativas=int(quantidade),
                segunda_sexta_inicio=semana_inicio,
                segunda_sexta_fim=semana_fim,
                sabado_ativo=sabado_ativo,
                sabado_inicio=sabado_inicio,
                sabado_fim=sabado_fim,
                domingo_ativo=domingo_ativo,
            )

        except Exception as erro:
            st.error(f"Não foi possível salvar: {erro}")

        else:
            st.success("Configurações salvas com sucesso.")
            st.rerun()

    st.subheader("Modelos de mensagens")
    st.dataframe(mensagens, use_container_width=True)


    st.subheader("Personalizar mensagens")

    st.caption(
        "Configure o texto e o intervalo de cada tentativa. "
        "Salvar nao ativa os disparos automaticos."
    )

    for modelo in mensagens:
        numero = int(modelo["numero_tentativa"])
        intervalo_atual = int(modelo["intervalo_minutos"])

        with st.expander(
            f"Tentativa {numero}",
            expanded=(numero == 1),
        ):
            with st.form(f"form_followup_modelo_{numero}"):

                mensagem = st.text_area(
                    "Mensagem enviada ao lead",
                    value=str(modelo["texto"]),
                    max_chars=4000,
                    height=140,
                    key=f"followup_texto_{numero}",
                )

                intervalo = st.number_input(
                    "Intervalo antes do envio (minutos)",
                    min_value=1,
                    max_value=43200,
                    value=intervalo_atual,
                    step=1,
                    key=f"followup_intervalo_{numero}",
                )

                estado_tentativa = st.selectbox(
                    "Estado da tentativa",
                    options=["Habilitada", "Desabilitada"],
                    index=0 if bool(modelo["ativo"]) else 1,
                    key=f"followup_estado_{empresa_id}_{numero}",
                )

                ativo = estado_tentativa == "Habilitada"

                salvar_modelo = st.form_submit_button(
                    "Salvar mensagem",
                    type="primary",
                )

            if salvar_modelo:
                try:
                    salvar_modelo_mensagem_followup(
                        empresa_id,
                        nivel=nivel,
                        empresa_login_id=st.session_state.get(
                            "empresa_login_id"
                        ),
                        numero_tentativa=numero,
                        intervalo_minutos=int(intervalo),
                        texto=mensagem,
                        ativo=ativo,
                    )

                except Exception as erro:
                    st.error(f"Erro ao salvar mensagem: {erro}")

                else:
                    st.success("Mensagem salva com sucesso.")
                    st.rerun()


    st.divider()
    st.subheader("Monitoramento do Follow-up")

    try:
        agendamentos = listar_agendamentos_followup(
            empresa_id,
            nivel=nivel,
            empresa_login_id=st.session_state.get(
                "empresa_login_id"
            ),
        )
    except PermissionError:
        st.error("Acesso nao autorizado ao monitoramento.")
        return
    except Exception as erro:
        st.error(f"Erro ao carregar monitoramento: {erro}")
        return

    estados = {
        "pendente": "Pendentes",
        "processando": "Processando",
        "enviado": "Enviados",
        "cancelado": "Cancelados",
        "falha": "Falhas",
        "inconclusivo": "Inconclusivos",
    }

    contagens = {
        estado: sum(
            1 for item in agendamentos
            if item["status"] == estado
        )
        for estado in estados
    }

    colunas = st.columns(3)

    for indice, (estado, titulo) in enumerate(estados.items()):
        with colunas[indice % 3]:
            st.metric(titulo, contagens[estado])

    st.caption(
        "Indicadores referentes aos ultimos "
        f"{len(agendamentos)} agendamentos consultados."
    )

    if not agendamentos:
        st.info("Nenhum agendamento encontrado para esta empresa.")
        return

    opcoes = ["Todos"] + list(estados.values())

    filtro = st.selectbox(
        "Filtrar por status",
        options=opcoes,
        key="followup_filtro_status",
    )

    if filtro == "Todos":
        registros = agendamentos
    else:
        estado_selecionado = next(
            estado
            for estado, titulo in estados.items()
            if titulo == filtro
        )
        registros = [
            item for item in agendamentos
            if item["status"] == estado_selecionado
        ]

    st.dataframe(
        [
            {
                "Agendamento": item["id"],
                "Lead": item["lead_id"],
                "Tentativa": item["numero_tentativa"],
                "Programado para": item["agendado_para"],
                "Status": item["status"],
                "Tentativas de envio": item["tentativas_envio"],
                "Enviado em": item["enviado_em"],
                "Cancelado em": item["cancelado_em"],
                "Erro": item["erro_envio"],
            }
            for item in registros
        ],
        use_container_width=True,
        hide_index=True,
    )
