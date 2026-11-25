import os
import unittest
from unittest.mock import patch

from app.services.waha_gestao_transporte import ErroGestaoWaha, TransporteGestaoWaha


class GestaoTransporteWahaTest(unittest.TestCase):
    def test_desativada_por_padrao_sem_rede(self):
        with (
            patch.dict(os.environ, {"ORION_WAHA_GESTAO_ATIVA": "0"}),
            patch("app.services.waha_gestao_transporte.requests.request") as request,
        ):
            with self.assertRaisesRegex(ErroGestaoWaha, "gestao_waha_desativada"):
                TransporteGestaoWaha().iniciar("orion-1-ficticia")
            request.assert_not_called()

    def test_estado_sem_credenciais_e_recusa_sessao_divergente(self):
        sessao = "orion-2-ficticia"
        with patch.object(TransporteGestaoWaha, "_requisitar") as requisitar:
            requisitar.return_value = {
                "name": sessao, "status": "WORKING",
                "me": {"id": "5511999999999:3@c.us", "token": "ficticio"},
                "config": {"webhooks": [{"url": "https://interno.invalid"}]},
            }
            self.assertEqual(TransporteGestaoWaha().consultar(sessao), {
                "estado": "WORKING", "numero": "5511999999999",
            })
            with self.assertRaisesRegex(ErroGestaoWaha, "sessao_waha_divergente"):
                TransporteGestaoWaha().consultar("outra")

    def test_recusa_multipla_sessao_e_qr_invalidos_com_erros_sanitizados(self):
        ambiente = {
            "ORION_WAHA_GESTAO_ATIVA": "1", "WAHA_API_KEY": "chave-ficticia",
            "WAHA_API_URL": "http://waha.invalid",
        }
        with (
            patch.dict(os.environ, ambiente),
            patch("app.services.waha_gestao_transporte.requests.request") as request,
        ):
            resposta = request.return_value.__enter__.return_value
            resposta.status_code = 422
            resposta.text = "Only default session is supported. Private data: secret."
            with self.assertRaisesRegex(ErroGestaoWaha, "^limite_sessoes_provedor$"):
                TransporteGestaoWaha().iniciar("orion-1-ficticia")
            self.assertFalse(request.call_args.kwargs["allow_redirects"])
            resposta.status_code = 200
            for blocos in ([b"<html>"], [b"\x89PNG\r\n\x1a\n", bytes(256 * 1024)]):
                resposta.iter_content.return_value = blocos
                with self.assertRaisesRegex(ErroGestaoWaha, "qr_waha_invalido"):
                    TransporteGestaoWaha().qr("orion-1-ficticia")
