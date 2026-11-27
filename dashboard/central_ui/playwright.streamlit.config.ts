import {defineConfig} from "@playwright/test";
export default defineConfig({
  testDir:"./tests", testMatch:"streamlit.spec.ts", workers:1,
  use:{baseURL:"http://127.0.0.1:48320",channel:"msedge"},
  webServer:[
    {command:"node tests/servidor.mjs",url:"http://127.0.0.1:48319",reuseExistingServer:false},
    {command:"node tests/streamlit.mjs",url:"http://127.0.0.1:48320/_stcore/health",reuseExistingServer:false},
  ]
});
