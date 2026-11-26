"""Integração com o PostgreSQL isolado, via porta local ou rede do container."""

import hashlib
import hmac
import json
import os
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, time, timedelta, timezone
from importlib.util import find_spec
from threading import Barrier
from unittest.mock import patch
from uuid import uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# O módulo de modelos importa a configuração padrão. Os testes só utilizam
# as sessões criadas abaixo e não precisam da configuração da aplicação.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["PYTHON_DOTENV_DISABLED"] = "1"

from app.models.models import (
    ConexaoCanal, Conversa, Empresa, Especialista, FollowupAgendamento,
    FollowupConfiguracao, FollowupModeloMensagem, Lead, Mensagem,
)
from app.services.estados_mensagem import (
    STATUS_ENVIO_CONFIRMADO_HTTP, STATUS_ENVIO_FALHA,
)
from app.services.followup_horarios import calcular_primeiro_followup
from app.services.followup_processamento_service import (
    autorizar_envio_followup_reservado,
    confirmar_inicio_envio_followup,
    processar_resposta_cliente_followup,
    recuperar_reservas_expiradas,
    reservar_agendamento_pendente,
)
from app.services.mensagem_service import registrar_mensagem, registrar_resultado_envio
from app.workers import followup_scheduler, followup_worker


class FollowupAutomaticoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        porta = os.getenv("ORION_FOLLOWUP_TEST_PORT", "55432")
        if porta not in ("5432", "55432"):
            raise ValueError("Porta fora do ambiente de testes")
        cls.engine = create_engine(
            f"postgresql+psycopg2://orion_test@127.0.0.1:{porta}/orion_crm_followup_test",
        )
        with cls.engine.connect() as conexao:
            assert conexao.execute(
                text("SELECT current_database(), current_user")
            ).one() == ("orion_crm_followup_test", "orion_test")

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def setUp(self):
        conexao = self.engine.connect()
        self.addCleanup(conexao.close)
        transacao = conexao.begin()
        self.addCleanup(transacao.rollback)
        self.sessoes = sessionmaker(
            bind=conexao, join_transaction_mode="create_savepoint", autoflush=False,
        )
        ambiente = patch.dict(os.environ, {
            "FOLLOWUP_AGENDAMENTO_ATIVO": "true",
            "FOLLOWUP_WORKER_ATIVO": "1",
            "FOLLOWUP_ENVIO_REAL_ATIVO": "0",
        })
        ambiente.start()
        self.addCleanup(ambiente.stop)
        with self.sessoes() as db:
            self.empresa = self.criar_empresa(db)
            self.outra_empresa = self.criar_empresa(db)
            db.commit()

    def criar_empresa(self, db):
        empresa = Empresa(slug=str(uuid4()), tipo="cliente", status_financeiro="em_dia", bloqueio_automatico=True, nome=f"Teste follow-up {uuid4()}", plano="Premium")
        db.add(empresa)
        db.flush()
        db.add(FollowupConfiguracao(empresa_id=empresa.id, ativo=True))
        db.add(FollowupModeloMensagem(
            empresa_id=empresa.id, numero_tentativa=1, intervalo_minutos=180,
            texto="Mensagem simulada",
        ))
        db.flush()
        return empresa.id

    def nova_lead(self, db, *, empresa=None, anuncio=False, **estado_conversa):
        empresa = empresa or self.empresa
        conversa = Conversa(
            empresa_id=empresa, canal="whatsapp", identificador=f"{uuid4().int}@c.us",
            anuncio_referral_id="anuncio-teste" if anuncio else None,
            anuncio_referral_confirmado=anuncio, **estado_conversa,
        )
        db.add(conversa)
        db.flush()
        lead = Lead(empresa_id=empresa, conversa_id=conversa.id, status="Em atendimento")
        db.add(lead)
        db.flush()
        self.mensagem(db, lead, "cliente")
        return lead

    def mensagem(self, db, lead, remetente):
        registro, criada = registrar_mensagem(
            db, empresa_id=lead.empresa_id, conversa_id=lead.conversa_id,
            remetente=remetente, texto="Teste local", from_me=remetente != "cliente",
            mensagem_id_externo=str(uuid4()),
        )
        self.assertTrue(criada)
        return registro

    def confirmar(self, db, lead, remetente="agente", status=STATUS_ENVIO_CONFIRMADO_HTTP):
        registro = self.mensagem(db, lead, remetente)
        self.assertTrue(registrar_resultado_envio(
            db, empresa_id=lead.empresa_id, conversa_id=lead.conversa_id,
            mensagem_id=registro.id, status_envio=status,
        ))
        db.refresh(lead)

    def marcar_idade(self, lead, minutos):
        self.assertIsNotNone(lead.entrada_followup_em)
        lead.entrada_followup_em = datetime.now(timezone.utc) - timedelta(minutes=minutos)

    def agendar(self, empresa=None):
        with self.sessoes() as db:
            return followup_scheduler.processar_leads_apos_cinco_minutos(
                db, empresa_id=empresa or self.empresa,
            )

    def agendamentos(self, db, lead_id):
        return db.query(FollowupAgendamento).filter_by(lead_id=lead_id).all()

    def test_cinco_minutos_origem_vendedor_duplicidade_e_isolamento(self):
        with self.sessoes() as db:
            ids = {}
            for nome, empresa, minutos, anuncio, remetente in (
                ("recente", self.empresa, 4, False, "agente"),
                ("organica", self.empresa, 6, False, "agente"),
                ("anuncio", self.empresa, 6, True, "humano"),
                ("outra", self.outra_empresa, 6, False, "agente"),
            ):
                lead = self.nova_lead(db, empresa=empresa, anuncio=anuncio)
                self.confirmar(db, lead, remetente)
                self.marcar_idade(lead, minutos)
                ids[nome] = lead.id
            db.commit()

        self.assertEqual(self.agendar(), 2)
        self.assertEqual(self.agendar(), 0)
        with self.sessoes() as db:
            for nome, lead_id in ids.items():
                agendado = nome in ("organica", "anuncio")
                self.assertEqual(len(self.agendamentos(db, lead_id)), int(agendado))
                self.assertEqual(
                    db.get(Lead, lead_id).status,
                    "Aguardando resposta" if agendado else "Em atendimento",
                )
        self.assertEqual(self.agendar(self.outra_empresa), 1)

    def test_resposta_qualificacao_encaminhamento_e_humano_impedem_agendamento(self):
        with self.sessoes() as db:
            respondeu = self.nova_lead(db)
            self.confirmar(db, respondeu)
            self.mensagem(db, respondeu, "cliente")
            self.confirmar(db, respondeu)
            qualificada = self.nova_lead(db)
            qualificada.resumo_vendedor = "Já qualificada"
            encaminhada = self.nova_lead(db, etapa="aguardando_humano")
            assumida = self.nova_lead(db, humano_assumiu=True)
            for lead in (qualificada, encaminhada, assumida):
                self.confirmar(db, lead)
            for lead in (respondeu, qualificada, encaminhada, assumida):
                self.marcar_idade(lead, 6)
            db.commit()

        self.assertEqual(self.agendar(), 0)

    def test_primeira_confirmacao_ignora_falha_e_preserva_o_marco(self):
        with self.sessoes() as db:
            lead = self.nova_lead(db)
            self.confirmar(db, lead, status=STATUS_ENVIO_FALHA)
            self.assertIsNone(lead.entrada_followup_em)
            self.confirmar(db, lead)
            self.marcar_idade(lead, 6)
            db.flush()
            marco = lead.entrada_followup_em
            self.confirmar(db, lead, remetente="humano")
            self.assertEqual(lead.entrada_followup_em, marco)
            db.commit()
        self.assertEqual(self.agendar(), 1)

    def test_resposta_cancela_reserva_antes_do_inicio_e_replay_inicial_preserva(self):
        with self.sessoes() as db:
            lead = self.nova_lead(db)
            self.confirmar(db, lead)
            self.marcar_idade(lead, 6)
            lead_id = lead.id
            db.commit()
        self.assertEqual(self.agendar(), 1)
        with self.sessoes() as db:
            lead = db.get(Lead, lead_id)
            agendamento, = self.agendamentos(db, lead_id)
            inicial = db.query(Mensagem).filter_by(conversa_id=lead.conversa_id).order_by(
                Mensagem.id.asc()
            ).first()
            processar_resposta_cliente_followup(db, mensagem=inicial)
            self.assertEqual(agendamento.status, "pendente")

            agora = agendamento.agendado_para
            agendamento_id, motivo = reservar_agendamento_pendente(
                db, empresa_id=self.empresa, agora=agora,
            )
            self.assertEqual((agendamento_id, motivo), (agendamento.id, "reservado"))
            token = agendamento.reserva_token
            self.mensagem(db, lead, "cliente")
            db.flush()
            self.assertFalse(confirmar_inicio_envio_followup(
                db, empresa_id=self.empresa, agendamento_id=agendamento.id,
                reserva_token=token, agora=agora,
            )[0])
            db.refresh(lead)
            self.assertEqual(lead.status, "Em qualificação")
            self.assertEqual(agendamento.status, "cancelado")

    def test_autorizacao_exige_aguardando_resposta_e_recuperacao_separa_estados(self):
        with self.sessoes() as db:
            ids = []
            for _ in range(3):
                lead = self.nova_lead(db)
                self.confirmar(db, lead)
                self.marcar_idade(lead, 6)
                ids.append(lead.id)
            db.commit()
        self.assertEqual(self.agendar(), 3)
        with self.sessoes() as db:
            agendamentos = [self.agendamentos(db, lead_id)[0] for lead_id in ids]
            agora = max(agendamento.agendado_para for agendamento in agendamentos)
            for _ in agendamentos:
                self.assertEqual(reservar_agendamento_pendente(
                    db, empresa_id=self.empresa, agora=agora,
                )[1], "reservado")
            bloqueado, sem_inicio, com_inicio = agendamentos
            db.get(Lead, bloqueado.lead_id).status = "Em atendimento"
            db.flush()
            self.assertEqual(autorizar_envio_followup_reservado(
                db, empresa_id=self.empresa, agendamento_id=bloqueado.id,
                reserva_token=bloqueado.reserva_token, agora=agora,
            ), (False, "lead_nao_aguardando_resposta"))
            self.assertTrue(confirmar_inicio_envio_followup(
                db, empresa_id=self.empresa, agendamento_id=com_inicio.id,
                reserva_token=com_inicio.reserva_token, agora=agora,
            )[0])
            self.assertEqual(recuperar_reservas_expiradas(
                db, empresa_id=self.empresa, agora=agora + timedelta(minutes=3),
            ), 2)
            self.assertEqual(sem_inicio.status, "pendente")
            self.assertEqual(com_inicio.status, "inconclusivo")

    def test_flags_independentes_e_transporte_real_bloqueado(self):
        with self.sessoes() as db:
            lead = self.nova_lead(db)
            self.confirmar(db, lead)
            self.marcar_idade(lead, 6)
            lead_id = lead.id
            db.commit()
        with patch.object(followup_worker, "enviar_followup_via_waha") as transporte:
            with patch.dict(os.environ, {"FOLLOWUP_WORKER_ATIVO": "0"}):
                self.assertEqual(followup_worker.executar_ciclo_followup(
                    empresa_id=self.empresa, modo_simulacao=False,
                ), (False, "worker_desabilitado"))
            self.assertEqual(followup_worker.executar_ciclo_followup(
                empresa_id=self.empresa, modo_simulacao=False,
            ), (False, "envio_real_desabilitado"))
            for flag in ("0", "true"):
                with patch.dict(os.environ, {"FOLLOWUP_AGENDAMENTO_ATIVO": flag}):
                    followup_scheduler.executar_agendador(
                        empresa_ids=[self.empresa], max_ciclos=1,
                        session_factory=self.sessoes, modo_simulacao=False,
                    )
                with self.sessoes() as db:
                    self.assertEqual(
                        [a.status for a in self.agendamentos(db, lead_id)],
                        ["pendente"] if flag == "true" else [],
                    )
            transporte.assert_not_called()

    def test_janela_fuso_e_intervalo(self):
        manha = datetime(2026, 11, 20, 13, tzinfo=timezone.utc)
        self.assertEqual(
            calcular_primeiro_followup(manha, intervalo_minutos=180),
            datetime(2026, 11, 20, 16, tzinfo=timezone.utc),
        )
        sexta = datetime(2026, 11, 20, 20, tzinfo=timezone.utc)
        self.assertEqual(
            calcular_primeiro_followup(sexta, intervalo_minutos=180),
            datetime(2026, 11, 21, 11, tzinfo=timezone.utc),
        )
        self.assertEqual(
            calcular_primeiro_followup(
                sexta, intervalo_minutos=180, sabado_ativo=False, fuso_horario="UTC",
            ),
            datetime(2026, 11, 23, 8, tzinfo=timezone.utc),
        )

    def test_worker_simulado_usa_conexao_e_intervalo_da_proxima_tentativa(self):
        with self.sessoes() as db:
            especialista = Especialista(empresa_id=self.empresa, nome="Vendedor teste")
            db.add(especialista)
            db.flush()
            sessao = f"teste-{uuid4()}"
            conexao = ConexaoCanal(
                empresa_id=self.empresa, provedor="waha", canal="whatsapp",
                sessao_waha=sessao, especialista_id=especialista.id,
            )
            db.add(conexao)
            db.flush()
            lead = self.nova_lead(db, conexao_canal_id=conexao.id)
            self.confirmar(db, lead)
            self.marcar_idade(lead, 240)
            config = db.query(FollowupConfiguracao).filter_by(empresa_id=self.empresa).one()
            config.segunda_sexta_inicio = config.sabado_inicio = time(0)
            config.segunda_sexta_fim = config.sabado_fim = time(23, 59, 59, 999999)
            config.domingo_ativo = True
            config.quantidade_tentativas = 2
            db.add(FollowupModeloMensagem(
                empresa_id=self.empresa, numero_tentativa=2, intervalo_minutos=40,
                texto="Segunda tentativa simulada",
            ))
            lead_id = lead.id
            chat_id = db.get(Conversa, lead.conversa_id).identificador
            db.commit()

        destinos = []

        def simular(destino):
            destinos.append(destino)
            return "aceito_waha", "id-simulado"

        followup_scheduler.executar_agendador(
            empresa_ids=[self.empresa], max_ciclos=1, session_factory=self.sessoes,
            mapa_sessoes={}, simulador_envio=simular,
        )
        self.assertEqual(len(destinos), 1)
        self.assertEqual(destinos[0]["sessao"], sessao)
        self.assertEqual(destinos[0]["chat_id"], chat_id)
        self.assertEqual(destinos[0]["texto"], "Mensagem simulada")
        with self.sessoes() as db:
            primeira, segunda = sorted(
                self.agendamentos(db, lead_id), key=lambda a: a.numero_tentativa,
            )
            self.assertEqual(primeira.status, "enviado")
            self.assertEqual(segunda.status, "pendente")
            self.assertEqual(
                segunda.agendado_para - primeira.enviado_em, timedelta(minutes=40),
            )

    def test_dois_schedulers_concorrentes_criam_uma_tentativa(self):
        sessoes = sessionmaker(bind=self.engine, autoflush=False)
        with sessoes.begin() as db:
            empresa_id = self.criar_empresa(db)
            lead = self.nova_lead(db, empresa=empresa_id)
            self.confirmar(db, lead)
            self.marcar_idade(lead, 6)

        def limpar_dados_proprios():
            with sessoes.begin() as db:
                for modelo in (
                    FollowupAgendamento, Mensagem, Lead, Conversa,
                    FollowupModeloMensagem, FollowupConfiguracao,
                ):
                    db.query(modelo).filter_by(empresa_id=empresa_id).delete()
                db.query(Empresa).filter_by(id=empresa_id).delete()

        self.addCleanup(limpar_dados_proprios)
        inicio = Barrier(2, timeout=10)

        def ciclo():
            with sessoes() as db:
                inicio.wait()
                return followup_scheduler.processar_leads_apos_cinco_minutos(
                    db, empresa_id=empresa_id,
                )

        with ThreadPoolExecutor(max_workers=2) as workers:
            resultados = [workers.submit(ciclo) for _ in range(2)]
            self.assertEqual(sorted(futuro.result() for futuro in resultados), [0, 1])
        with sessoes() as db:
            self.assertEqual(
                db.query(FollowupAgendamento).filter_by(empresa_id=empresa_id).count(), 1,
            )

    def test_webhook_real_com_payloads_simulados(self):
        from fastapi.testclient import TestClient
        from app.database import database
        from app.models.models import Base

        with patch.dict(os.environ, {"OPENAI_API_KEY": "chave-ficticia"}):
            with patch.object(Base.metadata, "create_all"):
                import main

        casos = (
            ("texto", "message", {"body": "Obrigado"}, "texto"),
            ("audio", "message", {"_data": {"type": "ptt"}}, "midia"),
            ("imagem", "message.any", {"hasMedia": True, "media": {"url": None}}, "midia"),
            ("contato", "message", {"vCards": ["BEGIN:VCARD"]}, "contato"),
            ("localizacao", "message", {"type": "location"}, "localizacao"),
            ("reacao", "message.reaction", {"reaction": {"text": "👍", "messageId": "alvo"}}, "reacao"),
            ("remocao", "message.reaction", {"reaction": {"text": "", "messageId": "alvo"}}, None),
            ("ack", "message.ack", {"hasMedia": True}, None),
            ("protocolo", "message", {"type": "protocol", "body": ""}, None),
            ("vazio", "message", {"body": " ", "_data": None}, None),
        )
        with self.sessoes() as db:
            conexao = ConexaoCanal(
                empresa_id=self.empresa, provedor="waha", canal="whatsapp",
                sessao_waha=f"teste-{uuid4()}",
            )
            db.add(conexao)
            db.add(ConexaoCanal(
                empresa_id=self.empresa, provedor="waha", canal="whatsapp",
                sessao_waha="sessao-incorreta",
            ))
            db.flush()
            sessao = conexao.sessao_waha
            leads = {}
            for nome, *_ in casos:
                lead = self.nova_lead(db, conexao_canal_id=conexao.id)
                self.confirmar(db, lead)
                if nome != "audio":
                    self.marcar_idade(lead, 6)
                leads[nome] = (lead.id, lead.conversa_id, db.get(Conversa, lead.conversa_id).identificador)
            externa = self.nova_lead(db, conexao_canal_id=conexao.id)
            externa_id = externa.id
            chat_externo = db.get(Conversa, externa.conversa_id).identificador
            db.commit()
        self.assertEqual(self.agendar(), len(casos) - 1)
        # O texto usa a persistência real. O atendimento humano evita resposta da Sofia.
        with self.sessoes() as db:
            conversa = db.get(Conversa, leads["texto"][1])
            conversa.humano_assumiu = True
            conversa.status_atendimento = "finalizado"
            db.commit()

        with (
            patch.object(main, "SessionLocal", self.sessoes),
            patch.object(database, "SessionLocal", self.sessoes),
            patch.dict(main.SESSAO_EMPRESA, {sessao: self.empresa, "sessao-incorreta": self.empresa}),
            patch.object(main, "obter_lid_luciano", return_value=None),
            patch.object(main, "obter_telefone_real_waha", return_value=None),
            patch("requests.sessions.Session.request", side_effect=AssertionError("Rede proibida")),
            TestClient(main.app) as client,
        ):
            for evento in ("message", "message.any"):
                resposta = client.post("/webhook/waha", json={
                    "event": evento, "session": sessao, "payload": {
                        "id": str(uuid4()), "fromMe": True, "source": "app",
                        "to": chat_externo, "body": "Envio direto pelo aplicativo",
                    },
                })
                self.assertEqual(resposta.status_code, 200)
                self.assertEqual(resposta.json()["status"], "ignorado")
            with self.sessoes() as db:
                self.assertIsNone(db.get(Lead, externa_id).entrada_followup_em)

            for nome, evento, campos, tipo in casos:
                with self.subTest(nome=nome):
                    lead_id, conversa_id, chat_id = leads[nome]
                    mensagem_id = str(uuid4())
                    evento_waha = {
                        "event": evento, "session": sessao, "payload": {
                            "id": mensagem_id, "from": chat_id, "fromMe": False, **campos,
                        },
                    }
                    if nome == "imagem":
                        resposta = client.post("/webhook/waha", json={
                            **evento_waha, "session": "sessao-incorreta",
                        })
                        self.assertEqual(resposta.json()["status"], "ignorado")
                    for _ in range(2):
                        self.assertEqual(client.post("/webhook/waha", json=evento_waha).status_code, 200)
                    with self.sessoes() as db:
                        registros = db.query(Mensagem).filter_by(
                            conversa_id=conversa_id, mensagem_id_externo=mensagem_id,
                        ).all()
                        self.assertEqual([r.tipo for r in registros], [tipo] if tipo else [])
                        if nome == "audio":
                            self.marcar_idade(db.get(Lead, lead_id), 6)
                            db.commit()
                        else:
                            self.assertEqual(
                                self.agendamentos(db, lead_id)[0].status,
                                "cancelado" if tipo else "pendente",
                            )
        self.assertEqual(self.agendar(), 0)

    def test_sofia_descarta_resposta_preparada_apos_tomada_humana(self):
        from fastapi.testclient import TestClient
        from app.models.models import Base

        with patch.dict(os.environ, {"OPENAI_API_KEY": "chave-ficticia"}):
            with patch.object(Base.metadata, "create_all"):
                import main

        with self.sessoes() as db:
            conexao = ConexaoCanal(
                empresa_id=self.empresa, provedor="waha", canal="whatsapp",
                sessao_waha=f"teste-{uuid4()}", ativo=True,
            )
            db.add(conexao)
            db.flush()
            lead = self.nova_lead(db, conexao_canal_id=conexao.id)
            conversa = db.get(Conversa, lead.conversa_id)
            conversa_id, chat_id, sessao = conversa.id, conversa.identificador, conexao.sessao_waha
            db.commit()

        def preparar_resposta(_dados):
            # Simula a tomada ocorrida depois que a Sofia já preparou a resposta.
            with self.sessoes() as db:
                conversa = db.get(Conversa, conversa_id)
                conversa.humano_assumiu = True
                conversa.status_atendimento = "em_atendimento_humano"
                db.commit()
            return {"conversa_id": conversa_id, "resposta_agente": "Resposta simulada"}

        mensagem_id = str(uuid4())
        with (
            patch.object(main, "SessionLocal", self.sessoes),
            patch.dict(main.SESSAO_EMPRESA, {sessao: self.empresa}),
            patch.object(main, "receber_mensagem", side_effect=preparar_resposta),
            patch.object(main, "obter_lid_luciano", return_value=None),
            patch.object(main, "obter_telefone_real_waha", return_value=None),
            patch.object(main, "definir_presenca_digitacao"),
            patch.object(main, "calcular_delay_resposta", return_value=0),
            patch.object(main, "enviar_texto_waha") as transporte,
            patch("requests.sessions.Session.request", side_effect=AssertionError("Rede proibida")),
            TestClient(main.app) as client,
        ):
            resposta = client.post("/webhook/waha", json={
                "event": "message", "session": sessao,
                "payload": {"id": mensagem_id, "from": chat_id, "fromMe": False, "body": "Olá"},
            })
            self.assertEqual(resposta.status_code, 200)
            self.assertEqual(resposta.json().get("motivo"), "atendimento_humano_assumido")
            transporte.assert_not_called()

    def test_conexao_crm_assinada_sem_mapa_registra_texto_com_sofia_desativada(self):
        from fastapi.testclient import TestClient
        from app.database import database
        from app.models.models import Base
        from app.services.followup_sessao_waha_service import resolver_sessao_waha_conversa

        with patch.dict(os.environ, {"OPENAI_API_KEY": "chave-ficticia"}):
            with patch.object(Base.metadata, "create_all"):
                import main

        sessao = f"orion-{self.empresa}-{uuid4().hex}"
        with self.sessoes() as db:
            conexao = ConexaoCanal(
                empresa_id=self.empresa, sessao_waha=sessao, canal="whatsapp", provedor="waha",
                gerenciada_crm=True, sofia_ativa=False,
            )
            db.add(conexao)
            db.flush()
            conexao_id = conexao.id
            db.commit()

        chave = "hmac-ficticio-fase5"
        mensagem_id = str(uuid4())
        corpo = json.dumps({
            "event": "message", "session": sessao,
            "payload": {"id": mensagem_id, "from": "5511999999999@c.us", "fromMe": False, "body": "Mensagem simulada"},
        }).encode()
        headers = {
            "Content-Type": "application/json", "X-Webhook-Hmac-Algorithm": "sha512",
            "X-Webhook-Hmac": hmac.new(chave.encode(), corpo, hashlib.sha512).hexdigest(),
        }
        with (
            patch.dict(os.environ, {"WAHA_WEBHOOK_HMAC_KEY": chave}),
            patch.object(main, "SessionLocal", self.sessoes),
            patch.object(database, "SessionLocal", self.sessoes),
            patch.object(main, "obter_lid_luciano", return_value=None),
            patch.object(main, "obter_telefone_real_waha", return_value=None),
            patch.object(main, "conduzir_conversa") as sofia,
            patch("requests.sessions.Session.request", side_effect=AssertionError("Rede proibida")),
            TestClient(main.app) as client,
        ):
            resposta = client.post("/webhook/waha", content=corpo, headers=headers)
            self.assertEqual(resposta.json()["status"], "processado", resposta.text)
            sofia.assert_not_called()

        with self.sessoes() as db:
            registro = db.query(Mensagem).filter_by(empresa_id=self.empresa, mensagem_id_externo=mensagem_id).one()
            conversa = db.get(Conversa, registro.conversa_id)
            self.assertEqual((conversa.conexao_canal_id, conversa.status_atendimento), (conexao_id, "aguardando_humano"))
            db.get(ConexaoCanal, conexao_id).operacao_suspensa = True
            db.flush()
            self.assertEqual(resolver_sessao_waha_conversa(
                db, empresa_id=self.empresa, conexao_canal_id=conexao_id,
            ), (None, "conexao_waha_suspensa"))

    def test_ack_assinado_atualiza_saida_da_sofia_sem_perder_entrada_do_followup(self):
        from fastapi.testclient import TestClient
        from app.models.models import Base
        from app.services.followup_service import consultar_primeira_resposta_confirmada

        with patch.dict(os.environ, {"OPENAI_API_KEY": "chave-ficticia"}):
            with patch.object(Base.metadata, "create_all"):
                import main

        senha = "chave-hmac-ficticia"
        sessao = f"ack-ficticio-{uuid4()}"
        with self.sessoes() as db:
            conexao = ConexaoCanal(
                empresa_id=self.empresa, sessao_waha=sessao, canal="whatsapp", provedor="waha",
            )
            db.add(conexao)
            db.flush()
            lead = self.nova_lead(db, conexao_canal_id=conexao.id)
            self.confirmar(db, lead)
            self.marcar_idade(lead, 6)
            conversa_id = lead.conversa_id
            resposta = db.query(Mensagem).filter_by(
                conversa_id=conversa_id, remetente="agente",
            ).one()
            resposta.sessao_waha = sessao
            resposta.mensagem_id_waha = "sofia-ack-ficticio"
            mensagem_id = resposta.id
            db.commit()

        corpo = json.dumps({
            "event": "message.ack", "session": sessao,
            "payload": {"id": "sofia-ack-ficticio", "fromMe": True, "ack": 3, "ackName": "READ"},
        }).encode()
        headers = {"Content-Type": "application/json"}
        with (
            patch.dict(os.environ, {"WAHA_WEBHOOK_HMAC_KEY": senha}),
            patch.object(main, "SessionLocal", self.sessoes),
            patch("requests.sessions.Session.request", side_effect=AssertionError("Rede proibida")),
            TestClient(main.app) as client,
        ):
            self.assertEqual(client.post("/webhook/waha", content=corpo, headers=headers).status_code, 401)
            headers.update({
                "X-Webhook-Hmac-Algorithm": "sha512",
                "X-Webhook-Hmac": hmac.new(senha.encode(), corpo, hashlib.sha512).hexdigest(),
            })
            for resultado in ("ack_registrado", "ack_sem_transicao"):
                resposta = client.post("/webhook/waha", content=corpo, headers=headers)
                self.assertEqual(resposta.json().get("motivo"), resultado)
        with self.sessoes() as db:
            self.assertEqual(db.get(Mensagem, mensagem_id).status_envio, "lida_waha")
            primeira = consultar_primeira_resposta_confirmada(
                db, empresa_id=self.empresa, conversa_id=conversa_id,
            )
            self.assertEqual(primeira.id, mensagem_id)
        self.assertEqual(self.agendar(), 1)

    def test_webhook_midia_exige_assinatura_deduplica_e_preserva_followup(self):
        from tempfile import TemporaryDirectory
        from fastapi.testclient import TestClient
        from app.models.models import Base

        with patch.dict(os.environ, {"OPENAI_API_KEY": "chave-ficticia"}):
            with patch.object(Base.metadata, "create_all"):
                import main

        chave = "chave-assinatura-ficticia"
        with self.sessoes() as db:
            conexao = ConexaoCanal(
                empresa_id=self.empresa, provedor="waha", canal="whatsapp",
                sessao_waha=f"teste-{uuid4()}",
            )
            db.add(conexao)
            db.flush()
            sessao = conexao.sessao_waha
            lead = self.nova_lead(db, conexao_canal_id=conexao.id)
            lead_id = lead.id
            conversa = db.get(Conversa, lead.conversa_id)
            chat_id = conversa.identificador
            self.confirmar(db, lead)
            self.marcar_idade(lead, 6)
            db.commit()
        self.assertEqual(self.agendar(), 1)
        mensagem_id = str(uuid4())
        corpo = json.dumps({
            "event": "message", "session": sessao,
            "payload": {
                "id": mensagem_id, "fromMe": False, "from": chat_id, "hasMedia": True,
                "body": "Legenda fictícia", "media": {"url": "http://waha.invalido/anexo"},
            },
        }).encode()
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Hmac-Algorithm": "sha512",
            "X-Webhook-Hmac": hmac.new(chave.encode(), corpo, hashlib.sha512).hexdigest(),
        }
        with (
            TemporaryDirectory() as pasta,
            patch.dict(os.environ, {
                "ORION_CENTRAL_WHATSAPP_MIDIA_ATIVA": "1",
                "ORION_CENTRAL_WHATSAPP_MIDIA_DIR": pasta,
                "WAHA_WEBHOOK_HMAC_KEY": chave,
            }),
            patch.object(main, "SessionLocal", self.sessoes),
            patch.dict(main.SESSAO_EMPRESA, {sessao: self.empresa}),
            patch.object(main, "obter_lid_luciano", return_value=None),
            patch.object(main, "conduzir_conversa") as sofia,
            patch(
                "app.services.central_whatsapp_midia_entrada.baixar_midia_waha",
                return_value=("teste.pdf", "application/pdf", b"%PDF-1.7"),
            ) as obter_midia,
            patch("requests.sessions.Session.request", side_effect=AssertionError("Rede proibida")),
            TestClient(main.app) as client,
        ):
            sem_assinatura = client.post("/webhook/waha", content=corpo, headers={
                "Content-Type": "application/json",
            })
            self.assertEqual(sem_assinatura.status_code, 401)
            for motivo in ("midia_registrada", "midia_duplicada"):
                resposta = client.post("/webhook/waha", content=corpo, headers=headers)
                self.assertEqual(resposta.json().get("motivo"), motivo, resposta.text)
            obter_midia.assert_called_once()
            sofia.assert_not_called()
        with self.sessoes() as db:
            self.assertEqual(self.agendamentos(db, lead_id)[0].status, "cancelado")

    def test_sofia_preserva_encerramento_ocorrido_durante_geracao(self):
        from fastapi.testclient import TestClient
        from app.database import database
        from app.models.models import Base

        with patch.dict(os.environ, {"OPENAI_API_KEY": "chave-ficticia"}):
            with patch.object(Base.metadata, "create_all"):
                import main

        with self.sessoes() as db:
            lead = self.nova_lead(db)
            conversa = db.get(Conversa, lead.conversa_id)
            conversa_id, chat_id = conversa.id, conversa.identificador
            db.commit()

        def gerar_resposta(conversa, *_args, **_kwargs):
            with self.sessoes() as db:
                atual = db.get(Conversa, conversa_id)
                atual.humano_assumiu = True
                atual.status_atendimento = "finalizado"
                db.commit()
            conversa.status_atendimento = "aguardando_humano"
            conversa.historico = "Agente: Texto simulado que deve ser descartado"
            return "Texto simulado", {}

        with (
            patch.object(main, "SessionLocal", self.sessoes),
            patch.object(database, "SessionLocal", self.sessoes),
            patch.object(main, "carregar_contexto_empresa"),
            patch.object(main, "conduzir_conversa", side_effect=gerar_resposta),
            patch("requests.sessions.Session.request", side_effect=AssertionError("Rede proibida")),
            TestClient(main.app) as client,
        ):
            resposta = client.post("/mensagem", json={
                "empresa_id": self.empresa, "canal": "whatsapp", "identificador": chat_id,
                "mensagem": "Olá", "mensagem_id_externo": str(uuid4()),
            })
            self.assertEqual(resposta.status_code, 200)
            self.assertEqual(resposta.json().get("status"), "finalizado")
            self.assertIsNone(resposta.json()["resposta_agente"])
        with self.sessoes() as db:
            conversa = db.get(Conversa, conversa_id)
            self.assertTrue(conversa.humano_assumiu)
            self.assertEqual(conversa.status_atendimento, "finalizado")
            self.assertNotIn("Texto simulado", conversa.historico or "")

    def test_executores_manuais_registram_confirmacao_sem_sofia(self):
        from app.services.estados_mensagem import STATUS_PROCESSANDO
        from app.services.followup_executor_envio_humano import executar_envio_humano

        executores = [executar_envio_humano]
        if find_spec("app.services.central_whatsapp_executor") is not None:
            from app.services.central_whatsapp_executor import executar_envio_central

            executores.append(executar_envio_central)

        with self.sessoes() as db:
            vendedor = Especialista(empresa_id=self.empresa, nome="Vendedor teste")
            db.add(vendedor)
            db.flush()
            conexao = ConexaoCanal(
                empresa_id=self.empresa, provedor="waha", canal="whatsapp",
                sessao_waha=f"teste-{uuid4()}", especialista_id=vendedor.id,
            )
            db.add(conexao)
            db.flush()
            for executar in executores:
                lead = self.nova_lead(db, conexao_canal_id=conexao.id, humano_assumiu=True)
                chat_id = db.get(Conversa, lead.conversa_id).identificador
                for status in (STATUS_ENVIO_FALHA, STATUS_ENVIO_CONFIRMADO_HTTP):
                    registro = self.mensagem(db, lead, "humano")
                    registro.especialista_id = vendedor.id
                    registro.conexao_canal_id = conexao.id
                    registro.sessao_waha = conexao.sessao_waha
                    registro.status_processamento = STATUS_PROCESSANDO
                    db.flush()

                    def transportar(sessao, destinatario, texto):
                        self.assertEqual((sessao, destinatario), (conexao.sessao_waha, chat_id))
                        sucesso = status == STATUS_ENVIO_CONFIRMADO_HTTP
                        return sucesso, None if sucesso else status, str(uuid4()) if sucesso else None

                    kwargs = (
                        {"conexao_canal_id": conexao.id}
                        if executar is executar_envio_humano
                        else {"sessao": conexao.sessao_waha, "chat_id": chat_id}
                    )
                    self.assertEqual(executar(
                        db, empresa_id=self.empresa, conversa_id=lead.conversa_id,
                        mensagem_id=registro.id, especialista_id=vendedor.id,
                        transportador=transportar, **kwargs,
                    ), (status == STATUS_ENVIO_CONFIRMADO_HTTP, status))
                    db.refresh(registro)
                    db.refresh(lead)
                    self.assertEqual(registro.status_envio, status)
                    self.assertEqual(lead.entrada_followup_em is not None, status == STATUS_ENVIO_CONFIRMADO_HTTP)
                self.marcar_idade(lead, 6)
            db.commit()
        self.assertEqual(self.agendar(), 0)

    def test_saida_app_assinada_bloqueia_e_cancela_com_isolamento(self):
        from fastapi.testclient import TestClient
        from app.models.models import Base

        with patch.dict(os.environ, {"OPENAI_API_KEY": "chave-ficticia"}):
            with patch.object(Base.metadata, "create_all"):
                import main

        chave = "hmac-ficticio-para-testes"
        with self.sessoes() as db:
            conexao = ConexaoCanal(
                empresa_id=self.empresa, provedor="waha", canal="whatsapp",
                sessao_waha=f"teste-{uuid4()}",
            )
            db.add(conexao)
            db.flush()
            sessao = conexao.sessao_waha
            pendente = self.nova_lead(db, conexao_canal_id=conexao.id)
            recente = self.nova_lead(db, conexao_canal_id=conexao.id)
            outra = self.nova_lead(db, empresa=self.outra_empresa)
            pendente_id, recente_id, outra_id = pendente.id, recente.id, outra.id
            chat_pendente = db.get(Conversa, pendente.conversa_id).identificador
            chat_recente = db.get(Conversa, recente.conversa_id).identificador
            db.get(Conversa, outra.conversa_id).identificador = chat_pendente
            for lead in (pendente, recente, outra):
                self.confirmar(db, lead)
            for lead in (pendente, outra):
                self.marcar_idade(lead, 6)
            db.commit()
        self.assertEqual(self.agendar(), 1)
        self.assertEqual(self.agendar(self.outra_empresa), 1)

        with (
            patch.dict(os.environ, {"WAHA_WEBHOOK_HMAC_KEY": chave}),
            patch.dict(main.SESSAO_EMPRESA, {sessao: self.outra_empresa}),
            patch.object(main, "SessionLocal", self.sessoes),
            patch("requests.sessions.Session.request", side_effect=AssertionError("Rede proibida")),
            TestClient(main.app) as client,
        ):
            def enviar_evento(
                chat, *, source="app", mensagem_id=None, assinar=True,
                adulterar=False, entrada=False,
            ):
                corpo = json.dumps({
                    "event": "message.any", "session": sessao, "payload": {
                        "id": mensagem_id or str(uuid4()), "fromMe": not entrada,
                        "source": source, "from" if entrada else "to": chat,
                        "body": "Mensagem de teste",
                    },
                }).encode()
                headers = {"Content-Type": "application/json"}
                if assinar:
                    headers["X-Webhook-Hmac-Algorithm"] = "sha512"
                    headers["X-Webhook-Hmac"] = hmac.new(
                        chave.encode(), corpo, hashlib.sha512,
                    ).hexdigest()
                if adulterar:
                    corpo += b" "
                return client.post("/webhook/waha", content=corpo, headers=headers)

            self.assertEqual(enviar_evento(chat_pendente, assinar=False).status_code, 401)
            self.assertEqual(enviar_evento(chat_pendente, adulterar=True).status_code, 401)
            self.assertEqual(
                enviar_evento(chat_pendente, entrada=True).json()["motivo"], "empresa_divergente",
            )
            self.assertEqual(enviar_evento(chat_pendente, source="api").json()["status"], "ignorado")
            with self.sessoes() as db:
                agendamento, = self.agendamentos(db, pendente_id)
                self.assertEqual(agendamento.status, "pendente")
                self.assertEqual(reservar_agendamento_pendente(
                    db, empresa_id=self.empresa, agora=agendamento.agendado_para,
                ), (agendamento.id, "reservado"))
                db.commit()
            repetida = str(uuid4())
            for _ in range(2):
                self.assertEqual(enviar_evento(
                    chat_pendente, mensagem_id=repetida,
                ).json()["motivo"], "followup_bloqueado_saida_manual")
            self.assertEqual(enviar_evento(chat_recente).json()["status"], "processado")

        with self.sessoes() as db:
            self.assertEqual(self.agendamentos(db, pendente_id)[0].status, "cancelado")
            self.assertEqual(self.agendamentos(db, outra_id)[0].status, "pendente")
            registro = db.query(Mensagem).filter_by(mensagem_id_externo=repetida).one()
            self.assertEqual(registro.empresa_id, self.empresa)
            self.assertIsNone(registro.status_envio)
            self.marcar_idade(db.get(Lead, recente_id), 6)
            db.commit()
        self.assertEqual(self.agendar(), 0)
