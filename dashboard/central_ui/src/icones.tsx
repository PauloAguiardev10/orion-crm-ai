import type {ReactNode} from "react";

const caminhos: Record<string, ReactNode> = {
  enviar:<><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></>,
  microfone:<><rect x="9" y="2" width="6" height="13" rx="3"/><path d="M5 10v2a7 7 0 0 0 14 0v-2M12 19v3m-4 0h8"/></>,
  parar:<rect x="6" y="6" width="12" height="12" rx="2"/>,
  emoji:<><circle cx="12" cy="12" r="9"/><path d="M8 14c2 3 6 3 8 0M9 9h.01M15 9h.01"/></>,
  anexo:<path d="m20 11-8.1 8a5 5 0 0 1-7.1-7.1l8.5-8.5a3.5 3.5 0 0 1 5 5l-8.5 8.5a2 2 0 0 1-2.8-2.8l7.8-7.8"/>,
  nova:<><path d="M20 12v5a2 2 0 0 1-2 2H8l-5 3V6a2 2 0 0 1 2-2h7"/><path d="M18 2v8m-4-4h8"/></>,
  check:<path d="m5 12 4 4L19 6"/>,
  duplo:<path d="m2 12 4 4L16 6m-5 9 2 1 9-10"/>,
  relogio:<><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></>,
  alerta:<><circle cx="12" cy="12" r="9"/><path d="M12 7v6m0 4h.01"/></>,
  pino:<path d="m15 4 5 5-3 1-3 5-3 1-3-3 1-3 5-3 1-3ZM10 14l-6 6"/>,
};

export function Icone({nome}:{nome:string}){
  return <svg aria-hidden="true" width="19" height="19" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="1.65" strokeLinecap="round" strokeLinejoin="round">{caminhos[nome]}</svg>;
}

export function EstadoMensagem({envio,processamento,remetente}:{envio?:string|null;processamento?:string|null;remetente?:string}){
  const estados:Record<string,[string,string]> = {
    aceito_waha:["Aceita pela WAHA","relogio"],
    enviada_waha:["Enviada","check"], entregue_waha:["Entregue","duplo"],
    lida_waha:["Visualizada","duplo"], erro_waha:["Falha no envio","alerta"],
    falha_envio:["Falha no envio","alerta"], timeout_envio_inconclusivo:["Envio inconclusivo","alerta"],
  };
  const pendente = remetente==="humano" && (processamento==="recebida"||processamento==="processando");
  const estado=envio ? estados[envio] : pendente ? ["Aguardando envio","relogio"] : undefined;
  return estado ? <span className={"estado-mensagem "+(envio||"aguardando")} role="img" aria-label={estado[0]} title={estado[0]}><Icone nome={estado[1]}/></span> : null;
}
