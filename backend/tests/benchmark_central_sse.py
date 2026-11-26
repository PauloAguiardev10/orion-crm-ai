"""Mede as tres consultas do ciclo SSE em fixtures revertidas no PostgreSQL local."""

from concurrent.futures import ThreadPoolExecutor
from os import environ
from statistics import median, quantiles
from threading import Barrier
from time import perf_counter
from uuid import uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

environ["DATABASE_URL"] = "sqlite://"
environ["PYTHON_DOTENV_DISABLED"] = "1"
environ["ORION_API_AUTH_SECRET"] = "benchmark-descartavel-" * 3

from app.models.models import ConexaoCanal, Conversa, Empresa, Mensagem
from app.services.autenticacao_api import gerar_token_api
from app.services.central_whatsapp_consultas import listar_conversas, listar_historico
from app.services.followup_identidade_api import identificar_usuario_api


VENDEDORES = 12
RODADAS = 20
ESPERA = Barrier(VENDEDORES, timeout=45)


def medir(engine):
    with engine.connect() as conexao, conexao.begin() as transacao, Session(bind=conexao) as db:
        nome = f"Benchmark SSE {uuid4()}"
        empresa = Empresa(nome=nome, plano="Premium")
        db.add(empresa)
        db.flush()
        usuario = db.execute(text("""
            INSERT INTO usuarios (empresa_id, nome, email, senha_hash, nivel, status)
            VALUES (:empresa, 'Vendedor ficticio', :email, 'ficticio', 'vendedor', 'ativo')
            RETURNING id
        """), {"empresa": empresa.id, "email": f"{uuid4()}@example.invalid"}).scalar_one()
        especialista = db.execute(text("""
            SELECT id FROM especialistas WHERE empresa_id = :empresa AND usuario_id = :usuario
        """), {"empresa": empresa.id, "usuario": usuario}).scalar_one()
        canal = ConexaoCanal(empresa_id=empresa.id, especialista_id=especialista, canal="whatsapp",
                             provedor="waha", ativo=True, sessao_waha=str(uuid4()))
        db.add(canal)
        db.flush()
        chats = [Conversa(empresa_id=empresa.id, conexao_canal_id=canal.id, especialista_id=especialista,
                          canal="whatsapp", identificador=f"55119999{i:04d}@c.us") for i in range(15)]
        db.add_all(chats)
        db.flush()
        db.add_all(Mensagem(empresa_id=empresa.id, conversa_id=chat.id, conexao_canal_id=canal.id,
                            remetente="cliente", from_me=False, texto="Mensagem sintetica")
                   for chat in chats for _ in range(20))
        db.flush()
        token = gerar_token_api(usuario_id=usuario, empresa_id=empresa.id)
        amostras = []
        ESPERA.wait()
        for _ in range(RODADAS):
            inicio = perf_counter()
            identidade, _ = identificar_usuario_api(db, token=token)
            assert identidade is not None
            lista = listar_conversas(db, identidade=identidade, limite=100, deslocamento=0,
                                      conexao_id=None, fixar_conversa_id=chats[0].id)
            historico = listar_historico(db, identidade=identidade, conversa_id=chats[0].id,
                                        limite=100, deslocamento=0)
            assert len(lista) == 15 and historico is not None and len(historico) == 20
            amostras.append((perf_counter() - inicio) * 1000)
        transacao.rollback()
        return amostras


def main():
    engine = create_engine(
        "postgresql+psycopg2://orion_test@127.0.0.1:55432/orion_crm_followup_test",
        pool_size=VENDEDORES, max_overflow=0,
    )
    try:
        with engine.connect() as db:
            assert db.execute(text("SELECT current_database(), current_user, inet_server_port()")).one() == (
                "orion_crm_followup_test", "orion_test", 55432,
            )
        with ThreadPoolExecutor(max_workers=VENDEDORES) as pool:
            amostras = [ms for rodada in pool.map(lambda _: medir(engine), range(VENDEDORES)) for ms in rodada]
        print(f"{len(amostras)} ciclos | mediana {median(amostras):.2f} ms | "
              f"p95 {quantiles(amostras, n=100)[94]:.2f} ms | max {max(amostras):.2f} ms")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
