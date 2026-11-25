import os
import unittest
from unittest.mock import Mock, patch

from app.services.central_whatsapp_midia import baixar_midia_waha, enviar_midia_waha, validar_midia


class MidiaWhatsAppTest(unittest.TestCase):
    def test_rejeita_travessia_sessao_e_arquivo_alheio(self):
        with patch("app.services.central_whatsapp_midia.requests.get") as get:
            for caminho in (
                "/api/files/outra/mensagem.pdf", "/api/files/outro.pdf",
                "/api/files/%2e%2e/mensagem.pdf", "/admin/mensagem.pdf",
            ):
                with self.subTest(caminho=caminho), self.assertRaises(ValueError):
                    baixar_midia_waha(
                        {"mimetype": "application/pdf", "url": "http://waha.invalido" + caminho},
                        sessao="sessao-teste", mensagem_id="mensagem",
                    )
            get.assert_not_called()

    def test_busca_somente_na_origem_configurada_e_sem_redirecionamento(self):
        ambiente = {"WAHA_API_URL": "http://waha.invalido", "WAHA_API_KEY": "ficticia"}
        with (
            patch.dict(os.environ, ambiente),
            patch("app.services.central_whatsapp_midia.requests.get") as get,
        ):
            resposta = get.return_value.__enter__.return_value
            resposta.status_code = 200
            resposta.iter_content.return_value = [b"%PDF-", b"1.7"]
            resultado = baixar_midia_waha({
                "mimetype": "application/pdf", "url": "http://169.254.169.254/api/files/mensagem.pdf",
            }, sessao="sessao-teste", mensagem_id="mensagem")
            self.assertEqual(resultado, ("anexo.pdf", "application/pdf", b"%PDF-1.7"))
            self.assertEqual(get.call_args.args[0], "http://waha.invalido/api/files/mensagem.pdf")
            self.assertFalse(get.call_args.kwargs["allow_redirects"])

    def test_rota_waha_por_formato_e_falha_inconclusiva(self):
        formatos = (
            ("image/jpeg", "a.jpg", b"\xff\xd8\xff", "sendImage"),
            ("image/png", "a.png", b"\x89PNG\r\n\x1a\n", "sendImage"),
            ("audio/ogg", "a.ogg", b"OggS" + bytes(24) + b"OpusHead", "sendVoice"),
            ("video/mp4", "a.mp4", bytes(4) + b"ftyp", "sendVideo"),
            ("application/pdf", "a.pdf", b"%PDF-1.7", "sendFile"),
        )
        with (
            patch.dict(os.environ, {"WAHA_API_KEY": "ficticia"}),
            patch("app.services.central_whatsapp_midia.requests.post") as post,
        ):
            post.return_value = Mock(status_code=502)
            for mime, nome, dados, rota in formatos:
                with self.subTest(mime=mime):
                    self.assertEqual(validar_midia(nome, mime, dados), mime)
                    self.assertEqual(enviar_midia_waha(
                        "sessao-teste", "123@c.us", "", nome=nome, mime=mime, dados=dados,
                    ), (False, "timeout_envio_inconclusivo", None))
                    self.assertTrue(post.call_args.args[0].endswith("/api/" + rota))
                    self.assertEqual(post.call_args.kwargs["json"]["session"], "sessao-teste")
                    self.assertFalse(post.call_args.kwargs["allow_redirects"])
