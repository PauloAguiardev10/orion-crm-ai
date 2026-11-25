from datetime import datetime
from html import escape
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import streamlit as st


STATUS_ATENDIMENTO = {
    "em_atendimento_ia": "Atendimento pela Sofia",
    "aguardando_humano": "Aguardando atendimento humano",
    "em_atendimento_humano": "Em atendimento humano",
    "finalizado": "Encerrado",
}
TIPOS_ANEXO = {"imagem": "Imagem", "audio": "Áudio", "video": "Vídeo", "documento": "Documento", "midia": "Anexo"}

ESTILO_CENTRAL = """
<style>
.st-key-orion_whatsapp {color:#e7efff}
.st-key-orion_whatsapp [data-testid="stHorizontalBlock"] {align-items:flex-start}
.st-key-orion_whatsapp .orion-wa-heading {font-size:1.37rem; font-weight:720; color:#f1f6ff; margin:0 0 2px}
.st-key-orion_whatsapp .orion-wa-muted {color:#a2b4cf; font-size:.8rem}
.st-key-orion_whatsapp .orion-wa-hero {
    padding:16px 20px; border:1px solid #254259; border-radius:13px;
    background:linear-gradient(105deg,#102c43,#0f1930 65%,#1a1732)
}
.st-key-orion_whatsapp .orion-wa-contact {display:flex; align-items:center; gap:12px; min-width:0}
.st-key-orion_whatsapp .orion-wa-contact > div:nth-child(2) {min-width:0; flex:1}
.st-key-orion_whatsapp .orion-wa-avatar {
    display:grid; place-items:center; flex:0 0 42px; height:42px;
    border:1px solid #30546e; border-radius:50%; font-weight:700;
    color:#a7f2ff; background:#17354c; overflow:hidden
}
.st-key-orion_whatsapp .orion-wa-avatar img {width:100%; height:100%; object-fit:cover}
.st-key-orion_whatsapp .orion-wa-name {font-weight:680; overflow-wrap:anywhere; color:#eef5ff}
.st-key-orion_whatsapp .orion-wa-time {font-size:.73rem; color:#a2b4cf; white-space:nowrap; margin-left:auto}
.st-key-orion_whatsapp .orion-wa-unread {width:8px;height:8px;background:#38e8f1;border-radius:100%;flex:none}
.st-key-orion_whatsapp .orion-wa-preview {font-size:.82rem;color:#a9bad1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; margin:4px 0 0 54px}
.st-key-orion_whatsapp [class*="st-key-orion_wa_linha_"] {position:relative;padding:8px 10px;border:1px solid #24364e;border-radius:10px;background:#101a2c}
.st-key-orion_whatsapp [class*="st-key-orion_wa_ativa_"] {padding:8px 10px;border:1px solid #347482;border-radius:10px;background:#132d40}
.st-key-orion_whatsapp [class*="st-key-orion_wa_abrir_"] button {min-height:28px;font-size:.8rem}
.st-key-orion_whatsapp [class*="st-key-orion_wa_linha_"] [class*="st-key-orion_wa_abrir_"] {
    position:absolute;inset:0;z-index:2
}
.st-key-orion_whatsapp [class*="st-key-orion_wa_linha_"] [class*="st-key-orion_wa_abrir_"] button {
    position:absolute;inset:0;width:100%;height:100%;opacity:0.02
}
.st-key-orion_whatsapp [class*="st-key-orion_wa_linha_"]:has(button:focus-visible) {outline:2px solid #47d9e8}
.st-key-orion_whatsapp .st-key-orion_wa_voltar {display:none}
.st-key-orion_whatsapp button[data-testid^="stBaseButton-primary"],
.st-key-orion_whatsapp button[kind="primaryFormSubmit"] {
    background:#47d9e8; border-color:#47d9e8; color:#102236; font-weight:700
}
.st-key-orion_whatsapp button[data-testid^="stBaseButton-primary"]:hover,
.st-key-orion_whatsapp button[kind="primaryFormSubmit"]:hover {
    background:#8beaf0; border-color:#8beaf0; color:#102236
}
.st-key-orion_whatsapp [class*="st-key-orion_wa_historico_"] {background:#0b1425;border:1px solid #24364e}
.st-key-orion_whatsapp .orion-wa-data {color:#b3c7e0;font-size:.76rem;text-align:center;margin:4px 0}
.st-key-orion_whatsapp .orion-wa-balao {width:fit-content;max-width:90%;padding:8px 12px;
    border:1px solid #2a3d57;border-radius:12px 12px 12px 3px;background:#172439;
    color:#eef5ff;overflow-wrap:anywhere;white-space:pre-wrap;margin-bottom:6px}
.st-key-orion_whatsapp .orion-wa-enviada {margin-left:auto;border-color:#285661;border-radius:12px 12px 3px 12px;background:#153642}
.st-key-orion_whatsapp [class*="st-key-orion_wa_voz_"] {
    width:min(355px,90%);padding:6px 10px;
    border:1px solid #2a3d57;border-radius:12px;background:#172439
}
.st-key-orion_whatsapp [class*="st-key-orion_wa_voz_enviada_"] {margin-left:auto;background:#153642;border-color:#285661}
.st-key-orion_whatsapp [class*="st-key-orion_wa_voz_"] .orion-wa-balao {
    margin:0;padding:3px 0;background:transparent;border:0
}
.st-key-orion_whatsapp .orion-wa-meta {font-size:.71rem;color:#a4c4d3;margin-top:4px}
.st-key-orion_whatsapp .orion-wa-ficha {display:grid;gap:8px}
.st-key-orion_whatsapp .orion-wa-ficha div {display:grid;gap:1px;overflow-wrap:anywhere}
.st-key-orion_whatsapp .orion-wa-ficha span {color:#a2b4cf;font-size:.75rem}
.st-key-orion_whatsapp .orion-wa-ficha strong {color:#e7efff;font-size:.91rem}
@media (max-width:850px) {
    .st-key-orion_whatsapp [data-testid="stHorizontalBlock"] {flex-wrap:wrap}
    .st-key-orion_whatsapp [data-testid="stColumn"] {min-width:min(100%, 290px)}
    .st-key-orion_wa_lista [data-testid="stVerticalBlockBorderWrapper"],
    .st-key-orion_wa_lista[data-testid="stVerticalBlockBorderWrapper"] {max-height:320px}
    .st-key-orion_whatsapp:has(.orion-wa-mobile-conversa) .st-key-orion_wa_lista_painel {display:none}
    .st-key-orion_whatsapp .st-key-orion_wa_voltar {display:block}
}
</style>
"""


def horario(valor, timezone=None):
    if not valor:
        return None
    data = datetime.fromisoformat(valor)
    if timezone and data.tzinfo:
        try:
            return data.astimezone(ZoneInfo(timezone))
        except ZoneInfoNotFoundError:
            pass
    return data


def _avatar(nome):
    partes = nome.split()
    iniciais = "".join(p[0] for p in partes[:2]).upper() or "?"
    return f'<div class="orion-wa-avatar" aria-hidden="true">{escape(iniciais)}</div>'


def nome_contato(conversa):
    return conversa.get("nome") or conversa.get("identificador") or "Contato sem nome"


def cartao_contato(conversa, *, lista=False, nao_lida=False):
    nome = nome_contato(conversa)
    identificador = conversa.get("identificador") or ""
    if lista:
        hora = horario(conversa.get("ultima_mensagem_em") or conversa.get("atualizado_em"))
        data = hora.strftime("%d/%m · %H:%M") if hora else ""
        previa = conversa.get("ultima_mensagem") or TIPOS_ANEXO.get(conversa.get("ultimo_tipo"), "Sem mensagens")
    else:
        data, previa = "", ""
    ponto = '<span class="orion-wa-unread" role="img" aria-label="Mensagens não lidas"></span>' if nao_lida else ""
    st.markdown(
        f'<div class="orion-wa-contact">{_avatar(nome)}<div><div class="orion-wa-name">{escape(nome)}</div>'
        f'<div class="orion-wa-muted">{escape(identificador)}</div></div>'
        f'<span class="orion-wa-time">{escape(data)}</span>{ponto}</div>'
        + (f'<div class="orion-wa-preview" title="{escape(previa, quote=True)}">{escape(previa)}</div>' if lista else ""),
        unsafe_allow_html=True,
    )


def render_balao(mensagem, data, rotulo):
    enviado = mensagem.get("from_me") is True
    autor = None
    if enviado:
        autor = {
            "agente": "Sofia",
            "humano": mensagem.get("autor_nome") or "Atendente",
        }.get(mensagem.get("remetente"))
    icone = {"Enviada": "✓", "Entregue": "✓✓", "Lida": "✓✓",
             "Falha no envio": "!", "Aguardando envio": "◷"}.get(rotulo)
    estado = f"{icone} {rotulo}" if icone else rotulo
    metadados = " · ".join(filter(None, (autor, data.strftime("%H:%M") if data else None, estado)))
    corpo = mensagem.get("texto") or TIPOS_ANEXO.get(mensagem.get("tipo"), "")
    classe = " orion-wa-enviada" if enviado else ""
    st.markdown(
        f'<div class="orion-wa-balao{classe}">{escape(corpo)}'
        f'<div class="orion-wa-meta">{escape(metadados)}</div></div>',
        unsafe_allow_html=True,
    )


def render_ficha(conversa, detalhes):
    numero, _, dominio = (conversa.get("identificador") or "").partition("@")
    campos = [
        ("Cliente", detalhes.get("cliente") or conversa.get("nome")),
        ("Empresa do cliente", detalhes.get("empresa_cliente")),
        ("Empresa no CRM", detalhes.get("empresa_crm")),
        ("Telefone", detalhes.get("telefone") or (numero if dominio == "c.us" and numero.isdigit() else None)),
        ("Temperatura", detalhes.get("temperatura")),
        ("Score", detalhes.get("score")),
        ("Serviço de interesse", detalhes.get("servico")),
        ("Responsável", conversa.get("responsavel_nome") or "Não atribuído"),
        ("Atendimento", STATUS_ATENDIMENTO.get(conversa.get("status_atendimento"), conversa.get("status_atendimento"))),
    ]
    itens = "".join(
        f"<div><span>{escape(rotulo)}</span><strong>{escape(str(valor))}</strong></div>"
        for rotulo, valor in campos if valor is not None and valor != ""
    )
    st.markdown(f'<div class="orion-wa-ficha">{itens}</div>', unsafe_allow_html=True)
    if detalhes.get("resumo_vendedor"):
        st.markdown("**Resumo comercial da Sofia**")
        st.markdown(escape(detalhes["resumo_vendedor"]), unsafe_allow_html=False)
    if detalhes.get("followup_status"):
        estado = detalhes["followup_status"].capitalize()
        st.markdown("**Follow-up Automático**")
        st.text(f"Tentativa {detalhes['followup_tentativa']} · {estado}")
        if detalhes["followup_status"] in ("pendente", "processando"):
            agendado = horario(detalhes.get("followup_agendado"), detalhes.get("timezone"))
            if agendado:
                st.caption(agendado.strftime("%d/%m/%Y às %H:%M"))
