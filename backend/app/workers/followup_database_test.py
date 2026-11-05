"""Conexao exclusiva para testes locais do Follow-up."""

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker


def criar_sessoes_followup_teste(database_url: str):
    """Cria sessoes apenas para o PostgreSQL isolado."""

    url = make_url(database_url)

    if (
        url.get_backend_name() != "postgresql"
        or url.host != "127.0.0.1"
        or url.port != 55432
        or url.database != "orion_crm_followup_test"
        or url.username != "orion_test"
    ):
        raise ValueError("conexao_fora_do_banco_de_testes")

    engine = create_engine(
        url,
        pool_pre_ping=True,
        future=True,
    )

    return sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )
