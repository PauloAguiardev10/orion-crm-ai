from database.db import conectar


def carregar_empresa_atendimento_config(
    empresa_id: int,
):
    """
    Carrega os dados institucionais e operacionais utilizados
    no atendimento da Sofia para uma empresa espec?fica.

    Retorna None quando ainda n?o existir configura??o.
    """

    conn = conectar()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    empresa_id,
                    descricao_empresa,
                    whatsapp_comercial,
                    email_comercial,
                    site,
                    instagram_url,
                    facebook_url,
                    horario_atendimento,
                    regiao_atendimento,
                    informacoes_comerciais,
                    observacoes_atendimento,
                    responsavel_leads,
                    whatsapp_notificacao,
                    email_notificacao,
                    criado_em,
                    atualizado_em
                FROM empresa_atendimento_config
                WHERE empresa_id = %s
                """,
                (
                    int(empresa_id),
                ),
            )

            resultado = cursor.fetchone()

        if resultado is None:
            return None

        colunas = [
            "id",
            "empresa_id",
            "descricao_empresa",
            "whatsapp_comercial",
            "email_comercial",
            "site",
            "instagram_url",
            "facebook_url",
            "horario_atendimento",
            "regiao_atendimento",
            "informacoes_comerciais",
            "observacoes_atendimento",
            "responsavel_leads",
            "whatsapp_notificacao",
            "email_notificacao",
            "criado_em",
            "atualizado_em",
        ]

        return dict(
            zip(
                colunas,
                resultado,
            )
        )

    finally:
        conn.close()


def salvar_empresa_atendimento_config(
    empresa_id: int,
    descricao_empresa=None,
    whatsapp_comercial=None,
    email_comercial=None,
    site=None,
    instagram_url=None,
    facebook_url=None,
    horario_atendimento=None,
    regiao_atendimento=None,
    informacoes_comerciais=None,
    observacoes_atendimento=None,
    responsavel_leads=None,
    whatsapp_notificacao=None,
    email_notificacao=None,
):
    """
    Cria ou atualiza a ficha de atendimento da empresa.

    Esta fun??o grava somente dados institucionais e operacionais.
    Nenhuma configura??o comportamental da Sofia ? alterada aqui.
    """

    conn = conectar()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO empresa_atendimento_config (
                    empresa_id,
                    descricao_empresa,
                    whatsapp_comercial,
                    email_comercial,
                    site,
                    instagram_url,
                    facebook_url,
                    horario_atendimento,
                    regiao_atendimento,
                    informacoes_comerciais,
                    observacoes_atendimento,
                    responsavel_leads,
                    whatsapp_notificacao,
                    email_notificacao
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (empresa_id)
                DO UPDATE SET
                    descricao_empresa = EXCLUDED.descricao_empresa,
                    whatsapp_comercial = EXCLUDED.whatsapp_comercial,
                    email_comercial = EXCLUDED.email_comercial,
                    site = EXCLUDED.site,
                    instagram_url = EXCLUDED.instagram_url,
                    facebook_url = EXCLUDED.facebook_url,
                    horario_atendimento = EXCLUDED.horario_atendimento,
                    regiao_atendimento = EXCLUDED.regiao_atendimento,
                    informacoes_comerciais = EXCLUDED.informacoes_comerciais,
                    observacoes_atendimento = EXCLUDED.observacoes_atendimento,
                    responsavel_leads = EXCLUDED.responsavel_leads,
                    whatsapp_notificacao = EXCLUDED.whatsapp_notificacao,
                    email_notificacao = EXCLUDED.email_notificacao,
                    atualizado_em = CURRENT_TIMESTAMP
                """,
                (
                    int(empresa_id),
                    descricao_empresa,
                    whatsapp_comercial,
                    email_comercial,
                    site,
                    instagram_url,
                    facebook_url,
                    horario_atendimento,
                    regiao_atendimento,
                    informacoes_comerciais,
                    observacoes_atendimento,
                    responsavel_leads,
                    whatsapp_notificacao,
                    email_notificacao,
                ),
            )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()
