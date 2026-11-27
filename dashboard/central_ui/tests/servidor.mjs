import { createServer } from "node:http";
import { readFile } from "node:fs/promises";

const listeners = new Set();
const ana = {id:1,nome:"Ana Martins",identificador:"5511999999999@c.us",telefone:"5511999999999",ultima_mensagem:"Pode me mandar os detalhes?",pode_assumir:true,status_atendimento:"aguardando_humano",nao_lidas:2,ultima_recebida_id:2};
const bruno = {id:2,nome:"Bruno Lima",identificador:"5511888888888@c.us",ultima_mensagem:"Obrigado pelo retorno",pode_assumir:true};
const mensagens = Array.from({length:36},(_,i)=>({id:i+1,texto:"Mensagem fictícia "+(i+1)+" para validar a rolagem.", criado_em:"2026-11-29T12:00:00Z", from_me:i%2===1, remetente:i%2===0?"cliente":"humano"}));
for(const [id,estado] of [[2,null],[4,"aceito_waha"],[6,"enviada_waha"],[8,"entregue_waha"],[10,"lida_waha"],[12,"falha_envio"]]){
  Object.assign(mensagens[id-1],{status_envio:estado,status_processamento:id===2?"recebida":"concluida"});
}
mensagens.push({id:80,texto:"Áudio de teste",criado_em:"2026-11-29T11:50:00Z",tem_anexo:true,midia_tipo:"audio/wav",from_me:false});
mensagens.push(
  {id:81,texto:"Imagem de teste",criado_em:"2026-11-29T11:51:00Z",tem_anexo:true,midia_tipo:"image/png",from_me:false},
  {id:82,texto:"Vídeo de teste",criado_em:"2026-11-29T11:52:00Z",tem_anexo:true,midia_tipo:"video/mp4",from_me:false},
);
function wav(){
  const tamanho=16000,b=Buffer.alloc(44+tamanho);
  b.write("RIFF");b.writeUInt32LE(tamanho+36,4);b.write("WAVEfmt ",8);
  b.writeUInt32LE(16,16);b.writeUInt16LE(1,20);b.writeUInt16LE(1,22);
  b.writeUInt32LE(8000,24);b.writeUInt32LE(16000,28);b.writeUInt16LE(2,32);b.writeUInt16LE(16,34);
  b.write("data",36);b.writeUInt32LE(tamanho,40);
  return b;
}
const delta = (alteradas, ordem=alteradas.map(item=>item.id)) => ({alteradas,ordem,removidas:[]});
const evento = (resp, dados) => resp.write("event: dados\ndata: "+JSON.stringify(dados)+"\n\n");

createServer(async (req,res)=>{
  const url=new URL(req.url,"http://127.0.0.1");
  const {pathname}=url;
  if(pathname==="/"){
    res.setHeader("Content-Type","text/html; charset=utf-8");
    return res.end(`<!doctype html><html><body style="margin:0"><iframe title="Central" style="width:100vw;height:100vh;border:0" src="/central-ui/"></iframe><script>
      addEventListener("message",e=>{if(e.data.type==="streamlit:componentReady")e.source.postMessage({type:"streamlit:render",args:{token:"simulado",usuario:10,empresa:1}},location.origin)});
    </script></body></html>`);
  }
  if(pathname==="/__evento"||pathname==="/__reconectar"){
    const mensagem={id:mensagens.length+1,texto:`Evento simulado ${mensagens.length+1}`,criado_em:"2026-11-29T12:01:00Z",remetente:"cliente",from_me:false};
    mensagens.push(mensagem);ana.ultima_mensagem=mensagem.texto;
    for(const cliente of listeners) {
      if(pathname==="/__reconectar") cliente.end();
      else evento(cliente,{mensagens:delta([mensagem],mensagens.map(m=>m.id)),conversas:delta([ana],[1,2])});
    }
    return res.end(mensagem.texto);
  }
  if(pathname.startsWith("/central-ui/")){
    const nome=pathname.slice("/central-ui/".length) || "index.html";
    if(nome.includes("..")){res.statusCode=404;return res.end();}
    const tipos={html:"text/html",css:"text/css",js:"text/javascript",png:"image/png"};
    res.setHeader("Content-Type",tipos[nome.split(".").pop()]||"application/octet-stream");
    try{return res.end(await readFile(new URL("../dist/"+nome,import.meta.url)));}catch{res.statusCode=404;return res.end();}
  }
  if(req.headers.authorization!=="Bearer simulado"||url.searchParams.get("empresa_id")!=="1"){
    res.statusCode=401;res.setHeader("Content-Type","application/json");return res.end('{"detail":"Acesso negado"}');
  }
  if(pathname.endsWith("/mensagens/81/anexo")){
    res.setHeader("Content-Type","image/png");
    return res.end(Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aT8sAAAAASUVORK5CYII=","base64"));
  }
  if(pathname.endsWith("/mensagens/82/anexo")){
    res.setHeader("Content-Type","video/mp4");
    return res.end(await readFile(new URL("./video-ficticio.mp4",import.meta.url)));
  }
  if(pathname.endsWith("/mensagens/80/anexo")){res.setHeader("Content-Type","audio/wav");return res.end(wav());}
  if(pathname.endsWith("/eventos")){
    const chat=url.searchParams.get("conversa_id");
    res.writeHead(200,{"Content-Type":"text/event-stream","Cache-Control":"no-store"});
    listeners.add(res);res.on("close",()=>listeners.delete(res));
    evento(res,{conversas:delta([ana,bruno]),mensagens:chat?delta(chat==="1"?mensagens:[]):null});
    return;
  }
  res.setHeader("Content-Type","application/json");
  if(pathname.endsWith("/conversas/iniciar")) return res.end(JSON.stringify([{id:1,nome:"Comercial"}]));
  if(pathname.endsWith("/contexto-ui")) return res.end(JSON.stringify({timezone:"America/Fortaleza"}));
  if(pathname.endsWith("/detalhes")) return res.end(JSON.stringify({telefone:"5511999999999",empresa_cliente:"Empresa fictícia",temperatura:"Morna",resumo_vendedor:"Solicitou detalhes da proposta.",followup_status:"Pendente"}));
  if(pathname.endsWith("/contatos")) return res.end(JSON.stringify({contatos:[{id:"5511999999999@c.us",nome:"Ana Martins",telefone:"5511999999999"}],proxima:null}));
  if(pathname.endsWith("/reservar-anexo")){
    const partes=[];
    for await(const parte of req) partes.push(parte);
    if(!Buffer.concat(partes).includes('filename="documento.pdf"')){
      res.statusCode=400;return res.end('{"detail":"Anexo ausente no transporte de teste"}');
    }
    return res.end(JSON.stringify({mensagem_id:91}));
  }
  if(pathname.endsWith("/reservar-mensagem")) return res.end(JSON.stringify({mensagem_id:90}));
  if(pathname.endsWith("/executar-mensagem")) return res.end(JSON.stringify({sucesso:true,situacao:"enviado"}));
  if(pathname.endsWith("/leitura")) return res.end(JSON.stringify({ultima_lida_id:2}));
  res.statusCode=404;res.end('{"detail":"Indisponível"}');
}).listen(48319,"127.0.0.1");
