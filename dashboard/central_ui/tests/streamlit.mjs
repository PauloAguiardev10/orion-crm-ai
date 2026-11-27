import {spawn} from "node:child_process";
import {fileURLToPath} from "node:url";

const arquivo=fileURLToPath(new URL("./pagina_streamlit.py",import.meta.url));
const processo=spawn(process.env.ORION_TEST_PYTHON||"python",[
  "-B","-m","streamlit","run",arquivo,"--server.headless=true",
  "--theme.base=dark","--client.toolbarMode=minimal","--server.address=127.0.0.1","--server.port=48320","--browser.gatherUsageStats=false",
],{stdio:"inherit",env:{...process.env,PYTHON_DOTENV_DISABLED:"1"}});
processo.on("exit",code=>process.exit(code??0));
for(const sinal of ["SIGINT","SIGTERM"])process.on(sinal,()=>processo.kill(sinal));
