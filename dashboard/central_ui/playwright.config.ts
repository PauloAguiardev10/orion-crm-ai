import {defineConfig} from "@playwright/test";
export default defineConfig({
  testDir:"./tests", testIgnore:"streamlit.spec.ts", workers:1,
  use:{baseURL:"http://127.0.0.1:48319",channel:"msedge",viewport:{width:1250,height:820}},
  webServer:{command:"node tests/servidor.mjs",url:"http://127.0.0.1:48319",reuseExistingServer:false}
});
