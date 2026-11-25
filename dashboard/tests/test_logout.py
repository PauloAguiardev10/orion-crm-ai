import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from itsdangerous import URLSafeTimedSerializer
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"
COOKIE = "orion_crm_sessao"
SEGREDO = "ficticio-exclusivo-testes-auth-" * 2


class LogoutTest(unittest.TestCase):
    def setUp(self):
        self.cookies = {}
        self.sessoes = {}
        self.contas = {"primeiro": (101, 11), "segundo": (202, 22)}
        manager = Mock()
        manager.get.side_effect = lambda cookie: self.cookies.get(cookie)
        manager.set.side_effect = lambda cookie, token, **_: self.cookies.update({cookie: token})
        manager.delete.side_effect = self.cookies.pop
        self.manager = manager

        def criar_sessao(usuario_id):
            nome = next(nome for nome, (uid, _) in self.contas.items() if uid == usuario_id)
            _, empresa = self.contas[nome]
            token = f"simulado-{len(self.sessoes)}-{usuario_id}"
            self.sessoes[token] = {
                "usuario_id": usuario_id, "empresa_id": empresa, "empresa_nome": f"Empresa {empresa}",
                "usuario": nome, "nome": nome, "nivel": "admin_empresa",
            }
            return token

        self.revogar = Mock(side_effect=lambda token: self.sessoes.pop(token, None) is not None)
        modulos = {
            "extra_streamlit_components": SimpleNamespace(CookieManager=lambda **_: manager),
            "styles.theme": SimpleNamespace(carregar_tema=lambda: None),
            "components.sidebar": SimpleNamespace(render_sidebar=lambda: "\U0001f4ac Conversas"),
            "services.leads_service": SimpleNamespace(carregar_leads=lambda _: None),
            "services.sessao_persistente_service": SimpleNamespace(
                criar_sessao=criar_sessao, validar_sessao=self.sessoes.get, revogar_sessao=self.revogar,
            ),
            "services.auth_service": SimpleNamespace(
                validar_login=lambda usuario, senha: usuario in self.contas and senha == "simulada",
                obter_usuario_id=lambda usuario: self.contas[usuario][0],
                obter_empresa_usuario=lambda usuario: f"Empresa {self.contas[usuario][1]}",
                obter_empresa_id_usuario=lambda usuario: self.contas[usuario][1],
                obter_nivel_usuario=lambda _: "admin_empresa",
            ),
            "utils.bloqueio": SimpleNamespace(empresa_bloqueada=lambda: False, tela_bloqueio=lambda: None),
        }
        for pagina, render in (
            ("visao_geral", "visao_geral"), ("leads", "leads"), ("followup", "followup"),
            ("produtos", "produtos"), ("pedidos", "pedidos"), ("conversas", "conversas"),
            ("especialistas", "especialistas"), ("funil_comercial", "funil"),
            ("servicos_canais", "servicos_canais"), ("resultados", "resultados"),
            ("integracoes", "integracoes"), ("configuracoes", "configuracoes"), ("empresas", "empresas"),
        ):
            modulos[f"app_pages.{pagina}"] = SimpleNamespace(**{f"render_{render}": lambda *_: None})
        self.enterContext(patch.dict(sys.modules, modulos))
        self.enterContext(patch.dict(os.environ, {
            "PYTHON_DOTENV_DISABLED": "1", "ORION_API_AUTH_SECRET": SEGREDO,
        }))

    def login(self, app, usuario):
        app.text_input(key="login_usuario").set_value(usuario)
        app.text_input(key="login_senha").set_value("simulada")
        next(b for b in app.button if b.label.startswith("Entrar")).click().run()
        self.assertFalse(app.exception)
        self.assertTrue(app.session_state["logado"])

    def logout(self, app):
        app.session_state["central_atualizacao"] = {"historico": "cache ficticio"}
        app.session_state["central_anexo_bytes"] = b"ficticio"
        app.session_state["texto_central_7"] = "rascunho ficticio"
        next(b for b in app.button if b.label == "Sair").click().run()
        self.assertFalse(app.exception)
        self.assertFalse(app.session_state["logado"])
        self.assertIsNone(app.session_state["token_sessao_persistente"])
        self.assertIsNone(app.session_state["empresa_ativa_id"])
        for chave in ("token_central", "central_atualizacao", "central_anexo_bytes", "texto_central_7"):
            self.assertNotIn(chave, app.session_state)
        self.assertTrue(any(b.label.startswith("Entrar") for b in app.button))

    def test_login_e_logout_com_cookie(self):
        app = AppTest.from_file(str(APP)).run()
        self.login(app, "primeiro")
        app = AppTest.from_file(str(APP)).run()
        token = self.cookies[COOKIE]
        self.logout(app)
        self.manager.delete.assert_called_once_with(COOKIE)
        self.revogar.assert_called_once_with(token)
        self.assertNotIn(COOKIE, self.cookies)

    def test_logout_com_cookie_ausente_e_novo_login_em_outra_empresa(self):
        app = AppTest.from_file(str(APP)).run()
        self.login(app, "primeiro")
        app = AppTest.from_file(str(APP)).run()
        token = self.cookies.pop(COOKIE)
        self.logout(app)
        self.revogar.assert_called_once_with(token)
        self.login(app, "segundo")
        self.assertEqual(app.session_state["empresa_ativa_id"], 22)
        self.assertEqual(
            URLSafeTimedSerializer(SEGREDO, salt="orion-api-vendedores-v1").loads(app.session_state["token_central"]),
            {"usuario_id": 202, "empresa_id": 22},
        )

    def test_recarga_restaura_login_e_token_respeita_empresa_do_login(self):
        app = AppTest.from_file(str(APP)).run()
        self.login(app, "primeiro")
        app = AppTest.from_file(str(APP)).run()
        self.assertFalse(app.exception)
        self.assertTrue(app.session_state["logado"])
        self.assertEqual(app.session_state["empresa_login_id"], 11)
        app.session_state["empresa_ativa_id"] = 22
        app.run()
        self.assertEqual(
            URLSafeTimedSerializer(SEGREDO, salt="orion-api-vendedores-v1").loads(app.session_state["token_central"]),
            {"usuario_id": 101, "empresa_id": 11},
        )