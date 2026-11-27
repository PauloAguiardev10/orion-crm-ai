import os
import sys
from pathlib import Path
from unittest.mock import patch

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from app_pages.conversas import render_conversas
os.environ["DATABASE_URL"] = "postgresql://fixture@127.0.0.1:1/fixture"
from components import sidebar
from styles.theme import carregar_tema

st.set_page_config(layout="wide")
carregar_tema()
os.environ["ORION_CENTRAL_UI_URL"] = "http://127.0.0.1:48319/central-ui/"
st.session_state.update(
    usuario_id=10, empresa_ativa_id=1, empresa_login_id=1, token_central="simulado",
    empresa_login_nome="Orion CRM AI", nivel="vendedor", menu_principal_followup_v2="💬 Conversas",
)
with (
    patch.object(sidebar, "conectar", side_effect=AssertionError("Banco proibido na captura")),
    patch.object(sidebar, "obter_logo_empresa", return_value=None),
    patch.object(sidebar, "obter_status_whatsapp", return_value={"conectado": True}),
):
    sidebar.render_sidebar()
render_conversas(None)
