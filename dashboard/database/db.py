import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from sqlalchemy.engine import make_url


# Raiz do projeto: agente-sdr-forway/
ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = ROOT_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)


DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        f"DATABASE_URL não encontrada no arquivo: {ENV_PATH}"
    )


def _obter_configuracao_banco() -> dict:
    """
    Converte a DATABASE_URL utilizada pelo SQLAlchemy
    nos parâmetros esperados pelo psycopg2.
    """
    url = make_url(DATABASE_URL)

    if url.get_backend_name() != "postgresql":
        raise RuntimeError(
            "O Dashboard requer uma DATABASE_URL do PostgreSQL."
        )

    if not url.database:
        raise RuntimeError(
            "O nome do banco não foi informado na DATABASE_URL."
        )

    if not url.username:
        raise RuntimeError(
            "O usuário do PostgreSQL não foi informado na DATABASE_URL."
        )

    return {
        "host": url.host or "localhost",
        "port": url.port or 5432,
        "dbname": url.database,
        "user": url.username,
        "password": url.password or "",
    }


def conectar():
    """
    Abre uma conexão PostgreSQL para o Dashboard.

    A configuração é carregada exclusivamente da DATABASE_URL
    presente no arquivo .env da raiz do projeto.
    """
    configuracao = _obter_configuracao_banco()

    return psycopg2.connect(
        **configuracao,
        connect_timeout=10,
        application_name="orion_dashboard",
    )


def testar_conexao() -> dict:
    """
    Testa a conexão e informa o banco e o usuário atuais.
    """
    conn = None

    try:
        conn = conectar()

        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    current_database(),
                    current_user,
                    version()
                """
            )

            banco, usuario, versao = cursor.fetchone()

        return {
            "conectado": True,
            "banco": banco,
            "usuario": usuario,
            "versao": versao,
        }

    except Exception as erro:
        return {
            "conectado": False,
            "erro": str(erro),
        }

    finally:
        if conn is not None:
            conn.close()