"""Contratos HTTP e autorização no PostgreSQL local isolado."""

import os
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Barrier
from tempfile import TemporaryDirectory
from unittest.mock import patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

with patch.dict(os.environ, {"DATABASE_URL": "sqlite://", "PYTHON_DOTENV_DISABLED": "1"}):
    from app.models.models import Cliente, ConexaoCanal, Conversa, Empresa, Especialista, FollowupAgendamento, Lead, Mensagem
    from app.routes.central_whatsapp_api import router
    from app.services.autenticacao_api import gerar_token_api
    from app.services.central_whatsapp_atendimento import gerenciar_atendimento_whatsapp
    from app.services.central_whatsapp_ack import registrar_ack_waha
    from app.services.mensagem_service import registrar_resultado_envio
    from app.services.waha_gestao_transporte import ErroGestaoWaha
    from app.services.central_whatsapp_midia_entrada import registrar_midia_recebida
    from app.services.followup_dependencia_api import obter_db_api


class CentralWhatsAppConsultasTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        porta = os.getenv("ORION_FOLLOWUP_TEST_PORT", "55432")
        if porta not in ("5432", "55432"):
            raise ValueError("Porta fora do ambiente de testes")
        cls.engine = create_engine(
            f"postgresql+psycopg2://orion_test@127.0.0.1:{porta}/orion_crm_followup_test",
        )
        cls.addClassCleanup(cls.engine.dispose)
        with cls.engine.connect() as conexao:
            if conexao.execute(text("SELECT current_database(), current_user")).one() != (
                "orion_crm_followup_test", "orion_test",
            ):
                raise RuntimeError("Banco fora do ambiente de testes")

    def setUp(self):
        conexao = self.engine.connect()
        self.addCleanup(conexao.close)
        transacao = conexao.begin()
        self.addCleanup(transacao.rollback)
        self.db = Session(bind=conexao, join_transaction_mode="create_savepoint")
        self.addCleanup(self.db.close)
        ambiente = patch.dict(os.environ, {"ORION_API_AUTH_SECRET": "chave-ficticia-central-" * 2})
        ambiente.start()
        self.addCleanup(ambiente.stop)
        app = FastAPI()
        app.include_router(router)

        def sessao_api():
            with Session(bind=conexao, join_transaction_mode="create_savepoint") as db:
                yield db

        app.dependency_overrides[obter_db_api] = sessao_api
        self.client = self.enterContext(TestClient(app))
        self.empresa = self.criar(Empresa(nome=f"Central teste {uuid4()}", plano="Premium")).id
        self.outra_empresa = self.criar(Empresa(nome=f"Central teste {uuid4()}", plano="Premium")).id
        self.vendedor = self.usuario(self.empresa, "vendedor")
        self.colega = self.usuario(self.empresa, "vendedor")
        self.admin = self.usuario(self.empresa, "admin_empresa")
        self.vendedor_externo = self.usuario(self.outra_empresa, "vendedor")
        titular = self.criar(Especialista(
            empresa_id=self.empresa, nome="Titular fictício", usuario_id=self.vendedor,
        )).id
        colega = self.criar(Especialista(
            empresa_id=self.empresa, nome="Colega fictício", usuario_id=self.colega,
        )).id
        self.privada = self.conexao(self.empresa, titular)
        self.compartilhada = self.conexao(self.empresa, None)
        conexao_externa = self.conexao(self.outra_empresa, None)
        inativa = self.conexao(self.empresa, titular, ativo=False)
        self.direta = self.conversa(self.empresa, self.privada)
        self.atribuida = self.conversa(self.empresa, self.compartilhada, titular)
        self.sem_atribuicao = self.conversa(self.empresa, self.compartilhada)
        self.de_outro_vendedor = self.conversa(self.empresa, self.privada, colega)
        self.fora = self.conversa(self.outra_empresa, conexao_externa)
        self.desativada = self.conversa(self.empresa, inativa, titular)
        self.db.commit()

    def criar(self, registro):
        self.db.add(registro)
        self.db.flush()
        return registro

    def usuario(self, empresa, nivel, status="ativo"):
        return self.db.execute(text("""
            INSERT INTO usuarios (empresa_id, nome, email, senha_hash, nivel, status)
            VALUES (:empresa, 'Pessoa fictícia', :email, 'hash-ficticio', :nivel, :status)
            RETURNING id
        """), {
            "empresa": empresa, "email": f"{uuid4()}@example.invalid",
            "nivel": nivel, "status": status,
        }).scalar_one()

    def conexao(self, empresa, titular, *, ativo=True):
        return self.criar(ConexaoCanal(
            empresa_id=empresa, especialista_id=titular, ativo=ativo,
            canal="whatsapp", provedor="waha", sessao_waha=str(uuid4()),
        )).id

    def conversa(self, empresa, conexao, especialista=None):
        return self.criar(Conversa(
            empresa_id=empresa, conexao_canal_id=conexao, especialista_id=especialista,
            canal="whatsapp", identificador=f"{uuid4().int}@c.us",
        )).id

    def consultar(self, caminho, usuario=None, *, empresa=None, **params):
        headers = {}
        if usuario is not None:
            token = gerar_token_api(usuario_id=usuario, empresa_id=empresa or self.empresa)
            headers["Authorization"] = f"Bearer {token}"
        return self.client.get(f"/api/central-whatsapp/{caminho}", headers=headers, params=params)

    def historico(self, conversa, usuario, **params):
        return self.consultar(f"conversas/{conversa}/mensagens", usuario, **params)

    def alterar(self, acao, conversa_id, usuario, *, empresa_ativa=None, **dados):
        token = gerar_token_api(usuario_id=usuario, empresa_id=self.empresa)
        return self.client.post(
            f"/api/central-whatsapp/{acao}-atendimento",
            headers={"Authorization": f"Bearer {token}"},
            params={"empresa_id": empresa_ativa} if empresa_ativa is not None else {},
            json={"conversa_id": conversa_id, **dados},
        )

    def especialista(self, usuario):
        return self.db.query(Especialista.id).filter_by(
            empresa_id=self.empresa, usuario_id=usuario,
        ).scalar()

    def test_contexto_comercial_reusa_escopo_e_filtra_vinculos_divergentes(self):
        outra_pessoa = self.criar(Cliente(empresa_id=self.outra_empresa, nome="Cliente externo"))
        conversa = self.db.get(Conversa, self.atribuida)
        conversa.cliente_id = outra_pessoa.id
        conversa.nome = "Contato teste"
        self.criar(Lead(
            empresa_id=self.empresa, conversa_id=conversa.id, produto="Serviço fictício",
            temperatura="quente", score=90, resumo_vendedor="Resumo autorizado",
        ))
        self.criar(Lead(
            empresa_id=self.outra_empresa, conversa_id=conversa.id, resumo_vendedor="Resumo externo",
        ))
        self.db.commit()
        caminho = f"conversas/{conversa.id}/detalhes"
        resposta = self.consultar(caminho, self.vendedor)
        self.assertEqual(resposta.status_code, 200, resposta.text)
        self.assertEqual(resposta.json()["cliente"], "Contato teste")
        self.assertEqual(resposta.json()["resumo_vendedor"], "Resumo autorizado")
        self.assertEqual(resposta.json()["score"], 90)
        self.assertNotIn("externo", resposta.text.lower())
        self.assertEqual(self.consultar(caminho, self.colega).status_code, 404)
        self.assertEqual(self.consultar(f"conversas/{self.sem_atribuicao}/detalhes", self.vendedor).status_code, 404)

        filtros = self.consultar("filtros-conversas", self.vendedor).json()
        self.assertEqual({f["conexao_id"] for f in filtros}, {self.privada, self.compartilhada})
        encontrados = self.consultar(
            "conversas", self.vendedor, busca="contato TESTE",
            conexao_id=self.compartilhada, responsavel_id=self.especialista(self.vendedor),
            status=conversa.status_atendimento,
        )
        self.assertEqual([item["id"] for item in encontrados.json()], [self.atribuida])
        self.assertEqual(self.consultar("conversas", self.colega, fixar_conversa_id=self.atribuida).json(), [])

    def test_leitura_persiste_por_usuario_e_valida_mensagem(self):
        conversa_id = self.atribuida
        ids = [
            self.criar(Mensagem(
                empresa_id=self.empresa, conversa_id=conversa_id, remetente="cliente",
                from_me=False, texto="Fictícia",
            )).id for _ in range(2)
        ]
        self.db.commit()
        caminho = f"/api/central-whatsapp/conversas/{conversa_id}/leitura"
        def marcar(usuario, mensagem_id):
            token = gerar_token_api(usuario_id=usuario, empresa_id=self.empresa)
            return self.client.post(caminho, headers={"Authorization": f"Bearer {token}"},
                                    json={"mensagem_id": mensagem_id})
        self.assertEqual(marcar(self.colega, ids[1]).status_code, 404)
        for mensagem_id in reversed(ids):
            self.assertEqual(marcar(self.vendedor, mensagem_id).json(), {"ultima_lida_id": ids[1]})
        for usuario, ultima in ((self.vendedor, ids[1]), (self.admin, None)):
            lista = self.consultar("conversas", usuario).json()
            self.assertEqual(next(item for item in lista if item["id"] == conversa_id)["ultima_lida_id"], ultima)

    def test_ack_antecipado_e_aplicado_sem_reenvio(self):
        sessao = self.db.get(ConexaoCanal, self.compartilhada).sessao_waha
        for ack in (3, 1, 2, 3):
            self.assertEqual(registrar_ack_waha(self.db, {
                "session": sessao, "payload": {"id": "ack-antecipado", "fromMe": True, "ack": ack},
            }), "ack_pendente")
        mensagem = self.criar(Mensagem(
            empresa_id=self.empresa, conversa_id=self.atribuida, remetente="humano",
            from_me=True, texto="Fictícia", conexao_canal_id=self.compartilhada,
        ))
        self.assertTrue(registrar_resultado_envio(
            self.db, empresa_id=self.empresa, conversa_id=self.atribuida, mensagem_id=mensagem.id,
            sessao_waha=sessao, mensagem_id_waha="ack-antecipado", status_envio="aceito_waha",
        ))
        self.db.refresh(mensagem)
        self.assertEqual(mensagem.status_envio, "lida_waha")
        pendentes = self.db.execute(text(
            "SELECT count(*) FROM central_ack_pendente WHERE mensagem_waha = 'ack-antecipado'"
        )).scalar_one()
        self.assertEqual(pendentes, 0)

    def test_assumir_cancela_followup_pendente_da_conversa(self):
        lead = self.criar(Lead(empresa_id=self.empresa, conversa_id=self.atribuida))
        agora = datetime.now(timezone.utc)
        agendamento = self.criar(FollowupAgendamento(
            empresa_id=self.empresa, conversa_id=self.atribuida, lead_id=lead.id,
            agendado_para=agora, entrada_lead_em=agora, status="pendente",
        ))
        self.db.commit()
        self.assertEqual(self.alterar("assumir", self.atribuida, self.vendedor).status_code, 200)
        self.db.refresh(agendamento)
        self.assertEqual(agendamento.status, "cancelado")

    def test_gestao_conexoes_respeita_plano_hierarquia_e_vinculo(self):
        base = "/api/central-whatsapp/conexoes"
        def headers(usuario):
            return {"Authorization": "Bearer " + gerar_token_api(usuario_id=usuario, empresa_id=self.empresa)}

        corpo = {"nome_conexao": "Nova conexão", "sofia_ativa": False}
        admin = headers(self.admin)
        self.assertEqual(self.client.post(base, headers=headers(self.vendedor), json=corpo).status_code, 403)
        self.assertEqual(self.client.post(base, headers=admin, json={**corpo, "especialista_id": 2147483647}).status_code, 403)
        resposta = self.client.post(base, headers=admin, json={**corpo, "especialista_id": self.especialista(self.colega)})
        self.assertEqual(resposta.status_code, 201, resposta.text)
        cadastrada = resposta.json()
        self.assertFalse(cadastrada["sofia_ativa"])
        self.assertTrue(cadastrada["suspensa"])
        self.assertNotIn("sessao_waha", cadastrada)
        self.assertEqual(self.client.post(base, headers=admin, json=corpo).status_code, 201)
        self.assertEqual(self.client.post(base, headers=admin, json=corpo).json()["detail"], "limite_plano_atingido")
        self.assertEqual(self.client.get(base, headers=admin, params={"empresa_id": self.outra_empresa}).status_code, 403)
        self.assertEqual(self.client.put(f"{base}/{self.compartilhada}", headers=admin, json=corpo).status_code, 409)

    def test_qr_provisionamento_limite_provedor_e_desconexao_confirmada(self):
        base = "/api/central-whatsapp/conexoes"
        headers = {"Authorization": "Bearer " + gerar_token_api(usuario_id=self.admin, empresa_id=self.empresa)}
        png = b"\x89PNG\r\n\x1a\n"
        with patch("app.routes.central_whatsapp_api.TransporteGestaoWaha") as classe:
            transporte = classe.return_value
            resposta = self.client.post(base, headers=headers, json={"nome_conexao": "Piloto"})
            self.assertEqual(resposta.status_code, 201, resposta.text)
            caminho = f"{base}/{resposta.json()['id']}"
            self.assertEqual(self.client.post(f"{base}/{self.compartilhada}/conectar", headers=headers).status_code, 409)
            self.assertEqual(self.client.post(caminho + "/desconectar", headers=headers, json={"confirmar": False}).status_code, 422)
            classe.assert_not_called()
            transporte.consultar.side_effect = ErroGestaoWaha("recurso_waha_indisponivel", 404)
            transporte.criar.side_effect = ErroGestaoWaha("limite_sessoes_provedor", 409)
            recusada = self.client.post(caminho + "/conectar", headers=headers)
            self.assertEqual(recusada.json()["detail"], "limite_sessoes_provedor")
            transporte.iniciar.assert_not_called()
            transporte.criar.side_effect = None
            self.assertEqual(self.client.post(caminho + "/conectar", headers=headers).status_code, 200)
            transporte.iniciar.assert_called_once_with(transporte.criar.call_args.args[0])
            transporte.consultar.side_effect = None
            transporte.consultar.return_value = {"estado": "SCAN_QR_CODE", "numero": None}
            transporte.qr.return_value = png
            qr = self.client.get(caminho + "/qr", headers=headers)
            self.assertEqual(qr.status_code, 200)
            self.assertEqual(qr.content, png)
            self.assertIn("no-store", qr.headers["Cache-Control"])
            self.assertEqual(self.client.get(caminho + "/qr").status_code, 401)
            transporte.qr.assert_called_once()
            self.assertEqual(self.client.post(caminho + "/desconectar", headers=headers, json={"confirmar": True}).status_code, 200)
            transporte.desconectar.assert_called_once()
            self.assertEqual(self.client.get(caminho + "/qr", headers=headers).status_code, 409)

    def test_franquia_preserva_legado_e_exclui_admin_orion(self):
        planos = self.db.execute(text("""
            SELECT p, orion_limite_plano(p, 'conexoes'), orion_limite_plano(p, 'usuarios')
            FROM (VALUES (' Lite '), ('PRO'), ('Premium')) AS planos(p)
        """)).all()
        self.assertEqual([(p[1], p[2]) for p in planos], [(1, 2), (2, 5), (5, 10)])
        empresa = self.db.get(Empresa, self.empresa)
        empresa.plano = "Lite"
        self.db.flush()
        orion = self.usuario(self.empresa, "orion_admin")
        for criar, restricao in (
            (lambda: self.usuario(self.empresa, "usuario"), "orion_limite_usuarios"),
            (lambda: self.conexao(self.empresa, None), "orion_limite_conexoes"),
        ):
            with self.assertRaises(IntegrityError) as erro, self.db.begin_nested():
                criar()
            self.assertEqual(erro.exception.orig.diag.constraint_name, restricao)
        self.db.execute(text("UPDATE usuarios SET nivel = 'admin_empresa' WHERE id = :id"),
                        {"id": self.vendedor})
        self.db.get(ConexaoCanal, self.privada).ativo = False
        self.db.commit()
        capacidade = self.consultar("conexoes", orion).json()
        self.assertEqual((capacidade["usuarios_contabilizados"], capacidade["limite_usuarios"]), (3, 2))
        self.assertEqual(len(capacidade["conexoes"]), 3)

    def test_franquia_serializa_a_ultima_vaga_de_usuarios_e_conexoes(self):
        with Session(self.engine) as db, db.begin():
            empresa = Empresa(nome=f"Franquia concorrente {uuid4()}", plano="Lite")
            db.add(empresa)
            db.flush()
            empresa_id = empresa.id
            db.execute(text("""
                INSERT INTO usuarios (empresa_id, nome, email, senha_hash, nivel, status)
                VALUES (:empresa, 'Fictício', :email, 'ficticio', 'admin_empresa', 'ativo')
            """), {"empresa": empresa_id, "email": f"{uuid4()}@example.invalid"})

        def limpar():
            with Session(self.engine) as db, db.begin():
                db.execute(text("DELETE FROM usuarios WHERE empresa_id = :id"), {"id": empresa_id})
                db.query(ConexaoCanal).filter_by(empresa_id=empresa_id).delete()
                db.query(Empresa).filter_by(id=empresa_id).delete()

        self.addCleanup(limpar)
        inicio = Barrier(2, timeout=10)

        def admitir(recurso):
            try:
                with Session(self.engine) as db, db.begin():
                    inicio.wait()
                    if recurso == "usuarios":
                        db.execute(text("""
                            INSERT INTO usuarios (empresa_id, nome, email, senha_hash, nivel, status)
                            VALUES (:empresa, 'Fictício', :email, 'ficticio', 'usuario', 'ativo')
                        """), {"empresa": empresa_id, "email": f"{uuid4()}@example.invalid"})
                    else:
                        db.add(ConexaoCanal(empresa_id=empresa_id, canal="whatsapp", provedor="waha",
                                            sessao_waha=uuid4().hex))
                return "admitido"
            except IntegrityError as erro:
                return erro.orig.diag.constraint_name

        with ThreadPoolExecutor(max_workers=2) as pool:
            for recurso in ("usuarios", "conexoes"):
                self.assertCountEqual(list(pool.map(admitir, [recurso, recurso])),
                                      ["admitido", f"orion_limite_{recurso}"])

    def test_atualizacao_condicional_detecta_mensagem_e_revalida_permissao(self):
        token = gerar_token_api(usuario_id=self.vendedor, empresa_id=self.empresa)
        headers = {"Authorization": f"Bearer {token}"}
        base = "/api/central-whatsapp"
        lista = self.client.get(base + "/conversas", headers=headers)
        caminho = base + f"/conversas/{self.atribuida}/mensagens"
        historico = self.client.get(caminho, headers=headers)
        anterior = {**headers, "If-None-Match": historico.headers["ETag"]}
        self.assertEqual(self.client.get(caminho, headers=anterior).status_code, 304)
        registro = self.criar(Mensagem(
            empresa_id=self.empresa, conversa_id=self.atribuida, conexao_canal_id=self.compartilhada,
            from_me=False, remetente="cliente", texto="Nova mensagem fictícia",
        ))
        mensagem_id = registro.id
        self.db.commit()
        atual = self.client.get(caminho, headers=anterior)
        self.assertEqual([m["id"] for m in atual.json()], [mensagem_id])
        atual_lista = self.client.get(base + "/conversas", headers={
            **headers, "If-None-Match": lista.headers["ETag"],
        }, params={"fixar_conversa_id": self.atribuida, "limite": 1})
        self.assertEqual(atual_lista.json()[0]["ultima_recebida_id"], mensagem_id)
        self.assertEqual(self.alterar("assumir", self.atribuida, self.vendedor).status_code, 200)
        self.assertEqual(self.alterar(
            "transferir", self.atribuida, self.vendedor,
            responsavel_atual_id=self.especialista(self.vendedor),
            destino_id=self.especialista(self.colega),
        ).status_code, 200)
        self.assertEqual(self.client.get(caminho, headers={
            **headers, "If-None-Match": atual.headers["ETag"],
        }).status_code, 404)

    def test_ack_correlaciona_empresa_conexao_id_e_ignora_regressao(self):
        sessao = self.db.get(ConexaoCanal, self.compartilhada).sessao_waha
        outra_sessao = self.db.get(ConexaoCanal, self.privada).sessao_waha
        registro = self.criar(Mensagem(
            empresa_id=self.empresa, conversa_id=self.atribuida,
            conexao_canal_id=self.compartilhada, remetente="humano", from_me=True,
            texto="Fictícia", sessao_waha=sessao, mensagem_id_waha="id-teste",
            status_envio="aceito_waha",
        ))
        externo = self.criar(Mensagem(
            empresa_id=self.outra_empresa, conversa_id=self.fora,
            remetente="humano", from_me=True, texto="Fictícia externa",
            sessao_waha=sessao, mensagem_id_waha="id-teste", status_envio="aceito_waha",
        ))
        def ack(numero, nome, *, sessao_evento=sessao, saida=True):
            return registrar_ack_waha(self.db, {
                "session": sessao_evento,
                "payload": {"id": "id-teste", "fromMe": saida, "ack": numero, "ackName": nome},
            })
        self.assertEqual(ack(3, "READ", saida=False), "ack_invalido")
        self.assertEqual(ack(3, "DEVICE"), "ack_invalido")
        self.assertEqual(ack(3, "READ", sessao_evento=outra_sessao), "ack_pendente")
        for numero, nome, estado in (
            (1, "SERVER", "enviada_waha"), (2, "DEVICE", "entregue_waha"), (3, "READ", "lida_waha"),
        ):
            self.assertEqual(ack(numero, nome), "ack_registrado")
            self.db.refresh(registro)
            self.assertEqual(registro.status_envio, estado)
        for numero, nome in ((-1, "ERROR"), (2, "DEVICE"), (3, "READ")):
            self.assertEqual(ack(numero, nome), "ack_sem_transicao")
        self.db.refresh(externo)
        self.assertEqual(externo.status_envio, "aceito_waha")

    def test_acks_concorrentes_gravam_estado_mais_avancado(self):
        sessao = f"ack-teste-{uuid4()}"
        with Session(self.engine) as db, db.begin():
            empresa = Empresa(nome=sessao)
            db.add(empresa)
            db.flush()
            empresa_id = empresa.id
            conexao = ConexaoCanal(
                empresa_id=empresa_id, sessao_waha=sessao, canal="whatsapp", provedor="waha", ativo=True,
            )
            db.add(conexao)
            db.flush()
            conversa = Conversa(
                empresa_id=empresa_id, conexao_canal_id=conexao.id,
                canal="whatsapp", identificador="5511000000000@c.us",
            )
            db.add(conversa)
            db.flush()
            registro = Mensagem(
                empresa_id=empresa_id, conversa_id=conversa.id, conexao_canal_id=conexao.id,
                remetente="humano", from_me=True, sessao_waha=sessao,
                mensagem_id_waha="ack-concorrente", status_envio="aceito_waha",
            )
            db.add(registro)
            db.flush()
            mensagem_id = registro.id

        def limpar():
            with Session(self.engine) as db, db.begin():
                for modelo in (Mensagem, Conversa, ConexaoCanal):
                    db.query(modelo).filter_by(empresa_id=empresa_id).delete()
                db.query(Empresa).filter_by(id=empresa_id).delete()

        self.addCleanup(limpar)
        inicio = Barrier(3, timeout=10)

        def confirmar(numero):
            with Session(self.engine) as db, db.begin():
                inicio.wait()
                return registrar_ack_waha(db, {
                    "session": sessao,
                    "payload": {"id": "ack-concorrente", "fromMe": True, "ack": numero},
                })

        with ThreadPoolExecutor(max_workers=3) as workers:
            resultados = list(workers.map(confirmar, (2, 3, 3)))
        self.assertEqual(resultados[1:].count("ack_registrado"), 1)
        with Session(self.engine) as db:
            self.assertEqual(db.get(Mensagem, mensagem_id).status_envio, "lida_waha")

    def test_anexo_saida_idempotente_validado_e_com_acesso_por_conversa(self):
        self.assertEqual(self.alterar("assumir", self.atribuida, self.vendedor).status_code, 200)
        token = gerar_token_api(usuario_id=self.vendedor, empresa_id=self.empresa)
        headers = {"Authorization": f"Bearer {token}"}
        corpo = {"conversa_id": self.atribuida, "chave_solicitacao": "anexo-teste"}
        dados = b"%PDF-1.7\n%Teste ficticio"
        with (
            TemporaryDirectory() as pasta,
            patch.dict(os.environ, {
                "ORION_CENTRAL_WHATSAPP_MIDIA_ATIVA": "1",
                "ORION_CENTRAL_WHATSAPP_ENVIO_ATIVO": "1",
                "ORION_CENTRAL_WHATSAPP_MIDIA_DIR": pasta,
            }),
            patch(
                "app.routes.central_whatsapp_api.enviar_midia_waha",
                return_value=(True, None, "id-waha-ficticio"),
            ) as transporte,
        ):
            def reservar(nome, conteudo):
                return self.client.post(
                    "/api/central-whatsapp/reservar-anexo", headers=headers, data=corpo,
                    files={"arquivo": (nome, conteudo, "application/pdf")},
                )

            self.assertEqual(reservar("../teste.pdf", dados).status_code, 422)
            self.assertEqual(reservar("teste.pdf", b"<html>").status_code, 422)
            reserva = reservar("teste.pdf", dados)
            self.assertEqual(reserva.status_code, 200, reserva.text)
            mensagem_id = reserva.json()["mensagem_id"]
            self.assertEqual(reservar("teste.pdf", dados).json()["situacao"], "solicitacao_duplicada")
            self.assertEqual(reservar("teste.pdf", dados + b"alterado").status_code, 409)
            requisicao = {"conversa_id": self.atribuida, "mensagem_id": mensagem_id}
            for codigo in (200, 409):
                resposta = self.client.post(
                    "/api/central-whatsapp/executar-mensagem", headers=headers, json=requisicao,
                )
                self.assertEqual(resposta.status_code, codigo, resposta.text)
            transporte.assert_called_once()
            self.assertEqual(transporte.call_args.kwargs["dados"], dados)
            self.assertEqual(transporte.call_args.args[0], self.db.get(ConexaoCanal, self.compartilhada).sessao_waha)

            caminho = f"conversas/{self.atribuida}/mensagens/{mensagem_id}/anexo"
            anexo = self.consultar(caminho, self.vendedor)
            self.assertEqual(anexo.content, dados)
            self.assertIn("no-store", anexo.headers["cache-control"])
            self.assertEqual(self.consultar(caminho, self.colega).status_code, 404)
            self.assertEqual(self.consultar(caminho, self.vendedor_externo, empresa=self.outra_empresa).status_code, 404)
            historico = self.historico(self.atribuida, self.vendedor).json()[0]
            self.assertTrue(historico["tem_anexo"])
            self.assertNotIn("midia_url", historico)

    def test_midia_recebida_de_sessao_valida_e_deduplicada(self):
        sessao = self.db.get(ConexaoCanal, self.compartilhada).sessao_waha
        dados = {
            "empresa_id": self.empresa, "conexao_id": self.compartilhada, "sessao": sessao,
            "chat_id": "5511000000000@c.us", "mensagem_id": "midia-ficticia",
            "payload": {"body": "Legenda", "media": {"url": "http://waha.invalid/api/files/midia-ficticia.pdf"}},
        }
        with (
            TemporaryDirectory() as pasta,
            patch.dict(os.environ, {"ORION_CENTRAL_WHATSAPP_MIDIA_DIR": pasta}),
            patch("app.services.central_whatsapp_midia_entrada.baixar_midia_waha",
                  return_value=("teste.pdf", "application/pdf", b"%PDF-1.7")) as download,
        ):
            self.assertEqual(registrar_midia_recebida(
                self.db, **{**dados, "empresa_id": self.outra_empresa},
            ), "conexao_indisponivel")
            self.assertEqual(registrar_midia_recebida(self.db, **dados), "midia_registrada")
            self.assertEqual(registrar_midia_recebida(self.db, **dados), "midia_duplicada")
            download.assert_called_once()
            registro = self.db.query(Mensagem).filter_by(
                empresa_id=self.empresa, mensagem_id_externo="midia-ficticia",
            ).one()
            self.assertEqual((registro.tipo, registro.texto), ("documento", "Legenda"))

    def test_fila_transferencia_e_encerramento_corporativo(self):
        fila = self.consultar("conversas", self.colega, incluir_fila=True).json()
        self.assertEqual([c["id"] for c in fila], [self.sem_atribuicao])
        self.assertTrue(fila[0]["pode_assumir"])

        self.assertEqual(self.alterar("assumir", self.sem_atribuicao, self.vendedor).status_code, 200)
        origem = self.especialista(self.vendedor)
        destino = self.especialista(self.colega)
        dados = {"responsavel_atual_id": origem, "destino_id": destino}
        self.assertEqual(self.alterar("transferir", self.sem_atribuicao, self.colega, **dados).status_code, 403)
        self.assertEqual(self.alterar("transferir", self.sem_atribuicao, self.admin, **dados).status_code, 200)
        self.assertEqual(self.alterar("transferir", self.sem_atribuicao, self.admin, **dados).status_code, 409)
        self.assertEqual(self.historico(self.sem_atribuicao, self.vendedor).status_code, 404)
        self.assertEqual(self.historico(self.sem_atribuicao, self.colega).status_code, 200)
        self.assertEqual(self.alterar(
            "transferir", self.sem_atribuicao, self.colega,
            responsavel_atual_id=destino, destino_id=origem,
        ).status_code, 200)
        self.assertEqual(self.alterar(
            "encerrar", self.sem_atribuicao, self.vendedor, responsavel_atual_id=origem,
        ).status_code, 200)

        registro = self.db.get(Conversa, self.sem_atribuicao, populate_existing=True)
        self.assertEqual(registro.especialista_id, origem)
        self.assertEqual(registro.status_atendimento, "finalizado")
        self.assertTrue(registro.humano_assumiu)
        self.assertEqual(self.alterar("assumir", self.sem_atribuicao, self.vendedor).status_code, 409)
        token = gerar_token_api(usuario_id=self.vendedor, empresa_id=self.empresa)
        with patch.dict(os.environ, {"ORION_CENTRAL_WHATSAPP_ENVIO_ATIVO": "1"}):
            reserva = self.client.post(
                "/api/central-whatsapp/reservar-mensagem",
                headers={"Authorization": f"Bearer {token}"},
                json={"conversa_id": registro.id, "texto": "simulação", "chave_solicitacao": "teste"},
            )
        self.assertEqual(reserva.status_code, 403)

    def test_transferencia_rejeita_destino_inativo_externo_e_conexao_privada(self):
        origem = self.especialista(self.vendedor)
        externo = self.criar(Especialista(
            empresa_id=self.outra_empresa, nome="Externo", usuario_id=self.vendedor_externo,
        )).id
        inativo = self.criar(Especialista(
            empresa_id=self.empresa, nome="Inativo",
            usuario_id=self.usuario(self.empresa, "vendedor", "inativo"),
        )).id
        self.db.commit()
        self.assertEqual(self.alterar("assumir", self.atribuida, self.vendedor).status_code, 200)
        for destino in (inativo, externo):
            self.assertEqual(self.alterar(
                "transferir", self.atribuida, self.vendedor,
                responsavel_atual_id=origem, destino_id=destino,
            ).status_code, 403)
        self.assertEqual(self.alterar("assumir", self.direta, self.vendedor).status_code, 200)
        self.assertEqual(self.alterar(
            "transferir", self.direta, self.vendedor,
            responsavel_atual_id=origem, destino_id=self.especialista(self.colega),
        ).status_code, 403)

    def test_supervisao_respeita_hierarquia_e_exclui_conexao_privada_externa(self):
        parceiro = self.usuario(self.empresa, "parceiro_admin")
        orion = self.usuario(self.empresa, "orion_admin")
        externo = self.criar(Especialista(
            empresa_id=self.outra_empresa, nome="Externo", usuario_id=self.vendedor_externo,
        )).id
        privada = self.conversa(self.outra_empresa, self.conexao(self.outra_empresa, externo))
        self.db.commit()
        for usuario in (self.vendedor, self.admin, parceiro):
            self.assertEqual(self.consultar(
                "conversas", usuario, empresa_id=self.outra_empresa,
            ).status_code, 403)
        self.db.get(Empresa, self.outra_empresa).parceiro_id = self.empresa
        registro = self.db.get(Conversa, self.fora)
        registro.especialista_id = externo
        registro.humano_assumiu = True
        registro.status_atendimento = "em_atendimento_humano"
        self.db.commit()
        for supervisor in (parceiro, orion):
            resposta = self.consultar("conversas", supervisor, empresa_id=self.outra_empresa)
            self.assertEqual([c["id"] for c in resposta.json()], [self.fora])
            self.assertEqual(self.historico(
                privada, supervisor, empresa_id=self.outra_empresa,
            ).status_code, 404)
        self.assertEqual(self.alterar(
            "encerrar", self.fora, self.admin, empresa_ativa=self.outra_empresa,
            responsavel_atual_id=externo,
        ).status_code, 403)
        self.assertEqual(self.alterar(
            "encerrar", self.fora, parceiro, empresa_ativa=self.outra_empresa,
            responsavel_atual_id=externo,
        ).status_code, 200)

    def test_envio_pendente_impede_transferencia_e_encerramento(self):
        origem, destino = self.especialista(self.vendedor), self.especialista(self.colega)
        self.assertEqual(self.alterar("assumir", self.atribuida, self.vendedor).status_code, 200)
        self.criar(Mensagem(
            empresa_id=self.empresa, conversa_id=self.atribuida,
            conexao_canal_id=self.compartilhada, especialista_id=origem,
            remetente="humano", from_me=True, texto="Envio fictício",
            status_envio="timeout_envio_inconclusivo",
        ))
        self.db.commit()
        for acao, dados in (("transferir", {"destino_id": destino}), ("encerrar", {})):
            resposta = self.alterar(
                acao, self.atribuida, self.vendedor, responsavel_atual_id=origem, **dados,
            )
            self.assertEqual((resposta.status_code, resposta.json()), (409, {"detail": "envio_pendente"}))

    def test_tomada_transferencia_e_encerramento_concorrentes(self):
        with Session(self.engine) as db, db.begin():
            empresa = Empresa(nome=f"Concorrência fictícia {uuid4()}")
            db.add(empresa)
            db.flush()
            empresa_id = empresa.id
            usuarios = []
            for _ in range(2):
                usuario = db.execute(text("""
                    INSERT INTO usuarios (empresa_id, nome, email, senha_hash, nivel, status)
                    VALUES (:empresa, 'Teste', :email, 'ficticio', 'vendedor', 'ativo')
                    RETURNING id
                """), {"empresa": empresa_id, "email": f"{uuid4()}@example.invalid"}).scalar_one()
                usuarios.append(usuario)
                db.add(Especialista(empresa_id=empresa_id, nome="Teste", usuario_id=usuario))
            conexao = ConexaoCanal(
                empresa_id=empresa_id, canal="whatsapp", provedor="waha",
                sessao_waha=str(uuid4()), ativo=True,
            )
            db.add(conexao)
            db.flush()
            conversa = Conversa(
                empresa_id=empresa_id, conexao_canal_id=conexao.id, canal="whatsapp",
                identificador=f"{uuid4().int}@c.us",
            )
            db.add(conversa)
            db.flush()
            conversa_id = conversa.id

        def limpar():
            with Session(self.engine) as db, db.begin():
                for modelo in (Conversa, ConexaoCanal, Especialista):
                    db.query(modelo).filter_by(empresa_id=empresa_id).delete()
                db.execute(text("DELETE FROM usuarios WHERE empresa_id = :empresa"), {"empresa": empresa_id})
                db.query(Empresa).filter_by(id=empresa_id).delete()

        self.addCleanup(limpar)
        inicio = Barrier(2, timeout=10)

        def assumir(usuario):
            with Session(self.engine) as db, db.begin():
                inicio.wait()
                return gerenciar_atendimento_whatsapp(
                    db, empresa_id=empresa_id, identidade={"usuario_id": usuario, "nivel": "vendedor"},
                    conversa_id=conversa_id, acao="assumir",
                )

        with ThreadPoolExecutor(max_workers=2) as workers:
            resultados = list(workers.map(assumir, usuarios))
        self.assertCountEqual(resultados, [
            (True, "atendimento_assumido"), (False, "atendimento_ja_assumido"),
        ])

        with Session(self.engine) as db:
            responsavel = db.get(Conversa, conversa_id).especialista_id
            especialistas = {
                e.id: e.usuario_id for e in db.query(Especialista).filter_by(empresa_id=empresa_id)
            }
            destino = next(e for e in especialistas if e != responsavel)

        def alterar(acao):
            with Session(self.engine) as db, db.begin():
                inicio.wait()
                return gerenciar_atendimento_whatsapp(
                    db, empresa_id=empresa_id,
                    identidade={"usuario_id": especialistas[responsavel], "nivel": "vendedor"},
                    conversa_id=conversa_id, acao=acao, responsavel_atual_id=responsavel,
                    destino_id=destino if acao == "transferir" else None,
                )

        with ThreadPoolExecutor(max_workers=2) as workers:
            transferencia, encerramento = workers.map(alterar, ("transferir", "encerrar"))
        self.assertNotEqual(transferencia[0], encerramento[0])
        with Session(self.engine) as db:
            final = db.get(Conversa, conversa_id)
            self.assertTrue(final.humano_assumiu)
            if transferencia[0]:
                self.assertEqual((final.especialista_id, final.status_atendimento), (
                    destino, "em_atendimento_humano",
                ))
            else:
                self.assertEqual((final.especialista_id, final.status_atendimento), (
                    responsavel, "finalizado",
                ))

    def test_exige_token_valido_usuario_ativo_e_empresa_do_usuario(self):
        inativo = self.usuario(self.empresa, "vendedor", "inativo")
        self.db.commit()
        for caminho in ("conversas", f"conversas/{self.direta}/mensagens"):
            self.assertEqual(self.consultar(caminho).status_code, 401)
            self.assertEqual(self.consultar(caminho, inativo).status_code, 401)
            self.assertEqual(self.consultar(caminho, self.vendedor_externo).status_code, 401)
            resposta = self.client.get(f"/api/central-whatsapp/{caminho}", headers={
                "Authorization": "Bearer credencial-invalida",
            })
            self.assertEqual(resposta.status_code, 401)

    def test_listagem_escopo_de_vendedor_administrador_e_conexao(self):
        vendedor = self.consultar("conversas", self.vendedor)
        self.assertEqual(vendedor.status_code, 200)
        self.assertEqual({c["id"] for c in vendedor.json()}, {self.direta, self.atribuida})
        self.assertEqual(self.consultar("conversas", self.colega).json(), [])
        administrador = self.consultar("conversas", self.admin)
        self.assertEqual({c["id"] for c in administrador.json()}, {
            self.direta, self.atribuida, self.sem_atribuicao, self.de_outro_vendedor,
        })
        filtrada = self.consultar("conversas", self.vendedor, conexao_id=self.compartilhada)
        self.assertEqual([c["id"] for c in filtrada.json()], [self.atribuida])
        self.assertEqual(self.consultar("conversas", self.admin, deslocamento=4).json(), [])
        self.assertEqual(self.consultar("conversas", self.admin, limite=201).status_code, 422)

    def test_historico_inacessivel_equivale_a_inexistente(self):
        esperado = self.historico(2147483647, self.vendedor)
        self.assertEqual(esperado.status_code, 404)
        for conversa in (self.fora, self.de_outro_vendedor, self.sem_atribuicao, self.desativada):
            resposta = self.historico(conversa, self.vendedor)
            self.assertEqual((resposta.status_code, resposta.json()), (404, esperado.json()))
        self.assertEqual(self.historico(self.fora, self.admin).status_code, 404)
        self.assertEqual(self.historico(self.direta, self.vendedor).json(), [])

    def test_historico_e_previa_excluem_outra_conexao_e_paginam(self):
        horario = datetime(2026, 1, 1, 12)
        for conexao, corpo in (
            (None, "legada"), (self.privada, "atual"), (self.compartilhada, "fora do escopo"),
        ):
            self.criar(Mensagem(
                empresa_id=self.empresa, conversa_id=self.direta, conexao_canal_id=conexao,
                remetente="cliente", from_me=False, texto=corpo, criado_em=horario,
            ))
        self.db.commit()
        historico = self.historico(self.direta, self.vendedor)
        self.assertEqual([m["texto"] for m in historico.json()], ["legada", "atual"])
        pagina = self.historico(self.direta, self.vendedor, limite=1, deslocamento=1)
        self.assertEqual([m["texto"] for m in pagina.json()], ["legada"])
        por_cursor = self.historico(self.direta, self.vendedor, antes_id=historico.json()[-1]["id"])
        self.assertEqual([m["texto"] for m in por_cursor.json()], ["legada"])
        lista = self.consultar("conversas", self.vendedor, conexao_id=self.privada)
        self.assertEqual(lista.json()[0]["ultima_mensagem"], "atual")
