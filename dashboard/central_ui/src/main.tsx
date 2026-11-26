import {useEffect, useLayoutEffect, useRef, useState} from "react";
import {createRoot} from "react-dom/client";
import {aplicar, consumir, ErroApi, json, request, type Auth, type Delta} from "./api";
import logo from "../../assets/logo_orion.png";
import "./style.css";
import {EstadoMensagem, Icone} from "./icones";

type Chat = {id:number; nome?:string; telefone?:string; identificador:string; ultima_mensagem?:string; atualizado_em?:string; ultima_recebida_id?:number; ultima_lida_id?:number; nao_lidas?:number; central_arquivada?:boolean; digitando?:boolean; pode_assumir?:boolean; pode_supervisionar?:boolean; sofia_institucional?:boolean; operacao_suspensa?:boolean; humano_assumiu?:boolean; especialista_id?:number; responsavel_nome?:string; conexao_canal_id?:number; status_atendimento?:string};
type Mensagem = {id:number; texto?:string; autor_nome?:string; remetente?:string; criado_em?:string; from_me?:boolean; status_envio?:string; status_processamento?:string; participante?:string; tipo?:string; central_eventos?:Record<string,{texto?:string}>; tem_anexo?:boolean; midia_tipo?:string};
type Contato = {id:string; nome?:string; telefone?:string};
type Conexao = {id:number; nome:string};
type Detalhes = Record<string, string|number|null>;
const emojis = ["😀","🙂","👍","🙏","❤️","🎉","✅","👋","😊","🙌","🤝","📎"];
const nome = (c: Chat) => c.nome || c.telefone || (c.identificador.endsWith("@c.us") ? c.identificador.split("@")[0] : "Contato WhatsApp");
const hora = (data?:string) => data && !Number.isNaN(Date.parse(data)) ? new Date(data).toLocaleTimeString("pt-BR",{hour:"2-digit",minute:"2-digit"}) : "";
const dia = (data?:string) => data && !Number.isNaN(Date.parse(data))
  ? new Intl.DateTimeFormat("pt-BR",{dateStyle:"long"}).format(new Date(data)) : "";
const atendimento:Record<string,string> = {aguardando_humano:"Aguardando atendimento",em_atendimento_humano:"Em atendimento",em_atendimento_ia:"Atendimento pela Sofia",finalizado:"Encerrado"};
const post = (body: unknown): RequestInit => ({method:"POST", body:JSON.stringify(body)});

function Anexo({auth, chat, mensagem}: {auth:Auth;chat:number;mensagem:Mensagem}) {
  const [url,setUrl]=useState("");
  const origem=useRef("");
  useEffect(()=>()=>{ if(origem.current) URL.revokeObjectURL(origem.current); },[]);
  const [erro,setErro]=useState(false);
  if (!url) return <button onClick={async()=>{
    try {
      const blob=await (await request(auth,`/conversas/${chat}/mensagens/${mensagem.id}/anexo`)).blob();
      origem.current=URL.createObjectURL(blob); setUrl(origem.current);
    } catch {setErro(true);}
  }}>{erro ? "Tentar carregar anexo" : "Abrir anexo"}</button>;
  if(mensagem.midia_tipo?.startsWith("image/")) return <img src={url} alt="Imagem da conversa"/>;
  if(mensagem.midia_tipo?.startsWith("video/")) return <video src={url} controls/>;
  if(mensagem.midia_tipo?.startsWith("audio/")) return <audio src={url} controls/>;
  return <a href={url} download={`documento-${mensagem.id}.pdf`}>Baixar documento</a>;
}

function FotoContato({auth,conexao,contato}:{auth:Auth;conexao:number;contato:Contato}){
  const [foto,setFoto]=useState("");
  const [erro,setErro]=useState(false);
  const abortar=useRef(new AbortController());
  const atual=useRef("");
  useEffect(()=>()=>{abortar.current.abort();if(atual.current)URL.revokeObjectURL(atual.current);},[]);
  if(foto) return <img className="foto-contato" alt="Foto do contato" src={foto}/>;
  return <button aria-label={"Ver foto de "+(contato.nome||"contato")} onClick={async()=>{
    const ctrl=abortar.current;
    try{
      const resposta=await request(auth,"/conexoes/"+conexao+"/contatos/foto?chat="+encodeURIComponent(contato.id),{signal:ctrl.signal});
      const blob=await resposta.blob();
      if(!ctrl.signal.aborted){
        if(atual.current)URL.revokeObjectURL(atual.current);
        atual.current=URL.createObjectURL(blob);setFoto(atual.current);
      }
    }catch{if(!ctrl.signal.aborted)setErro(true);}
  }}>{erro?"Sem foto":"Foto"}</button>;
}

function Central({auth}:{auth:Auth}) {
  const escopo=`orion.central.${auth.usuario}.${auth.empresa ?? "propria"}`;
  const [selecionada,selecionar]=useState<number|null>(()=>Number(sessionStorage.getItem(escopo+".chat"))||null);
  const [fixadas,setFixadas]=useState<number[]>(()=>{
    try {
      const valor=JSON.parse(localStorage.getItem(escopo+".fixadas")||"[]");
      return Array.isArray(valor)?valor.filter((id:unknown)=>typeof id==="number"):[];
    } catch { return []; }
  });
  const [lista,setLista]=useState<Chat[]>([]);
  const [mensagens,setMensagens]=useState<Mensagem[]>([]);
  const [anteriores,setAnteriores]=useState<Mensagem[]>([]);
  const [online,setOnline]=useState(false);
  const [erro,setErro]=useState("");
  const [busca,setBusca]=useState("");
  const [verArquivo,setVerArquivo]=useState(false);
  const [presencaHabilitada,setPresencaHabilitada]=useState(false);
  const [arquivoHabilitado,setArquivoHabilitado]=useState(false);
  const [filtro,setFiltro]=useState("");
  const [painel,setPainel]=useState(false);
  const [detalhes,setDetalhes]=useState<Detalhes>({});
  const [foto,setFoto]=useState("");
  const [atendentes,setAtendentes]=useState<Conexao[]>([]);
  const [destino,setDestino]=useState(0);
  const [nova,setNova]=useState(false);
  const [conexoes,setConexoes]=useState<Conexao[]>([]);
  const [conexao,setConexao]=useState(0);
  const [telefone,setTelefone]=useState("");
  const [contatos,setContatos]=useState<Contato[]>([]);
  const [pagina,setPagina]=useState<number|null>(0);
  const [buscaContato,setBuscaContato]=useState("");
  const [encaminhar,setEncaminhar]=useState<Mensagem|null>(null);
  const [encaminharDestino,setEncaminharDestino]=useState(0);
  const [citacao,setCitacao]=useState<Mensagem|null>(null);
  const [emoji,setEmoji]=useState(false);
  const [acoesHabilitadas,setAcoesHabilitadas]=useState(false);
  const [menu,setMenu]=useState<number|null>(null);
  const [edicao,setEdicao]=useState<string|null>(null);
  const [arquivo,setArquivo]=useState<File|null>(null);
  const [gravando,setGravando]=useState(false);
  const [enviando,setEnviando]=useState(false);
  const envioEmCurso=useRef(false);
  const [rascunhos,setRascunhos]=useState<Record<number,string>>(()=>JSON.parse(sessionStorage.getItem(escopo+".rascunhos")||"{}"));
  const historico=useRef<HTMLDivElement>(null);
  const entrada=useRef<HTMLTextAreaElement>(null);
  const arquivoInput=useRef<HTMLInputElement>(null);
  const gravador=useRef<MediaRecorder|null>(null);
  const trilhas=useRef<MediaStream|null>(null);
  const posicao=useRef<{chat:number|null;top:number;fundo:boolean}>({chat:null,top:0,fundo:true});
  const chat=lista.find(c=>c.id===selecionada);
  const rascunho=selecionada ? rascunhos[selecionada]||"" : "";
  const mensagensVisiveis=[...new Map([...anteriores,...mensagens].map(m=>[m.id,m])).values()]
    .sort((a,b)=>(a.criado_em||"").localeCompare(b.criado_em||"")||a.id-b.id);

  useEffect(()=>{
    const ctrl=new AbortController();
    void json<{acoes_mensagem:boolean;arquivo:boolean;presenca:boolean}>(auth,"/capacidades",{signal:ctrl.signal})
      .then(v=>{if(!ctrl.signal.aborted){setAcoesHabilitadas(v.acoes_mensagem);setArquivoHabilitado(v.arquivo);setPresencaHabilitada(v.presenca);}}).catch(()=>undefined);
    return ()=>ctrl.abort();
  },[auth]);
  useEffect(()=>{
    if(!presencaHabilitada||!selecionada) return;
    const ctrl=new AbortController();
    void json(auth,"/conversas/"+selecionada+"/presenca",{method:"POST",signal:ctrl.signal}).catch(()=>undefined);
    return ()=>ctrl.abort();
  },[auth,presencaHabilitada,selecionada]);
  useEffect(()=>{try{localStorage.setItem(escopo+".fixadas",JSON.stringify(fixadas));}catch{/* armazenamento bloqueado */}},[escopo,fixadas]);
  useEffect(()=>{sessionStorage.setItem(escopo+".rascunhos",JSON.stringify(rascunhos));},[escopo,rascunhos]);
  useEffect(()=>()=>{trilhas.current?.getTracks().forEach(t=>t.stop());},[]);
  useEffect(()=>{
    const abortar=new AbortController();
    let ativo=true, espera=600, timer:number|undefined, expirou=false;
    const acompanhar=async()=>{
      while(ativo&&!expirou){
        try {
          const resposta=await request(auth,`/eventos${selecionada?`?conversa_id=${selecionada}`:""}`,{signal:abortar.signal});
          if(!ativo) return;
          setOnline(true); espera=600;
          await consumir(resposta,(tipo, bruto)=>{
            if(!ativo) return;
            if(tipo==="sessao"){expirou=true; setLista([]); setMensagens([]); setAnteriores([]); setErro("Sessão expirada. Entre novamente."); return;}
            const dados=JSON.parse(bruto) as {conversas?:Delta<Chat>;mensagens?:Delta<Mensagem>|null};
            if(dados.conversas) setLista(a=>aplicar(a,dados.conversas!));
            if(dados.mensagens){
              const el=historico.current;
              if(el&&posicao.current.chat===selecionada){
                posicao.current={chat:selecionada,top:el.scrollTop,
                  fundo:el.scrollHeight-el.scrollTop-el.clientHeight<35};
              }
              setMensagens(a=>aplicar(a,dados.mensagens!));
            }
            else if(dados.mensagens===null){setMensagens([]);setAnteriores([]);}
          });
        } catch(e) {if(ativo && e instanceof ErroApi && [401,403].includes(e.status)){expirou=true;setLista([]);setMensagens([]);setAnteriores([]);setErro("Sessão expirada. Entre novamente.");}}
        if(!ativo||expirou) break;
        setOnline(false);
        await new Promise<void>(resolver=>{timer=window.setTimeout(resolver,espera);});
        espera=Math.min(8000,espera*2);
      }
      if(ativo) setOnline(false);
    };
    void acompanhar();
    return ()=>{ativo=false;abortar.abort();clearTimeout(timer);};
  },[auth,selecionada]);
  useLayoutEffect(()=>{
    const el=historico.current;
    if(!el||!selecionada||!mensagensVisiveis.length) return;
    if(posicao.current.chat!==selecionada){
      const salva=sessionStorage.getItem(`${escopo}.scroll.${selecionada}`);
      el.scrollTop=salva===null ? el.scrollHeight : Number(salva);
      posicao.current={chat:selecionada,top:el.scrollTop,fundo:el.scrollHeight-el.scrollTop-el.clientHeight<35};
    } else el.scrollTop=posicao.current.fundo ? el.scrollHeight : posicao.current.top;
  },[mensagens,anteriores,selecionada,escopo,chat?.id]);
  useEffect(()=>{
    if(!selecionada) return;
    const ultima=mensagens.filter(m=>!m.from_me&&m.remetente==="cliente").reduce((max,m)=>Math.max(max,m.id),0);
    if(ultima && ultima>(chat?.ultima_lida_id||0)) void json(auth,`/conversas/${selecionada}/leitura`,post({mensagem_id:ultima})).catch(()=>undefined);
  },[auth,selecionada,mensagens,chat?.ultima_lida_id]);
  useEffect(()=>{
    if(!painel||!selecionada) return;
    const abortar=new AbortController(); let url="";
    setDetalhes({});setFoto("");setAtendentes([]);setDestino(0);
    void json<Conexao[]>(auth,"/atendentes",{signal:abortar.signal}).then(v=>{if(!abortar.signal.aborted)setAtendentes(v);}).catch(()=>undefined);
    void json<Detalhes>(auth,`/conversas/${selecionada}/detalhes`,{signal:abortar.signal}).then(v=>{if(!abortar.signal.aborted)setDetalhes(v);}).catch(()=>undefined);
    void request(auth,`/conversas/${selecionada}/foto`,{signal:abortar.signal}).then(r=>r.blob()).then(b=>{if(!abortar.signal.aborted){url=URL.createObjectURL(b);setFoto(url);}}).catch(()=>undefined);
    return ()=>{abortar.abort();if(url)URL.revokeObjectURL(url);};
  },[auth,painel,selecionada]);

  function abrir(id:number|null){
    if(selecionada===id) return;
    if(enviando||gravando) return;
    setErro(""); setEncaminhar(null); setEncaminharDestino(0); setCitacao(null); setMensagens([]);setAnteriores([]);setArquivo(null);setFoto("");setDetalhes({});
    selecionar(id);
    if(id) sessionStorage.setItem(escopo+".chat",String(id));
    else sessionStorage.removeItem(escopo+".chat");
  }
  async function contatosPagina(inicio:number){
    if(!conexao) return;
    try{
      const r=await json<{contatos:Contato[];proxima:number|null}>(auth,`/conexoes/${conexao}/contatos?deslocamento=${inicio}&busca=${encodeURIComponent(buscaContato)}`);
      setContatos(a=>inicio ? [...new Map([...a,...r.contatos].map(c=>[c.id,c])).values()] : r.contatos);
      setPagina(r.proxima);
    }catch(e){setErro(String(e));}
  }
  async function iniciar(){
    try {const r=await json<{id:number}>(auth,"/conversas/iniciar",post({conexao_id:conexao,telefone}));abrir(r.id);setNova(false);}
    catch(e){setErro(String(e));}
  }
  async function gravar(){
    if(gravando){gravador.current?.stop(); return;}
    try{
      const stream=await navigator.mediaDevices.getUserMedia({audio:true});
      trilhas.current=stream;
      const recorder=new MediaRecorder(stream);gravador.current=recorder;
      const dados:Blob[]=[];
      recorder.ondataavailable=e=>dados.push(e.data);
      recorder.onstop=()=>{
        stream.getTracks().forEach(t=>t.stop());setGravando(false);
        const tipo=recorder.mimeType.split(";")[0];
        if(!["audio/webm","audio/ogg","audio/wav"].includes(tipo)){setErro("Formato de gravação indisponível neste navegador.");return;}
        const extensao=tipo.split("/")[1];
        setArquivo(new File(dados,`gravacao.${extensao}`,{type:tipo}));
      };
      recorder.start();setGravando(true);
    }catch{setErro("Microfone indisponível.");}
  }
  async function acaoMensagem(id:number, acao:"reagir"|"editar"|"excluir", valor=""){
    if(!chat) return;
    setMenu(null);setEdicao(null);
    try{
      await json(auth,"/conversas/"+chat.id+"/mensagens/"+id+"/acao",post({acao,valor}));
      if(acao==="reagir") setErro("Reação confirmada pela WAHA.");
    }catch(e){setErro(String(e));}
  }
  async function encaminharMensagem(){
    if(!chat||!encaminhar||!encaminharDestino||envioEmCurso.current) return;
    envioEmCurso.current=true;setEnviando(true);
    try{
      const dados={conversa_id:encaminharDestino,encaminhar_conversa_id:chat.id,
        responder_mensagem_id:encaminhar.id,texto:"Mensagem encaminhada",chave_solicitacao:crypto.randomUUID()};
      const r=await json<{mensagem_id:number}>(auth,"/reservar-mensagem",post(dados));
      const status=await json<{sucesso:boolean;situacao:string}>(auth,"/executar-mensagem",
        post({conversa_id:encaminharDestino,mensagem_id:r.mensagem_id}));
      if(!status.sucesso)throw new Error(status.situacao);
      setEncaminhar(null);setEncaminharDestino(0);
    }catch(e){setErro(String(e));}
    finally{envioEmCurso.current=false;setEnviando(false);}
  }
  async function enviar(){
    if(!chat||envioEmCurso.current||(!rascunho.trim()&&!arquivo)) return;
    if(arquivo&&citacao){setErro("Envie a resposta citada como texto ou remova a citação.");return;}
    if(arquivo&&arquivo.size>8*1024*1024){setErro("O anexo excede 8 MB.");return;}
    envioEmCurso.current=true;setEnviando(true);setErro("");
    try {
      const chave=crypto.randomUUID();
      let reserva:{mensagem_id:number};
      if(arquivo){
        const form=new FormData();
        form.set("conversa_id",String(chat.id));form.set("legenda",rascunho);form.set("chave_solicitacao",chave);
        form.set("gravacao",String(arquivo.name.startsWith("gravacao.")));form.set("arquivo",arquivo);
        reserva=await json(auth,"/reservar-anexo",{method:"POST",body:form});
      } else reserva=await json(auth,"/reservar-mensagem",post({conversa_id:chat.id,texto:rascunho,chave_solicitacao:chave,responder_mensagem_id:citacao?.id}));
      const resultado=await json<{sucesso:boolean;situacao:string}>(auth,"/executar-mensagem",post({conversa_id:chat.id,mensagem_id:reserva.mensagem_id}));
      if(!resultado.sucesso) throw new Error(resultado.situacao.includes("inconclusivo") ? "Envio inconclusivo. Consulte o histórico antes de tentar novamente." : resultado.situacao);
      setRascunhos(a=>a[chat.id]===rascunho?{...a,[chat.id]:""}:a);setArquivo(null);setCitacao(null);
    }catch(e){setErro(String(e));}
    finally{envioEmCurso.current=false;setEnviando(false);}
  }

  return <main className={`central ${chat?"aberta":""} ${painel?"com-ficha":""}`}>
    <nav className="barra" aria-label="Central"><img src={logo} alt="Orion Systems"/><span className={online?"online":"offline"}>{online?"Ao vivo":"Reconectando"}</span></nav>
    <aside className="lista">
      <header><h1>Conversas</h1><button onClick={async()=>{
        setNova(v=>!v);
        if(!nova) try{setConexoes(await json(auth,"/conversas/iniciar"));}catch(e){setErro(String(e));}
      }}><Icone nome="nova"/> Nova conversa</button></header>
      <input aria-label="Pesquisar conversas" placeholder="Pesquisar nome ou telefone" value={busca} onChange={e=>setBusca(e.target.value)}/>
      <select aria-label="Filtrar atendimentos" value={filtro} onChange={e=>setFiltro(e.target.value)}>
        <option value="">Todos os atendimentos</option><option value="em_atendimento_humano">Em atendimento</option><option value="aguardando_humano">Aguardando</option><option value="finalizado">Encerrados</option>
      </select>
      {arquivoHabilitado&&<button aria-pressed={verArquivo} onClick={()=>setVerArquivo(v=>!v)}>{verArquivo?"Mostrar ativas":"Mostrar arquivadas"}</button>}
      {nova&&<section className="nova">
        <select aria-label="Conexão" value={conexao} onChange={e=>{setConexao(Number(e.target.value));setContatos([]);setPagina(0);}}><option value="0">Escolher conexão</option>{conexoes.map(c=><option key={c.id} value={c.id}>{c.nome}</option>)}</select>
        <input aria-label="Telefone com DDI" placeholder="+55…" value={telefone} onChange={e=>setTelefone(e.target.value)}/>
        <div className="acoes"><button disabled={!conexao||!telefone} onClick={iniciar}>Abrir atendimento</button><button disabled={!conexao||pagina===null} onClick={()=>void contatosPagina(pagina||0)}>{pagina?"Carregar mais":"Consultar contatos"}</button></div>
        <div className="acoes"><input aria-label="Pesquisar contatos" placeholder="Pesquisar na conexão" value={buscaContato} onChange={e=>{setBuscaContato(e.target.value);setContatos([]);setPagina(0);}}/><button disabled={!conexao} onClick={()=>void contatosPagina(0)}>Pesquisar</button></div>
        {contatos.map(c=><div className="linha-contato" key={conexao+":"+c.id}>
          <FotoContato auth={auth} conexao={conexao} contato={c}/>
          <button className="contato" disabled={!c.telefone} onClick={()=>c.telefone&&setTelefone("+"+c.telefone)}>{c.nome||"Contato"} · {c.telefone||"Telefone indisponível"}</button>
        </div>)}
      </section>}
      <div className="linhas">
      {[...lista].sort((a,b)=>Number(fixadas.includes(b.id))-Number(fixadas.includes(a.id))).filter(c=>(!arquivoHabilitado||Boolean(c.central_arquivada)===verArquivo)&&(!filtro||c.status_atendimento===filtro)&&`${nome(c)} ${c.telefone||""}`.toLowerCase().includes(busca.toLowerCase())).map(c=>
        <button className={`linha ${selecionada===c.id?"selecionada":""}`} key={c.id} onClick={()=>abrir(c.id)}>
          <span className="avatar">{nome(c).slice(0,2).toUpperCase()}</span><span className="resumo"><strong>{fixadas.includes(c.id)&&<span className="pin" title="Fixada neste navegador"><Icone nome="pino"/></span>}{nome(c)}</strong><small>{c.ultima_mensagem||"Conversa WhatsApp"}</small></span>
          <span className="linha-meta">{hora(c.atualizado_em)}{(c.ultima_recebida_id||0)>(c.ultima_lida_id||0)&&<b aria-label="Mensagens não lidas">{c.nao_lidas||"●"}</b>}</span>
        </button>)}
      </div>
    </aside>
    <section className="chat">
      {erro&&<div className="alerta" role="status">{erro}<button aria-label="Dispensar aviso" onClick={()=>setErro("")}>×</button></div>}
      {!chat?<div className="vazio"><img src={logo} alt="Orion Systems"/><p>Selecione uma conversa para começar.</p></div>:<>
        <header><button className="voltar" onClick={()=>abrir(null)}>Voltar</button><div><strong>{nome(chat)}</strong><small>{chat.digitando?"Digitando…":chat.telefone||chat.responsavel_nome||""}</small></div><button className="fixar-chat" aria-label={fixadas.includes(chat.id)?"Desafixar neste navegador":"Fixar neste navegador"} title="Preferência interna deste navegador" aria-pressed={fixadas.includes(chat.id)} onClick={()=>setFixadas(a=>a.includes(chat.id)?a.filter(id=>id!==chat.id):[...a,chat.id])}><Icone nome="pino"/></button><button aria-expanded={painel} onClick={()=>setPainel(p=>!p)}>Informações</button></header>
        <div className="historico" ref={historico} onScroll={e=>{
          const el=e.currentTarget;posicao.current={chat:chat.id,top:el.scrollTop,fundo:el.scrollHeight-el.scrollTop-el.clientHeight<35};
          sessionStorage.setItem(`${escopo}.scroll.${chat.id}`,String(el.scrollTop));
        }}>
          {mensagensVisiveis.length>0&&<button className="anteriores" onClick={async()=>{
            try{const antigos=await json<Mensagem[]>(auth,`/conversas/${chat.id}/mensagens?limite=50&antes_id=${mensagensVisiveis[0].id}`);setAnteriores(a=>[...antigos,...a]);}catch(e){setErro(String(e));}
          }}>Carregar mensagens anteriores</button>}
          {mensagensVisiveis.map((m,i)=><div className="linha-mensagem" key={m.id}>
            {dia(m.criado_em)&&dia(m.criado_em)!==dia(mensagensVisiveis[i-1]?.criado_em)&&<div className="data-mensagem">{dia(m.criado_em)}</div>}
            <article className={m.from_me?"enviada":"recebida"}>
            {(m.autor_nome||m.remetente==="sofia")&&<strong>{m.autor_nome||"Sofia"}</strong>}
            {m.participante&&<strong className="participante">{m.participante}</strong>}
            {m.texto&&<p>{m.texto}</p>}
            {m.tipo!=="excluida"&&["reacao_cliente","reacao_conta"].map(k=>m.central_eventos?.[k]?.texto&&<span key={k} className="reacao">{m.central_eventos[k].texto}</span>)}
            {m.tem_anexo&&<Anexo auth={auth} chat={chat.id} mensagem={m}/>}
            {acoesHabilitadas&&chat.humano_assumiu&&chat.pode_assumir&&!chat.sofia_institucional&&m.tipo!=="excluida"&&<div className="acoes-mensagem">
              <button aria-label="Ações da mensagem" aria-expanded={menu===m.id} onClick={()=>{setMenu(menu===m.id?null:m.id);setEdicao(null);}}>⋯</button>
              {menu===m.id&&<div className="acoes">
                {["👍","❤️","😂","😮","😢","🙏"].map(reacao=><button key={reacao} onClick={()=>void acaoMensagem(m.id,"reagir",reacao)}>{reacao}</button>)}
                <button onClick={()=>void acaoMensagem(m.id,"reagir")}>Remover reação</button>
                {m.from_me&&m.remetente==="humano"&&<><button onClick={()=>{if(window.confirm("Excluir esta mensagem no WhatsApp?"))void acaoMensagem(m.id,"excluir");}}>Excluir</button>
                {!m.tem_anexo&&<button onClick={()=>setEdicao(m.texto||"")}>Editar</button>}</>}
                {edicao!==null&&<><textarea aria-label="Editar mensagem" maxLength={4096} value={edicao} onChange={e=>setEdicao(e.target.value)}/><button disabled={!edicao.trim()} onClick={()=>void acaoMensagem(m.id,"editar",edicao)}>Salvar</button></>}
              </div>}
            </div>}
            {m.tipo!=="excluida"&&chat.pode_assumir&&!chat.sofia_institucional&&!chat.operacao_suspensa&&<button className="responder" onClick={()=>{setCitacao(m);entrada.current?.focus();}}>Responder</button>}
            {m.tipo!=="excluida"&&chat.humano_assumiu&&chat.pode_assumir&&!chat.sofia_institucional&&<button onClick={()=>{setEncaminhar(m);setEncaminharDestino(0);}}>Encaminhar</button>}
            <small className="meta-mensagem">{hora(m.criado_em)} {m.from_me&&<EstadoMensagem envio={m.status_envio} processamento={m.status_processamento} remetente={m.remetente}/>}</small>
          </article></div>)}
        </div>
        {encaminhar&&<div className="compositor">
          <select aria-label="Destino do encaminhamento" value={encaminharDestino} onChange={e=>setEncaminharDestino(Number(e.target.value))}>
            <option value="0">Escolher conversa da mesma conexão</option>
            {lista.filter(c=>c.id!==chat.id&&c.conexao_canal_id===chat.conexao_canal_id&&c.pode_assumir&&!c.operacao_suspensa&&!c.sofia_institucional&&c.status_atendimento!=="finalizado")
              .map(c=><option value={c.id} key={c.id}>{nome(c)}</option>)}
          </select>
          <button disabled={!encaminharDestino||enviando} onClick={()=>void encaminharMensagem()}>Confirmar encaminhamento</button>
          <button onClick={()=>setEncaminhar(null)}>Cancelar</button>
        </div>}
        {chat.pode_assumir&&!chat.sofia_institucional&&!chat.operacao_suspensa&&chat.status_atendimento!=="finalizado"&&<form className="compositor" onSubmit={e=>{e.preventDefault();void enviar();}}>
          {emoji&&<div className="emojis" aria-label="Selecionar emoji">{emojis.map(item=><button type="button" key={item} onClick={()=>{
            const inicio=entrada.current?.selectionStart??rascunho.length,fim=entrada.current?.selectionEnd??inicio;
            setRascunhos(a=>({...a,[chat.id]:rascunho.slice(0,inicio)+item+rascunho.slice(fim)}));
            setEmoji(false);requestAnimationFrame(()=>{entrada.current?.focus();entrada.current?.setSelectionRange(inicio+item.length,inicio+item.length);});
          }}>{item}</button>)}</div>}
          {citacao&&<div className="arquivo"><span>Resposta a: {citacao.texto||"Mensagem"}</span><button type="button" onClick={()=>setCitacao(null)}>Remover citação</button></div>}
          {arquivo&&<div className="arquivo">{arquivo.name}<button type="button" onClick={()=>setArquivo(null)}>Remover</button></div>}
          <button type="button" aria-label="Emojis" onClick={()=>setEmoji(v=>!v)}><Icone nome="emoji"/></button>
          <button type="button" aria-label="Anexar arquivo" onClick={()=>arquivoInput.current?.click()}><Icone nome="anexo"/></button>
          <input hidden ref={arquivoInput} type="file" accept=".jpg,.jpeg,.png,.webp,.ogg,.opus,.mp4,.pdf" onChange={e=>{setArquivo(e.target.files?.[0]||null);e.target.value="";}}/>
          <textarea ref={entrada} rows={1} aria-label="Mensagem" placeholder="Digite uma mensagem" maxLength={4096} value={rascunho} onChange={e=>setRascunhos(a=>({...a,[chat.id]:e.target.value}))}/>
          <button type="button" aria-label={gravando?"Parar gravação":"Gravar áudio"} onClick={gravar}><Icone nome={gravando?"parar":"microfone"}/></button>
          <button className="enviar" disabled={enviando||gravando||(!rascunho.trim()&&!arquivo)}><Icone nome="enviar"/> Enviar</button>
        </form>}
      </>}
    </section>
    {chat&&painel&&<aside className="ficha"><header><strong>Informações</strong><button aria-label="Fechar informações" onClick={()=>setPainel(false)}>×</button></header>
      {arquivoHabilitado&&chat.humano_assumiu&&chat.pode_assumir&&!chat.sofia_institucional&&<button onClick={async()=>{
        try{await json(auth,"/conversas/"+chat.id+"/arquivar",post({arquivada:!chat.central_arquivada}));}
        catch(e){setErro(String(e));}
      }}>{chat.central_arquivada?"Desarquivar":"Arquivar"}</button>}
      {foto&&<img src={foto} alt="Foto do contato"/>}<h2>{nome(chat)}</h2>
      {Object.entries({telefone:detalhes.telefone,empresa:detalhes.empresa_cliente,responsavel:chat.responsavel_nome,atendimento:atendimento[chat.status_atendimento||""]||chat.status_atendimento,temperatura:detalhes.temperatura,resumo:detalhes.resumo_vendedor,follow_up:detalhes.followup_status}).filter(([,v])=>v!=null).map(([k,v])=><p key={k}><small>{k.replaceAll("_"," ")}</small>{v}</p>)}
      {chat.humano_assumiu&&chat.especialista_id&&chat.status_atendimento!=="finalizado"&&(chat.pode_assumir||chat.pode_supervisionar)&&<button onClick={async()=>{
        try{await json(auth,"/encerrar-atendimento",post({conversa_id:chat.id,responsavel_atual_id:chat.especialista_id}));}catch(e){setErro(String(e));}
      }}>Encerrar atendimento</button>}
      {chat.pode_supervisionar&&chat.humano_assumiu&&chat.especialista_id&&chat.status_atendimento!=="finalizado"&&<div className="acoes">
        <select aria-label="Novo responsável" value={destino} onChange={e=>setDestino(Number(e.target.value))}><option value={0}>Selecionar atendente</option>{atendentes.filter(a=>a.id!==chat.especialista_id).map(a=><option value={a.id} key={a.id}>{a.nome}</option>)}</select>
        <button disabled={!destino} onClick={async()=>{try{await json(auth,"/transferir-atendimento",post({conversa_id:chat.id,responsavel_atual_id:chat.especialista_id,destino_id:destino}));setDestino(0);}catch(e){setErro(String(e));}}}>Transferir</button>
      </div>}
    </aside>}
  </main>;
}
function Integracao(){
  const [auth,setAuth]=useState<Auth|null>(null);
  useEffect(()=>{
    const enviar=(type:string, campos:object={})=>parent.postMessage({isStreamlitMessage:true,type,...campos},"*");
    const receber=(evento:MessageEvent)=>{
      if(evento.source!==parent||evento.data?.type!=="streamlit:render") return;
      const {token,usuario,empresa}=evento.data.args||{};
      if(typeof token!=="string"||typeof usuario!=="number") return;
      setAuth(a=>a?.token===token&&a?.empresa===empresa&&a?.usuario===usuario?a:{token,empresa,usuario});
    };
    addEventListener("message",receber);
    enviar("streamlit:componentReady",{apiVersion:1});
    const altura=()=>enviar("streamlit:setFrameHeight",{height:Math.max(610,Math.min(850,screen.availHeight-150))});
    altura();addEventListener("resize",altura);
    return ()=>{removeEventListener("message",receber);removeEventListener("resize",altura);};
  },[]);
  return auth?<Central key={`${auth.usuario}:${auth.empresa}`} auth={auth}/>:<p className="carregando">Abra a Central pelo Orion CRM.</p>;
}
createRoot(document.getElementById("root")!).render(<Integracao/>);
