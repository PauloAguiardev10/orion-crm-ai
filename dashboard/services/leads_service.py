import pandas as pd
from datetime import datetime

from database.db import conectar

from services.intencao_service import (
    detectar_intencao,
    calcular_score,
    definir_temperatura,
    gerar_resumo,
)


STATUS_LISTA = [
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
                leads.responsavel,
                leads.valor_negocio,
                leads.mensalidade,
                leads.motivo_perda,
                leads.observacao_comercial,
                leads.criado_em

            FROM leads

            LEFT JOIN clientes
                ON clientes.id = leads.cliente_id

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

        agora = datetime.now()

        leads["horas_desde_entrada"] = leads["criado_em"].apply(
            lambda data: round(
                (
                    agora - data.to_pydatetime()
                ).total_seconds()
                / 3600,
                1,
            )
            if pd.notna(data)
            else 0
        )

    return leads


def atualizar_lead(
    lead_id,
    novo_status,
    responsavel,
    valor_negocio=0,
    mensalidade=0,
    motivo_perda="",
    observacao_comercial="",
):

    garantir_colunas_leads()

    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            UPDATE leads
            SET
                status = %s,
                responsavel = %s,
                valor_negocio = %s,
                mensalidade = %s,
                motivo_perda = %s,
                observacao_comercial = %s,
                atualizado_em = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (
                novo_status,
                responsavel,
                float(valor_negocio or 0),
                float(mensalidade or 0),
                motivo_perda,
                observacao_comercial,
                int(lead_id),
            ),
        )

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
                    WHERE id = %s
                )
                """,
                (int(lead_id),),
            )

        conn.commit()

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