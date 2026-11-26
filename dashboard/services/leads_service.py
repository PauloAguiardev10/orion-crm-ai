import pandas as pd

from utils.tempo import horas_desde_timestamp_utc

from database.db import conectar

from services.intencao_service import (
    detectar_intencao,
    calcular_score,
    definir_temperatura,
    gerar_resumo,
)


STATUS_LISTA = [
    "Aguardando resposta",
    "Em qualificação",
    "Aguardando atendimento",
    "Em atendimento",
    "Proposta enviada",
    "Negócio fechado",
    "Não fechado",
]


def garantir_colunas_leads():
    """
    No PostgreSQL, as tabelas e colunas já foram criadas.

    O dashboard não deve criar nem alterar a estrutura do banco.
    Ele apenas consulta e atualiza os dados.
    """
    return None


def carregar_leads(empresa_id=1):

    garantir_colunas_leads()

    conn = conectar()

    try:
        leads = pd.read_sql_query(
            """
            SELECT
                leads.id,
                leads.especialista_id,
                leads.empresa_id,

                clientes.nome,
                clientes.empresa,
                clientes.telefone,
                clientes.canal,

                (
                    SELECT conversas.historico
                    FROM conversas
                    WHERE conversas.canal = clientes.canal
                      AND (
                          conversas.telefone = clientes.telefone
                          OR conversas.nome = clientes.nome
                      )
                      AND conversas.empresa_id = leads.empresa_id
                    ORDER BY conversas.id DESC
                    LIMIT 1
                ) AS historico,

                leads.produto,
                leads.temperatura,
                leads.prioridade,
                leads.score,
                leads.origem,
                leads.observacoes,
                leads.resumo_vendedor,
                leads.status,

                COALESCE(
                    especialistas.nome,
                    NULLIF(
                        leads.responsavel,
                        'Não atribuído'
                    )
                ) AS responsavel,

                leads.valor_negocio,
                leads.mensalidade,
                leads.motivo_perda,
                leads.observacao_comercial,
                leads.criado_em

            FROM leads

            LEFT JOIN clientes
                ON clientes.id = leads.cliente_id
               AND clientes.empresa_id = leads.empresa_id

            LEFT JOIN especialistas
                ON especialistas.id = leads.especialista_id
               AND especialistas.empresa_id = leads.empresa_id

            WHERE leads.empresa_id = %s

            ORDER BY leads.id DESC
            """,
            conn,
            params=(empresa_id,),
        )

    finally:
        conn.close()

    if not leads.empty:

        leads["status"] = leads["status"].fillna(
            "Aguardando atendimento"
        )

        leads["responsavel"] = leads["responsavel"].fillna(
            "Não atribuído"
        )

        leads["temperatura"] = leads["temperatura"].fillna(
            "fria"
        )

        leads["prioridade"] = leads["prioridade"].fillna(
            "baixa"
        )

        leads["produto"] = leads["produto"].fillna(
            "Não identificado"
        )

        leads["canal"] = leads["canal"].fillna(
            "WhatsApp"
        )

        leads["canal"] = leads["canal"].replace(
            {
                "Facebook": "Facebook Messenger",
                "Messenger": "Facebook Messenger",
                "Instagram": "Instagram Direct",
            }
        )

        leads["valor_negocio"] = leads["valor_negocio"].fillna(0)
        leads["mensalidade"] = leads["mensalidade"].fillna(0)
        leads["motivo_perda"] = leads["motivo_perda"].fillna("")
        leads["observacao_comercial"] = leads[
            "observacao_comercial"
        ].fillna("")

        leads["criado_em"] = pd.to_datetime(
            leads["criado_em"],
            errors="coerce",
        )

        leads["horas_desde_entrada"] = leads["criado_em"].apply(
            lambda data: horas_desde_timestamp_utc(
                data.to_pydatetime()
            )
            if pd.notna(data)
            else 0
        )

    return leads


ESCOPO_RESPONSAVEL_LEAD = """
    FROM especialistas e
    LEFT JOIN usuarios u ON u.id = e.usuario_id AND u.empresa_id = e.empresa_id
    WHERE e.empresa_id = %s
      AND (e.usuario_id IS NULL OR (u.status = 'ativo'
           AND u.nivel IN ('vendedor', 'usuario', 'admin_empresa', 'parceiro_admin', 'orion_admin')))
"""


def carregar_responsaveis_leads(empresa_id):
    conn = conectar()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT e.id, e.nome " + ESCOPO_RESPONSAVEL_LEAD + " ORDER BY e.nome, e.id",
                (int(empresa_id),),
            )
            return cursor.fetchall()
    finally:
        conn.close()


def atualizar_lead(
    lead_id,
    novo_status,
    responsavel,
    valor_negocio=0,
    mensalidade=0,
    motivo_perda="",
    observacao_comercial="",
    *,
    empresa_id,
    especialista_id=None,
    preservar_responsavel=False,
):

    garantir_colunas_leads()

    conn = conectar()
    cursor = conn.cursor()

    try:
        if not preservar_responsavel and especialista_id is not None:
            cursor.execute("SELECT e.nome " + ESCOPO_RESPONSAVEL_LEAD + " AND e.id = %s",
                           (int(empresa_id), int(especialista_id)))
            registro = cursor.fetchone()
            if registro is None:
                return False
            responsavel = registro[0]
        cursor.execute(
            """
            UPDATE leads
            SET
                status = %s,
                responsavel = CASE WHEN %s THEN responsavel ELSE %s END,
                especialista_id = CASE WHEN %s THEN especialista_id ELSE %s END,
                valor_negocio = %s,
                mensalidade = %s,
                motivo_perda = %s,
                observacao_comercial = %s,
                atualizado_em = CURRENT_TIMESTAMP
            WHERE id = %s AND empresa_id = %s
            """,
            (
                novo_status,
                preservar_responsavel,
                responsavel,
                preservar_responsavel,
                especialista_id,
                float(valor_negocio or 0),
                float(mensalidade or 0),
                motivo_perda,
                observacao_comercial,
                int(lead_id),
                int(empresa_id),
            ),
        )

        if cursor.rowcount != 1:
            return False

        # Quando o Luciano/especialista marca a lead como
        # "Em atendimento", sincroniza a conversa para
        # indicar que o atendimento humano foi assumido.
        if novo_status == "Em atendimento":
            cursor.execute(
                """
                UPDATE conversas
                SET
                    humano_assumiu = TRUE,
                    status_atendimento = 'em_atendimento_humano',
                    atualizado_em = CURRENT_TIMESTAMP
                WHERE id = (
                    SELECT conversa_id
                    FROM leads
                    WHERE id = %s AND empresa_id = %s
                ) AND empresa_id = %s
                """,
                (int(lead_id), int(empresa_id), int(empresa_id)),
            )

        conn.commit()
        return True

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()


def analisar_lead_automaticamente(
    nome,
    mensagem,
):

    intencao = detectar_intencao(
        mensagem
    )

    score = calcular_score(
        mensagem
    )

    temperatura = definir_temperatura(
        score
    )

    resumo = gerar_resumo(
        nome,
        mensagem,
        intencao,
        temperatura,
    )

    return {
        "intencao": intencao,
        "score": score,
        "temperatura": temperatura,
        "resumo": resumo,
    }
