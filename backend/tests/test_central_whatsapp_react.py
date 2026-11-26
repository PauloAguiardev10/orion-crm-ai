"""Contratos da Central React com transporte inteiramente simulado."""

import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

with patch.dict(os.environ, {"DATABASE_URL": "sqlite://", "PYTHON_DOTENV_DISABLED": "1"}):
    from app.routes.central_whatsapp_api import router
    from app.services.central_whatsapp_acoes import executar_acao_mensagem
    from app.services.central_whatsapp_eventos import delta


class CentralReactTest(unittest.TestCase):
    def test_sse_exige_credencial_sem_executar_consultas(self):
        app = FastAPI()
        app.include_router(router)
        with TestClient(app) as client, patch(
            "app.services.central_whatsapp_eventos.snapshot", side_effect=HTTPException(403),
        ) as snapshot:
            self.assertEqual(client.get("/api/central-whatsapp/eventos?empresa_id=9").status_code, 401)
            snapshot.assert_not_called()
            resposta = client.get("/api/central-whatsapp/eventos?empresa_id=9", headers={
                "Authorization": "Bearer ficticio",
            })
            self.assertEqual(resposta.status_code, 403)
            self.assertEqual(snapshot.call_args.args[:3], ("ficticio", 9, None))

    def test_sse_delta_preserva_ordem_remove_revogados_e_atualiza_so_o_necessario(self):
        self.assertEqual(delta([{"id": 1}, {"id": 2}], [{"id": 2}, {"id": 3}]), {
            "ordem": [2, 3], "alteradas": [{"id": 3}], "removidas": [1],
        })
        self.assertIsNone(delta([{"id": 9}], None))

    def test_acao_recusa_id_waha_de_outro_chat_sem_rede(self):
        db = Mock()
        mensagem = SimpleNamespace(
            from_me=False, tipo="texto", mensagem_id_waha=None,
            mensagem_id_externo="false_5511999999998@c.us_REAL",
        )
        db.query.return_value.filter_by.return_value.one_or_none.return_value = mensagem
        destino = {"sessao": "default", "chat_id": "5511999999999@c.us", "conexao_canal_id": 3}
        with patch("app.services.central_whatsapp_acoes.preparar_destino_central",
                   return_value=(destino, "destino_autorizado")), patch(
                       "app.services.central_whatsapp_acoes.requests.request",
                   ) as transporte:
            args = {"empresa_id": 1, "usuario_id": 2, "conversa_id": 4, "mensagem_id": 5,
                    "acao": "reagir", "valor": ""}
            with self.assertRaisesRegex(ValueError, "mensagem_indisponivel"):
                executar_acao_mensagem(db, **args)
            transporte.assert_not_called()
            mensagem.mensagem_id_externo = "false_5511999999999@c.us_REAL"
            transporte.return_value.status_code = 200
            with patch.dict(os.environ, {"WAHA_API_URL": "http://waha.invalid", "WAHA_API_KEY": "ficticia"}):
                executar_acao_mensagem(db, **args)
            self.assertEqual(transporte.call_args.args, ("PUT", "http://waha.invalid/api/reaction"))
            self.assertFalse(transporte.call_args.kwargs["allow_redirects"])

    def test_citacao_e_encaminhamento_usam_campos_documentados(self):
        from app.services.followup_transporte_waha import transportar_mensagem_waha
        original = "false_5511999999999@c.us_EXEMPLO"
        with patch.dict(os.environ, {"WAHA_API_URL": "http://waha.invalid", "WAHA_API_KEY": "ficticia"}), patch(
            "app.services.followup_transporte_waha.requests.post",
        ) as post:
            post.return_value.status_code = 200
            post.return_value.json.return_value = {"id": "confirmada"}
            self.assertTrue(transportar_mensagem_waha(
                "default", "5511999999999@c.us", "Resposta", reply_to=original,
            )[0])
            self.assertEqual(post.call_args.kwargs["json"]["reply_to"], original)
            self.assertTrue(transportar_mensagem_waha(
                "default", "5511999999998@c.us", "Encaminhada", encaminhar=original,
            )[0])
            self.assertEqual(post.call_args.args[0], "http://waha.invalid/api/forwardMessage")
            self.assertEqual(post.call_args.kwargs["json"], {
                "session": "default", "chatId": "5511999999998@c.us", "messageId": original,
            })

    def test_busca_contato_avanca_paginas_do_provedor(self):
        from app.services.central_whatsapp_contatos import listar_contatos_waha
        estado = {"name": "default", "status": "WORKING", "engine": "NOWEB",
                  "config": {"noweb": {"store": {"enabled": True}}}}
        lote = [{"id": f"55119999{i:04d}@c.us", "name": "Contato ficticio"} for i in range(50)]
        alvo = {"id": "551199991234@c.us", "name": "Encontrado"}
        with patch.dict(os.environ, {"WAHA_API_URL": "http://waha.invalid", "WAHA_API_KEY": "ficticia"}), patch(
            "app.services.central_whatsapp_contatos.requests.get",
        ) as get:
            get.side_effect = [Mock(status_code=200, json=Mock(return_value=v)) for v in (estado, lote, [alvo])]
            resultado = listar_contatos_waha("default", 0, "encontrado")
            self.assertEqual(resultado["contatos"][0]["nome"], alvo["name"])
            self.assertIsNone(resultado["proxima"])
            self.assertEqual([c.kwargs["params"]["offset"] for c in get.call_args_list[1:]], [0, 50])
