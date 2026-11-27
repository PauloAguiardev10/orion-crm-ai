from services.central_whatsapp_api import (
    gerenciar_atendimento_api,
    obter_anexo_api,
    reservar_anexo_api,
    reservar_mensagem_api,
    executar_mensagem_api,
    consultar_status_mensagem_api,
    consultar_pendencias_central_api,
)
from app_pages.conexoes_whatsapp import render_conexoes_whatsapp
from app_pages.gravador_voz import gravar_voz
from app_pages.central_whatsapp_layout import (
    ESTILO_CENTRAL, STATUS_ATENDIMENTO, cartao_contato, horario, nome_contato, render_balao, render_ficha,
)
from uuid import uuid4
from contextlib import nullcontext
import os
from pathlib import Path
import requests
from base64 import b64encode
from html import escape
import streamlit as st
import streamlit.components.v1 as components
from streamlit.components.v1 import html as render_html



from services.central_whatsapp_service import (
    SessaoCentralExpirada,
    consultar_contexto_whatsapp,
    listar_atendentes_whatsapp,
    listar_conversas_whatsapp,
    listar_filtros_whatsapp,
    listar_mensagens_whatsapp,
    marcar_leitura_whatsapp,
)


def render_acoes_atendimento(conversa, *, usuario_id, token, empresa_id):
    conversa_id = conversa["id"]
    responsavel_id = conversa.get("especialista_id")
    proprio = conversa.get("especialista_usuario_id") == usuario_id
    ativo = (
        conversa.get("humano_assumiu") is True
        and conversa.get("status_atendimento") == "em_atendimento_humano"
    )

    def alterar(acao, **dados):
        sucesso, mensagem = gerenciar_atendimento_api(
            acao=acao, conversa_id=conversa_id, token=token, empresa_id=empresa_id, **dados,
        )
        if sucesso:
            st.session_state["central_atendimento_resultado"] = mensagem
            st.rerun()
        st.error(mensagem)

    if conversa.get("pode_assumir") and not ativo:
        if st.button("Assumir atendimento", key=f"assumir_whatsapp_{conversa_id}"):
            alterar("assumir")

    if ativo and responsavel_id is not None and (proprio or conversa.get("pode_supervisionar")):
        if conversa.get("corporativa"):
            try:
                atendentes = {
                    item["id"]: item["nome"]
                    for item in listar_atendentes_whatsapp(token=token, empresa_id=empresa_id)
                    if item["id"] != responsavel_id
                }
            except SessaoCentralExpirada:
                st.warning("Sua sessão da Central expirou. Entre novamente no CRM.")
                atendentes = {}
            except Exception:
                st.error("Não foi possível carregar os atendentes autorizados.")
                atendentes = {}
            if atendentes:
                destino = st.selectbox(
                    "Transferir para", list(atendentes), format_func=atendentes.get,
                    index=None, key=f"destino_whatsapp_{conversa_id}",
                )
                if st.button("Transferir atendimento", disabled=destino is None,
                             key=f"transferir_whatsapp_{conversa_id}"):
                    alterar("transferir", responsavel_atual_id=responsavel_id, destino_id=destino)
        if st.button("Encerrar atendimento", key=f"encerrar_whatsapp_{conversa_id}"):
            alterar("encerrar", responsavel_atual_id=responsavel_id)


def render_anexo_whatsapp(mensagem, *, conversa_id, empresa_id, token):
    mime = mensagem.get("midia_tipo")
    if not mensagem.get("tem_anexo"):
        if mensagem.get("tipo") in ("midia", "imagem", "audio", "video", "documento"):
            st.caption("Anexo indisponível")
        return
    chave = (empresa_id, conversa_id, mensagem["id"])
    chave_estado = "central_anexo_aberto"
    if st.session_state.get(chave_estado) != chave:
        if not st.button("Abrir anexo", key=f"abrir_anexo_{mensagem['id']}"):
            return
        st.session_state[chave_estado] = chave
        st.rerun()
    identidade_anexo = (token, chave)
    armazenado = st.session_state.get("central_anexo_bytes")
    try:
        if armazenado is not None and armazenado[0] == identidade_anexo:
            _, dados, nome = armazenado
        else:
            dados, nome = obter_anexo_api(
                conversa_id=conversa_id, mensagem_id=mensagem["id"],
                empresa_id=empresa_id, token=token,
            )
            st.session_state["central_anexo_bytes"] = (identidade_anexo, dados, nome)
    except (ValueError, OSError):
        st.caption("Anexo indisponível")
        return
    # Entrega os bytes apenas na sessão Streamlit que passou pela autorização.
    if mime not in ("image/jpeg", "image/png", "audio/ogg", "video/mp4", "application/pdf"):
        return
    origem = f"data:{mime};base64,{b64encode(dados).decode('ascii')}"
    nome = escape(nome, quote=True)
    if mime.startswith("image/"):
        html = f'<img src="{origem}" alt="{nome}" style="max-width:100%;height:auto">'
        altura = 360
    elif mime == "audio/ogg":
        html = (f'<audio controls preload="none" src="{origem}" style="max-width:100%"></audio>'
                '<select aria-label="Velocidade de reprodução" '
                'onchange="document.querySelector(\'audio\').playbackRate=Number(this.value)">'
                '<option value="1">1x</option><option value="1.5">1,5x</option>'
                '<option value="2">2x</option></select>')
        altura = 90
    elif mime == "video/mp4":
        html = f'<video controls preload="none" src="{origem}" style="max-width:100%"></video>'
        altura = 360
    else:
        html = f'<a href="{origem}" download="{nome}">Baixar {nome}</a>'
        altura = 45
    render_html(html, height=altura, scrolling=True)


ROTULOS_ENVIO = {
    "aceito_waha": "Aceita pela WAHA",
    "enviada_waha": "Enviada",
    "entregue_waha": "Entregue",
    "lida_waha": "Lida",
    "falha_envio": "Falha no envio",
    "erro_waha": "Falha no envio",
    "timeout_envio_inconclusivo": "Envio inconclusivo",
}


def rotulo_envio(mensagem):
    if mensagem.get("from_me") is not True:
        return None
    estado = mensagem.get("status_envio")
    if estado is None and mensagem.get("remetente") in ("humano", "agente"):
        if mensagem.get("status_processamento") in ("recebida", "processando"):
            return "Aguardando envio"
    return ROTULOS_ENVIO.get(estado)


def render_importacao_noweb(conversa, *, token, empresa_id):
    conexao_id = conversa.get("conexao_canal_id")
    if not conexao_id:
        return
    with st.expander("Sincronizar hist?rico NOWEB"):
        st.caption("Importa texto e dados dispon?veis deste contato. Use somente em conversas autorizadas.")
        confirmar = st.checkbox("Confirmo a importação desta conversa", key=f"confirmar_noweb_{conversa['id']}")
        if not st.button("Importar hist?rico", disabled=not confirmar, key=f"importar_noweb_{conversa['id']}"):
            return
        origem = os.getenv("ORION_API_INTERNA_URL", "http://127.0.0.1:8000").rstrip("/")
        try:
            resultado = requests.post(
                f"{origem}/api/central-whatsapp/conexoes/{conexao_id}/historico/{conversa['id']}",
                params={"empresa_id": empresa_id}, headers={"Authorization": f"Bearer {token}"},
                json={"confirmar": True}, timeout=35, allow_redirects=False,
            )
            if resultado.status_code == 200:
                st.success(f"Mensagens importadas: {resultado.json()['importadas']}.")
                return
        except (requests.RequestException, ValueError):
            pass
        st.warning("Histórico NOWEB indisponível para esta conversa.")


def render_inicio_conversa(*, token, empresa_id, selecao, sufixo):
    if not st.toggle("Nova conversa", key=f"nova_conversa_{sufixo}"):
        return
    endpoint = os.getenv("ORION_API_INTERNA_URL", "http://127.0.0.1:8000").rstrip("/")
    endpoint += "/api/central-whatsapp/conversas/iniciar"
    credenciais = {"headers": {"Authorization": f"Bearer {token}"},
                    "params": {"empresa_id": empresa_id}, "timeout": 8, "allow_redirects": False}
    try:
        resposta = requests.get(endpoint, **credenciais)
        if resposta.status_code != 200:
            st.warning("Conexões indispon?veis.")
            return
        conexoes = {item["id"]: item["nome"] for item in resposta.json()}
        if not conexoes:
            st.info("Nenhuma conexão disponível para iniciar conversa.")
            return
        with st.form(f"form_nova_conversa_{sufixo}"):
            conexao = st.selectbox("Conexão para envio", conexoes, format_func=conexoes.get)
            telefone = st.text_input("Telefone com c?digo do pa?s", max_chars=16)
            iniciar = st.form_submit_button("Abrir atendimento")
        if iniciar:
            resposta = requests.post(endpoint, json={"conexao_id": conexao, "telefone": telefone.strip()},
                                     **credenciais)
            if resposta.status_code == 201:
                st.session_state[selecao] = resposta.json()["id"]
                st.rerun()
            st.warning("Não foi possível abrir a conversa. Confira o telefone e a conexão escolhida.")
    except (requests.RequestException, ValueError):
        st.warning("Serviço de novas conversas indisponível.")


def render_central_whatsapp():
    usuario_id = st.session_state.get("usuario_id")
    token = st.session_state.get("token_central")
    empresa_id = st.session_state.get("empresa_ativa_id")
    if not usuario_id or not token:
        st.warning("Entre novamente no CRM para acessar a Central WhatsApp.")
        return

    escopo = (usuario_id, empresa_id, token)
    sufixo = f"{usuario_id}_{empresa_id}"
    estado_local = st.session_state.get("central_atualizacao")
    if estado_local is None or estado_local["escopo"] != escopo:
        estado_local = {
            "escopo": escopo, "lista": {}, "historico": {}, "detalhes": {},
            "vistas": {}, "filtros": {},
        }
        st.session_state["central_atualizacao"] = estado_local
        st.session_state.pop("central_anexo_bytes", None)
    chave_selecao = f"central_whatsapp_conversa_{sufixo}"
    fixar = st.session_state.get(chave_selecao)
    filtros = {
        nome: st.session_state.get(f"orion_wa_{nome}_{sufixo}")
        for nome in ("busca", "conexao_id", "responsavel_id", "status")
    }
    consulta = (fixar, *filtros.values())
    if estado_local.get("consulta") != consulta:
        estado_local["lista"].clear()
        estado_local["consulta"] = consulta

    with st.container(key="orion_whatsapp"):
        st.markdown(ESTILO_CENTRAL, unsafe_allow_html=True)
        st.image(str(Path(__file__).resolve().parents[1] / "assets" / "logo_orion.png"), width=132)
        st.markdown(
            '<div class="orion-wa-hero"><div class="orion-wa-heading">Central WhatsApp</div>'
            '<div class="orion-wa-muted">Conversas e atendimento comercial</div></div>',
            unsafe_allow_html=True,
        )
        ocultar_ficha = st.toggle("Recolher informações comerciais", key=f"orion_wa_recolher_{sufixo}")
        paineis = st.columns([1, 2.4] if ocultar_ficha else [1, 2, 1], gap="medium")

        try:
            conversas = listar_conversas_whatsapp(
                token=token, empresa_id=empresa_id, fixar_conversa_id=fixar,
                cache=estado_local["lista"], **filtros,
            )
        except SessaoCentralExpirada:
            st.warning("Sua sessão da Central expirou. Entre novamente no CRM.")
            return
        except Exception:
            st.error("Não foi possível atualizar as conversas WhatsApp.")
            return

        por_id = {item["id"]: item for item in conversas}
        selecionada = fixar if fixar in por_id else None
        if estado_local.get("aberta") != selecionada:
            estado_local["historico"].clear()
            estado_local["detalhes"].clear()
            estado_local["anteriores"] = {}
            estado_local["sem_anteriores"] = False
            estado_local["ultima_pagina"] = []
            estado_local["aberta"] = selecionada
            st.session_state.pop("central_anexo_bytes", None)

        vistas = estado_local["vistas"]
        for item in conversas:
            lida = item.get("ultima_lida_id") or 0
            if lida:
                vistas[item["id"]] = max(vistas.get(item["id"], 0), lida)
        with paineis[0], st.container(key="orion_wa_lista_painel"):
            st.markdown("**Conversas**")
            render_inicio_conversa(token=token, empresa_id=empresa_id, selecao=chave_selecao, sufixo=sufixo)
            try:
                opcoes = listar_filtros_whatsapp(token=token, empresa_id=empresa_id, cache=estado_local["filtros"])
            except (ValueError, requests.RequestException, SessaoCentralExpirada):
                opcoes = []
            render_lista_conversas(conversas, opcoes, estado_local, vistas, selecionada, chave_selecao, sufixo)

        if selecionada is None:
            with paineis[1]:
                st.info("Selecione uma conversa para abrir o atendimento.")
            return

        conversa = por_id[selecionada]
        with paineis[1]:
            st.markdown('<span class="orion-wa-mobile-conversa"></span>', unsafe_allow_html=True)
            if st.button("Voltar às conversas", key="orion_wa_voltar"):
                st.session_state[chave_selecao] = None
                st.rerun()
            cartao_contato(conversa)
            if st.toggle("Mostrar foto do contato", key=f"foto_contato_{sufixo}_{selecionada}"):
                origem = os.getenv("ORION_API_INTERNA_URL", "http://127.0.0.1:8000").rstrip("/")
                try:
                    foto = requests.get(
                        f"{origem}/api/central-whatsapp/conversas/{selecionada}/foto",
                        params={"empresa_id": empresa_id}, headers={"Authorization": f"Bearer {token}"},
                        timeout=12, allow_redirects=False,
                    )
                    if foto.status_code == 200:
                        st.image(foto.content, width=48)
                    else:
                        st.caption("Foto indisponível.")
                except requests.RequestException:
                    st.caption("Foto indisponível.")
            estado = conversa.get("status_atendimento")
            if estado:
                st.caption(STATUS_ATENDIMENTO.get(estado, estado))
            resultado = st.session_state.pop("central_atendimento_resultado", None)
            if resultado:
                st.success(resultado)
            try:
                mensagens = listar_mensagens_whatsapp(
                    token=token, conversa_id=selecionada, empresa_id=empresa_id,
                    cache=estado_local["historico"],
                )
            except SessaoCentralExpirada:
                st.warning("Sua sessão da Central expirou. Entre novamente no CRM.")
                return
            except Exception:
                st.warning("O histórico está temporariamente indisponível.")
                return

            recebidas = [
                item["id"] for item in mensagens
                if item.get("from_me") is False and item.get("remetente") == "cliente"
            ]
            if recebidas and max(recebidas) > vistas.get(selecionada, 0):
                try:
                    vistas[selecionada] = marcar_leitura_whatsapp(
                        token=token, empresa_id=empresa_id, conversa_id=selecionada, mensagem_id=max(recebidas),
                    )
                except (ValueError, KeyError, requests.RequestException):
                    pass
            anteriores = estado_local["anteriores"]
            if anteriores and mensagens:
                ids_recentes = {m["id"] for m in mensagens}
                for item in estado_local["ultima_pagina"]:
                    if item["id"] not in ids_recentes:
                        anteriores[item["id"]] = item
            estado_local["ultima_pagina"] = mensagens
            por_mensagem = {**anteriores, **{item["id"]: item for item in mensagens}}
            historico = sorted(por_mensagem.values(), key=lambda item: (item.get("criado_em") or "", item["id"]))
            if historico and (len(mensagens) >= 100 or anteriores) and not estado_local["sem_anteriores"]:
                if st.button("Carregar mensagens anteriores", key=f"orion_wa_anteriores_{selecionada}"):
                    try:
                        pagina = listar_mensagens_whatsapp(
                            token=token, conversa_id=selecionada, empresa_id=empresa_id,
                            limite=50, antes_id=historico[0]["id"],
                        )
                        anteriores.update((item["id"], item) for item in pagina)
                        estado_local["sem_anteriores"] = len(pagina) < 50
                        historico = [item for item in pagina if item["id"] not in por_mensagem] + historico
                    except (ValueError, requests.RequestException, SessaoCentralExpirada):
                        st.warning("Não foi possível carregar mensagens anteriores.")
            termo = st.text_input("Pesquisar nas mensagens carregadas",
                                  key=f"orion_wa_pesquisa_historico_{sufixo}_{selecionada}").strip().casefold()
            visiveis = [m for m in historico if not termo or termo in (m.get("texto") or "").casefold()]
            with st.container(height=495, key=f"orion_wa_historico_{selecionada}", autoscroll=False):
                if not visiveis:
                    st.info("Nenhuma mensagem encontrada." if termo else "Nenhuma mensagem registrada.")
                dia_anterior = None
                for mensagem in visiveis:
                    data = horario(mensagem.get("criado_em"))
                    dia = data.date() if data else None
                    if dia and dia != dia_anterior:
                        st.markdown(
                            f'<div class="orion-wa-data">{dia:%d/%m/%Y}</div>', unsafe_allow_html=True,
                        )
                    dia_anterior = dia
                    lado = "enviada" if mensagem.get("from_me") else "recebida"
                    balao = (
                        st.container(key=f"orion_wa_voz_{lado}_{mensagem['id']}")
                        if mensagem.get("midia_tipo") == "audio/ogg" else nullcontext()
                    )
                    with balao:
                        render_balao(mensagem, data, rotulo_envio(mensagem))
                        render_anexo_whatsapp(
                            mensagem, conversa_id=selecionada, empresa_id=empresa_id, token=token,
                        )
            render_compositor(conversa, mensagens, usuario_id=usuario_id, empresa_id=empresa_id)

        if not ocultar_ficha:
            with paineis[2]:
                st.markdown("**Informações comerciais**")
                try:
                    detalhes = consultar_contexto_whatsapp(
                        token=token, empresa_id=empresa_id, conversa_id=selecionada,
                        cache=estado_local["detalhes"],
                    )
                except requests.HTTPError as erro:
                    detalhes = {}
                    if erro.response is None or erro.response.status_code != 404:
                        st.caption("Dados comerciais temporariamente indisponíveis.")
                except (ValueError, requests.RequestException, SessaoCentralExpirada):
                    detalhes = {}
                    st.caption("Dados comerciais temporariamente indisponíveis.")
                render_ficha(conversa, detalhes)
                if st.session_state.get("nivel") in ("orion_admin", "parceiro_admin", "admin_empresa"):
                    render_importacao_noweb(conversa, token=token, empresa_id=empresa_id)
                render_acoes_atendimento(
                    conversa, usuario_id=int(usuario_id), token=token, empresa_id=empresa_id,
                )


def render_lista_conversas(conversas, opcoes, estado, vistas, selecionada, chave_selecao, sufixo):
    conexoes = {
        item["conexao_id"]: item["nome_conexao"] or f"Conexão #{item['conexao_id']}"
        for item in opcoes
    }
    responsaveis = {
        item["responsavel_id"]: item["responsavel_nome"]
        for item in opcoes if item["responsavel_id"] is not None
    }
    st.text_input(
        "Pesquisar contatos e conversas", placeholder="Nome, número ou última mensagem",
        key=f"orion_wa_busca_{sufixo}", max_chars=120,
    )
    with st.expander("Filtros"):
        st.selectbox(
            "Conexão", [None, *conexoes], key=f"orion_wa_conexao_id_{sufixo}",
            format_func=lambda item: conexoes.get(item, "Todas as conexões"),
        )
        st.selectbox(
            "Responsável", [None, 0, *responsaveis], key=f"orion_wa_responsavel_id_{sufixo}",
            format_func=lambda item: "Não atribuído" if item == 0 else responsaveis.get(item, "Todos os responsáveis"),
        )
        st.selectbox(
            "Status", [None, *STATUS_ATENDIMENTO], key=f"orion_wa_status_{sufixo}",
            format_func=lambda item: STATUS_ATENDIMENTO.get(item, "Todos os status"),
        )
    def tem_nao_lida(item):
        return item["id"] != selecionada and (item.get("ultima_recebida_id") or 0) > vistas.get(item["id"], 0)

    nao_lidas = [nome_contato(item) for item in conversas if tem_nao_lida(item)]
    if nao_lidas:
        st.caption(f"Não lidas ({len(nao_lidas)}) · " + ", ".join(nao_lidas[:3]))

    if not conversas:
        st.info("Nenhuma conversa encontrada.")
        return

    consulta = estado["consulta"][1:]
    if estado.get("filtros_pagina") != consulta:
        estado["filtros_pagina"] = consulta
        estado["pagina"] = 0
    tamanho = 12
    pagina = min(estado["pagina"], (len(conversas) - 1) // tamanho)
    with st.container(height=495, key="orion_wa_lista"):
        for item in conversas[pagina * tamanho:(pagina + 1) * tamanho]:
            conversa_id = item["id"]
            classe = "ativa" if conversa_id == selecionada else "linha"
            with st.container(key=f"orion_wa_{classe}_{conversa_id}"):
                cartao_contato(item, lista=True, nao_lida=tem_nao_lida(item))
                if st.button(
                    "Aberta" if conversa_id == selecionada else "Abrir",
                    key=f"orion_wa_abrir_{conversa_id}", disabled=conversa_id == selecionada,
                    help=f"Abrir conversa de {nome_contato(item)}",
                ):
                    st.session_state[chave_selecao] = conversa_id
                    st.rerun()
    if len(conversas) > tamanho:
        anterior, seguinte = st.columns(2)
        if anterior.button("Anterior", disabled=pagina == 0, key="orion_wa_pagina_anterior"):
            estado["pagina"] = pagina - 1
            st.rerun()
        if seguinte.button("Próxima", disabled=(pagina + 1) * tamanho >= len(conversas), key="orion_wa_pagina_seguinte"):
            estado["pagina"] = pagina + 1
            st.rerun()


def render_compositor(conversa, mensagens, *, usuario_id, empresa_id):
    pode_responder = (
        conversa.get("pode_assumir") is True
        and not conversa.get("sofia_institucional")
        and not conversa.get("operacao_suspensa")
        and conversa.get("status_atendimento") != "finalizado"
        and empresa_id in (None, st.session_state.get("empresa_login_id"))
    )

    if pode_responder:
        st.markdown("**Responder pelo WhatsApp**")

        chave_texto = f"texto_central_{conversa['id']}"
        chave_pendente = f"pendente_central_{conversa['id']}"

        if chave_pendente not in st.session_state:
            st.session_state[chave_pendente] = None

        pendente = st.session_state[chave_pendente]
        if pendente and pendente.get("mensagem_id") is not None:
            estado_pendente = next((
                m.get("status_envio") for m in mensagens if m["id"] == pendente["mensagem_id"]
            ), None)
            if estado_pendente in ROTULOS_ENVIO and estado_pendente != "timeout_envio_inconclusivo":
                st.session_state[chave_pendente] = None
                pendente = None

        if pendente is not None:
            st.warning(
                "Existe uma solicitacao pendente ou inconclusiva. "
                "Nao envie novamente antes de verificar."
            )

            mensagem_id_pendente = pendente.get("mensagem_id")

            if mensagem_id_pendente is None:
                st.info(
                    "Reserva sem confirmacao. Consulte os registros "
                    "antes de liberar uma nova tentativa."
                )
            elif st.button(
                "Verificar status",
                key=f"status_central_{conversa['id']}",
            ):
                consultado, resultado = consultar_status_mensagem_api(
                    conversa_id=int(conversa["id"]),
                    mensagem_id=int(mensagem_id_pendente),
                    token=st.session_state.get("token_central", ""),
                )

                if not consultado:
                    st.error(
                        "Consulta indisponivel: "
                        + str(resultado.get("situacao"))
                    )
                else:
                    status = resultado.get("status_envio")
                    if status in ("aceito_waha", "enviada_waha", "entregue_waha", "lida_waha"):
                        st.success(ROTULOS_ENVIO[status])
                        st.session_state[chave_pendente] = None
                    elif status in ("falha_envio", "erro_waha"):
                        st.session_state[chave_pendente] = None
                        st.error(
                            "Falha de envio registrada. "
                            "Nenhum reenvio automatico sera realizado."
                        )
                    elif status == "timeout_envio_inconclusivo":
                        st.warning(
                            "Envio inconclusivo. "
                            "Verifique no WhatsApp antes de prosseguir."
                        )
                    else:
                        st.info(
                            "Mensagem ainda sem resultado de envio."
                        )
        else:
            consulta_ok, dados_pendencias = consultar_pendencias_central_api(
                conversa_id=int(conversa["id"]),
                token=st.session_state.get("token_central", ""),
            )

            if not consulta_ok:
                st.error(
                    "Nao foi possivel verificar pendencias: "
                    + str(dados_pendencias.get("situacao"))
                )
                st.warning(
                    "Envio bloqueado ate confirmar o estado no banco."
                )
            elif dados_pendencias.get("pendencias"):
                st.warning(
                    "Existem mensagens pendentes ou inconclusivas "
                    "registradas no banco. Nenhum novo envio sera iniciado."
                )
                for item in dados_pendencias["pendencias"]:
                    st.caption(
                        f"Mensagem {item['mensagem_id']} | "
                        f"Processamento: {item['status_processamento']} | "
                        f"Envio: {item['status_envio']}"
                    )

                    if st.button(
                        "Verificar status da mensagem "
                        + str(item["mensagem_id"]),
                        key=f"verificar_banco_{conversa['id']}_{item['mensagem_id']}",
                    ):
                        consultado, resultado = consultar_status_mensagem_api(
                            conversa_id=int(conversa["id"]),
                            mensagem_id=int(item["mensagem_id"]),
                            token=st.session_state.get("token_central", ""),
                        )

                        if consultado:
                            st.info(
                                "Processamento: "
                                + str(resultado.get("status_processamento"))
                                + " | Envio: "
                                + str(resultado.get("status_envio"))
                            )
                        else:
                            st.error(
                                "Consulta indisponivel: "
                                + str(resultado.get("situacao"))
                            )
            else:
                chave_voz = f"orion_voz_geracao_{conversa['id']}"
                geracao = st.session_state.get(chave_voz, 0)
                with st.form(f"form_envio_central_{conversa['id']}"):
                    texto_resposta = st.text_area(
                        "Digite sua mensagem",
                        max_chars=4096,
                        height=80,
                        key=chave_texto,
                    )
                    anexos, microfone, envio = st.columns([1, 1.6, 1])
                    with anexos.popover("Anexar arquivo", icon=":material/attach_file:"):
                        anexo = st.file_uploader(
                            "Arquivo",
                            type=["jpg", "jpeg", "png", "ogg", "opus", "mp4", "pdf"],
                            max_upload_size=8,
                            key=f"arquivo_central_{conversa['id']}",
                        )
                    with microfone:
                        gravacao = gravar_voz(f"voz_{conversa['id']}_{geracao}")
                    enviar = envio.form_submit_button(
                        "Enviar mensagem", type="primary", icon=":material/send:",
                    )

                if enviar:
                    if gravacao and anexo:
                        st.error("Envie a gravação e o arquivo em mensagens separadas.")
                    elif not texto_resposta.strip() and anexo is None and gravacao is None:
                        st.error("Digite uma mensagem ou anexe um arquivo.")
                    elif anexo is not None and anexo.size > 8 * 1024 * 1024:
                        st.error("O anexo excede 8 MB.")
                    else:
                        chave_solicitacao = uuid4().hex

                        st.session_state[chave_pendente] = {
                            "chave": chave_solicitacao,
                            "texto": texto_resposta.strip(),
                        }

                        argumentos = (
                            {"texto": texto_resposta.strip()} if anexo is None
                            else {"legenda": texto_resposta.strip(), "arquivo": anexo}
                        )
                        reservar = reservar_mensagem_api if anexo is None else reservar_anexo_api
                        if gravacao:
                            argumentos = {"legenda": "", "arquivo": gravacao, "gravacao": True}
                            reservar = reservar_anexo_api
                        sucesso, dados = reservar(
                            conversa_id=int(conversa["id"]),
                            chave_solicitacao=chave_solicitacao,
                            token=st.session_state.get(
                                "token_central", ""
                            ),
                            **argumentos,
                        )

                        if not sucesso:
                            situacao = dados.get("situacao")
                            http_status = dados.get("http_status")

                            if http_status in (400, 401, 403, 404, 409, 411, 413, 422, 503):
                                st.session_state[chave_pendente] = None

                            st.error(
                                "Reserva nao confirmada: "
                                + str(situacao)
                            )
                        elif dados.get("situacao") != "envio_reservado":
                            st.warning(
                                "Solicitacao ja existente. "
                                "Nenhum novo envio foi iniciado."
                            )
                        else:
                            mensagem_id = dados["mensagem_id"]
                            st.session_state[chave_pendente][
                                "mensagem_id"
                            ] = int(mensagem_id)

                            enviado, resultado = executar_mensagem_api(
                                conversa_id=int(conversa["id"]),
                                mensagem_id=int(mensagem_id),
                                token=st.session_state.get(
                                    "token_central", ""
                                ),
                            )

                            if enviado:
                                st.session_state[chave_pendente] = None
                                if gravacao:
                                    st.session_state[chave_voz] = geracao + 1
                                st.success(
                                    "Mensagem aceita pelo WAHA."
                                )
                                st.rerun()
                            else:
                                st.error(
                                    "Envio nao confirmado: "
                                    + str(resultado.get("situacao"))
                                )


def central_react_disponivel():
    return bool(os.getenv("ORION_CENTRAL_UI_URL", "").strip() and st.session_state.get("token_central"))


def render_conversas(leads):
    if not central_react_disponivel():
        render_conexoes_whatsapp()
        central, comercial = st.tabs(["Central WhatsApp", "Histórico comercial"],
                                     key="orion_wa_aba", on_change="rerun")
        if central.open:
            with central:
                st.fragment(run_every=10)(render_central_whatsapp)()
        if comercial.open:
            with comercial:
                render_historico_comercial(leads)
        return

    central, comercial, gestao = st.tabs(["Central WhatsApp", "Histórico comercial", "Conexões"],
                                        key="orion_wa_abas_react", on_change="rerun")
    if central.open:
        with central:
            st.markdown("""
<style>
.stMain:has(.st-key-orion_central_area) {overflow:hidden}
.stMainBlockContainer:has(.st-key-orion_central_area) {
  padding: 0 .6rem 0 !important; max-width:none; box-sizing:border-box;
}
.st-key-orion_central_area iframe {
  display:block; width:100%; height:calc(100dvh - 6rem) !important;
  border:0;
}
@media(max-width:720px) {
  .stMainBlockContainer:has(.st-key-orion_central_area) {padding:0 .2rem 0 !important}
  .st-key-orion_central_area iframe {height:calc(100dvh - 6rem) !important}
}
</style>
""", unsafe_allow_html=True)
            with st.container(key="orion_central_area"):
                componente = components.declare_component(
                    "orion_central_whatsapp", url=os.getenv("ORION_CENTRAL_UI_URL").strip(),
                )
                componente(token=st.session_state["token_central"],
                           empresa=st.session_state.get("empresa_ativa_id"),
                           usuario=st.session_state.get("usuario_id"), key="orion_central_react")
    if comercial.open:
        with comercial:
            render_historico_comercial(leads)
    if gestao.open:
        with gestao:
            render_conexoes_whatsapp()


def render_historico_comercial(leads):
    st.title("💬 Conversas")

    st.markdown(
        """
        <style>
        .conversas-shell {
            background:
                radial-gradient(circle at 0% 0%, rgba(34,211,238,.08), transparent 36%),
                linear-gradient(145deg, rgba(15,23,42,.96), rgba(3,8,20,.95));
            border: 1px solid rgba(34,211,238,.22);
            border-radius: 18px;
            padding: 16px 18px;
            margin: 8px 0 18px 0;
            box-shadow: 0 0 26px rgba(34,211,238,.06);
        }

        .conversas-shell-title {
            color: #FFFFFF;
            font-size: 15px;
            font-weight: 800;
            margin-bottom: 4px;
        }

        .conversas-shell-subtitle {
            color: #94A3B8;
            font-size: 13px;
        }

        .conversa-empty {
            background:
                radial-gradient(circle at 50% 0%, rgba(99,102,241,.09), transparent 44%),
                linear-gradient(145deg, rgba(15,23,42,.96), rgba(3,8,20,.95));
            border: 1px dashed rgba(99,102,241,.38);
            border-radius: 18px;
            padding: 28px 20px;
            text-align: center;
            color: #CBD5E1;
            margin: 10px 0 18px 0;
            box-shadow: 0 0 24px rgba(99,102,241,.06);
        }

        .conversa-empty strong {
            color: #FFFFFF;
        }

        .conversa-info-card {
            background:
                linear-gradient(145deg, rgba(15,23,42,.97), rgba(3,8,20,.96));
            border: 1px solid rgba(34,211,238,.20);
            border-radius: 18px;
            padding: 18px;
            margin: 10px 0 18px 0;
            box-shadow: 0 0 24px rgba(34,211,238,.055);
        }

        .conversa-meta-line {
            color: #CBD5E1;
            font-size: 14px;
            margin-bottom: 7px;
        }

        .conversa-meta-line strong {
            color: #FFFFFF;
        }

        .conversa-resumo-card {
            background:
                radial-gradient(circle at 0% 0%, rgba(168,85,247,.10), transparent 38%),
                linear-gradient(145deg, rgba(15,23,42,.97), rgba(3,8,20,.96));
            border: 1px solid rgba(168,85,247,.26);
            border-left: 4px solid #A855F7;
            border-radius: 18px;
            padding: 18px 20px;
            margin: 8px 0 16px 0;
            box-shadow: 0 0 26px rgba(168,85,247,.07);
            color: #E2E8F0;
            line-height: 1.65;
        }

        .conversa-historico-card {
            background:
                radial-gradient(circle at 0% 0%, rgba(34,211,238,.08), transparent 38%),
                linear-gradient(145deg, rgba(15,23,42,.97), rgba(3,8,20,.96));
            border: 1px solid rgba(34,211,238,.24);
            border-left: 4px solid #22D3EE;
            border-radius: 18px;
            padding: 18px 20px;
            margin: 8px 0 16px 0;
            box-shadow: 0 0 26px rgba(34,211,238,.065);
            color: #E2E8F0;
            line-height: 1.6;
            white-space: pre-wrap;
        }

        [data-testid="stMetric"] {
            background:
                linear-gradient(145deg, rgba(15,23,42,.97), rgba(3,8,20,.96));
            border: 1px solid rgba(34,211,238,.24);
            border-radius: 18px;
            padding: 14px 16px;
            box-shadow: 0 0 24px rgba(34,211,238,.055);
        }

        [data-testid="stSelectbox"] > div > div {
            border-radius: 12px !important;
        }

        [data-testid="stSelectbox"] > div > div:focus-within {
            border-color: rgba(34,211,238,.68) !important;
            box-shadow:
                0 0 0 1px rgba(34,211,238,.16),
                0 0 18px rgba(34,211,238,.09) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="conversas-shell">
            <div class="conversas-shell-title">Central de conversas comerciais</div>
            <div class="conversas-shell-subtitle">
                Consulte o contexto da lead, indicadores, resumo comercial e histórico completo.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if leads.empty:
        st.markdown(
            """
            <div class="conversa-empty">
                <strong>Nenhuma conversa encontrada ainda.</strong><br>
                Quando uma lead iniciar atendimento, os dados aparecerão nesta estrutura.
            </div>
            """,
            unsafe_allow_html=True,
        )

        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric("Canal", "—")

        with c2:
            st.metric("Score", "0")

        with c3:
            st.metric("Temperatura", "—")

        st.markdown(
            """
            <div class="conversa-info-card">
                <div class="conversa-meta-line"><strong>Responsável:</strong> Não atribuído</div>
                <div class="conversa-meta-line"><strong>Status:</strong> Aguardando atendimento</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("## 🧠 Resumo Comercial")

        st.markdown(
            """
            <div class="conversa-resumo-card">
                Resumo ainda não disponível para esta conversa.
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("## 💬 Histórico da Conversa")

        st.markdown(
            """
            <div class="conversa-historico-card">
                Histórico real ainda não disponível.
            </div>
            """,
            unsafe_allow_html=True,
        )

        return

    leads = leads.copy()

    colunas_padrao = {
        "id": 0,
        "produto": "Produto não informado",
        "origem": "WhatsApp",
        "canal": None,
        "responsavel": "Não atribuído",
        "score": 0,
        "temperatura": "Não informada",
        "status": "Aguardando atendimento",
        "historico": "",
        "resumo_vendedor": "",
    }

    for coluna, padrao in colunas_padrao.items():
        if coluna not in leads.columns:
            leads[coluna] = padrao

    if "canal" not in leads.columns or leads["canal"].isna().all():
        leads["canal"] = leads["origem"]

    leads["opcao_conversa"] = leads.apply(
        lambda row: f"#{row['id']} | {row['produto']} | {row['canal']}",
        axis=1
    )

    conversa_escolhida = st.selectbox(
        "Selecione uma conversa:",
        leads["opcao_conversa"].tolist()
    )

    lead = leads[
        leads["opcao_conversa"] == conversa_escolhida
    ].iloc[0]

    st.subheader(f"🧩 {lead['produto']}")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("Canal", lead["canal"])

    with c2:
        st.metric("Score", lead["score"])

    with c3:
        st.metric("Temperatura", lead["temperatura"])

    st.markdown(
        f"""
        <div class="conversa-info-card">
            <div class="conversa-meta-line">
                <strong>Responsável:</strong> {escape(str(lead['responsavel']))}
            </div>
            <div class="conversa-meta-line">
                <strong>Status:</strong> {escape(str(lead['status']))}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    st.markdown("## 🧠 Resumo Comercial")

    resumo = str(lead["resumo_vendedor"]).strip()

    if resumo and resumo.lower() not in ["none", "nan"]:
        st.markdown(
            f"""
            <div class="conversa-resumo-card">
                {escape(resumo)}
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="conversa-resumo-card">
                Resumo ainda não disponível para esta conversa.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    st.markdown("## 💬 Histórico da Conversa")

    historico = str(lead["historico"]).strip()

    if historico and historico.lower() not in ["none", "nan"]:
        st.markdown(
            f"""
            <div class="conversa-historico-card">
                {escape(historico)}
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="conversa-historico-card">
                Histórico real ainda não disponível para esta lead.
            </div>
            """,
            unsafe_allow_html=True,
        )
