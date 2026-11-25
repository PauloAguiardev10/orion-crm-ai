import os
import unittest
from unittest.mock import MagicMock, patch

with patch.dict(os.environ, {"DATABASE_URL": "postgresql://ficticio@127.0.0.1:1/teste",
                             "PYTHON_DOTENV_DISABLED": "1"}):
    from services import usuarios_service


class ErroBancoSimulado(Exception):
    def __init__(self, pgcode, restricao):
        self.pgcode = pgcode
        self.diag = type("Diagnostico", (), {"constraint_name": restricao})()


class FranquiaUsuariosTest(unittest.TestCase):
    def test_restricao_do_postgresql_retorna_mensagem_e_desfaz_a_transacao(self):
        conn = MagicMock()
        cursor = conn.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = None
        cursor.execute.side_effect = [None, ErroBancoSimulado("23514", "orion_limite_usuarios")]
        with (
            patch.object(usuarios_service, "conectar", return_value=conn),
            patch.object(usuarios_service, "criar_tabela_usuarios"),
        ):
            with self.assertRaisesRegex(usuarios_service.FranquiaUsuariosAtingida, "limite de usuários"):
                usuarios_service.criar_usuario("atendente-teste", "ficticia", "Empresa fictícia", "usuario", 42)
        self.assertEqual(cursor.execute.call_args_list[0].args[1][0], 42)
        conn.rollback.assert_called_once()
        conn.commit.assert_not_called()
