from dashboard.database.db import conectar


def coluna_existe(cursor, tabela: str, coluna: str) -> bool:
    cursor.execute(
        '''
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = %s
              AND column_name = %s
        )
        ''',
        (tabela, coluna),
    )
    return bool(cursor.fetchone()[0])


def constraint_existe(cursor, nome_constraint: str) -> bool:
    cursor.execute(
        '''
        SELECT EXISTS (
            SELECT 1
            FROM pg_constraint
            WHERE conname = %s
        )
        ''',
        (nome_constraint,),
    )
    return bool(cursor.fetchone()[0])


def migrar_hierarquia_parceiros() -> None:
    conn = conectar()

    try:
        with conn.cursor() as cursor:
            if not coluna_existe(cursor, 'empresas', 'parceiro_id'):
                cursor.execute(
                    '''
                    ALTER TABLE empresas
                    ADD COLUMN parceiro_id INTEGER
                    '''
                )
                print('Coluna criada: empresas.parceiro_id')

            if not constraint_existe(
                cursor,
                'empresas_parceiro_id_fkey',
            ):
                cursor.execute(
                    '''
                    ALTER TABLE empresas
                    ADD CONSTRAINT empresas_parceiro_id_fkey
                    FOREIGN KEY (parceiro_id)
                    REFERENCES empresas(id)
                    ON DELETE RESTRICT
                    '''
                )
                print('Foreign key criada: empresas_parceiro_id_fkey')

            cursor.execute(
                '''
                CREATE INDEX IF NOT EXISTS ix_empresas_parceiro_id
                ON empresas (parceiro_id)
                '''
            )

            cursor.execute(
                '''
                UPDATE empresas
                SET parceiro_id = NULL
                WHERE tipo IN ('master', 'parceiro')
                '''
            )

            cursor.execute(
                '''
                UPDATE empresas AS cliente
                SET parceiro_id = parceiro.id
                FROM empresas AS parceiro
                WHERE parceiro.slug = 'forway'
                  AND cliente.id <> parceiro.id
                  AND cliente.tipo = 'cliente'
                  AND (
                      cliente.parceiro_nome = 'Forway'
                      OR cliente.parceiro_nome = parceiro.nome
                  )
                  AND cliente.parceiro_id IS NULL
                '''
            )

            cursor.execute(
                '''
                UPDATE empresas
                SET parceiro_nome = parceiro.nome
                FROM empresas AS parceiro
                WHERE empresas.parceiro_id = parceiro.id
                '''
            )

        conn.commit()
        print('Hierarquia de parceiros migrada com sucesso.')

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def validar_hierarquia() -> None:
    conn = conectar()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                '''
                SELECT
                    empresa.id,
                    empresa.nome,
                    empresa.tipo,
                    empresa.parceiro_id,
                    parceiro.nome AS parceiro
                FROM empresas AS empresa
                LEFT JOIN empresas AS parceiro
                    ON parceiro.id = empresa.parceiro_id
                ORDER BY empresa.id
                '''
            )

            registros = cursor.fetchall()

            print('')
            print('Empresas e vínculos:')
            for registro in registros:
                print(registro)

    finally:
        conn.close()


def main() -> None:
    migrar_hierarquia_parceiros()
    validar_hierarquia()


if __name__ == '__main__':
    main()