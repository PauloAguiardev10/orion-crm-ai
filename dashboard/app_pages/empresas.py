
import streamlit as st
import pandas as pd

from datetime import datetime, timedelta

from database.db import conectar

from services.usuarios_service import criar_admin_empresa


PLANOS_VALORES = {
    "Lite": 350.0,
    "Pro": 700.0,
    "Premium": 1000.0,
}


SERVICOS_ADICIONAIS = {
    "Produtos": 150.0,
    "Pedidos": 150.0,
    "Instagram": 200.0,
    "Facebook": 150.0,
    "Relatórios": 250.0,
    "IA Vendas": 350.0,
    "Agente de Vendas": 500.0,
    "PIX Automático": 200.0,
    "Link Pagamento": 200.0,
}


SERVICOS_PREMIUM = [
    "IA Vendas",
    "Agente de Vendas",
    "PIX Automático",
    "Link Pagamento",
    "Relatórios",
]


def limpar_formulario_nova_empresa():
    st.session_state["reset_nova_empresa"] = (
        st.session_state.get("reset_nova_empresa", 0) + 1
    )


def garantir_colunas_empresas():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS empresas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            plano TEXT DEFAULT 'Lite',
            status TEXT DEFAULT 'ativa',
            valor_mensal REAL DEFAULT 350,
            logo_path TEXT,
            parceiro_nome TEXT DEFAULT 'Forway',
            data_adesao TEXT,
            data_vencimento TEXT,
            status_financeiro TEXT DEFAULT 'em_dia',
            bloqueio_automatico INTEGER DEFAULT 1,
            servicos TEXT DEFAULT '',
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("PRAGMA table_info(empresas)")
    colunas = [col[1] for col in cursor.fetchall()]

    novas_colunas = {
        "logo_path": "ALTER TABLE empresas ADD COLUMN logo_path TEXT",
        "parceiro_nome": "ALTER TABLE empresas ADD COLUMN parceiro_nome TEXT DEFAULT 'Forway'",
        "data_adesao": "ALTER TABLE empresas ADD COLUMN data_adesao TEXT",
        "data_vencimento": "ALTER TABLE empresas ADD COLUMN data_vencimento TEXT",
        "status_financeiro": "ALTER TABLE empresas ADD COLUMN status_financeiro TEXT DEFAULT 'em_dia'",
        "bloqueio_automatico": "ALTER TABLE empresas ADD COLUMN bloqueio_automatico INTEGER DEFAULT 1",
        "valor_mensal": "ALTER TABLE empresas ADD COLUMN valor_mensal REAL DEFAULT 350",
        "servicos": "ALTER TABLE empresas ADD COLUMN servicos TEXT DEFAULT ''",
    }

    for coluna, comando in novas_colunas.items():
        if coluna not in colunas:
            cursor.execute(comando)

    conn.commit()
    conn.close()


def listar_empresas():
    garantir_colunas_empresas()

    nivel = st.session_state.get("nivel")
    empresa_logada = st.session_state.get("empresa")

    conn = conectar()

    if nivel == "parceiro_admin":
        empresas = pd.read_sql_query("""
            SELECT *
            FROM empresas
            WHERE parceiro_nome = ?
            AND nome != 'Orion Systems'
            ORDER BY id DESC
        """, conn, params=(empresa_logada,))
    else:
        empresas = pd.read_sql_query("""
            SELECT *
            FROM empresas
            ORDER BY id DESC
        """, conn)

    conn.close()
    return empresas


def calcular_valor_mensal(plano, servicos):
    valor = PLANOS_VALORES.get(plano, 350.0)

    for servico in servicos:
        valor += SERVICOS_ADICIONAIS.get(servico, 0.0)

    return valor


def criar_empresa(
    nome,
    plano,
    status,
    logo_path,
    parceiro_nome,
    data_adesao,
    data_vencimento,
    servicos,
):
    garantir_colunas_empresas()

    conn = conectar()
    cursor = conn.cursor()

    valor_mensal = calcular_valor_mensal(plano, servicos)

    cursor.execute("""
        INSERT INTO empresas (
            nome,
            plano,
            status,
            valor_mensal,
            logo_path,
            parceiro_nome,
            data_adesao,
            data_vencimento,
            status_financeiro,
            bloqueio_automatico,
            servicos
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        nome.strip(),
        plano,
        status,
        valor_mensal,
        logo_path.strip(),
        parceiro_nome,
        data_adesao,
        data_vencimento,
        "em_dia",
        1,
        ",".join(servicos),
    ))

    conn.commit()
    empresa_id = cursor.lastrowid
    conn.close()

    return empresa_id


def atualizar_empresa(
    empresa_id,
    plano,
    status,
    valor_mensal,
    logo_path,
    parceiro_nome,
    data_vencimento,
    status_financeiro,
    bloqueio_automatico,
    servicos,
):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE empresas
        SET plano = ?,
            status = ?,
            valor_mensal = ?,
            logo_path = ?,
            parceiro_nome = ?,
            data_vencimento = ?,
            status_financeiro = ?,
            bloqueio_automatico = ?,
            servicos = ?
        WHERE id = ?
    """, (
        plano,
        status,
        valor_mensal,
        logo_path.strip(),
        parceiro_nome,
        data_vencimento,
        status_financeiro,
        int(bloqueio_automatico),
        ",".join(servicos),
        int(empresa_id),
    ))

    conn.commit()
    conn.close()


def excluir_empresa(empresa_id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM usuarios
        WHERE empresa_id = ?
    """, (int(empresa_id),))

    cursor.execute("""
        DELETE FROM empresas
        WHERE id = ?
    """, (int(empresa_id),))

    conn.commit()
    conn.close()


def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def obter_servicos_por_plano(plano):
    if plano == "Lite":
        return list(SERVICOS_ADICIONAIS.keys())

    if plano == "Pro":
        return SERVICOS_PREMIUM

    return []


def formatar_opcao_servico(servico):
    valor = SERVICOS_ADICIONAIS.get(servico, 0.0)
    return f"{servico} — {formatar_moeda(valor)}/mês"


def converter_labels_para_servicos(labels):
    servicos = []

    for label in labels:
        servico = label.split(" — ")[0].strip()

        if servico in SERVICOS_ADICIONAIS:
            servicos.append(servico)

    return servicos


def render_empresas():
    nivel = st.session_state.get("nivel")
    empresa_logada = st.session_state.get("empresa")
    reset_key = st.session_state.get("reset_nova_empresa", 0)

    st.title("🏢 Empresas")

    if nivel == "parceiro_admin":
        st.info(f"Painel parceiro: {empresa_logada}. Você visualiza apenas clientes vinculados à sua operação.")

    empresas = listar_empresas()

    st.markdown("## 📋 Empresas cadastradas")

    if empresas.empty:
        st.info("Nenhuma empresa cadastrada.")
    else:
        st.dataframe(
            empresas,
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("---")

    st.markdown("## ➕ Nova empresa")

    c1, c2 = st.columns(2)

    with c1:
        nome = st.text_input(
            "Nome empresa",
            key=f"nova_empresa_nome_{reset_key}",
        )

        usuario_admin = st.text_input(
            "Usuário admin",
            key=f"nova_empresa_usuario_{reset_key}",
        )

        logo_path = st.text_input(
            "Logo",
            value="assets/logo_forway.png",
            key=f"nova_empresa_logo_{reset_key}",
        )

        if nivel == "parceiro_admin":
            parceiro_nome = empresa_logada
            st.text_input(
                "Parceiro responsável",
                value=parceiro_nome,
                disabled=True,
                key=f"nova_empresa_parceiro_{reset_key}",
            )
        else:
            parceiro_nome = st.selectbox(
                "Parceiro responsável",
                ["Forway", "Orion"],
                key=f"nova_empresa_parceiro_select_{reset_key}",
            )

    with c2:
        senha_admin = st.text_input(
            "Senha admin",
            type="password",
            key=f"nova_empresa_senha_{reset_key}",
        )

        plano = st.selectbox(
            "Plano",
            ["Lite", "Pro", "Premium"],
            key=f"nova_empresa_plano_{reset_key}",
        )

        status = st.selectbox(
            "Status",
            ["ativa", "suspensa"],
            key=f"nova_empresa_status_{reset_key}",
        )

    servicos = []
    servicos_disponiveis = obter_servicos_por_plano(plano)

    if plano == "Premium":
        st.success("Plano Premium com todos os recursos liberados.")
    else:
        opcoes_servicos = [
            formatar_opcao_servico(servico)
            for servico in servicos_disponiveis
        ]

        servicos_labels = st.multiselect(
            "Serviços adicionais",
            opcoes_servicos,
            key=f"servicos_nova_empresa_{reset_key}",
        )

        servicos = converter_labels_para_servicos(servicos_labels)

    valor_total_novo = calcular_valor_mensal(plano, servicos)

    st.metric(
        "Mensalidade calculada",
        formatar_moeda(valor_total_novo),
    )

    data_adesao = datetime.now().strftime("%Y-%m-%d")
    data_vencimento = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

    st.info(f"Adesão: {data_adesao} | Vencimento: {data_vencimento}")

    if st.button("Cadastrar empresa", use_container_width=True):
        if not nome.strip() or not usuario_admin.strip() or not senha_admin.strip():
            st.warning("Preencha todos os campos obrigatórios.")
        else:
            try:
                empresa_id = criar_empresa(
                    nome,
                    plano,
                    status,
                    logo_path,
                    parceiro_nome,
                    data_adesao,
                    data_vencimento,
                    servicos,
                )

                criar_admin_empresa(
                    empresa_id,
                    nome,
                    usuario_admin,
                    senha_admin,
                )

                st.success("Empresa cadastrada com admin criado.")

                limpar_formulario_nova_empresa()

                st.rerun()

            except Exception as erro:
                st.error(f"Erro ao cadastrar empresa: {erro}")

    st.markdown("---")

    st.markdown("## ⚙️ Gerenciar empresa")

    empresas = listar_empresas()

    if empresas.empty:
        st.info("Nenhuma empresa disponível para gerenciamento.")
        return

    opcoes = {
        f"{row['id']} - {row['nome']}": row["id"]
        for _, row in empresas.iterrows()
    }

    selecionada = st.selectbox(
        "Empresa",
        list(opcoes.keys()),
        key="empresa_gerenciar",
    )

    empresa_id = int(opcoes[selecionada])

    empresa = empresas[
        empresas["id"] == empresa_id
    ].iloc[0]

    novo_plano = st.selectbox(
        "Plano atualizado",
        ["Lite", "Pro", "Premium"],
        index=["Lite", "Pro", "Premium"].index(empresa["plano"])
        if empresa["plano"] in ["Lite", "Pro", "Premium"]
        else 0,
    )

    novo_status = st.selectbox(
        "Status atualizado",
        ["ativa", "suspensa"],
        index=["ativa", "suspensa"].index(empresa["status"])
        if empresa["status"] in ["ativa", "suspensa"]
        else 0,
    )

    status_financeiro = st.selectbox(
        "Status financeiro",
        ["em_dia", "vencido", "inadimplente"],
        index=["em_dia", "vencido", "inadimplente"].index(empresa["status_financeiro"])
        if empresa["status_financeiro"] in ["em_dia", "vencido", "inadimplente"]
        else 0,
    )

    novo_logo_path = st.text_input(
        "Logo atualizada",
        value=empresa["logo_path"] if empresa["logo_path"] else "",
    )

    if nivel == "parceiro_admin":
        novo_parceiro_nome = empresa_logada
        st.text_input("Parceiro", value=novo_parceiro_nome, disabled=True)
    else:
        novo_parceiro_nome = st.selectbox(
            "Parceiro",
            ["Forway", "Orion"],
            index=["Forway", "Orion"].index(empresa["parceiro_nome"])
            if empresa["parceiro_nome"] in ["Forway", "Orion"]
            else 0,
        )

    data_vencimento = st.text_input(
        "Vencimento",
        value=empresa["data_vencimento"] if empresa["data_vencimento"] else "",
    )

    bloqueio_automatico = st.checkbox(
        "Bloquear automaticamente",
        value=bool(empresa["bloqueio_automatico"]),
    )

    servicos_atuais = []

    if "servicos" in empresa and empresa["servicos"]:
        servicos_atuais = [
            item.strip()
            for item in str(empresa["servicos"]).split(",")
            if item.strip()
        ]

    servicos_disponiveis_edicao = obter_servicos_por_plano(novo_plano)

    if novo_plano == "Premium":
        servicos_ativos = []
        st.success("Plano Premium com todos os recursos liberados.")
    else:
        opcoes_servicos_edicao = [
            formatar_opcao_servico(servico)
            for servico in servicos_disponiveis_edicao
        ]

        default_servicos = [
            formatar_opcao_servico(servico)
            for servico in servicos_atuais
            if servico in servicos_disponiveis_edicao
        ]

        servicos_labels_ativos = st.multiselect(
            "Serviços adicionais ativos",
            opcoes_servicos_edicao,
            default=default_servicos,
            key="servicos_editar_empresa",
        )

        servicos_ativos = converter_labels_para_servicos(servicos_labels_ativos)

    valor_total = calcular_valor_mensal(
        novo_plano,
        servicos_ativos,
    )

    st.metric(
        "Mensalidade",
        formatar_moeda(valor_total),
    )

    b1, b2 = st.columns(2)

    with b1:
        if st.button("Salvar alterações", use_container_width=True):
            atualizar_empresa(
                empresa_id,
                novo_plano,
                novo_status,
                valor_total,
                novo_logo_path,
                novo_parceiro_nome,
                data_vencimento,
                status_financeiro,
                bloqueio_automatico,
                servicos_ativos,
            )

            st.success("Empresa atualizada.")
            st.rerun()

    with b2:
        if nivel == "orion_admin":
            if st.button("Excluir empresa", use_container_width=True):
                if empresa["nome"] == "Orion Systems":
                    st.error("Orion Systems não pode ser excluída.")
                else:
                    excluir_empresa(empresa_id)
                    st.warning("Empresa excluída.")
                    st.rerun()
        else:
            st.caption("Exclusão de empresa disponível apenas para Orion Admin.")

