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
    def test_worker_inicia_novamente_apos_reiniciar_fastapi(self):
        from threading import Event
        from app.services.central_whatsapp_sync import ciclo_sync_noweb

        iniciado = Event()
        def worker(parar):
            iniciado.set()
            parar.wait()

        app = FastAPI(lifespan=ciclo_sync_noweb)
        with patch.dict(os.environ, {"ORION_WAHA_HISTORICO_ATIVO": "1"}), patch(
            "app.services.central_whatsapp_sync._executar_worker", side_effect=worker,
        ) as executar:
            for _ in range(2):
                iniciado.clear()
                with TestClient(app):
                    self.assertTrue(iniciado.wait(2))
                self.assertTrue(executar.call_args.args[0].is_set())
            self.assertEqual(executar.call_count, 2)

    def test_nova_sessao_comercial_configura_store_antes_de_iniciar(self):
        from app.services.waha_gestao_transporte import TransporteGestaoWaha

        sessao = "orion-waha:piloto:default"
        rota = SimpleNamespace(sessao="default", chave_hmac="chave-teste",
                               webhook="https://crm.invalid/webhook/waha/piloto")
        transporte = TransporteGestaoWaha(sessao)
        with patch.object(transporte, "_destino", return_value=rota), patch.object(transporte, "_requisitar") as http:
            transporte.criar(sessao)
            dados = http.call_args.kwargs["corpo"]
            self.assertEqual(http.call_args.args, ("POST", "/api/sessions"))
            self.assertEqual(dados["name"], "default")
            self.assertIs(dados["start"], False)
            self.assertEqual(dados["config"]["noweb"], {"store": {"enabled": True, "fullSync": True}})
            self.assertEqual(dados["config"]["metadata"]["orionSessao"], sessao)

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

    def test_citacao_recebida_e_telefone_lid_exigem_vinculo_confirmado(self):
        from app.services.central_whatsapp_citacoes import extrair_citacao_waha
        from app.services.central_whatsapp_contatos import telefone_confirmado_contato

        chat = "123456789@lid"
        alvo = f"false_{chat}_EXEMPLO"
        self.assertEqual(extrair_citacao_waha({"replyTo": {"id": alvo}}, chat), alvo)
        self.assertIsNone(extrair_citacao_waha({"replyTo": {"id": alvo}}, "555555555@lid"))
        self.assertIsNone(telefone_confirmado_contato({"id": chat, "number": "123456789"}, chat))
        self.assertEqual(telefone_confirmado_contato({
            "id": "5585999999999@c.us", "lid": chat,
        }, chat), "5585999999999")

    def test_catalogo_comercial_pagina_e_exclui_grupo_sem_autorizacao(self):
        import json
        from app.services.central_whatsapp_historico_noweb import (
            chats_autorizados_noweb, pagina_catalogo_noweb,
        )

        sessao = "default"
        contatos = [f"55859999{i:04d}@c.us" for i in range(101)]
        estado = {"name": sessao, "status": "WORKING", "engine": "NOWEB",
                  "config": {"noweb": {"store": {"enabled": True}}}}
        with patch.dict(os.environ, {
            "WAHA_API_URL": "http://waha.invalid", "WAHA_API_KEY": "ficticia",
            "ORION_WAHA_CATALOGO_COMERCIAL": json.dumps([sessao]),
            "ORION_WAHA_GRUPOS_AUTORIZADOS": "{}",
            "ORION_WAHA_PAREAMENTO_CONTATOS": json.dumps({sessao: contatos[:12]}),
        }), patch("app.services.central_whatsapp_historico_noweb.requests.Session") as cliente:
            self.assertEqual(len(chats_autorizados_noweb(sessao)), 12)
            get = cliente.return_value.__enter__.return_value.get
            get.side_effect = [Mock(status_code=200, json=Mock(return_value=v)) for v in (
                estado, [{"id": c.replace("@c.us", "@s.whatsapp.net")} for c in contatos[:100]],
                estado, [{"id": contatos[-1].replace("@c.us", "@s.whatsapp.net")}, {"id": "123@g.us"}],
                estado, [],
            )]
            paginas = [pagina_catalogo_noweb(sessao, offset) for offset in (0, 100, 200)]
            self.assertEqual([chat for chats, _ in paginas for chat in chats], contatos)
            self.assertIsNone(paginas[-1][1])
            self.assertEqual([c.kwargs["params"]["offset"] for c in get.call_args_list[1::2]], [0, 100, 200])
            self.assertEqual(pagina_catalogo_noweb("outra-sessao", 0), ([], None))
