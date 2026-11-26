import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from app_pages import conexoes_whatsapp


class GestaoConexoesWhatsAppPainelTest(unittest.TestCase):
    def test_qr_e_desconexao_exigem_controle_explicito(self):
        png = b"\x89PNG\r\n\x1a\n"
        conexao = {
            "id": 7, "nome": "Sessão simulada", "sofia_ativa": True,
            "gerenciada": True, "suspensa": True, "pareamento_pendente": True, "especialista_id": None,
        }
        estado = {"estado": "SCAN_QR_CODE", "numero": None}

        def api(metodo, caminho, *, corpo=None, imagem=False):
            if caminho == "conexoes":
                return {"plano": "PRO", "limite": 2, "conexoes": [conexao]}
            if caminho.endswith("/estado"):
                return estado
            if caminho.endswith("/qr"):
                self.assertTrue(imagem)
                return png
            self.assertEqual((metodo, caminho, corpo), (
                "POST", "conexoes/7/desconectar", {"confirmar": True},
            ))
            conexao["suspensa"] = True
            estado["estado"] = "STOPPED"
            return {"situacao": "conexao_suspensa"}

        with (
            patch.object(conexoes_whatsapp, "_api", side_effect=api) as transporte,
            patch.object(conexoes_whatsapp, "listar_atendentes_whatsapp", return_value=[]),
            patch.object(conexoes_whatsapp, "html") as exibir,
        ):
            app = AppTest.from_string("""
import streamlit as st
from app_pages.conexoes_whatsapp import render_conexoes_whatsapp
st.session_state.update(nivel='admin_empresa', empresa_ativa_id=1, empresa_login_id=1)
render_conexoes_whatsapp()
""").run()
            transporte.assert_not_called()
            app.toggle[0].set_value(True).run()
            self.assertFalse(app.exception)
            self.assertIn("data:image/png;base64", exibir.call_args.args[0])
            self.assertTrue(app.button(key="desconectar_waha_7").disabled)
            app.checkbox(key="confirmar_waha_7").check().run()
            self.assertFalse(app.button(key="desconectar_waha_7").disabled)
            app.button(key="desconectar_waha_7").click().run()
            self.assertFalse(app.exception)
            self.assertTrue(any("Desconectada" in item.value for item in app.markdown))
