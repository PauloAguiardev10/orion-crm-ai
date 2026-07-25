# Dashboard – Empresas

## Arquivo

`dashboard/app_pages/empresas.py`

---

## Objetivo

O módulo `empresas.py` implementa a página de gerenciamento de empresas do dashboard.

Ele concentra funções relacionadas a:

- cadastro de empresas;
- definição de plano;
- definição de serviços adicionais;
- cálculo de mensalidade;
- criação do usuário administrador da empresa;
- atualização de dados;
- controle financeiro;
- suspensão de empresas;
- exclusão de empresas;
- restrição de visualização por perfil administrativo.

A página utiliza banco de dados SQLite diretamente por meio da função `conectar()`.

---

## Função principal

```python
def render_empresas():
```

A função `render_empresas()` constrói toda a interface da página.

Seu fluxo principal é:

1. identificar o nível de acesso do usuário;
2. identificar a empresa atualmente autenticada;
3. listar as empresas permitidas para aquele perfil;
4. exibir o formulário de cadastro;
5. calcular a mensalidade;
6. criar a empresa e o usuário administrador;
7. permitir a atualização dos dados;
8. permitir a exclusão, quando autorizada.

---

# Constantes de planos

O módulo define os valores básicos dos planos:

```python
PLANOS_VALORES = {
    "Lite": 350.0,
    "Pro": 700.0,
    "Premium": 1000.0,
}
```

Os planos disponíveis são:

| Plano | Valor-base mensal |
|---|---:|
| Lite | R$ 350,00 |
| Pro | R$ 700,00 |
| Premium | R$ 1.000,00 |

Esses valores são usados no cálculo da mensalidade da empresa.

---

# Serviços adicionais

O módulo possui a constante:

```python
SERVICOS_ADICIONAIS = {
    "Produtos": 150.0,
    "Pedidos": 150.0,
    "Instagram": 200.0,
    "Facebook": 150.0,
    "Relatórios": 250.0,
    "IA Vendas": 350.0,
    "Agente de Vendas": 500.0,
    "PIX Automático": 200.0,
    "Link Pagamento": 200.0,
}
```

Serviços e valores:

| Serviço | Valor mensal |
|---|---:|
| Produtos | R$ 150,00 |
| Pedidos | R$ 150,00 |
| Instagram | R$ 200,00 |
| Facebook | R$ 150,00 |
| Relatórios | R$ 250,00 |
| IA Vendas | R$ 350,00 |
| Agente de Vendas | R$ 500,00 |
| PIX Automático | R$ 200,00 |
| Link Pagamento | R$ 200,00 |

---

# Serviços premium

O módulo define:

```python
SERVICOS_PREMIUM = [
    "IA Vendas",
    "Agente de Vendas",
    "PIX Automático",
    "Link Pagamento",
    "Relatórios",
]
```

Essa lista é utilizada pela função `obter_servicos_por_plano()`.

No código atual:

- o plano Lite pode selecionar qualquer item de `SERVICOS_ADICIONAIS`;
- o plano Pro pode selecionar apenas os itens de `SERVICOS_PREMIUM`;
- o plano Premium não apresenta serviços adicionais selecionáveis.

O Premium é tratado pela interface como plano com todos os recursos liberados.

---

# Limpeza do formulário

A função:

```python
def limpar_formulario_nova_empresa():
```

incrementa:

```python
st.session_state["reset_nova_empresa"]
```

Código:

```python
st.session_state["reset_nova_empresa"] = (
    st.session_state.get("reset_nova_empresa", 0) + 1
)
```

Esse valor é usado na composição das chaves dos componentes Streamlit.

Depois de um cadastro bem-sucedido, a função é chamada antes de:

```python
st.rerun()
```

Com isso, o formulário é recriado com novas chaves.

---

# Estrutura da tabela empresas

A função:

```python
def garantir_colunas_empresas():
```

verifica se a tabela `empresas` existe e se possui as colunas esperadas.

A criação inicial utiliza:

```sql
CREATE TABLE IF NOT EXISTS empresas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT UNIQUE NOT NULL,
    plano TEXT DEFAULT 'Lite',
    status TEXT DEFAULT 'ativa',
    valor_mensal REAL DEFAULT 350,
    logo_path TEXT,
    parceiro_nome TEXT DEFAULT 'Forway',
    data_adesao TEXT,
    data_vencimento TEXT,
    status_financeiro TEXT DEFAULT 'em_dia',
    bloqueio_automatico INTEGER DEFAULT 1,
    servicos TEXT DEFAULT '',
    criado_em TEXT DEFAULT CURRENT_TIMESTAMP
)
```

---

## Colunas da tabela

| Coluna | Finalidade |
|---|---|
| `id` | Identificador da empresa |
| `nome` | Nome único da empresa |
| `plano` | Plano comercial |
| `status` | Situação operacional |
| `valor_mensal` | Mensalidade calculada |
| `logo_path` | Caminho da imagem da empresa |
| `parceiro_nome` | Parceiro responsável |
| `data_adesao` | Data de entrada da empresa |
| `data_vencimento` | Data prevista de vencimento |
| `status_financeiro` | Situação financeira |
| `bloqueio_automatico` | Indicação de bloqueio automático |
| `servicos` | Serviços adicionais em texto |
| `criado_em` | Data e hora de criação |

---

## Inclusão automática de colunas

A função consulta a estrutura por:

```sql
PRAGMA table_info(empresas)
```

Depois verifica as seguintes colunas:

```python
novas_colunas = {
    "logo_path": "...",
    "parceiro_nome": "...",
    "data_adesao": "...",
    "data_vencimento": "...",
    "status_financeiro": "...",
    "bloqueio_automatico": "...",
    "valor_mensal": "...",
    "servicos": "...",
}
```

Se alguma coluna estiver ausente, é executado um comando:

```sql
ALTER TABLE empresas ADD COLUMN ...
```

Essa função atua como uma migração simples da tabela SQLite.

---

# Listagem das empresas

A função:

```python
def listar_empresas():
```

primeiro executa:

```python
garantir_colunas_empresas()
```

Depois obtém:

```python
nivel = st.session_state.get("nivel")
empresa_logada = st.session_state.get("empresa")
```

---

## Perfil parceiro_admin

Quando o nível é:

```text
parceiro_admin
```

a consulta executada é:

```sql
SELECT *
FROM empresas
WHERE parceiro_nome = ?
AND nome != 'Orion Systems'
ORDER BY id DESC
```

O parâmetro utilizado é:

```python
empresa_logada
```

Esse perfil vê apenas empresas cujo `parceiro_nome` corresponde ao nome armazenado na sessão.

A empresa chamada:

```text
Orion Systems
```

é excluída dessa listagem.

---

## Outros perfis

Para os demais níveis, a consulta é:

```sql
SELECT *
FROM empresas
ORDER BY id DESC
```

Portanto, o código não restringe a consulta aos demais perfis dentro desta função.

A proteção de acesso à página, caso exista, deve ser realizada em outro ponto do dashboard.

---

## Retorno

A consulta é carregada com:

```python
pd.read_sql_query(...)
```

O retorno é um DataFrame do pandas.

---

# Cálculo da mensalidade

A função:

```python
def calcular_valor_mensal(plano, servicos):
```

começa com o valor-base do plano:

```python
valor = PLANOS_VALORES.get(plano, 350.0)
```

Se o plano não for localizado, o padrão utilizado é:

```text
R$ 350,00
```

Depois, para cada serviço:

```python
valor += SERVICOS_ADICIONAIS.get(servico, 0.0)
```

O valor final corresponde a:

```text
valor-base do plano + serviços selecionados
```

---

## Exemplo

Plano Pro:

```text
R$ 700,00
```

Serviço adicional Relatórios:

```text
R$ 250,00
```

Mensalidade calculada:

```text
R$ 950,00
```

---

# Criação da empresa

A função:

```python
def criar_empresa(
    nome,
    plano,
    status,
    logo_path,
    parceiro_nome,
    data_adesao,
    data_vencimento,
    servicos,
):
```

é responsável por inserir a empresa na tabela.

Antes da inserção:

```python
garantir_colunas_empresas()
```

---

## Cálculo do valor

O valor mensal é calculado por:

```python
valor_mensal = calcular_valor_mensal(
    plano,
    servicos
)
```

---

## Inserção

A consulta grava:

```sql
INSERT INTO empresas (
    nome,
    plano,
    status,
    valor_mensal,
    logo_path,
    parceiro_nome,
    data_adesao,
    data_vencimento,
    status_financeiro,
    bloqueio_automatico,
    servicos
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```

Valores fixos no cadastro:

```python
status_financeiro = "em_dia"
bloqueio_automatico = 1
```

Os serviços são armazenados como texto separado por vírgulas:

```python
",".join(servicos)
```

O nome e o caminho da logo recebem:

```python
.strip()
```

---

## Retorno

Após o `commit`, a função captura:

```python
empresa_id = cursor.lastrowid
```

e retorna o ID da empresa criada.

---

# Atualização da empresa

A função:

```python
def atualizar_empresa(...)
```

atualiza:

- plano;
- status;
- valor mensal;
- caminho da logo;
- parceiro responsável;
- data de vencimento;
- status financeiro;
- bloqueio automático;
- serviços.

A consulta utiliza:

```sql
UPDATE empresas
SET plano = ?,
    status = ?,
    valor_mensal = ?,
    logo_path = ?,
    parceiro_nome = ?,
    data_vencimento = ?,
    status_financeiro = ?,
    bloqueio_automatico = ?,
    servicos = ?
WHERE id = ?
```

O campo de bloqueio é convertido para inteiro:

```python
int(bloqueio_automatico)
```

Os serviços continuam armazenados como string:

```python
",".join(servicos)
```

No código atual, essa função não atualiza:

- nome da empresa;
- data de adesão;
- data de criação.

---

# Exclusão da empresa

A função:

```python
def excluir_empresa(empresa_id):
```

realiza duas exclusões.

Primeiro remove os usuários:

```sql
DELETE FROM usuarios
WHERE empresa_id = ?
```

Depois remove a empresa:

```sql
DELETE FROM empresas
WHERE id = ?
```

Ao final:

```python
conn.commit()
conn.close()
```

---

## Escopo da exclusão

Esta função remove diretamente:

- usuários associados à empresa;
- registro da empresa.

Ela não mostra exclusão explícita de outros dados relacionados, como:

- leads;
- conversas;
- pedidos;
- produtos;
- serviços;
- especialistas.

A existência de exclusões em cascata dependeria da estrutura do banco, que não é demonstrada neste arquivo.

---

# Formatação monetária

A função:

```python
def formatar_moeda(valor):
```

converte valores para o padrão brasileiro.

Exemplo:

```text
R$ 1.250,00
```

Ela é usada:

- nos rótulos dos serviços;
- na mensalidade calculada;
- na mensalidade exibida durante a edição.

---

# Serviços disponíveis por plano

A função:

```python
def obter_servicos_por_plano(plano):
```

possui o comportamento:

```python
if plano == "Lite":
    return list(SERVICOS_ADICIONAIS.keys())

if plano == "Pro":
    return SERVICOS_PREMIUM

return []
```

Resultado:

| Plano | Serviços selecionáveis |
|---|---|
| Lite | Todos os serviços adicionais |
| Pro | Apenas a lista `SERVICOS_PREMIUM` |
| Premium | Nenhum item adicional exibido |

No plano Premium, a página informa que todos os recursos estão liberados.

---

# Formatação das opções de serviço

A função:

```python
def formatar_opcao_servico(servico):
```

retorna um texto no formato:

```text
Serviço — R$ valor/mês
```

Exemplo:

```text
Produtos — R$ 150,00/mês
```

---

# Conversão dos rótulos

A função:

```python
def converter_labels_para_servicos(labels):
```

recebe os rótulos apresentados no `multiselect`.

Para cada item:

```python
servico = label.split(" — ")[0].strip()
```

Depois verifica:

```python
if servico in SERVICOS_ADICIONAIS:
```

Somente nomes reconhecidos são incluídos no resultado.

---

# Interface da página

A função `render_empresas()` obtém:

```python
nivel = st.session_state.get("nivel")
empresa_logada = st.session_state.get("empresa")
reset_key = st.session_state.get("reset_nova_empresa", 0)
```

---

## Título

A página apresenta:

```text
Empresas
```

---

## Mensagem para parceiro

Quando o nível é:

```text
parceiro_admin
```

é exibida:

```text
Painel parceiro: [nome].
Você visualiza apenas clientes vinculados à sua operação.
```

Essa mensagem corresponde ao filtro utilizado em `listar_empresas()`.

---

# Listagem das empresas

A página chama:

```python
empresas = listar_empresas()
```

Quando não existem registros:

```text
Nenhuma empresa cadastrada.
```

Quando existem:

```python
st.dataframe(
    empresas,
    use_container_width=True,
    hide_index=True,
)
```

Todas as colunas retornadas são exibidas.

---

# Cadastro de nova empresa

A seção possui o título:

```text
Nova empresa
```

O formulário é dividido em duas colunas.

---

## Primeira coluna

Campos:

```python
nome = st.text_input("Nome empresa")
```

```python
usuario_admin = st.text_input("Usuário admin")
```

```python
logo_path = st.text_input(
    "Logo",
    value="assets/logo_forway.png"
)
```

---

## Parceiro responsável

### parceiro_admin

Quando o perfil atual é `parceiro_admin`:

```python
parceiro_nome = empresa_logada
```

O campo é exibido desabilitado.

O parceiro não pode selecionar outro responsável.

### Outros perfis

Para os demais:

```python
["Forway", "Orion"]
```

são as opções disponíveis.

---

## Segunda coluna

Campos:

```python
senha_admin = st.text_input(
    "Senha admin",
    type="password"
)
```

```python
plano = st.selectbox(
    "Plano",
    ["Lite", "Pro", "Premium"]
)
```

```python
status = st.selectbox(
    "Status",
    ["ativa", "suspensa"]
)
```

---

# Serviços na criação

Inicialmente:

```python
servicos = []
```

Depois:

```python
servicos_disponiveis = obter_servicos_por_plano(plano)
```

---

## Plano Premium

Quando o plano é Premium:

```python
st.success(
    "Plano Premium com todos os recursos liberados."
)
```

Nenhum `multiselect` é exibido.

A lista `servicos` permanece vazia.

---

## Planos Lite e Pro

A página gera os rótulos:

```python
opcoes_servicos = [
    formatar_opcao_servico(servico)
    for servico in servicos_disponiveis
]
```

Depois apresenta:

```python
st.multiselect(
    "Serviços adicionais",
    opcoes_servicos
)
```

Os rótulos selecionados são convertidos em nomes internos por:

```python
converter_labels_para_servicos()
```

---

# Mensalidade no cadastro

A mensalidade é calculada por:

```python
valor_total_novo = calcular_valor_mensal(
    plano,
    servicos
)
```

Depois é apresentada com:

```python
st.metric(
    "Mensalidade calculada",
    formatar_moeda(valor_total_novo)
)
```

---

# Datas automáticas

A data de adesão é calculada com:

```python
datetime.now().strftime("%Y-%m-%d")
```

A data de vencimento é definida como 30 dias após a data atual:

```python
(datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
```

A interface mostra:

```text
Adesão: AAAA-MM-DD | Vencimento: AAAA-MM-DD
```

Esses campos não são editáveis durante o cadastro.

---

# Processamento do cadastro

Ao clicar em:

```text
Cadastrar empresa
```

a página valida:

```python
if not nome.strip() or not usuario_admin.strip() or not senha_admin.strip():
```

Portanto, os campos obrigatórios verificados diretamente são:

- nome;
- usuário administrador;
- senha do administrador.

Quando algum estiver vazio:

```text
Preencha todos os campos obrigatórios.
```

---

## Criação da empresa

Dentro de um bloco `try`, é executado:

```python
empresa_id = criar_empresa(...)
```

Depois:

```python
criar_admin_empresa(
    empresa_id,
    nome,
    usuario_admin,
    senha_admin,
)
```

A criação da empresa e do administrador ocorre em chamadas separadas.

---

## Cadastro bem-sucedido

Após as chamadas:

```python
st.success(
    "Empresa cadastrada com admin criado."
)
```

Depois:

```python
limpar_formulario_nova_empresa()
st.rerun()
```

---

## Erros

Qualquer exceção capturada pelo bloco:

```python
except Exception as erro:
```

é apresentada na interface:

```python
st.error(
    f"Erro ao cadastrar empresa: {erro}"
)
```

O código não implementa rollback conjunto entre a criação da empresa e do usuário administrador.

Se a empresa for criada e a criação do administrador falhar, a empresa pode permanecer cadastrada, dependendo da implementação do serviço.

---

# Gerenciamento de empresa

A página recarrega a listagem:

```python
empresas = listar_empresas()
```

Se estiver vazia, a função exibe:

```text
Nenhuma empresa disponível para gerenciamento.
```

e encerra com:

```python
return
```

---

## Seleção da empresa

As opções seguem o formato:

```text
ID - Nome
```

O código cria:

```python
opcoes = {
    f"{row['id']} - {row['nome']}": row["id"]
    for _, row in empresas.iterrows()
}
```

Depois localiza a empresa selecionada no DataFrame.

---

# Campos de atualização

A página permite editar:

- plano;
- status;
- status financeiro;
- logo;
- parceiro;
- vencimento;
- bloqueio automático;
- serviços adicionais.

---

## Plano atualizado

Opções:

```text
Lite
Pro
Premium
```

O valor atual é utilizado para definir o índice inicial.

---

## Status atualizado

Opções:

```text
ativa
suspensa
```

---

## Status financeiro

Opções:

```text
em_dia
vencido
inadimplente
```

O código apenas armazena e permite alterar esse status.

Não existe, neste arquivo, lógica automática que o modifique com base na data de vencimento.

---

## Logo

O caminho atual é carregado no campo:

```python
st.text_input(
    "Logo atualizada",
    value=...
)
```

O módulo não realiza upload de arquivo nem valida a existência do caminho.

---

## Parceiro

Para `parceiro_admin`:

```python
novo_parceiro_nome = empresa_logada
```

O campo fica desabilitado.

Para outros perfis:

```text
Forway
Orion
```

são as opções.

---

## Data de vencimento

O vencimento é editado por um campo de texto:

```python
st.text_input(
    "Vencimento",
    value=...
)
```

Não existe seletor de data nem validação direta do formato.

---

## Bloqueio automático

A interface utiliza:

```python
st.checkbox(
    "Bloquear automaticamente",
    value=bool(empresa["bloqueio_automatico"])
)
```

O valor é salvo como inteiro durante a atualização.

O código desta página apenas grava a configuração.

A execução efetiva de um bloqueio automático não está implementada neste arquivo.

---

# Serviços na edição

Os serviços atuais são lidos do campo textual:

```python
empresa["servicos"]
```

A conversão utiliza:

```python
str(empresa["servicos"]).split(",")
```

Itens vazios são ignorados.

---

## Plano Premium

Quando o plano atualizado é Premium:

```python
servicos_ativos = []
```

A interface exibe:

```text
Plano Premium com todos os recursos liberados.
```

Nenhum serviço adicional fica armazenado na lista de edição.

---

## Planos Lite e Pro

A página:

1. carrega os serviços permitidos pelo plano;
2. cria os rótulos com valores;
3. converte os serviços atuais em rótulos;
4. apresenta um `multiselect`;
5. converte novamente os rótulos em nomes.

---

# Mensalidade na edição

A mensalidade é recalculada por:

```python
valor_total = calcular_valor_mensal(
    novo_plano,
    servicos_ativos
)
```

Depois é apresentada:

```python
st.metric(
    "Mensalidade",
    formatar_moeda(valor_total)
)
```

O usuário não edita manualmente o valor.

---

# Salvamento das alterações

Ao clicar em:

```text
Salvar alterações
```

a página chama:

```python
atualizar_empresa(
    empresa_id,
    novo_plano,
    novo_status,
    valor_total,
    novo_logo_path,
    novo_parceiro_nome,
    data_vencimento,
    status_financeiro,
    bloqueio_automatico,
    servicos_ativos,
)
```

Após a chamada:

```python
st.success("Empresa atualizada.")
st.rerun()
```

Não existe verificação do retorno da função.

Também não existe tratamento local de exceções nessa operação.

---

# Exclusão pela interface

A exclusão só é apresentada quando:

```python
nivel == "orion_admin"
```

---

## Proteção da Orion Systems

Quando a empresa selecionada possui o nome:

```text
Orion Systems
```

a exclusão é bloqueada:

```python
st.error(
    "Orion Systems não pode ser excluída."
)
```

Para outras empresas:

```python
excluir_empresa(empresa_id)
```

Depois:

```python
st.warning("Empresa excluída.")
st.rerun()
```

---

## Outros perfis

Para usuários que não são `orion_admin`, é exibida:

```text
Exclusão de empresa disponível apenas para Orion Admin.
```

---

# Dependências

O módulo utiliza:

```python
import streamlit as st
import pandas as pd
```

Também importa:

```python
from datetime import datetime, timedelta
```

Módulos internos:

```text
database.db
services.usuarios_service
```

Função de serviço utilizada:

```python
criar_admin_empresa
```

---

# Fluxo da página

```text
Acesso à página
       │
       ▼
Lê nível e empresa da sessão
       │
       ▼
Garante tabela e colunas
       │
       ▼
Lista empresas permitidas
       │
       ▼
Exibe empresas cadastradas
       │
       ▼
Formulário de nova empresa
       │
       ├── Define plano
       ├── Seleciona serviços
       ├── Calcula mensalidade
       ├── Define datas
       ├── Cria empresa
       └── Cria administrador
       │
       ▼
Gerenciamento
       │
       ├── Atualiza plano e status
       ├── Atualiza financeiro
       ├── Atualiza parceiro
       ├── Atualiza vencimento
       ├── Atualiza serviços
       └── Recalcula mensalidade
       │
       ▼
Orion Admin pode excluir
```

---

# Controle de acesso observado

O módulo diferencia diretamente dois níveis:

```text
parceiro_admin
orion_admin
```

---

## parceiro_admin

O perfil:

- visualiza apenas empresas vinculadas ao parceiro;
- não vê a empresa `Orion Systems`;
- não escolhe outro parceiro no cadastro;
- não altera o parceiro durante a edição;
- não pode excluir empresas.

---

## orion_admin

O perfil:

- pode visualizar todas as empresas;
- pode escolher o parceiro;
- pode alterar o parceiro;
- pode excluir empresas;
- não pode excluir a empresa chamada `Orion Systems`.

---

## Outros níveis

Para níveis diferentes de `parceiro_admin`, `listar_empresas()` retorna todas as empresas.

Entretanto, a exclusão continua limitada ao `orion_admin`.

Por isso, a proteção de acesso à página para outros tipos de usuário precisa existir em outra parte do sistema, caso seja necessária.

---

# Limitações observadas no código atual

O módulo não implementa diretamente:

- upload real de logo;
- validação do caminho da imagem;
- calendário para vencimento;
- validação do formato da data;
- cobrança automática;
- geração de faturas;
- pagamento recorrente;
- integração com gateway;
- bloqueio automático baseado em vencimento;
- histórico de planos;
- histórico financeiro;
- confirmação antes da exclusão;
- exclusão completa de todos os registros relacionados;
- transação única entre empresa e administrador;
- edição do nome da empresa;
- edição do usuário administrador;
- alteração da senha do administrador;
- busca ou filtros;
- paginação da listagem;
- tratamento de exceções na atualização e exclusão.

---

# Pontos de atenção

## Migração dentro da página

A função `garantir_colunas_empresas()` altera diretamente a estrutura da tabela.

Ela é chamada durante a listagem e a criação de empresas.

Embora funcional, essa responsabilidade está dentro do módulo da página.

Em uma estrutura futura, migrações poderiam ser separadas da camada de interface.

---

## Armazenamento dos serviços

Os serviços adicionais são salvos em uma única coluna de texto:

```text
Produtos,Pedidos,Instagram
```

Essa abordagem simplifica a implementação, mas não utiliza uma tabela relacional específica para os vínculos entre empresas e serviços.

---

## Premium com lista vazia

No plano Premium:

```python
servicos = []
```

ou:

```python
servicos_ativos = []
```

Portanto, a liberação de todos os recursos não é representada pela gravação de todos os serviços na coluna.

Ela depende de outras regras do sistema que interpretem o plano Premium.

---

## Bloqueio automático

O campo `bloqueio_automatico` é cadastrado e editado, mas este módulo não executa o bloqueio.

A documentação não deve afirmar que empresas vencidas são suspensas automaticamente apenas com base neste arquivo.

---

## Status financeiro

O campo pode receber:

```text
em_dia
vencido
inadimplente
```

Mas a atualização é manual nesta página.

Não existe cálculo automático baseado na data.

---

## Exclusão parcial de dados

A exclusão remove:

- usuários;
- empresa.

Sem analisar o restante do banco, não é possível afirmar que leads, pedidos, produtos, especialistas e conversas sejam removidos.

---

## Criação em duas etapas

A empresa é criada antes do administrador:

```python
empresa_id = criar_empresa(...)
criar_admin_empresa(...)
```

Essas ações não são envolvidas em uma única transação dentro deste módulo.

---

# Possíveis evoluções

O módulo pode ser evoluído com:

- upload de logo;
- seletor de data;
- validação de vencimento;
- cobrança recorrente;
- controle de inadimplência;
- bloqueio automático real;
- histórico financeiro;
- histórico de troca de plano;
- confirmação de exclusão;
- exclusão segura de dependências;
- transação atômica para empresa e administrador;
- gerenciamento completo do administrador;
- busca e filtros;
- paginação;
- tabela relacional para serviços;
- logs de auditoria;
- separação das operações SQL em serviços;
- controle explícito de acesso à página.

Esses itens são possibilidades futuras e não fazem parte da implementação atual.

---

# Resumo

O módulo `empresas.py` implementa o gerenciamento administrativo das empresas cadastradas no Orion CRM AI.

Ele permite:

- cadastrar empresas;
- escolher planos;
- adicionar serviços;
- calcular mensalidades;
- criar um administrador;
- controlar status operacional e financeiro;
- configurar vencimento;
- definir parceiro responsável;
- atualizar empresas;
- excluir empresas conforme o perfil.

O módulo também diferencia os perfis `parceiro_admin` e `orion_admin`, mantém compatibilidade com a tabela SQLite e aplica regras comerciais de plano e serviços adicionais.

A implementação atual realiza cadastro e administração básica, mas não executa cobrança, bloqueio financeiro automático, upload de logo ou exclusão completa garantida de todos os dados relacionados.