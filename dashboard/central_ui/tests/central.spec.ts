import {test,expect} from "@playwright/test";

test("mantém rascunho, foco, seleção e rolagem durante eventos e reconexão",async({page,request},info)=>{
  await page.goto("/");
  const central=page.frameLocator("iframe");
  await central.getByRole("button",{name:/Ana Martins/}).click();
  const entrada=central.getByRole("textbox",{name:"Mensagem",exact:true});
  await entrada.fill("Rascunho em edição");
  const historico=central.locator(".historico");
  await expect(historico.getByText("Mensagem fictícia 36 para validar a rolagem.")).toBeAttached();
  await historico.evaluate(el=>{el.scrollTop=120;});
  await expect.poll(()=>historico.evaluate(el=>el.scrollTop)).toBe(120);
  await entrada.press("End");
  const digitacao=entrada.pressSequentially(" continua", {delay:55});
  const evento=await (await request.post("/__evento")).text();
  await expect(historico.getByText(evento)).toHaveCount(1);
  await digitacao;
  await expect(entrada).toBeFocused();
  await expect(entrada).toHaveValue("Rascunho em edição continua");
  await expect.poll(()=>historico.evaluate(el=>el.scrollTop)).toBe(120);
  const seguinte=await (await request.post("/__reconectar")).text();
  await expect(historico.getByText(seguinte)).toHaveCount(1);
  await expect(entrada).toHaveValue("Rascunho em edição continua");
  await expect(central.getByRole("button",{name:/Ana Martins/})).toHaveClass(/selecionada/);
  await entrada.press("End");
  await central.getByRole("button",{name:"Emojis"}).click();
  await central.getByRole("button",{name:"😀",exact:true}).click();
  await expect(entrada).toHaveValue("Rascunho em edição continua😀");
  for(const estado of ["Aguardando envio","Aceita pela WAHA","Enviada","Entregue","Visualizada","Falha no envio"]){
    await expect(central.getByRole("img",{name:estado,exact:true})).toHaveCount(1);
  }
  await expect(central.locator(".data-mensagem")).toHaveCount(1);
  const fixar=central.getByRole("button",{name:"Fixar neste navegador"});
  await fixar.click();
  await expect(central.getByRole("button",{name:"Desafixar neste navegador"})).toHaveAttribute("aria-pressed","true");
  await central.getByRole("button",{name:"Informações",exact:true}).click();
  await expect(central.locator(".ficha").getByText(/Empresa fictícia/)).toBeVisible();
  await historico.evaluate(el=>{el.scrollTop=40;});
  await page.screenshot({path:info.outputPath("central-orion-completa.png")});
  await central.getByRole("img",{name:"Visualizada",exact:true}).scrollIntoViewIfNeeded();
  await page.screenshot({path:info.outputPath("central-orion-confirmacoes.png")});
});

test("pesquisa contatos e exige autenticação para receber eventos",async({page,request})=>{
  expect((await request.get("/api/central-whatsapp/eventos")).status()).toBe(401);
  await page.goto("/");
  const central=page.frameLocator("iframe");
  await central.getByRole("button",{name:"Nova conversa"}).click();
  await central.getByRole("combobox",{name:"Conexão",exact:true}).selectOption("1");
  await central.getByRole("button",{name:"Consultar contatos"}).click();
  await central.getByRole("textbox",{name:"Pesquisar contatos"}).fill("Martins");
  const busca=page.waitForRequest(r=>r.url().includes("busca=Martins"));
  await central.getByRole("button",{name:"Pesquisar",exact:true}).click();
  await busca;
  await central.getByRole("button",{name:/Ana Martins ·/}).click();
  await expect(central.getByRole("textbox",{name:"Telefone com DDI"})).toHaveValue("+5511999999999");
});


test("reserva e executa o texto pelo fluxo existente",async({page})=>{
  await page.goto("/");
  const central=page.frameLocator("iframe");
  await central.getByRole("button",{name:/Ana Martins/}).click();
  const entrada=central.getByRole("textbox",{name:"Mensagem",exact:true});
  await entrada.fill("Envio simulado do Orion");
  const requisicao=page.waitForRequest(r=>r.url().includes("/reservar-mensagem"));
  const execucao=page.waitForResponse(r=>r.url().includes("/executar-mensagem"));
  await central.getByRole("button",{name:"Enviar",exact:true}).click();
  expect((await requisicao).postDataJSON()).toMatchObject({conversa_id:1,texto:"Envio simulado do Orion"});
  expect((await execucao).ok()).toBeTruthy();
  await expect(entrada).toHaveValue("");
});


test("carrega e reproduz audio recebido e envia anexo pelo fluxo simulado",async({page})=>{
  await page.goto("/");
  const central=page.frameLocator("iframe");
  await central.getByRole("button",{name:/Ana Martins/}).click();
  const anexo=(texto:string)=>central.locator("article").filter({hasText:texto}).getByRole("button",{name:"Abrir anexo"});
  await anexo("Imagem de teste").click();
  await expect.poll(()=>central.getByAltText("Imagem da conversa").evaluate(el=>(el as HTMLImageElement).naturalWidth)).toBe(1);
  await anexo("Vídeo de teste").click();
  const video=central.locator(".historico video");
  await video.evaluate(async el=>{const v=el as HTMLVideoElement;v.muted=true;await v.play();});
  await expect.poll(()=>video.evaluate(el=>(el as HTMLVideoElement).currentTime)).toBeGreaterThan(0);
  await anexo("Áudio de teste").click();
  const audio=central.locator("audio");
  await expect(audio).toBeAttached();
  await audio.evaluate(async el=>{const a=el as HTMLAudioElement;a.muted=true;await a.play();});
  await expect.poll(()=>audio.evaluate(el=>(el as HTMLAudioElement).currentTime)).toBeGreaterThan(0);
  await central.locator('input[type=file]').setInputFiles({name:"documento.pdf",mimeType:"application/pdf",buffer:Buffer.from("%PDF-1.7")});
  const reserva=page.waitForResponse(r=>r.url().includes("/reservar-anexo"));
  await central.getByRole("button",{name:"Enviar",exact:true}).click();
  expect((await reserva).ok()).toBeTruthy();
});
