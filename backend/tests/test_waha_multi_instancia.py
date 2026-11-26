import hashlib
import hmac
import json
import os
import unittest
from unittest.mock import patch

from app.services.followup_transporte_waha import transportar_mensagem_waha
from app.services.waha_destino import ConfiguracaoWahaInvalida, alias_waha, resolver_waha
from app.services.waha_gestao_transporte import ErroGestaoWaha, TransporteGestaoWaha


def configuracao_waha(sessoes):
    ambiente = {}
    instancias = {}
    for instancia, fisicas in sessoes.items():
        api, webhook = f"TEST_API_{instancia}", f"TEST_HMAC_{instancia}"
        ambiente[api], ambiente[webhook] = f"api-{instancia}", f"hmac-{instancia}"
        instancias[instancia] = {
            "origem": f"http://{instancia}.orion.invalid:3000",
            "api_key_env": api, "hmac_env": webhook, "sessoes": fisicas,
        }
    ambiente["ORION_WAHA_INSTANCIAS"] = json.dumps(instancias)
    return ambiente


class WahaMultiInstanciaTest(unittest.TestCase):
    def setUp(self):
        self.a = alias_waha("a", "default")
        self.b = alias_waha("b", "default")
        self.enterContext(patch.dict(os.environ, {
            **configuracao_waha({"a": ["default", "outra"], "b": ["default"]}),
            "WAHA_API_URL": "http://legado.orion.invalid",
            "WAHA_API_KEY": "api-legada", "WAHA_WEBHOOK_HMAC_KEY": "hmac-legado",
        }))

    def test_duas_default_e_legado_seguem_destinos_distintos(self):
        with patch("app.services.followup_transporte_waha.requests.post") as post:
            post.return_value.status_code = 200
            post.return_value.json.return_value = {"id": "id-enviado"}
            for sessao in (self.a, self.b, "default"):
                self.assertTrue(transportar_mensagem_waha(sessao, "123@lid", "teste")[0])
            for chamada, host, chave in zip(
                post.call_args_list, ("a.orion.invalid:3000", "b.orion.invalid:3000", "legado.orion.invalid"),
                ("api-a", "api-b", "api-legada"),
            ):
                self.assertEqual(chamada.args[0], f"http://{host}/api/sendText")
                self.assertEqual(chamada.kwargs["json"]["session"], "default")
                self.assertEqual(chamada.kwargs["headers"], {"X-Api-Key": chave})
                self.assertFalse(chamada.kwargs["allow_redirects"])

    def test_sem_configuracao_nao_cai_no_legado(self):
        os.environ.pop("TEST_API_a")
        with patch("app.services.followup_transporte_waha.requests.post") as post:
            self.assertEqual(transportar_mensagem_waha(self.a, "123@lid", "teste"),
                             (False, "falha_envio", None))
            post.assert_not_called()
        with self.assertRaises(ConfiguracaoWahaInvalida):
            resolver_waha(alias_waha("b", "nao_provisionada"))

    def test_gestao_rejeita_sessao_preexistente_sem_vinculo_e_roteia_qr(self):
        transporte = TransporteGestaoWaha(self.a)
        with patch.object(transporte, "_requisitar") as requisitar:
            requisitar.return_value = {"name": "default", "status": "WORKING"}
            with self.assertRaises(ErroGestaoWaha):
                transporte.consultar(self.a)
            requisitar.return_value["config"] = {"metadata": {"orionSessao": self.a}}
            self.assertEqual(transporte.consultar(self.a)["estado"], "WORKING")
            transporte.qr(self.a)
            requisitar.assert_called_with("GET", "/api/default/auth/qr", imagem=True)
            with self.assertRaises(ErroGestaoWaha):
                transporte.qr(self.b)

    def test_voz_usa_a_instancia_do_anexo(self):
        from app.services.central_whatsapp_midia import enviar_midia_waha

        with patch("app.services.central_whatsapp_midia.requests.post") as post:
            post.return_value.status_code = 200
            post.return_value.json.return_value = {"id": "voz-enviada"}
            self.assertTrue(enviar_midia_waha(
                self.b, "123@lid", "", nome="voz.ogg", mime="audio/ogg", dados=b"ogg-simulado",
            )[0])
            chamada = post.call_args
            self.assertEqual(chamada.args[0], "http://b.orion.invalid:3000/api/sendVoice")
            self.assertEqual(chamada.kwargs["headers"], {"X-Api-Key": "api-b"})
            self.assertEqual(chamada.kwargs["json"]["session"], "default")

    def test_webhook_assina_origem_e_entrega_alias_ao_fluxo_incluindo_ack(self):
        from fastapi.testclient import TestClient
        with patch.dict(os.environ, {
            "DATABASE_URL": "sqlite://", "PYTHON_DOTENV_DISABLED": "1",
            "OPENAI_API_KEY": "chave-ficticia",
        }):
            import main

        evento = {"event": "message.ack", "session": "default", "payload": {"ack": 2}}
        corpo = json.dumps(evento).encode()
        assinatura = hmac.new(b"hmac-a", corpo, hashlib.sha512).hexdigest()
        headers = {"Content-Type": "application/json", "X-Webhook-Hmac-Algorithm": "sha512",
                   "X-Webhook-Hmac": assinatura}
        with TestClient(main.app) as client, patch.object(
            main, "processar_webhook_waha", return_value={"status": "processado"},
        ) as processar:
            self.assertEqual(client.post("/webhook/waha/b", content=corpo, headers=headers).status_code, 401)
            processar.assert_not_called()
            self.assertEqual(client.post("/webhook/waha/a", content=corpo, headers=headers).status_code, 200)
            processar.assert_called_once_with({**evento, "session": self.a}, True)

    def test_saida_da_sofia_usa_a_instancia_e_nao_redireciona(self):
        with patch.dict(os.environ, {
            "DATABASE_URL": "sqlite://", "PYTHON_DOTENV_DISABLED": "1",
            "OPENAI_API_KEY": "chave-ficticia",
        }):
            import main

        with patch.object(main.requests, "post") as post:
            post.return_value.status_code = 200
            post.return_value.json.return_value = {"id": "id-sofia"}
            self.assertEqual(main.enviar_texto_waha(self.a, "123@lid", "teste", {}),
                             (True, None, "id-sofia"))
            self.assertEqual(post.call_args.args[0], "http://a.orion.invalid:3000/api/sendText")
            self.assertEqual(post.call_args.kwargs["json"]["session"], "default")
            self.assertEqual(post.call_args.kwargs["headers"], {"X-Api-Key": "api-a"})
            self.assertFalse(post.call_args.kwargs["allow_redirects"])
