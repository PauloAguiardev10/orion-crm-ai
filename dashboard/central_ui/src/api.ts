export type Auth = {token: string; empresa?: number; usuario: number};
export type Delta<T> = {ordem: number[]; alteradas: T[]; removidas: number[]};
export const base = "/api/central-whatsapp";

export class ErroApi extends Error {
  constructor(public status:number, mensagem:string){super(mensagem);}
}

export async function request(auth: Auth, path: string, init: RequestInit = {}) {
  const url = new URL(base + path, location.origin);
  if (auth.empresa) url.searchParams.set("empresa_id", String(auth.empresa));
  const headers = new Headers(init.headers);
  headers.set("Authorization", "Bearer " + auth.token);
  if (typeof init.body === "string") headers.set("Content-Type", "application/json");
  const resposta = await fetch(url, {...init, headers, redirect: "error", cache: "no-store"});
  if (!resposta.ok) {
    const erro = await resposta.json().catch(() => ({}));
    throw new ErroApi(resposta.status, typeof erro.detail === "string" ? erro.detail : "Operação indisponível");
  }
  return resposta;
}
export async function json<T>(auth: Auth, path: string, init?: RequestInit): Promise<T> {
  return (await request(auth, path, init)).json();
}
export function aplicar<T extends {id: number}>(atual: T[], delta: Delta<T>): T[] {
  const dados = new Map(atual.map(item => [item.id, item]));
  for (const item of delta.alteradas) dados.set(item.id, item);
  for (const id of delta.removidas) dados.delete(id);
  return delta.ordem.flatMap(id => dados.has(id) ? [dados.get(id)!] : []);
}
export async function consumir(resposta: Response, receber: (tipo: string, dados: string) => void) {
  if (!resposta.body || !resposta.headers.get("content-type")?.startsWith("text/event-stream")) {
    throw new Error("Fluxo indisponível");
  }
  const leitor = resposta.body.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = "";
  try {
    for (;;) {
      const {value, done} = await leitor.read();
      if (done) break;
      buffer += value.replaceAll("\r\n", "\n");
      if (buffer.length > 16_000_000) throw new Error("Evento excedeu o limite");
      let fim: number;
      while ((fim = buffer.indexOf("\n\n")) !== -1) {
        const linhas = buffer.slice(0, fim).split("\n");
        buffer = buffer.slice(fim + 2);
        const tipo = linhas.find(l => l.startsWith("event: "))?.slice(7);
        const dados = linhas.filter(l => l.startsWith("data: ")).map(l => l.slice(6)).join("\n");
        if (tipo && dados) receber(tipo, dados);
      }
    }
  } finally {
    await leitor.cancel().catch(() => undefined);
    leitor.releaseLock();
  }
}
