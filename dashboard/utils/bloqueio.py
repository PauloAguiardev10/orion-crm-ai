import streamlit as st

from database.db import conectar


def empresa_bloqueada():

    empresa_id = st.session_state.get(
        "empresa_id"
    )

    nivel = st.session_state.get(
        "nivel"
    )

    if nivel in [
        "orion_admin",
        "parceiro_admin"
    ]:
        return False

    conn = None

    try:

        conn = conectar()

        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT

                    status,
                    status_financeiro,
                    bloqueio_automatico

                FROM empresas

                WHERE id = %s
            """, (
                empresa_id,
            ))

            resultado = cursor.fetchone()

        if not resultado:
            return False

        status = resultado[0]

        financeiro = resultado[1]

        bloqueio = resultado[2]

        if status != "ativa":
            return True

        if (
            financeiro in [
                "vencido",
                "inadimplente"
            ]
            and bloqueio
        ):
            return True

    except Exception:
        return False

    finally:

        if conn:
            conn.close()

    return False


def tela_bloqueio():

    st.markdown(
        "<br><br>",
        unsafe_allow_html=True
    )

    st.markdown(
        "## 🚫 Sistema Bloqueado"
    )

    st.markdown(
        "### O acesso desta empresa foi temporariamente suspenso."
    )

    st.write(
        """
        Detectamos pendência financeira,
        vencimento contratual
        ou bloqueio administrativo.
        """
    )

    st.info(
        """
        Entre em contato com a equipe da
        Forway ou Orion Systems
        para regularizar o acesso.
        """
    )

    st.stop()