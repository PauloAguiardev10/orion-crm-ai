import os

import psycopg2
from psycopg2.extras import DictCursor


def conectar():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        database=os.getenv("POSTGRES_DB", "orion_crm_ai"),
        user=os.getenv("POSTGRES_USER", "orion_user"),
        password=os.environ["POSTGRES_PASSWORD"],
        cursor_factory=DictCursor,
    )