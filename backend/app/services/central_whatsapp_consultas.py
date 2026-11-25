from sqlalchemy import text


PERFIS_ADMINISTRATIVOS = ("orion_admin", "parceiro_admin", "admin_empresa")
PERFIS_CENTRAL = (*PERFIS_ADMINISTRATIVOS, "usuario", "vendedor")

VINCULOS_CONVERSA = """
    FROM conversas c
    JOIN conexoes_canais cc
      ON cc.id = c.conexao_canal_id AND cc.empresa_id = c.empresa_id
    LEFT JOIN especialistas titular
      ON titular.id = cc.especialista_id AND titular.empresa_id = c.empresa_id
    LEFT JOIN especialistas responsavel
      ON responsavel.id = c.especialista_id AND responsavel.empresa_id = c.empresa_id
"""

PERMISSAO_CONVERSA = """
    WHERE c.empresa_id = :empresa_id
      AND LOWER(c.canal) = 'whatsapp'
      AND LOWER(cc.canal) = 'whatsapp'
      AND LOWER(cc.provedor) = 'waha'
      AND cc.ativo IS TRUE
      AND (
        (:administrador AND (:empresa_propria OR cc.especialista_id IS NULL)) OR (
          (cc.especialista_id IS NULL OR titular.usuario_id = :usuario_id)
          AND (responsavel.usuario_id = :usuario_id OR (
            c.especialista_id IS NULL AND (
              titular.usuario_id = :usuario_id OR (
                :incluir_fila AND cc.especialista_id IS NULL AND EXISTS (
                  SELECT 1 FROM especialistas e
                  WHERE e.empresa_id = c.empresa_id AND e.usuario_id = :usuario_id
                )
              )
            )
          ))
        )
      )
"""

ESCOPO_CONVERSA = VINCULOS_CONVERSA + PERMISSAO_CONVERSA

# Registros legados sem conexão explícita herdam o vínculo da conversa.
ESCOPO_MENSAGEM = """
    m.empresa_id = c.empresa_id AND m.conversa_id = c.id
    AND (m.conexao_canal_id IS NULL OR m.conexao_canal_id = c.conexao_canal_id)
"""


def _parametros(identidade, limite, deslocamento, incluir_fila=False):
    return {
        "empresa_id": identidade["empresa_id"],
        "usuario_id": identidade["usuario_id"],
        "administrador": identidade["nivel"] in PERFIS_ADMINISTRATIVOS,
        "empresa_propria": identidade.get("empresa_propria", True),
        "incluir_fila": incluir_fila,
        "limite": limite,
        "deslocamento": deslocamento,
    }


def listar_conversas(
    db, *, identidade, limite, deslocamento, conexao_id, incluir_fila=False, fixar_conversa_id=None,
    busca=None, responsavel_id=None, status=None,
):
    # As interpolações contêm apenas cláusulas constantes, com parâmetros SQL.
    consulta = text(f"""
        SELECT c.id, c.identificador, c.nome, c.status_atendimento,
               c.atualizado_em, c.conexao_canal_id, c.especialista_id,
               responsavel.usuario_id AS especialista_usuario_id,
               responsavel.nome AS responsavel_nome,
               c.humano_assumiu,
               cc.especialista_id IS NULL AS corporativa,
               (:administrador AND cc.especialista_id IS NULL) AS pode_supervisionar,
               (cc.especialista_id IS NULL OR titular.usuario_id = :usuario_id)
                 AND NOT (c.humano_assumiu IS TRUE AND c.status_atendimento IS NOT DISTINCT FROM 'finalizado')
                 AND COALESCE(responsavel.usuario_id = :usuario_id, c.especialista_id IS NULL)
                 AND EXISTS (
                   SELECT 1 FROM especialistas e
                   WHERE e.empresa_id = c.empresa_id AND e.usuario_id = :usuario_id
                 ) AS pode_assumir,
               COALESCE(responsavel.nome, titular.nome) AS vendedor_nome,
               (SELECT MAX(m.id) FROM mensagens m WHERE {ESCOPO_MENSAGEM}
                AND m.from_me IS FALSE AND m.remetente = 'cliente') AS ultima_recebida_id,
               (SELECT l.ultima_mensagem_id FROM central_conversa_leitura l
                WHERE l.empresa_id = c.empresa_id AND l.conversa_id = c.id
                  AND l.usuario_id = :usuario_id) AS ultima_lida_id,
               cc.nome_conexao AS conexao_nome,
               ultima.texto AS ultima_mensagem, ultima.tipo AS ultimo_tipo,
               ultima.criado_em AS ultima_mensagem_em
        {VINCULOS_CONVERSA}
        LEFT JOIN LATERAL (
            SELECT m.texto, m.tipo, m.criado_em FROM mensagens m WHERE {ESCOPO_MENSAGEM}
            ORDER BY m.criado_em DESC NULLS LAST, m.id DESC LIMIT 1
        ) ultima ON TRUE
        {PERMISSAO_CONVERSA}
        AND ({"c.id = :fixar_conversa_id OR" if fixar_conversa_id is not None else ""} (
            (:conexao_id IS NULL OR c.conexao_canal_id = :conexao_id)
            AND (:responsavel_id IS NULL OR COALESCE(c.especialista_id, 0) = :responsavel_id)
            AND (:status IS NULL OR c.status_atendimento = :status)
            AND (:busca IS NULL OR strpos(lower(COALESCE(c.nome, '')), :busca) > 0
                OR strpos(lower(c.identificador), :busca) > 0
                OR strpos(lower(COALESCE(ultima.texto, '')), :busca) > 0)
        ))
        ORDER BY {"(c.id = :fixar_conversa_id) DESC," if fixar_conversa_id is not None else ""}
                 c.atualizado_em DESC NULLS LAST, c.id DESC
        LIMIT :limite OFFSET :deslocamento
    """)
    parametros = _parametros(identidade, limite, deslocamento, incluir_fila)
    parametros.update(conexao_id=conexao_id, responsavel_id=responsavel_id, status=status,
                      busca=busca.strip().lower() if busca and busca.strip() else None)
    if fixar_conversa_id is not None:
        parametros["fixar_conversa_id"] = fixar_conversa_id
    return [dict(linha) for linha in db.execute(consulta, parametros).mappings()]


def listar_historico(
    db, *, identidade, conversa_id, limite, deslocamento, incluir_fila=False, antes_id=None,
):
    cursor = """
        AND (COALESCE(m.criado_em, '-infinity'::timestamp), m.id) < (
            SELECT COALESCE(a.criado_em, '-infinity'::timestamp), a.id
            FROM mensagens a
            WHERE a.id = :antes_id AND a.empresa_id = c.empresa_id AND a.conversa_id = c.id
              AND (a.conexao_canal_id IS NULL OR a.conexao_canal_id = c.conexao_canal_id)
        )
    """ if antes_id is not None else ""
    consulta = text(f"""
        WITH autorizada AS (
            SELECT c.id, c.empresa_id, c.conexao_canal_id
            {ESCOPO_CONVERSA}
            AND c.id = :conversa_id
        )
        SELECT pagina.*
        FROM autorizada c
        LEFT JOIN LATERAL (
            SELECT m.id, m.remetente, m.texto, m.tipo,
                   m.midia_tipo, (m.midia_url IS NOT NULL) AS tem_anexo,
                   m.from_me, m.criado_em, m.status_envio, m.status_processamento,
                   autor.nome AS autor_nome
            FROM mensagens m
            LEFT JOIN especialistas autor ON autor.id = m.especialista_id AND autor.empresa_id = m.empresa_id
            WHERE {ESCOPO_MENSAGEM}
            {cursor}
            ORDER BY m.criado_em DESC NULLS LAST, m.id DESC
            LIMIT :limite OFFSET :deslocamento
        ) pagina ON TRUE
        ORDER BY pagina.criado_em ASC NULLS FIRST, pagina.id ASC
    """)
    linhas = db.execute(consulta, {
        **_parametros(identidade, limite, deslocamento, incluir_fila),
        "conversa_id": conversa_id,
        "antes_id": antes_id,
    }).mappings().all()
    if not linhas:
        return None
    return [dict(linha) for linha in linhas if linha["id"] is not None]


def listar_filtros_conversas(db, *, identidade, incluir_fila):
    consulta = text(f"""
        SELECT DISTINCT cc.id AS conexao_id, cc.nome_conexao,
               responsavel.id AS responsavel_id, responsavel.nome AS responsavel_nome
        {ESCOPO_CONVERSA}
        ORDER BY cc.id, responsavel.id
    """)
    return [dict(linha) for linha in db.execute(
        consulta, _parametros(identidade, 1, 0, incluir_fila),
    ).mappings()]


def consultar_contexto_conversa(db, *, identidade, conversa_id):
    consulta = text(f"""
        WITH autorizada AS (
            SELECT c.id, c.empresa_id, c.cliente_id, c.telefone,
                   c.nome, c.servico_interesse, c.servico
            {ESCOPO_CONVERSA}
            AND c.id = :conversa_id
        )
        SELECT COALESCE(pessoa.nome, c.nome) AS cliente,
               COALESCE(pessoa.telefone, c.telefone) AS telefone,
               COALESCE(pessoa.empresa_cliente, pessoa.empresa) AS empresa_cliente,
               empresa.nome AS empresa_crm, empresa.timezone,
               lead.temperatura, lead.score, lead.resumo_vendedor,
               COALESCE(lead.produto, c.servico_interesse, c.servico) AS servico,
               tentativa.status AS followup_status, tentativa.agendado_para AS followup_agendado,
               tentativa.numero_tentativa AS followup_tentativa
        FROM autorizada c
        JOIN empresas empresa ON empresa.id = c.empresa_id
        LEFT JOIN LATERAL (
            SELECT l.cliente_id, l.id, l.temperatura, l.score, l.resumo_vendedor, l.produto
            FROM leads l WHERE l.empresa_id = c.empresa_id AND l.conversa_id = c.id
            ORDER BY l.id DESC LIMIT 1
        ) lead ON TRUE
        LEFT JOIN clientes pessoa ON pessoa.empresa_id = c.empresa_id
            AND pessoa.id = COALESCE(c.cliente_id, lead.cliente_id)
        LEFT JOIN LATERAL (
            SELECT f.status, f.agendado_para, f.numero_tentativa
            FROM followup_agendamentos f
            WHERE f.empresa_id = c.empresa_id AND f.conversa_id = c.id AND f.lead_id = lead.id
            ORDER BY f.numero_tentativa DESC LIMIT 1
        ) tentativa ON TRUE
    """)
    linha = db.execute(consulta, {
        **_parametros(identidade, 1, 0), "conversa_id": conversa_id,
    }).mappings().one_or_none()
    return dict(linha) if linha is not None else None


def consultar_anexo(db, *, identidade, conversa_id, mensagem_id):
    consulta = text(f"""
        WITH autorizada AS (
            SELECT c.id, c.empresa_id, c.conexao_canal_id
            {ESCOPO_CONVERSA}
            AND c.id = :conversa_id
        )
        SELECT m.midia_tipo, m.midia_url
        FROM autorizada c JOIN mensagens m ON {ESCOPO_MENSAGEM}
        WHERE m.id = :mensagem_id AND m.midia_url IS NOT NULL
    """)
    return db.execute(consulta, {
        **_parametros(identidade, 1, 0),
        "conversa_id": conversa_id, "mensagem_id": mensagem_id,
    }).mappings().one_or_none()


def registrar_leitura(db, *, identidade, conversa_id, mensagem_id):
    consulta = text(f"""
        WITH autorizada AS (
            SELECT c.id, c.empresa_id, c.conexao_canal_id
            {ESCOPO_CONVERSA}
            AND c.id = :conversa_id
        )
        INSERT INTO central_conversa_leitura (empresa_id, usuario_id, conversa_id, ultima_mensagem_id)
        SELECT c.empresa_id, :usuario_id, c.id, m.id
        FROM autorizada c JOIN mensagens m ON {ESCOPO_MENSAGEM}
        WHERE m.id = :mensagem_id AND m.from_me IS FALSE AND m.remetente = 'cliente'
        ON CONFLICT (empresa_id, usuario_id, conversa_id) DO UPDATE
          SET ultima_mensagem_id = GREATEST(central_conversa_leitura.ultima_mensagem_id,
                                           EXCLUDED.ultima_mensagem_id)
        RETURNING ultima_mensagem_id
    """)
    return db.execute(consulta, {
        **_parametros(identidade, 1, 0, True), "conversa_id": conversa_id, "mensagem_id": mensagem_id,
    }).scalar_one_or_none()
