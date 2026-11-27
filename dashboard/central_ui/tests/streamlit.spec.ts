import {expect,test} from "@playwright/test";

for(const [width,height] of [[1366,768],[1920,1080],[390,844]]){
  test("Central dentro do Streamlit em "+width+"x"+height,async({page},info)=>{
    await page.setViewportSize({width,height});
    await page.goto("/");
    const iframe=page.locator(".st-key-orion_central_area iframe");
    await expect(iframe).toBeVisible({timeout:12000});
    await expect.poll(()=>iframe.evaluate(el=>el.style.getPropertyValue("--orion-central-altura"))).not.toBe("");
    const central=iframe.contentFrame();
    await expect(central.getByRole("button",{name:"Favoritas"})).toBeVisible();
    await central.getByRole("button",{name:/Ana Martins/}).click();
    const compositor=central.getByRole("textbox",{name:"Mensagem",exact:true});
    const enviar=central.getByRole("button",{name:"Enviar",exact:true});
    const historico=central.locator(".historico");
    await expect.poll(()=>historico.evaluate(el=>el.scrollHeight>el.clientHeight)).toBeTruthy();
    await historico.evaluate(el=>el.scrollTop=0);
    await expect(compositor).toBeVisible();
    await expect(compositor).toBeInViewport();
    await expect(enviar).toBeInViewport();
    await compositor.fill("Rascunho com histórico longo");
    await expect(page.locator(".stMain")).toHaveCSS("overflow-y","hidden");
    await expect(page.getByText("Usar Central classica")).toHaveCount(0);
    const caixa=await iframe.boundingBox();
    expect(caixa!.y+caixa!.height).toBeLessThanOrEqual(height+2);
    for(const controle of [compositor,enviar]){
      const area=await controle.boundingBox();
      expect(area!.y+area!.height).toBeLessThanOrEqual(caixa!.y+caixa!.height+1);
      expect(area!.y+area!.height).toBeLessThanOrEqual(height);
    }
    await page.screenshot({path:info.outputPath("central-streamlit-"+width+".png")});
  });
}
