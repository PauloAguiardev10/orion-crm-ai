
from database.db import conectar


def listar_conversas_whatsapp(
    *,
    empresa_id: int,
    usuario_id: int,
    nivel: str,
    limite: int = 100,
) -> list[dict]:
    """Lista conversas WhatsApp respeitando empresa e vendedor."""

    if not empresa_id or not usuario_id:
        return []

    if nivel not in (
        "orion_admin",
        "parceiro_admin",
        "admin_empresa",
        "usuario",
        "vendedor",
    ):
        return []

    limite = max(1, min(int(limite), 200))

    administrador = nivel in (
        "orion_admin",
        "parceiro_admin",
        "admin_empresa",
    )

    sql = """
        SELECT
            c.id,
            c.empresa_id,
            c.conexao_canal_id,
            c.identificador,
            c.nome,
            c.telefone,
            c.etapa,
            c.status_atendimento,
            c.humano_assumiu,
            c.atualizado_em,
            cc.sessao_waha,
            e.nome AS vendedor_nome,
            (
                SELECT m.texto
                FROM mensagens m
                WHERE m.empresa_id = c.empresa_id
                  AND m.conversa_id = c.id
                ORDER BY m.criado_em DESC, m.id DESC
                LIMIT 1
            ) AS ultima_mensagem
        FROM conversas c
        JOIN conexoes_canais cc
          ON cc.id = c.conexao_canal_id
         AND cc.empresa_id = c.empresa_id
        LEFT JOIN especialistas e
          ON e.id = cc.especialista_id
         AND e.empresa_id = c.empresa_id
        WHERE c.empresa_id = %s
          AND LOWER(c.canal) = 'whatsapp'
          AND LOWER(cc.canal) = 'whatsapp'
          AND LOWER(cc.provedor) = 'waha'
          AND cc.ativo IS TRUE
    """

    parametros = [empresa_id]

    if not administrador:
        sql += """
          AND e.usuario_id = %s
        """
        parametros.append(usuario_id)

    sql += """
        ORDER BY c.atualizado_em DESC NULLS LAST, c.id DESC
        LIMIT %s
    """

    parametros.append(limite)

    conexao = conectar()

    try:
        with conexao.cursor() as cursor:
            cursor.execute(sql, parametros)

            colunas = [
                coluna[0]
                for coluna in cursor.description
            ]

            return [
                dict(zip(colunas, linha))
                for linha in cursor.fetchall()
            ]
    finally:
        conexao.close()


def listar_mensagens_whatsapp(
    *,
    empresa_id: int,
    usuario_id: int,
    nivel: str,
    conversa_id: int,
    limite: int = 100,
) -> list[dict]:
    """Consulta mensagens de uma conversa autorizada."""

    if not all((empresa_id, usuario_id, conversa_id)):
        return []

    if nivel not in (
        "orion_admin",
        "parceiro_admin",
        "admin_empresa",
        "usuario",
        "vendedor",
    ):
        return []

    administrador = nivel in (
        "orion_admin",
        "parceiro_admin",
        "admin_empresa",
    )

    limite = max(1, min(int(limite), 200))

    sql = """
        SELECT
            m.id,
            m.remetente,
            m.texto,
            m.tipo,
            m.from_me,
            m.criado_em,
            m.status_envio
        FROM mensagens m
        JOIN conversas c
          ON c.id = m.conversa_id
         AND c.empresa_id = m.empresa_id
        JOIN conexoes_canais cc
          ON cc.id = c.conexao_canal_id
         AND cc.empresa_id = c.empresa_id
        LEFT JOIN especialistas e
          ON e.id = cc.especialista_id
         AND e.empresa_id = c.empresa_id
        WHERE m.empresa_id = %s
          AND m.conversa_id = %s
          AND LOWER(c.canal) = 'whatsapp'
          AND LOWER(cc.canal) = 'whatsapp'
          AND LOWER(cc.provedor) = 'waha'
          AND cc.ativo IS TRUE
    """

    parametros = [empresa_id, conversa_id]

    if not administrador:
        sql += " AND e.usuario_id = %s"
        parametros.append(usuario_id)

    sql += """
        ORDER BY m.criado_em DESC, m.id DESC
        LIMIT %s
    """
    parametros.append(limite)

    conexao = conectar()

    try:
        with conexao.cursor() as cursor:
            cursor.execute(sql, parametros)

            colunas = [
                coluna[0]
                for coluna in cursor.description
            ]

            registros = [
                dict(zip(colunas, linha))
                for linha in cursor.fetchall()
            ]

            return list(reversed(registros))
    finally:
        conexao.close()
