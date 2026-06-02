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
    "Não fechado"
]


def garantir_colunas_leads():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER DEFAULT 1,
            nome TEXT,
            empresa TEXT,
            telefone TEXT,
            canal TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER DEFAULT 1,
            nome TEXT,
            telefone TEXT,
            canal TEXT,
            historico TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER DEFAULT 1,
            cliente_id INTEGER,
            produto TEXT,
            temperatura TEXT,
            prioridade TEXT,
            score INTEGER DEFAULT 0,
            origem TEXT,
            observacoes TEXT,
            resumo_vendedor TEXT,
            status TEXT DEFAULT 'Aguardando atendimento',
            responsavel TEXT DEFAULT 'Não atribuído',
            valor_negocio REAL DEFAULT 0,
            mensalidade REAL DEFAULT 0,
            motivo_perda TEXT,
            observacao_comercial TEXT,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("PRAGMA table_info(leads)")
    colunas_leads = [col[1] for col in cursor.fetchall()]

    colunas_obrigatorias_leads = {
        "empresa_id": "INTEGER DEFAULT 1",
        "cliente_id": "INTEGER",
        "produto": "TEXT",
        "temperatura": "TEXT",
        "prioridade": "TEXT",
        "score": "INTEGER DEFAULT 0",
        "origem": "TEXT",
        "observacoes": "TEXT",
        "resumo_vendedor": "TEXT",
        "status": "TEXT DEFAULT 'Aguardando atendimento'",
        "responsavel": "TEXT DEFAULT 'Não atribuído'",
        "valor_negocio": "REAL DEFAULT 0",
        "mensalidade": "REAL DEFAULT 0",
        "motivo_perda": "TEXT",
        "observacao_comercial": "TEXT",
        "criado_em": "TEXT DEFAULT CURRENT_TIMESTAMP",
    }

    for coluna, tipo in colunas_obrigatorias_leads.items():
        if coluna not in colunas_leads:
            cursor.execute(f"""
                ALTER TABLE leads
                ADD COLUMN {coluna} {tipo}
            """)

    cursor.execute("PRAGMA table_info(clientes)")
    colunas_clientes = [col[1] for col in cursor.fetchall()]

    colunas_obrigatorias_clientes = {
        "empresa_id": "INTEGER DEFAULT 1",
        "nome": "TEXT",
        "empresa": "TEXT",
        "telefone": "TEXT",
        "canal": "TEXT",
    }

    for coluna, tipo in colunas_obrigatorias_clientes.items():
        if coluna not in colunas_clientes:
            cursor.execute(f"""
                ALTER TABLE clientes
                ADD COLUMN {coluna} {tipo}
            """)

    cursor.execute("PRAGMA table_info(conversas)")
    colunas_conversas = [col[1] for col in cursor.fetchall()]

    colunas_obrigatorias_conversas = {
        "empresa_id": "INTEGER DEFAULT 1",
        "nome": "TEXT",
        "telefone": "TEXT",
        "canal": "TEXT",
        "historico": "TEXT",
    }

    for coluna, tipo in colunas_obrigatorias_conversas.items():
        if coluna not in colunas_conversas:
            cursor.execute(f"""
                ALTER TABLE conversas
                ADD COLUMN {coluna} {tipo}
            """)

    conn.commit()
    conn.close()


def carregar_leads(empresa_id=1):

    garantir_colunas_leads()

    conn = conectar()

    leads = pd.read_sql_query("""
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

        WHERE leads.empresa_id = ?

        ORDER BY leads.id DESC
    """, conn, params=(empresa_id,))

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

        leads["canal"] = leads["canal"].replace({
            "Facebook": "Facebook Messenger",
            "Messenger": "Facebook Messenger",
            "Instagram": "Instagram Direct"
        })

        leads["valor_negocio"] = leads["valor_negocio"].fillna(0)
        leads["mensalidade"] = leads["mensalidade"].fillna(0)
        leads["motivo_perda"] = leads["motivo_perda"].fillna("")
        leads["observacao_comercial"] = leads["observacao_comercial"].fillna("")

        leads["criado_em"] = pd.to_datetime(
            leads["criado_em"],
            errors="coerce"
        )

        agora = datetime.now()

        leads["horas_desde_entrada"] = leads["criado_em"].apply(
            lambda data: round(
                (
                    agora - data.to_pydatetime()
                ).total_seconds() / 3600,
                1
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
    observacao_comercial=""
):

    garantir_colunas_leads()

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE leads
        SET status = ?,
            responsavel = ?,
            valor_negocio = ?,
            mensalidade = ?,
            motivo_perda = ?,
            observacao_comercial = ?
        WHERE id = ?
    """, (
        novo_status,
        responsavel,
        float(valor_negocio or 0),
        float(mensalidade or 0),
        motivo_perda,
        observacao_comercial,
        int(lead_id)
    ))

    conn.commit()
    conn.close()


def analisar_lead_automaticamente(
    nome,
    mensagem
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
        temperatura
    )

    return {
        "intencao": intencao,
        "score": score,
        "temperatura": temperatura,
        "resumo": resumo,
    }