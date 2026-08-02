import pandas as pd

from database.db import conectar


def listar_empresas_permitidas(
    nivel: str,
    empresa_login_id: int,
) -> pd.DataFrame:
    """
    Retorna as empresas que o usuário pode selecionar como contexto ativo.

    - orion_admin: todas as empresas ativas;
    - parceiro_admin: o próprio parceiro e seus clientes;
    - demais níveis: somente a própria empresa.
    """
    conn = conectar()

    try:
        if nivel == "orion_admin":
            return pd.read_sql_query(
                """
                SELECT
                    empresa.id,
                    empresa.nome,
                    empresa.tipo,
                    empresa.parceiro_id,
                    parceiro.nome AS parceiro_nome
                FROM empresas AS empresa
                LEFT JOIN empresas AS parceiro
                    ON parceiro.id = empresa.parceiro_id
                WHERE empresa.status = 'ativa'
                ORDER BY
                    CASE empresa.tipo
                        WHEN 'master' THEN 1
                        WHEN 'parceiro' THEN 2
                        ELSE 3
                    END,
                    parceiro.nome NULLS FIRST,
                    empresa.nome
                """,
                conn,
            )

        if nivel == "parceiro_admin":
            return pd.read_sql_query(
                """
                SELECT
                    empresa.id,
                    empresa.nome,
                    empresa.tipo,
                    empresa.parceiro_id,
                    parceiro.nome AS parceiro_nome
                FROM empresas AS empresa
                LEFT JOIN empresas AS parceiro
                    ON parceiro.id = empresa.parceiro_id
                WHERE empresa.status = 'ativa'
                  AND (
                      empresa.id = %s
                      OR empresa.parceiro_id = %s
                  )
                ORDER BY
                    CASE
                        WHEN empresa.id = %s THEN 0
                        ELSE 1
                    END,
                    empresa.nome
                """,
                conn,
                params=(
                    int(empresa_login_id),
                    int(empresa_login_id),
                    int(empresa_login_id),
                ),
            )

        return pd.read_sql_query(
            """
            SELECT
                empresa.id,
                empresa.nome,
                empresa.tipo,
                empresa.parceiro_id,
                parceiro.nome AS parceiro_nome
            FROM empresas AS empresa
            LEFT JOIN empresas AS parceiro
                ON parceiro.id = empresa.parceiro_id
            WHERE empresa.id = %s
              AND empresa.status = 'ativa'
            """,
            conn,
            params=(int(empresa_login_id),),
        )

    finally:
        conn.close()


def obter_empresa_por_id(empresa_id: int):
    conn = conectar()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    nome,
                    tipo,
                    parceiro_id
                FROM empresas
                WHERE id = %s
                  AND status = 'ativa'
                """,
                (int(empresa_id),),
            )

            resultado = cursor.fetchone()

        if not resultado:
            return None

        return {
            "id": int(resultado[0]),
            "nome": resultado[1],
            "tipo": resultado[2],
            "parceiro_id": resultado[3],
        }

    finally:
        conn.close()