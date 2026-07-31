import streamlit as st

from database.db import conectar


def obter_plano_empresa(empresa_id):
    conn = None

    try:
        conn = conectar()

        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT plano
                FROM empresas
                WHERE id = %s
            """, (
                empresa_id,
            ))

            resultado = cursor.fetchone()

        if resultado:
            return resultado[0]

    except Exception:
        pass

    finally:
        if conn:
            conn.close()

    return "Lite"


def verificar_permissao(plano_minimo):
    empresa_id = st.session_state.get("empresa_id")

    plano = obter_plano_empresa(empresa_id)

    ordem_planos = {
        "Lite": 1,
        "Pro": 2,
        "Premium": 3,
    }

    atual = ordem_planos.get(plano, 1)
    necessario = ordem_planos.get(plano_minimo, 1)

    return atual >= necessario


def tela_upgrade(recurso, plano):
    st.markdown("<br><br>", unsafe_allow_html=True)

    st.warning(
        f"🚫 O recurso '{recurso}' está disponível apenas no plano {plano}."
    )

    st.info(
        "Faça upgrade do plano para liberar esta função e outros recursos premium."
    )

    st.markdown("---")

    st.markdown("## 🚀 Benefícios do Upgrade")

    st.markdown("""
✅ IA Vendas  
✅ PIX Automático  
✅ Produtos e Pedidos  
✅ CRM Avançado  
✅ Funil Comercial  
✅ Analytics Completo  
""")