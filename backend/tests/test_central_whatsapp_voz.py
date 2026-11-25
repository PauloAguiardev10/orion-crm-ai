from io import BytesIO
import os
import unittest
import wave

from app.services.central_whatsapp_voz import converter_gravacao


class CentralWhatsAppVozTest(unittest.TestCase):
    def test_validacao_rejeita_tipo_e_assinatura_incompativeis(self):
        for dados, tipo in ((b"texto", "audio/webm"), (b"RIFF", "audio/wav"), (b"x", "video/mp4")):
            with self.subTest(tipo=tipo), self.assertRaisesRegex(ValueError, "gravacao_invalida"):
                converter_gravacao(dados, tipo)

    @unittest.skipUnless(os.getenv("ORION_WAHA_FFMPEG"), "FFmpeg não configurado no ambiente de testes")
    def test_conversao_real_wav_para_opus_e_deterministica(self):
        saida = BytesIO()
        with wave.open(saida, "wb") as arquivo:
            arquivo.setparams((1, 2, 8000, 0, "NONE", "not compressed"))
            arquivo.writeframes(bytes(16_000))
        voz = converter_gravacao(saida.getvalue(), "audio/wav")
        self.assertTrue(voz.startswith(b"OggS"))
        self.assertEqual(voz[28:36], b"OpusHead")
        self.assertEqual(voz, converter_gravacao(saida.getvalue(), "audio/wav"))
