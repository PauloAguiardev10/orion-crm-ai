from pathlib import Path
import re
import unicodedata
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from utils.tempo import agora_empresa

from database.db import conectar
from services.usuarios_service import criar_admin_empresa, hash_senha

from services.empresa_atendimento_service import (
    carregar_empresa_atendimento_config,
    salvar_empresa_atendimento_config,
)


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


def salvar_logo_empresa(arquivo_logo, empresa_id):
    """
    Salva o logotipo da empresa no dashboard.
    """

    if arquivo_logo is None:
        return None

    extensao = Path(
        arquivo_logo.name
    ).suffix.lower()

    permitidas = {
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
    }

    if extensao not in permitidas:
        raise ValueError(
            "Formato de imagem nao permitido."
        )

    pasta_dashboard = (
        Path(__file__).resolve().parent.parent
    )

    pasta_logos = (
        pasta_dashboard
        / "assets"
        / "logos"
    )

    pasta_logos.mkdir(
        parents=True,
        exist_ok=True,
    )

    nome_arquivo = (
        f"empresa_{int(empresa_id)}{extensao}"
    )

    destino = (
        pasta_logos
        / nome_arquivo
    )

    destino.write_bytes(
        arquivo_logo.getvalue()
    )

    return (
        f"assets/logos/{nome_arquivo}"
    )


def limpar_formulario_nova_empresa():
    st.session_state["reset_nova_empresa"] = (
        st.session_state.get("reset_nova_empresa", 0) + 1
    )


def garantir_colunas_empresas():
    """
    A estrutura PostgreSQL já é criada pelos scripts de migração.
    A função é mantida por compatibilidade com chamadas antigas.
    """
    return


def gerar_slug(texto):
    texto_normalizado = unicodedata.normalize("NFKD", texto)
    texto_sem_acentos = "".join(
        caractere
        for caractere in texto_normalizado
        if not unicodedata.combining(caractere)
    )
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", texto_sem_acentos)
    return slug.strip("-").lower()


def gerar_slug_unico(cursor, nome):
    slug_base = gerar_slug(nome) or "empresa"
    slug = slug_base
    contador = 2

    while True:
        cursor.execute(
            """
            SELECT 1
            FROM empresas
            WHERE slug = %s
            LIMIT 1
            """,
            (slug,),
        )

        if not cursor.fetchone():
            return slug

        slug = f"{slug_base}-{contador}"
        contador += 1


def obter_empresa_logada():
    empresa_id = st.session_state.get("empresa_id")

    if not empresa_id:
        return None

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


def listar_parceiros():
    conn = conectar()

    try:
        return pd.read_sql_query(
            """
            SELECT
                id,
                nome
            FROM empresas
            WHERE tipo = 'parceiro'
              AND status = 'ativa'
            ORDER BY nome
            """,
            conn,
        )

    finally:
        conn.close()


def listar_empresas():
    nivel = st.session_state.get("nivel")
    empresa_id_logada = st.session_state.get(
        "empresa_login_id",
        st.session_state.get("empresa_id"),
    )

    conn = conectar()

    try:
        if nivel == "parceiro_admin":
            if not empresa_id_logada:
                return pd.DataFrame()

            return pd.read_sql_query(
                """
                SELECT
                    empresa.*
                FROM empresas AS empresa
                WHERE empresa.tipo = 'cliente'
                  AND empresa.parceiro_id = %s
                ORDER BY empresa.id DESC
                """,
                conn,
                params=(int(empresa_id_logada),),
            )

        return pd.read_sql_query(
            """
            SELECT
                empresa.*,
                parceiro.nome AS parceiro_vinculado
            FROM empresas AS empresa
            LEFT JOIN empresas AS parceiro
                ON parceiro.id = empresa.parceiro_id
            ORDER BY empresa.id DESC
            """,
            conn,
        )

    finally:
        conn.close()


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
    parceiro_id,
    parceiro_nome,
    data_adesao,
    data_vencimento,
    servicos,
):
    conn = conectar()

    try:
        valor_mensal = calcular_valor_mensal(
            plano,
            servicos,
        )

        with conn.cursor() as cursor:
            slug = gerar_slug_unico(cursor, nome.strip())

            cursor.execute(
                """
                INSERT INTO empresas (
                    nome,
                    slug,
                    tipo,
                    plano,
                    status,
                    valor_mensal,
                    logo_path,
                    parceiro_id,
                    parceiro_nome,
                    data_adesao,
                    data_vencimento,
                    status_financeiro,
                    bloqueio_automatico,
                    servicos
                )
                VALUES (
                    %s,
                    %s,
                    'cliente',
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    'em_dia',
                    TRUE,
                    %s
                )
                RETURNING id
                """,
                (
                    nome.strip(),
                    slug,
                    plano,
                    status,
                    valor_mensal,
                    logo_path.strip(),
                    int(parceiro_id),
                    parceiro_nome,
                    data_adesao,
                    data_vencimento,
                    ",".join(servicos),
                ),
            )

            empresa_id = int(cursor.fetchone()[0])

        conn.commit()
        return empresa_id

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def atualizar_empresa(
    empresa_id,
    plano,
    status,
    valor_mensal,
    logo_path,
    parceiro_id,
    parceiro_nome,
    data_vencimento,
    status_financeiro,
    bloqueio_automatico,
    servicos,
):
    conn = conectar()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE empresas
                SET
                    plano = %s,
                    status = %s,
                    valor_mensal = %s,
                    logo_path = %s,
                    parceiro_id = %s,
                    parceiro_nome = %s,
                    data_vencimento = %s,
                    status_financeiro = %s,
                    bloqueio_automatico = %s,
                    servicos = %s
                WHERE id = %s
                  AND tipo IN ('parceiro', 'cliente')
                """,
                (
                    plano,
                    status,
                    valor_mensal,
                    logo_path.strip(),
                    int(parceiro_id),
                    parceiro_nome,
                    data_vencimento,
                    status_financeiro,
                    bool(bloqueio_automatico),
                    ",".join(servicos),
                    int(empresa_id),
                ),
            )

            if cursor.rowcount == 0:
                raise RuntimeError(
                    "A empresa cliente não foi encontrada ou não pode ser alterada."
                )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def excluir_empresa(empresa_id):
    conn = conectar()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT tipo
                FROM empresas
                WHERE id = %s
                """,
                (int(empresa_id),),
            )

            empresa = cursor.fetchone()

            if not empresa:
                raise RuntimeError("Empresa não encontrada.")

            if empresa[0] != "cliente":
                raise RuntimeError(
                    "Somente empresas clientes podem ser excluídas por esta tela."
                )

            cursor.execute(
                """
                DELETE FROM usuarios
                WHERE empresa_id = %s
                """,
                (int(empresa_id),),
            )

            cursor.execute(
                """
                DELETE FROM empresas
                WHERE id = %s
                  AND tipo = 'cliente'
                """,
                (int(empresa_id),),
            )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def formatar_moeda(valor):
    return (
        f"R$ {valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


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



def listar_usuarios_empresa(empresa_id):
    """
    Lista usuarios ativos vinculados a uma empresa.
    """

    conn = conectar()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    usuario,
                    nivel,
                    status
                FROM usuarios
                WHERE empresa_id = %s
                  AND status = 'ativo'
                ORDER BY usuario
                """,
                (
                    int(empresa_id),
                ),
            )

            return cursor.fetchall()

    finally:
        conn.close()


def redefinir_senha_usuario_empresa(
    usuario_id,
    empresa_id,
    nova_senha,
):
    """
    Redefine a senha de um usuario especifico,
    exigindo correspondencia com a empresa.
    """

    nova_senha = str(
        nova_senha
    ).strip()

    if len(nova_senha) < 8:
        raise ValueError(
            "A nova senha deve possuir "
            "pelo menos 8 caracteres."
        )

    senha_hash = hash_senha(
        nova_senha
    )

    conn = conectar()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE usuarios
                SET
                    senha = %s,
                    senha_hash = %s,
                    atualizado_em = CURRENT_TIMESTAMP
                WHERE id = %s
                  AND empresa_id = %s
                  AND status = 'ativo'
                """,
                (
                    senha_hash,
                    senha_hash,
                    int(usuario_id),
                    int(empresa_id),
                ),
            )

            alterado = (
                cursor.rowcount == 1
            )

        if not alterado:
            raise RuntimeError(
                "Usuario nao encontrado "
                "na empresa selecionada."
            )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def render_empresas():
    nivel = st.session_state.get("nivel")
    empresa_logada = st.session_state.get("empresa")
    empresa_id_logada = st.session_state.get(
        "empresa_login_id",
        st.session_state.get("empresa_id"),
    )
    reset_key = st.session_state.get("reset_nova_empresa", 0)

    st.title("🏢 Empresas")

    st.markdown(
        """
        <style>
        /* ORION UI — EMPRESAS */
        [data-testid="stDataFrame"] {
            border: 1px solid rgba(34,211,238,.28);
            border-radius: 18px;
            overflow: hidden;
            box-shadow: 0 0 28px rgba(34,211,238,.08);
        }

        [data-testid="stMetric"] {
            background:
                radial-gradient(circle at 12% 0%, rgba(34,211,238,.12), transparent 42%),
                linear-gradient(145deg, rgba(15,23,42,.97), rgba(3,8,20,.96));
            border: 1px solid rgba(34,211,238,.32);
            border-radius: 18px;
            padding: 16px 18px;
            box-shadow: 0 0 25px rgba(34,211,238,.09);
        }

        [data-testid="stTextInput"] input,
        [data-testid="stSelectbox"] > div > div,
        [data-testid="stMultiSelect"] > div > div {
            border-radius: 12px !important;
        }

        [data-testid="stTextInput"] input:focus,
        [data-testid="stSelectbox"] > div > div:focus-within,
        [data-testid="stMultiSelect"] > div > div:focus-within {
            border-color: rgba(34,211,238,.70) !important;
            box-shadow: 0 0 0 1px rgba(34,211,238,.16),
                        0 0 18px rgba(34,211,238,.10) !important;
        }

        .orion-section-card {
            position: relative;
            overflow: hidden;
            background:
                radial-gradient(circle at 0% 0%, rgba(34,211,238,.09), transparent 38%),
                linear-gradient(145deg, rgba(15,23,42,.96), rgba(3,8,20,.95));
            border: 1px solid rgba(34,211,238,.24);
            border-radius: 18px;
            padding: 15px 17px;
            margin: 8px 0 16px 0;
            box-shadow: 0 0 26px rgba(34,211,238,.065);
        }

        .orion-section-card::before {
            content: "";
            position: absolute;
            left: 0;
            top: 12px;
            bottom: 12px;
            width: 3px;
            border-radius: 999px;
            background: #22D3EE;
            box-shadow: 0 0 12px rgba(34,211,238,.8);
        }

        .orion-section-title {
            color: #FFFFFF;
            font-size: 15px;
            font-weight: 800;
            margin-left: 5px;
        }

        .orion-section-subtitle {
            color: #94A3B8;
            font-size: 13px;
            margin: 4px 0 0 5px;
        }

        .orion-empty-card {
            background:
                radial-gradient(circle at 50% 0%, rgba(99,102,241,.09), transparent 45%),
                linear-gradient(145deg, rgba(15,23,42,.95), rgba(3,8,20,.94));
            border: 1px dashed rgba(99,102,241,.38);
            border-radius: 18px;
            padding: 24px 18px;
            margin: 8px 0 14px 0;
            text-align: center;
            color: #CBD5E1;
            box-shadow: 0 0 24px rgba(99,102,241,.06);
        }

        .orion-empty-card strong {
            color: #FFFFFF;
        }

        div[data-testid="stButton"] > button {
            border-radius: 12px;
            transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
        }

        div[data-testid="stButton"] > button:hover {
            transform: translateY(-1px);
            border-color: rgba(34,211,238,.62);
            box-shadow: 0 0 18px rgba(34,211,238,.12);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if nivel == "parceiro_admin":
        st.info(
            f"Painel parceiro: {empresa_logada}. "
            "Você visualiza apenas os clientes vinculados à sua operação."
        )

    parceiros = listar_parceiros()
    empresas = listar_empresas()

    st.markdown("## 📋 Empresas cadastradas")
    st.markdown(
        """
        <div class="orion-section-card">
            <div class="orion-section-title">Carteira de empresas</div>
            <div class="orion-section-subtitle">
                Visualize os clientes cadastrados e vinculados à operação.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if empresas.empty:
        st.markdown(
            """
            <div class="orion-empty-card">
                <strong>Nenhuma empresa cadastrada ainda.</strong><br>
                A estrutura permanece disponível e o primeiro cadastro pode ser feito abaixo.
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.dataframe(
            empresas,
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("---")
    st.markdown("## ➕ Nova empresa")
    st.markdown(
        """
        <div class="orion-section-card">
            <div class="orion-section-title">Cadastro de novo cliente</div>
            <div class="orion-section-subtitle">
                Configure acesso, plano, parceiro responsável e serviços contratados.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if nivel == "orion_admin" and parceiros.empty:
        st.warning(
            "Cadastre ao menos uma empresa do tipo parceiro antes de criar clientes."
        )
        return

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

        nova_empresa_logo = st.file_uploader(
            "Logotipo da empresa",
            type=[
                "png",
                "jpg",
                "jpeg",
                "webp",
            ],
            key=f"nova_empresa_logo_{reset_key}",
            help=(
                "Envie o logotipo que sera exibido "
                "na identidade visual do CRM desta empresa."
            ),
        )

        if nivel == "parceiro_admin":
            parceiro_id = int(empresa_id_logada)
            parceiro_nome = empresa_logada

            st.text_input(
                "Parceiro responsável",
                value=parceiro_nome,
                disabled=True,
                key=f"nova_empresa_parceiro_{reset_key}",
            )
        else:
            opcoes_parceiros = {
                row["nome"]: int(row["id"])
                for _, row in parceiros.iterrows()
            }

            parceiro_nome = st.selectbox(
                "Parceiro responsável",
                list(opcoes_parceiros.keys()),
                key=f"nova_empresa_parceiro_select_{reset_key}",
            )

            parceiro_id = opcoes_parceiros[parceiro_nome]

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

    agora_local = agora_empresa()

    data_adesao = agora_local.strftime(
        "%Y-%m-%d"
    )

    data_vencimento_nova = (
        agora_local + timedelta(days=30)
    ).strftime("%Y-%m-%d")

    st.info(
        f"Adesão: {data_adesao} | "
        f"Vencimento: {data_vencimento_nova}"
    )

    if st.button("Cadastrar empresa", use_container_width=True):
        if (
            not nome.strip()
            or not usuario_admin.strip()
            or not senha_admin.strip()
        ):
            st.warning("Preencha todos os campos obrigatórios.")

        else:
            try:
                empresa_id = criar_empresa(
                    nome,
                    plano,
                    status,
                    "",
                    parceiro_id,
                    parceiro_nome,
                    data_adesao,
                    data_vencimento_nova,
                    servicos,
                )

                if nova_empresa_logo is not None:
                    novo_logo_path = salvar_logo_empresa(
                        nova_empresa_logo,
                        empresa_id,
                    )

                    conn_logo = conectar()

                    try:
                        with conn_logo.cursor() as cursor:
                            cursor.execute(
                                """
                                UPDATE empresas
                                SET logo_path = %s
                                WHERE id = %s
                                  AND tipo = 'cliente'
                                """,
                                (
                                    novo_logo_path,
                                    int(empresa_id),
                                ),
                            )

                        conn_logo.commit()

                    except Exception:
                        conn_logo.rollback()
                        raise

                    finally:
                        conn_logo.close()

                criar_admin_empresa(
                    empresa_id,
                    nome,
                    usuario_admin,
                    senha_admin,
                )

                st.success(
                    f"Empresa cadastrada e vinculada a {parceiro_nome}."
                )

                limpar_formulario_nova_empresa()
                st.rerun()

            except Exception as erro:
                st.error(f"Erro ao cadastrar empresa: {erro}")

    st.markdown("---")
    st.markdown("## ⚙️ Gerenciar empresa")
    st.markdown(
        """
        <div class="orion-section-card">
            <div class="orion-section-title">Gestão da empresa</div>
            <div class="orion-section-subtitle">
                Atualize plano, status financeiro, serviços e vínculo operacional.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    empresas = listar_empresas()

    if nivel == "orion_admin":
        # Orion Admin pode administrar parceiros e clientes.
        empresas_gerenciaveis = empresas[
            empresas["tipo"].isin(
                ["parceiro", "cliente"]
            )
        ].copy()
    else:
        empresas_gerenciaveis = empresas.copy()

    if empresas_gerenciaveis.empty:
        st.markdown(
            """
            <div class="orion-empty-card">
                <strong>Nenhuma empresa disponível para gerenciamento.</strong><br>
                Quando um cliente for cadastrado, os controles de edição aparecerão nesta área.
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    opcoes = {
        f"{row['id']} - {row['nome']}": int(row["id"])
        for _, row in empresas_gerenciaveis.iterrows()
    }

    selecionada = st.selectbox(
        "Empresa",
        list(opcoes.keys()),
        key="empresa_gerenciar",
    )

    empresa_id = opcoes[selecionada]

    empresa = empresas_gerenciaveis[
        empresas_gerenciaveis["id"] == empresa_id
    ].iloc[0]

    novo_plano = st.selectbox(
        "Plano atualizado",
        ["Lite", "Pro", "Premium"],
        index=(
            ["Lite", "Pro", "Premium"].index(empresa["plano"])
            if empresa["plano"] in ["Lite", "Pro", "Premium"]
            else 0
        ),
    )

    novo_status = st.selectbox(
        "Status atualizado",
        ["ativa", "suspensa"],
        index=(
            ["ativa", "suspensa"].index(empresa["status"])
            if empresa["status"] in ["ativa", "suspensa"]
            else 0
        ),
    )

    status_financeiro = st.selectbox(
        "Status financeiro",
        ["em_dia", "vencido", "inadimplente"],
        index=(
            ["em_dia", "vencido", "inadimplente"].index(
                empresa["status_financeiro"]
            )
            if empresa["status_financeiro"]
            in ["em_dia", "vencido", "inadimplente"]
            else 0
        ),
    )

    logo_atual_path = (
        str(empresa["logo_path"]).strip()
        if empresa.get("logo_path")
        else ""
    )

    st.markdown("#### Identidade visual")

    st.caption(
        "Envie o logotipo da empresa. "
        "Depois de salvar, ele sera usado "
        "na identificacao visual do CRM."
    )

    nova_logo_arquivo = st.file_uploader(
        "Logotipo da empresa",
        type=[
            "png",
            "jpg",
            "jpeg",
            "webp",
        ],
        key=f"logo_empresa_upload_{empresa_id}",
    )

    novo_logo_path = logo_atual_path

    if nivel == "parceiro_admin":
        novo_parceiro_id = int(empresa_id_logada)
        novo_parceiro_nome = empresa_logada

        st.text_input(
            "Parceiro",
            value=novo_parceiro_nome,
            disabled=True,
        )
    else:
        opcoes_parceiros_edicao = {
            row["nome"]: int(row["id"])
            for _, row in parceiros.iterrows()
        }

        parceiro_atual = empresa.get("parceiro_vinculado")

        if (
            parceiro_atual not in opcoes_parceiros_edicao
            and empresa.get("parceiro_nome")
            in opcoes_parceiros_edicao
        ):
            parceiro_atual = empresa.get("parceiro_nome")

        nomes_parceiros = list(opcoes_parceiros_edicao.keys())
        indice_parceiro = (
            nomes_parceiros.index(parceiro_atual)
            if parceiro_atual in nomes_parceiros
            else 0
        )

        novo_parceiro_nome = st.selectbox(
            "Parceiro",
            nomes_parceiros,
            index=indice_parceiro,
        )

        novo_parceiro_id = opcoes_parceiros_edicao[
            novo_parceiro_nome
        ]

    data_vencimento_atual = (
        empresa["data_vencimento"]
        if empresa["data_vencimento"]
        else agora_empresa().date()
    )

    if isinstance(
        data_vencimento_atual,
        datetime,
    ):
        data_vencimento_atual = (
            data_vencimento_atual.date()
        )

    data_vencimento_edicao = st.date_input(
        "Vencimento",
        value=data_vencimento_atual,
        format="DD/MM/YYYY",
        key=f"data_vencimento_edicao_{empresa_id}",
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

    servicos_disponiveis_edicao = obter_servicos_por_plano(
        novo_plano
    )

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

        servicos_ativos = converter_labels_para_servicos(
            servicos_labels_ativos
        )

    valor_total = calcular_valor_mensal(
        novo_plano,
        servicos_ativos,
    )

    st.metric(
        "Mensalidade",
        formatar_moeda(valor_total),
    )

    # ========================================================
    # ACESSO ADMINISTRATIVO
    # ========================================================

    tipo_empresa_selecionada = str(
        empresa.get("tipo") or ""
    ).strip()

    parceiro_id_empresa = (
        int(empresa["parceiro_id"])
        if empresa.get("parceiro_id")
        else None
    )

    pode_redefinir_senha = False

    if nivel == "orion_admin":
        pode_redefinir_senha = (
            tipo_empresa_selecionada
            in {"parceiro", "cliente"}
        )

    elif nivel == "parceiro_admin":
        pode_redefinir_senha = (
            tipo_empresa_selecionada == "cliente"
            and parceiro_id_empresa
            == int(empresa_id_logada)
        )

    if pode_redefinir_senha:

        st.markdown("---")
        st.markdown(
            "### \U0001F510 Acesso administrativo"
        )

        st.caption(
            "Redefina a senha de acesso de um "
            "usuario desta empresa."
        )

        usuarios_empresa = (
            listar_usuarios_empresa(
                empresa_id
            )
        )

        if usuarios_empresa:

            opcoes_usuarios = {
                (
                    f"{usuario[1]} "
                    f"({usuario[2]})"
                ): int(usuario[0])
                for usuario
                in usuarios_empresa
            }

            usuario_selecionado = st.selectbox(
                "Usuario",
                list(
                    opcoes_usuarios.keys()
                ),
                key=(
                    f"usuario_redefinir_"
                    f"{empresa_id}"
                ),
            )

            nova_senha_admin = st.text_input(
                "Nova senha",
                type="password",
                key=(
                    f"nova_senha_admin_"
                    f"{empresa_id}"
                ),
            )

            confirmar_senha_admin = st.text_input(
                "Confirmar nova senha",
                type="password",
                key=(
                    f"confirmar_senha_admin_"
                    f"{empresa_id}"
                ),
            )

            if st.button(
                "Redefinir senha",
                key=(
                    f"redefinir_senha_"
                    f"{empresa_id}"
                ),
                use_container_width=True,
            ):

                if (
                    not nova_senha_admin
                    or not confirmar_senha_admin
                ):
                    st.warning(
                        "Informe e confirme "
                        "a nova senha."
                    )

                elif (
                    nova_senha_admin
                    != confirmar_senha_admin
                ):
                    st.error(
                        "As senhas informadas "
                        "nao coincidem."
                    )

                elif len(
                    nova_senha_admin
                ) < 8:
                    st.warning(
                        "A nova senha deve possuir "
                        "pelo menos 8 caracteres."
                    )

                else:
                    try:
                        redefinir_senha_usuario_empresa(
                            opcoes_usuarios[
                                usuario_selecionado
                            ],
                            empresa_id,
                            nova_senha_admin,
                        )

                        st.success(
                            "Senha redefinida "
                            "com sucesso."
                        )

                    except Exception as erro:
                        st.error(
                            "Erro ao redefinir senha: "
                            f"{erro}"
                        )

        else:
            st.info(
                "Esta empresa nao possui "
                "usuario ativo cadastrado."
            )

        st.markdown("---")

    b1, b2 = st.columns(2)

    with b1:
        if st.button("Salvar alterações", use_container_width=True):
            try:
                if nova_logo_arquivo is not None:
                    novo_logo_path = salvar_logo_empresa(
                        nova_logo_arquivo,
                        empresa_id,
                    )

                atualizar_empresa(
                    empresa_id,
                    novo_plano,
                    novo_status,
                    valor_total,
                    novo_logo_path,
                    novo_parceiro_id,
                    novo_parceiro_nome,
                    data_vencimento_edicao,
                    status_financeiro,
                    bloqueio_automatico,
                    servicos_ativos,
                )

                st.success("Empresa atualizada.")
                st.rerun()

            except Exception as erro:
                st.error(f"Erro ao atualizar empresa: {erro}")

    with b2:
        if nivel == "orion_admin":
            if st.button(
                "Excluir empresa",
                use_container_width=True,
            ):
                try:
                    excluir_empresa(empresa_id)
                    st.warning("Empresa excluída.")
                    st.rerun()

                except Exception as erro:
                    st.error(f"Erro ao excluir empresa: {erro}")
        else:
            st.caption(
                "Exclusão de empresa disponível apenas para Orion Admin."
            )

    # ============================================================
    # FICHA DE ATENDIMENTO DA SOFIA
    # ============================================================

    st.markdown("---")
    st.markdown("## 🧠 Ficha de Atendimento da Sofia")

    nome_empresa_ficha = str(
        empresa.get("nome")
        or ""
    ).strip()

    st.info(
        "Configurando atendimento da Sofia para: "
        f"{nome_empresa_ficha}"
    )

    st.markdown(
        """
        <div class="orion-section-card">
            <div class="orion-section-title">
                Informações para o atendimento inteligente
            </div>
            <div class="orion-section-subtitle">
                Cadastre as informações da empresa que serão utilizadas
                na preparação e operação do atendimento da Sofia.
                A lógica, qualificação e comportamento da inteligência
                artificial permanecem administrados pela Orion Systems.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    ficha_atendimento = (
        carregar_empresa_atendimento_config(
            empresa_id
        )
        or {}
    )

    st.markdown("### 🏢 Sobre a empresa")

    descricao_empresa = st.text_area(
        "Descrição da empresa",
        value=ficha_atendimento.get(
            "descricao_empresa"
        ) or "",
        placeholder=(
            "Explique de forma objetiva o que a empresa faz, "
            "seu posicionamento e principais diferenciais."
        ),
        key=f"ficha_descricao_{empresa_id}",
    )

    st.markdown("### 📞 Contato e presença digital")

    contato_1, contato_2 = st.columns(2)

    with contato_1:
        whatsapp_comercial = st.text_input(
            "WhatsApp para atendimento",
            value=ficha_atendimento.get(
                "whatsapp_comercial"
            ) or "",
            key=f"ficha_whatsapp_{empresa_id}",
        )

        site = st.text_input(
            "Site",
            value=ficha_atendimento.get(
                "site"
            ) or "",
            key=f"ficha_site_{empresa_id}",
        )

    with contato_2:
        email_comercial = st.text_input(
            "E-mail comercial",
            value=ficha_atendimento.get(
                "email_comercial"
            ) or "",
            key=f"ficha_email_{empresa_id}",
        )

        instagram_url = st.text_input(
            "Instagram",
            value=ficha_atendimento.get(
                "instagram_url"
            ) or "",
            key=f"ficha_instagram_{empresa_id}",
        )

        facebook_url = st.text_input(
            "Facebook",
            value=ficha_atendimento.get(
                "facebook_url"
            ) or "",
            key=f"ficha_facebook_{empresa_id}",
        )

    st.markdown("### 🕒 Operação de atendimento")

    operacao_1, operacao_2 = st.columns(2)

    with operacao_1:
        horario_atendimento = st.text_area(
            "Horário de atendimento",
            value=ficha_atendimento.get(
                "horario_atendimento"
            ) or "",
            placeholder=(
                "Ex.: Segunda a sexta, das 08h às 18h."
            ),
            key=f"ficha_horario_{empresa_id}",
        )

    with operacao_2:
        regiao_atendimento = st.text_area(
            "Região de atendimento",
            value=ficha_atendimento.get(
                "regiao_atendimento"
            ) or "",
            placeholder=(
                "Ex.: Atendimento online em todo o Brasil."
            ),
            key=f"ficha_regiao_{empresa_id}",
        )

    informacoes_comerciais = st.text_area(
        "Informações comerciais importantes",
        value=ficha_atendimento.get(
            "informacoes_comerciais"
        ) or "",
        placeholder=(
            "Informe condições, diferenciais ou informações "
            "comerciais importantes para o atendimento."
        ),
        key=f"ficha_comercial_{empresa_id}",
    )

    observacoes_atendimento = st.text_area(
        "Observações para o atendimento",
        value=ficha_atendimento.get(
            "observacoes_atendimento"
        ) or "",
        placeholder=(
            "Informações específicas que a Orion deve considerar "
            "ao estruturar o atendimento desta empresa."
        ),
        key=f"ficha_observacoes_{empresa_id}",
    )

    st.markdown("### 🔔 Notificações de novas leads")

    st.caption(
        "Informe quem deve receber as novas oportunidades "
        "qualificadas. Estes dados são utilizados internamente "
        "e não são apresentados ao cliente durante a conversa."
    )

    notificacao_1, notificacao_2 = st.columns(2)

    with notificacao_1:
        responsavel_leads = st.text_input(
            "Responsável pelas leads",
            value=ficha_atendimento.get(
                "responsavel_leads"
            ) or "",
            placeholder="Ex.: Luciano",
            key=f"ficha_responsavel_{empresa_id}",
        )

        whatsapp_notificacao = st.text_input(
            "WhatsApp para receber novas leads",
            value=ficha_atendimento.get(
                "whatsapp_notificacao"
            ) or "",
            placeholder="Ex.: 5585999999999",
            key=f"ficha_whatsapp_notificacao_{empresa_id}",
        )

    with notificacao_2:
        email_notificacao = st.text_input(
            "E-mail para notificações",
            value=ficha_atendimento.get(
                "email_notificacao"
            ) or "",
            placeholder="Opcional",
            key=f"ficha_email_notificacao_{empresa_id}",
        )

    st.info(
        "A configuração estratégica da Sofia — incluindo "
        "comportamento, qualificação, score, regras comerciais "
        "e lógica de atendimento — é administrada exclusivamente "
        "pela Orion Systems."
    )

    if st.button(
        "Salvar ficha de atendimento",
        use_container_width=True,
        key=f"salvar_ficha_atendimento_{empresa_id}",
    ):
        try:
            salvar_empresa_atendimento_config(
                empresa_id=empresa_id,
                descricao_empresa=descricao_empresa.strip(),
                whatsapp_comercial=whatsapp_comercial.strip(),
                email_comercial=email_comercial.strip(),
                site=site.strip(),
                instagram_url=instagram_url.strip(),
                facebook_url=facebook_url.strip(),
                horario_atendimento=horario_atendimento.strip(),
                regiao_atendimento=regiao_atendimento.strip(),
                informacoes_comerciais=informacoes_comerciais.strip(),
                observacoes_atendimento=observacoes_atendimento.strip(),
                responsavel_leads=responsavel_leads.strip(),
                whatsapp_notificacao=whatsapp_notificacao.strip(),
                email_notificacao=email_notificacao.strip(),
            )

            st.success(
                "Ficha de atendimento salva com sucesso."
            )

            st.rerun()

        except Exception as erro:
            st.error(
                f"Erro ao salvar ficha de atendimento: {erro}"
            )
