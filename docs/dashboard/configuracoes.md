# Dashboard – Configurações Operacionais

## Arquivo

`dashboard/app_pages/configuracoes.py`

---

## Objetivo

O módulo `configuracoes.py` implementa a página de configurações operacionais da empresa autenticada.

A página centraliza o gerenciamento de:

- usuários da empresa;
- níveis de acesso;
- senhas;
- serviços ou especialidades;
- especialistas e atendentes;
- vínculo entre funcionários e especialidades.

O módulo utiliza dados da sessão do Streamlit para identificar a empresa atual.

---

## Função principal

```python
def render_configuracoes():
```

A função `render_configuracoes()` é responsável por construir toda a interface da página.

Seu fluxo principal é:

1. obter o identificador da empresa autenticada;
2. carregar os usuários cadastrados;
3. filtrar os usuários da empresa atual;
4. permitir a criação e exclusão de funcionários;
5. permitir a alteração de senha;
6. cadastrar e excluir serviços ou especialidades;
7. vincular funcionários às especialidades;
8. listar os especialistas cadastrados.

---

## Identificação da empresa

A página obtém o identificador da empresa por meio de:

```python
empresa_id = st.session_state.empresa_id
```

Também utiliza:

```python
st.session_state.empresa
```

para comparar o nome da empresa dos usuários carregados.

Essas duas informações são usadas em diferentes partes da página:

- `empresa_id`: operações de serviços e especialistas;
- `empresa`: criação e filtragem de usuários.

---

## Controle de limpeza dos formulários

O módulo utiliza a função:

```python
def limpar_formularios():
```

Ela incrementa o valor:

```python
st.session_state["reset_config"]
```

Código:

```python
st.session_state["reset_config"] = (
    st.session_state.get("reset_config", 0) + 1
)
```

Esse contador é utilizado na composição das chaves dos componentes Streamlit.

Exemplo:

```python
key=f"novo_usuario_{reset_key}"
```

Ao incrementar o contador e executar `st.rerun()`, os campos passam a possuir novas chaves e são recriados vazios.

---

## Exclusão de usuário

O módulo implementa diretamente a função:

```python
def excluir_usuario(usuario_id, usuario_nome, empresa_id):
```

Essa função realiza duas operações.

### Exclusão do especialista

Primeiro, chama:

```python
excluir_especialista_por_nome(
    usuario_nome,
    empresa_id,
)
```

Essa operação remove o vínculo do usuário com os especialistas da empresa.

### Exclusão da tabela de usuários

Depois, abre uma conexão com o banco:

```python
conn = conectar()
cursor = conn.cursor()
```

Executa:

```sql
DELETE FROM usuarios
WHERE id = ?
```

O identificador é convertido para inteiro:

```python
int(usuario_id)
```

Ao final:

```python
conn.commit()
conn.close()
```

Portanto, a exclusão de um funcionário também tenta remover o especialista correspondente pelo nome antes de apagar o usuário.

---

# Usuários e especialistas da empresa

A primeira área da página possui o título:

```text
Usuários / Especialistas da Empresa
```

---

## Carregamento dos usuários

O código executa:

```python
usuarios = listar_usuarios()
```

Inicialmente:

```python
usuarios_empresa = usuarios
```

Quando a lista não está vazia, é aplicado o filtro:

```python
usuarios_empresa = usuarios[
    usuarios["empresa"] == st.session_state.empresa
]
```

Assim, a tabela exibida contém apenas usuários cujo campo `empresa` corresponde ao nome da empresa armazenado na sessão.

A tabela é exibida por:

```python
st.dataframe(
    usuarios_empresa,
    use_container_width=True,
    hide_index=True,
)
```

---

## Criação de funcionário

A página apresenta a seção:

```text
Criar funcionário
```

O formulário é dividido em duas colunas.

### Primeira coluna

Campo:

```python
novo_usuario = st.text_input("Usuário novo")
```

### Segunda coluna

Campos:

```python
nova_senha = st.text_input(
    "Senha do novo usuário",
    type="password"
)
```

e:

```python
nivel = st.selectbox(
    "Nível de acesso",
    ["admin_empresa", "usuario"],
    index=None,
    placeholder="Selecione o nível de acesso"
)
```

Os níveis disponíveis no código são:

```text
admin_empresa
usuario
```

---

## Validação da criação

Ao clicar em:

```text
Criar usuário
```

a página valida:

1. se o nome do usuário foi informado;
2. se a senha foi informada;
3. se o nível foi selecionado.

As mensagens utilizadas são:

```text
Informe o nome do usuário.
Informe a senha do usuário.
Selecione o nível de acesso.
```

Quando os campos são válidos, a página chama:

```python
criar_usuario(
    novo_usuario,
    nova_senha,
    st.session_state.empresa,
    nivel,
)
```

### Retorno verdadeiro

Quando a função retorna verdadeiro:

```python
st.success("Usuário criado com sucesso.")
limpar_formularios()
st.rerun()
```

### Retorno falso

Quando retorna falso:

```python
st.error("Não foi possível criar o usuário.")
```

---

## Exclusão de funcionário

A página cria uma lista no formato:

```text
ID - usuário
```

Código:

```python
usuarios_lista_excluir = [
    f"{row['id']} - {row['usuario']}"
    for _, row in usuarios_empresa.iterrows()
]
```

Quando existem usuários, é apresentado um `selectbox`.

Ao clicar em:

```text
Excluir usuário
```

a página verifica se um funcionário foi selecionado.

Depois separa o ID e o nome:

```python
usuario_id = usuario_excluir.split(" - ")[0]
usuario_nome = usuario_excluir.split(" - ", 1)[1]
```

Em seguida chama:

```python
excluir_usuario(
    usuario_id,
    usuario_nome,
    empresa_id,
)
```

Após a exclusão:

```python
st.success("Usuário excluído com sucesso.")
limpar_formularios()
st.rerun()
```

No código atual não existe:

- confirmação antes da exclusão;
- tratamento local de exceções;
- proteção explícita contra a exclusão do próprio usuário;
- proteção explícita contra a exclusão do último administrador.

Quando não existem usuários disponíveis:

```text
Nenhum usuário disponível para exclusão.
```

---

## Alteração de senha

A página apresenta a seção:

```text
Alterar senha
```

Os nomes dos usuários da empresa são convertidos em lista:

```python
usuarios_lista = usuarios_empresa["usuario"].tolist()
```

O usuário é selecionado por:

```python
usuario_alterar = st.selectbox(...)
```

A nova senha é recebida por:

```python
nova_senha_alterar = st.text_input(
    "Nova senha",
    type="password"
)
```

Ao clicar em:

```text
Alterar senha
```

a página valida:

- usuário selecionado;
- nova senha preenchida.

Depois chama:

```python
alterar_senha(
    usuario_alterar,
    nova_senha_alterar,
)
```

Quando a operação retorna verdadeiro:

```python
st.success("Senha alterada com sucesso.")
limpar_formularios()
st.rerun()
```

Quando retorna falso:

```python
st.error("Não foi possível alterar a senha.")
```

A chamada utiliza o nome do usuário, e não o ID nem o `empresa_id`.

A proteção contra usuários homônimos entre empresas depende da implementação de `alterar_senha()`.

---

# Serviços e especialidades

A página apresenta a seção:

```text
Serviços / Especialidades
```

---

## Cadastro de serviço

O nome do serviço é coletado por:

```python
novo_servico = st.text_input(
    "Novo serviço ou especialidade"
)
```

Ao clicar em:

```text
Cadastrar Serviço
```

a página verifica:

```python
if novo_servico.strip():
```

Quando preenchido, chama:

```python
cadastrar_servico(
    novo_servico,
    empresa_id,
)
```

Depois:

```python
st.success("Serviço cadastrado.")
limpar_formularios()
st.rerun()
```

Quando o campo está vazio:

```text
Informe o nome do serviço.
```

O retorno de `cadastrar_servico()` não é verificado pela página.

---

## Carregamento dos serviços

Os serviços são carregados por:

```python
servicos = carregar_servicos(empresa_id)
```

Quando existem registros, são apresentados em:

```python
st.dataframe(
    servicos,
    use_container_width=True,
    hide_index=True,
)
```

Quando não existem:

```text
Nenhum serviço/especialidade cadastrado.
```

---

## Exclusão de especialidade

A página cria opções no formato:

```text
ID - nome
```

Código:

```python
[
    f"{row['id']} - {row['nome']}"
    for _, row in servicos.iterrows()
]
```

Ao clicar em:

```text
Excluir especialidade
```

a página verifica se uma opção foi selecionada.

Depois extrai o ID:

```python
servico_id = servico_excluir.split(" - ")[0]
```

e chama:

```python
excluir_servico(
    servico_id,
    empresa_id,
)
```

Após a execução:

```python
st.success("Especialidade excluída com sucesso.")
limpar_formularios()
st.rerun()
```

O módulo não verifica o retorno da função.

Também não existe confirmação antes da exclusão.

---

# Especialistas e atendentes

A página apresenta a seção:

```text
Especialistas / Atendentes
```

É exibida a mensagem:

```text
Os especialistas são os próprios usuários cadastrados da empresa.
Selecione um funcionário e vincule as especialidades que ele atende.
```

Essa frase representa diretamente o modelo adotado pela interface: o especialista é criado a partir de um usuário já existente.

---

## Carregamento dos especialistas

O módulo executa:

```python
especialistas = carregar_especialistas(empresa_id)
```

Os funcionários disponíveis para vínculo são derivados dos usuários da empresa:

```python
funcionarios = usuarios_empresa["usuario"].tolist()
```

Quando não existem funcionários:

```text
Cadastre um funcionário antes de vincular especialidades.
```

---

## Seleção do funcionário

Quando existem funcionários, é exibido:

```python
funcionario_selecionado = st.selectbox(
    "Selecionar funcionário",
    funcionarios,
    index=None,
    placeholder="Selecione um funcionário"
)
```

A configuração das especialidades só é apresentada quando um funcionário é selecionado.

---

## Opções de serviços

O código cria um dicionário:

```python
opcoes_servicos = {
    row["nome"]: row["id"]
    for _, row in servicos.iterrows()
}
```

O formato é:

```text
nome do serviço → ID do serviço
```

Caso não existam serviços, o dicionário fica vazio:

```python
{}
```

---

## Carregamento das especialidades atuais

A página chama:

```python
ids_atuais = carregar_ids_servicos_especialista(
    funcionario_selecionado,
    empresa_id,
)
```

Depois converte os IDs atuais em nomes:

```python
nomes_atuais = [
    nome
    for nome, servico_id in opcoes_servicos.items()
    if servico_id in ids_atuais
]
```

Esses nomes são utilizados como valores iniciais do `multiselect`.

---

## Seleção das especialidades

A interface utiliza:

```python
especialidades = st.multiselect(
    "Especialidades que esse funcionário atende",
    list(opcoes_servicos.keys()),
    default=nomes_atuais
)
```

Depois converte novamente os nomes selecionados em IDs:

```python
servicos_ids = [
    opcoes_servicos[nome]
    for nome in especialidades
]
```

---

## Salvamento do vínculo

Ao clicar em:

```text
Salvar especialidades do funcionário
```

a página chama:

```python
cadastrar_especialista(
    funcionario_selecionado,
    servicos_ids,
    empresa_id,
)
```

Após a operação:

```python
st.success("Especialidades atualizadas com sucesso.")
limpar_formularios()
st.rerun()
```

A função é usada tanto para cadastrar quanto para atualizar o vínculo das especialidades do funcionário.

O retorno não é verificado nesta página.

---

## Listagem dos especialistas

Quando `especialistas` não está vazio:

```python
if not especialistas.empty:
```

a página apresenta:

```python
st.dataframe(
    especialistas,
    use_container_width=True,
    hide_index=True,
)
```

As colunas exibidas dependem do retorno de `carregar_especialistas()`.

---

# Mensagem final

Ao final da página é exibida:

```python
st.success(
    "Configurações operacionais salvas por empresa."
)
```

Essa mensagem é exibida sempre que a função chega ao final, independentemente de uma alteração ter sido realizada naquela execução.

Ela não representa, por si só, o retorno de uma operação de salvamento específica.

---

# Funções importadas

## Banco de dados

```python
from database.db import conectar
```

Utilizada diretamente na exclusão de usuários.

---

## Configurações e especialistas

O módulo importa de `services.configuracoes_service`:

```python
carregar_especialistas
carregar_servicos
cadastrar_especialista
cadastrar_servico
carregar_ids_servicos_especialista
excluir_especialista_por_nome
excluir_servico
```

| Função | Uso |
|---|---|
| `carregar_especialistas()` | Lista especialistas da empresa |
| `carregar_servicos()` | Lista serviços ou especialidades |
| `cadastrar_especialista()` | Salva o vínculo entre funcionário e serviços |
| `cadastrar_servico()` | Cadastra um serviço da empresa |
| `carregar_ids_servicos_especialista()` | Obtém os serviços atuais de um funcionário |
| `excluir_especialista_por_nome()` | Remove o especialista associado ao usuário excluído |
| `excluir_servico()` | Exclui uma especialidade |

---

## Usuários

O módulo importa de `services.usuarios_service`:

```python
listar_usuarios
criar_usuario
alterar_senha
```

| Função | Uso |
|---|---|
| `listar_usuarios()` | Carrega os usuários cadastrados |
| `criar_usuario()` | Cria um funcionário da empresa |
| `alterar_senha()` | Atualiza a senha de um usuário |

---

# Dependências

O módulo utiliza diretamente:

```python
import streamlit as st
```

Também depende de:

```text
database.db
services.configuracoes_service
services.usuarios_service
```

O retorno das funções de listagem é tratado como DataFrame, embora o pandas não seja importado diretamente nesta página.

---

# Fluxo da página

```text
Acesso à página
       │
       ▼
Obtém empresa_id e empresa da sessão
       │
       ▼
Carrega todos os usuários
       │
       ▼
Filtra usuários da empresa atual
       │
       ├── Criar usuário
       ├── Excluir usuário
       └── Alterar senha
       │
       ▼
Carrega serviços da empresa
       │
       ├── Cadastrar serviço
       └── Excluir especialidade
       │
       ▼
Carrega especialistas
       │
       ▼
Seleciona funcionário
       │
       ▼
Carrega especialidades atuais
       │
       ▼
Salva novos vínculos
       │
       ▼
Exibe tabela de especialistas
```

---

# Limitações observadas no código atual

O módulo não implementa diretamente:

- confirmação antes de excluir usuários;
- confirmação antes de excluir serviços;
- proteção contra exclusão do próprio usuário;
- proteção contra exclusão do último administrador;
- redefinição de senha por e-mail;
- validação de complexidade da senha;
- controle de permissões por ação;
- edição do nome do usuário;
- edição do nível de acesso;
- busca e filtros nas tabelas;
- tratamento local de exceções;
- auditoria de alterações;
- registro de quem realizou cada operação;
- verificação do retorno de cadastro e exclusão de serviços;
- verificação do retorno do vínculo de especialistas.

---

# Pontos de atenção

## Filtro por nome da empresa

Os usuários são filtrados usando:

```python
usuarios["empresa"] == st.session_state.empresa
```

Portanto, o filtro depende da igualdade textual do nome da empresa.

A página não utiliza `empresa_id` nessa filtragem.

---

## Exclusão direta no banco

A exclusão do usuário não é totalmente delegada ao serviço de usuários.

O módulo executa diretamente:

```sql
DELETE FROM usuarios
WHERE id = ?
```

Isso cria dependência entre a interface e a estrutura do banco de dados.

Uma futura alteração na tabela `usuarios` pode exigir mudança neste arquivo.

---

## Exclusão por nome do especialista

Antes de apagar o usuário, o vínculo de especialista é removido por:

```python
excluir_especialista_por_nome(
    usuario_nome,
    empresa_id,
)
```

Portanto, essa operação depende do nome do usuário para localizar o especialista.

---

## Alteração de senha por nome

A função:

```python
alterar_senha(
    usuario_alterar,
    nova_senha_alterar,
)
```

recebe apenas o nome do usuário e a senha.

A documentação não deve afirmar que a função diferencia usuários homônimos por empresa sem analisar seu código.

---

## Mensagem de sucesso permanente

A mensagem:

```text
Configurações operacionais salvas por empresa.
```

é apresentada ao final da renderização, mesmo quando nenhuma operação foi executada.

Ela deve ser entendida como uma mensagem informativa da página, e não como confirmação de uma ação específica.

---

# Possíveis evoluções

O módulo pode evoluir com:

- controle de permissões por funcionalidade;
- confirmação antes de exclusões;
- prevenção da exclusão do último administrador;
- prevenção da exclusão do usuário autenticado;
- redefinição segura de senha;
- validação de força da senha;
- alteração do nível de acesso;
- edição dos dados do funcionário;
- uso exclusivo de serviços para operações de banco;
- vínculos por ID de usuário em vez de nome;
- filtros e pesquisa;
- logs de auditoria;
- tratamento centralizado de exceções;
- mensagens de sucesso condicionadas ao retorno das operações.

Essas funcionalidades são possibilidades futuras e não fazem parte da implementação atual.

---

# Resumo

O módulo `configuracoes.py` centraliza as configurações operacionais da empresa.

Ele permite:

- criar e excluir funcionários;
- alterar senhas;
- cadastrar e excluir serviços;
- vincular especialidades aos funcionários;
- visualizar usuários, serviços e especialistas.

A página combina chamadas a serviços internos com uma operação direta no banco de dados para exclusão de usuários.

O escopo empresarial é controlado por `empresa_id` em parte das operações e pelo nome da empresa na filtragem dos usuários.