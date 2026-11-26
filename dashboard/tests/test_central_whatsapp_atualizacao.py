import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from app_pages import conversas


class CentralWhatsAppAtualizacaoTest(unittest.TestCase):
    def test_atualizacao_preserva_selecao_rascunho_e_nao_lidas(self):
        primeira = {
            "id": 1, "nome": "Ana", "especialista_id": 7, "especialista_usuario_id": 42,
            "pode_assumir": True, "humano_assumiu": True, "status_atendimento": "em_atendimento_humano",
        }
        segunda = {"id": 2, "nome": "Bob", "ultima_recebida_id": 20}
        lista = [primeira, segunda]
        historico = [{
            "id": 10, "from_me": True, "texto": "Mensagem fictícia",
            "status_envio": "aceito_waha", "criado_em": "2026-11-25T09:30:00",
        }]
        with (
            patch.object(conversas, "listar_conversas_whatsapp", side_effect=lambda **_: list(lista)),
            patch.object(conversas, "listar_mensagens_whatsapp", side_effect=lambda **_: list(historico)),
            patch.object(conversas, "listar_filtros_whatsapp", return_value=[]),
            patch.object(conversas, "marcar_leitura_whatsapp", side_effect=lambda **kw: kw["mensagem_id"]),
            patch.object(conversas, "gravar_voz", return_value=None),
            patch.object(conversas, "consultar_contexto_whatsapp", return_value={
                "empresa_cliente": "Empresa de teste", "score": 0, "resumo_vendedor": "Resumo fictício",
            }) as contexto,
            patch.object(conversas, "consultar_pendencias_central_api", return_value=(True, {"pendencias": []})),
            patch("requests.sessions.Session.request", side_effect=AssertionError("Rede proibida")),
        ):
            app = AppTest.from_string("""
import streamlit as st
from app_pages.conversas import render_central_whatsapp
st.session_state.update(usuario_id=42, token_central='ficticio', empresa_ativa_id=1, empresa_login_id=1)
render_central_whatsapp()
""").run()
            seletor = "central_whatsapp_conversa_42_1"
            self.assertFalse(app.exception)
            self.assertTrue(any("Bob" in caption.value for caption in app.caption))
            app.button(key="orion_wa_abrir_1").click().run()
            app.text_area(key="texto_central_1").set_value("Rascunho preservado").run()

            lista.reverse()
            historico[0]["status_envio"] = "lida_waha"
            historico.append({"id": 11, "from_me": False, "remetente": "cliente", "texto": "Nova mensagem"})
            app.run()

            self.assertFalse(app.exception)
            self.assertEqual(app.session_state[seletor], 1)
            self.assertEqual(app.text_area(key="texto_central_1").value, "Rascunho preservado")
            self.assertTrue(any("09:30" in m.value and "Lida" in m.value for m in app.markdown))
            self.assertTrue(any("Nova mensagem" in m.value for m in app.markdown))
            self.assertTrue(any("Empresa de teste" in m.value for m in app.markdown))
            self.assertEqual(app.session_state["central_atualizacao"]["vistas"], {1: 11})
            contexto.reset_mock()
            app.toggle(key="orion_wa_recolher_42_1").set_value(True).run()
            self.assertEqual(app.session_state[seletor], 1)
            self.assertEqual(app.text_area(key="texto_central_1").value, "Rascunho preservado")
            contexto.assert_not_called()
