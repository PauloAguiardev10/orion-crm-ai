"""Consultas das configuracoes do Follow-up Automatico."""

from database.db import conectar


def carregar_configuracoes_followup(
    empresa_id: int,
    *,
    nivel: str,
    empresa_login_id: int,
) -> dict:
    """Consulta configuracoes e modelos da empresa autorizada."""

    validar_acesso_configuracoes_followup(
        nivel=nivel,
        empresa_login_id=empresa_login_id,
        empresa_id=empresa_id,
    )

    empresa_id = int(empresa_id)

    if empresa_id <= 0:
        raise ValueError("Empresa invalida.")

    conn = conectar()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    ativo,
                    modo,
                    quantidade_tentativas,
                    fuso_horario,
                    segunda_sexta_inicio,
                    segunda_sexta_fim,
                    sabado_ativo,
                    sabado_inicio,
                    sabado_fim,
                    domingo_ativo
                FROM followup_configuracoes
                WHERE empresa_id = %s
                """,
                (empresa_id,),
            )

            registro = cursor.fetchone()

            if registro is None:
                return {
                    "configuracao": None,
                    "mensagens": [],
                }

            colunas = [coluna[0] for coluna in cursor.description]
            configuracao = dict(zip(colunas, registro))

            cursor.execute(
                """
                SELECT
                    numero_tentativa,
                    intervalo_minutos,
                    texto,
                    ativo
                FROM followup_modelos_mensagem
                WHERE empresa_id = %s
                ORDER BY numero_tentativa
                """,
                (empresa_id,),
            )

            colunas = [coluna[0] for coluna in cursor.description]

            mensagens = [
                dict(zip(colunas, linha))
                for linha in cursor.fetchall()
            ]

            return {
                "configuracao": configuracao,
                "mensagens": mensagens,
            }

    finally:
        conn.close()


def salvar_configuracoes_followup(
    empresa_id: int,
    *,
    nivel: str,
    empresa_login_id: int,
    quantidade_tentativas: int,
    segunda_sexta_inicio,
    segunda_sexta_fim,
    sabado_ativo: bool,
    sabado_inicio,
    sabado_fim,
    domingo_ativo: bool,
) -> None:
    """Salva configuracoes operacionais sem ativar disparos."""

    from datetime import time

    validar_acesso_configuracoes_followup(
        nivel=nivel,
        empresa_login_id=empresa_login_id,
        empresa_id=empresa_id,
    )

    empresa_id = int(empresa_id)
    quantidade_tentativas = int(quantidade_tentativas)

    if empresa_id <= 0:
        raise ValueError("Empresa invalida.")

    if not 1 <= quantidade_tentativas <= 10:
        raise ValueError("Quantidade de tentativas deve estar entre 1 e 10.")

    horarios = (
        segunda_sexta_inicio,
        segunda_sexta_fim,
        sabado_inicio,
        sabado_fim,
    )

    if not all(isinstance(valor, time) for valor in horarios):
        raise ValueError("Horarios invalidos.")

    if segunda_sexta_inicio >= segunda_sexta_fim:
        raise ValueError("Horario da semana invalido.")

    if sabado_inicio >= sabado_fim:
        raise ValueError("Horario de sabado invalido.")

    conn = conectar()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE followup_configuracoes
                SET
                    modo = 'personalizado',
                    quantidade_tentativas = %s,
                    segunda_sexta_inicio = %s,
                    segunda_sexta_fim = %s,
                    sabado_ativo = %s,
                    sabado_inicio = %s,
                    sabado_fim = %s,
                    domingo_ativo = %s,
                    atualizado_em = NOW()
                WHERE empresa_id = %s
                """,
                (
                    quantidade_tentativas,
                    segunda_sexta_inicio,
                    segunda_sexta_fim,
                    sabado_ativo,
                    sabado_inicio,
                    sabado_fim,
                    domingo_ativo,
                    empresa_id,
                ),
            )

            if cursor.rowcount != 1:
                raise ValueError("Configuracao da empresa nao encontrada.")

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def validar_acesso_configuracoes_followup(
    *,
    nivel: str,
    empresa_login_id: int,
    empresa_id: int,
) -> None:
    """Valida o perfil e o contexto multiempresa autorizado."""

    from services.empresa_contexto_service import (
        listar_empresas_permitidas,
    )

    niveis_administrativos = {
        "orion_admin",
        "parceiro_admin",
        "admin_empresa",
    }

    if nivel not in niveis_administrativos:
        raise PermissionError(
            "Usuario sem permissao para configurar Follow-up."
        )

    empresa_login_id = int(empresa_login_id)
    empresa_id = int(empresa_id)

    if empresa_login_id <= 0 or empresa_id <= 0:
        raise PermissionError("Contexto de empresa invalido.")

    empresas = listar_empresas_permitidas(
        nivel,
        empresa_login_id,
    )

    ids_permitidos = set(
        empresas["id"].astype(int).tolist()
    )

    if empresa_id not in ids_permitidos:
        raise PermissionError(
            "Empresa nao autorizada para este usuario."
        )


def salvar_modelo_mensagem_followup(
    empresa_id: int,
    *,
    nivel: str,
    empresa_login_id: int,
    numero_tentativa: int,
    intervalo_minutos: int,
    texto: str,
    ativo: bool,
) -> None:
    """Atualiza um modelo existente da empresa autorizada."""

    validar_acesso_configuracoes_followup(
        nivel=nivel,
        empresa_login_id=empresa_login_id,
        empresa_id=empresa_id,
    )

    empresa_id = int(empresa_id)
    numero_tentativa = int(numero_tentativa)
    intervalo_minutos = int(intervalo_minutos)
    texto = str(texto).strip()

    if not 1 <= numero_tentativa <= 10:
        raise ValueError("Tentativa invalida.")

    if not 1 <= intervalo_minutos <= 43200:
        raise ValueError("Intervalo fora do limite permitido.")

    if not 1 <= len(texto) <= 4000:
        raise ValueError("Mensagem deve ter entre 1 e 4000 caracteres.")

    conn = conectar()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE followup_modelos_mensagem
                SET
                    intervalo_minutos = %s,
                    texto = %s,
                    ativo = %s,
                    atualizado_em = NOW()
                WHERE empresa_id = %s
                  AND numero_tentativa = %s
                """,
                (
                    intervalo_minutos,
                    texto,
                    bool(ativo),
                    empresa_id,
                    numero_tentativa,
                ),
            )

            if cursor.rowcount != 1:
                raise ValueError(
                    "Modelo nao encontrado para esta empresa."
                )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def listar_agendamentos_followup(
    empresa_id: int,
    *,
    nivel: str,
    empresa_login_id: int,
    limite: int = 200,
) -> list[dict]:
    """Lista agendamentos da empresa autorizada, sem alterar dados."""

    validar_acesso_configuracoes_followup(
        nivel=nivel,
        empresa_login_id=empresa_login_id,
        empresa_id=empresa_id,
    )

    empresa_id = int(empresa_id)
    limite = int(limite)

    if empresa_id <= 0:
        raise ValueError("Empresa invalida.")

    if not 1 <= limite <= 500:
        raise ValueError("Limite deve estar entre 1 e 500.")

    conn = conectar()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    empresa_id,
                    lead_id,
                    conversa_id,
                    numero_tentativa,
                    agendado_para,
                    status,
                    tentativas_envio,
                    enviado_em,
                    cancelado_em,
                    erro_envio,
                    criado_em
                FROM followup_agendamentos
                WHERE empresa_id = %s
                ORDER BY criado_em DESC, id DESC
                LIMIT %s
                """,
                (empresa_id, limite),
            )

            colunas = [
                coluna[0]
                for coluna in cursor.description
            ]

            return [
                dict(zip(colunas, linha))
                for linha in cursor.fetchall()
            ]

    finally:
        conn.close()
