# Serviço – Produtos

## Arquivo

`dashboard/services/produtos_service.py`

---

# Objetivo

O módulo `produtos_service.py` implementa as operações de persistência relacionadas aos produtos cadastrados no dashboard.

Ele é responsável por:

- definir as categorias disponíveis;
- criar a tabela de produtos;
- listar produtos por empresa;
- carregar produtos;
- cadastrar produtos;
- atualizar produtos;
- excluir produtos.

As operações utilizam a função:

```python
conectar()
```

importada de:

```python
database.db
```

---

# Dependências

O módulo importa:

```python
import pandas as pd
```

e:

```python
from database.db import conectar
```

O pandas é utilizado para retornar a listagem de produtos como um DataFrame.

---

# Categorias de produtos

O módulo define a constante:

```python
CATEGORIAS_PRODUTOS = [
    "Serviço",
    "Produto",
    "Plano",
    "Marketing",
    "Automação",
    "Website"
]
```

As categorias disponíveis são:

| Categoria |
|---|
| Serviço |
| Produto |
| Plano |
| Marketing |
| Automação |
| Website |

Essa lista pode ser utilizada pela interface para limitar ou apresentar as opções de categoria.

O serviço não valida internamente se a categoria recebida pertence a essa lista.

---

# Criação da tabela

A função:

```python
def criar_tabela_produtos():
```

garante a existência da tabela:

```text
produtos
```

A consulta executada é:

```sql
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    empresa_id INTEGER DEFAULT 1,
    nome TEXT,
    categoria TEXT,
    descricao TEXT,
    preco REAL DEFAULT 0,
    ativo INTEGER DEFAULT 1,
    criado_em TEXT DEFAULT CURRENT_TIMESTAMP
)
```

---

# Campos da tabela

| Campo | Tipo | Finalidade |
|---|---|---|
| `id` | INTEGER | Identificador do produto |
| `empresa_id` | INTEGER | Empresa vinculada ao produto |
| `nome` | TEXT | Nome do produto |
| `categoria` | TEXT | Categoria do produto |
| `descricao` | TEXT | Descrição do produto |
| `preco` | REAL | Preço cadastrado |
| `ativo` | INTEGER | Indica se o produto está ativo |
| `criado_em` | TEXT | Data e hora de criação |

---

## Valores padrão

O código define os seguintes valores padrão:

```text
empresa_id = 1
preco = 0
ativo = 1
criado_em = CURRENT_TIMESTAMP
```

Os campos:

- nome;
- categoria;
- descrição;

não possuem restrição `NOT NULL`.

Portanto, a tabela permite valores nulos nesses campos.

---

# Função criar_tabela_produtos()

```python
def criar_tabela_produtos():
```

Fluxo:

1. abre conexão com o banco;
2. cria um cursor;
3. executa `CREATE TABLE IF NOT EXISTS`;
4. realiza `commit`;
5. fecha a conexão.

Como utiliza:

```sql
CREATE TABLE IF NOT EXISTS
```

a função pode ser chamada várias vezes sem recriar a tabela existente.

---

# Função listar_produtos()

```python
def listar_produtos(empresa_id=1):
```

A função lista os produtos vinculados a uma empresa.

O parâmetro possui o valor padrão:

```python
empresa_id=1
```

---

## Criação preventiva da tabela

Antes da consulta, executa:

```python
criar_tabela_produtos()
```

---

## Consulta SQL

A consulta executada é:

```sql
SELECT *
FROM produtos
WHERE empresa_id = ?
ORDER BY id DESC
```

O parâmetro é enviado por:

```python
params=(empresa_id,)
```

---

## Ordenação

Os produtos são ordenados por:

```text
id decrescente
```

Assim, os registros mais recentes tendem a aparecer primeiro.

---

## Retorno

A consulta utiliza:

```python
pd.read_sql_query()
```

A função retorna um:

```python
pandas.DataFrame
```

contendo todas as colunas da tabela.

---

# Função carregar_produtos()

```python
def carregar_produtos(empresa_id=1):
```

Essa função apenas chama:

```python
listar_produtos(empresa_id)
```

Implementação:

```python
return listar_produtos(empresa_id)
```

Ela não possui lógica adicional.

Na prática, funciona como um alias para `listar_produtos()`.

---

# Função cadastrar_produto()

```python
def cadastrar_produto(
    empresa_id,
    nome,
    categoria,
    descricao,
    preco,
    ativo=1
):
```

Essa função insere um novo produto na tabela.

---

## Parâmetros

| Parâmetro | Finalidade |
|---|---|
| `empresa_id` | Identifica a empresa proprietária |
| `nome` | Nome do produto |
| `categoria` | Categoria do produto |
| `descricao` | Descrição |
| `preco` | Preço |
| `ativo` | Situação do produto |

O parâmetro `ativo` possui:

```python
ativo=1
```

como valor padrão.

---

## Criação preventiva da tabela

Antes da inserção:

```python
criar_tabela_produtos()
```

---

## Consulta SQL

A consulta executada é:

```sql
INSERT INTO produtos (
    empresa_id,
    nome,
    categoria,
    descricao,
    preco,
    ativo
)
VALUES (?, ?, ?, ?, ?, ?)
```

Os valores são enviados na mesma ordem:

```python
(
    empresa_id,
    nome,
    categoria,
    descricao,
    preco,
    ativo
)
```

---

## Finalização

Após a inserção:

```python
conn.commit()
conn.close()
```

---

## Retorno

A função não possui uma instrução explícita de retorno.

Portanto, em Python, seu retorno é:

```python
None
```

Ela não retorna:

- ID do produto;
- confirmação booleana;
- número de registros;
- produto criado.

---

# Função atualizar_produto()

```python
def atualizar_produto(
    produto_id,
    nome,
    categoria,
    descricao,
    preco,
    ativo=1
):
```

Essa função atualiza os dados de um produto existente.

---

## Campos atualizados

A consulta altera:

- nome;
- categoria;
- descrição;
- preço;
- status ativo.

---

## Consulta SQL

```sql
UPDATE produtos
SET
    nome = ?,
    categoria = ?,
    descricao = ?,
    preco = ?,
    ativo = ?
WHERE id = ?
```

---

## Conversão do ID

O identificador é convertido para inteiro:

```python
int(produto_id)
```

Se o valor recebido não puder ser convertido para inteiro, ocorrerá uma exceção.

---

## Escopo da atualização

A atualização utiliza somente:

```sql
WHERE id = ?
```

Ela não utiliza:

```sql
AND empresa_id = ?
```

Portanto, a própria função não verifica se o produto pertence à empresa atual.

O isolamento por empresa depende da camada que chama essa função.

---

## Finalização

Após executar o `UPDATE`:

```python
conn.commit()
conn.close()
```

---

## Retorno

A função não retorna valor explícito.

Seu retorno é:

```python
None
```

Ela também não verifica:

```python
cursor.rowcount
```

Por isso, não informa se algum produto foi realmente encontrado ou alterado.

---

# Função excluir_produto()

```python
def excluir_produto(produto_id):
```

Essa função remove um produto da tabela.

---

## Criação preventiva da tabela

Antes da exclusão:

```python
criar_tabela_produtos()
```

---

## Consulta SQL

```sql
DELETE FROM produtos
WHERE id = ?
```

---

## Conversão do ID

O identificador é convertido por:

```python
int(produto_id)
```

---

## Escopo da exclusão

A exclusão utiliza somente:

```sql
WHERE id = ?
```

Não existe validação com:

```sql
empresa_id
```

Assim, a função não confirma internamente se o produto pertence à empresa autenticada.

---

## Finalização

Após a exclusão:

```python
conn.commit()
conn.close()
```

---

## Retorno

A função não retorna valor explícito.

Seu retorno é:

```python
None
```

Ela não informa:

- se o produto existia;
- se algum registro foi excluído;
- quantos registros foram removidos.

---

# Fluxo do módulo

```text
Página de Produtos
        │
        ▼
Chama produtos_service
        │
        ├── listar_produtos()
        ├── cadastrar_produto()
        ├── atualizar_produto()
        └── excluir_produto()
        │
        ▼
Conexão com o banco
        │
        ▼
Tabela produtos
```

---

# Fluxo de cadastro

```text
Recebe os dados do produto
        │
        ▼
Garante que a tabela exista
        │
        ▼
Abre conexão
        │
        ▼
Executa INSERT
        │
        ▼
Commit
        │
        ▼
Fecha conexão
```

---

# Fluxo de atualização

```text
Recebe produto_id e novos dados
        │
        ▼
Converte produto_id para inteiro
        │
        ▼
Executa UPDATE por ID
        │
        ▼
Commit
        │
        ▼
Fecha conexão
```

---

# Fluxo de exclusão

```text
Recebe produto_id
        │
        ▼
Converte produto_id para inteiro
        │
        ▼
Executa DELETE por ID
        │
        ▼
Commit
        │
        ▼
Fecha conexão
```

---

# Controle por empresa

A função de listagem aplica o filtro:

```sql
WHERE empresa_id = ?
```

Isso permite listar somente produtos vinculados a uma empresa específica.

Entretanto, as funções de atualização e exclusão utilizam apenas o ID do produto.

Resumo:

| Operação | Validação por `empresa_id` |
|---|---|
| Listagem | Sim |
| Cadastro | Recebe e grava |
| Atualização | Não |
| Exclusão | Não |

---

# Validações implementadas

O serviço não possui validações explícitas para:

- nome vazio;
- categoria vazia;
- categoria inválida;
- descrição;
- preço negativo;
- preço não numérico;
- empresa inexistente;
- produto duplicado;
- status ativo;
- propriedade do produto;
- existência do produto antes de atualizar;
- existência do produto antes de excluir.

Essas validações, caso existam, precisam estar na interface ou em outra camada.

---

# Tratamento de erros

O módulo não possui blocos:

```python
try
except
```

Erros de conexão, conversão ou banco serão propagados para a camada chamadora.

Também não existe rollback explícito.

---

# Integridade dos dados

O campo:

```text
empresa_id
```

não possui uma chave estrangeira declarada no `CREATE TABLE`.

O código não define:

```sql
FOREIGN KEY
```

Portanto, este arquivo não garante que o `empresa_id` informado exista na tabela de empresas.

---

# Status ativo

O campo:

```text
ativo
```

é armazenado como inteiro.

Valores esperados na utilização atual:

```text
1 = ativo
0 = inativo
```

Porém, o banco não possui uma restrição que limite o campo apenas a `0` ou `1`.

---

# Pontos de atenção

## Retornos das funções

As funções:

```python
cadastrar_produto()
atualizar_produto()
excluir_produto()
```

não retornam confirmação.

Isso significa que a interface não consegue confirmar diretamente pelo retorno do serviço se a operação afetou algum registro.

---

## Atualização sem empresa_id

A atualização localiza o produto somente pelo ID:

```sql
WHERE id = ?
```

Em um sistema multiempresa, seria mais seguro incluir também:

```sql
AND empresa_id = ?
```

Essa proteção não está implementada atualmente.

---

## Exclusão sem empresa_id

A exclusão também utiliza apenas o ID.

Por isso, a camada chamadora precisa garantir que o produto selecionado pertença à empresa autenticada.

---

## Ausência de campos obrigatórios

A tabela não define `NOT NULL` para:

- nome;
- categoria;
- descrição;
- preço;
- ativo.

O serviço também não valida esses campos antes de inserir.

---

## Alias carregar_produtos()

A função:

```python
carregar_produtos()
```

não adiciona comportamento diferente.

Ela apenas reutiliza `listar_produtos()`.

---

## Criação da tabela durante as operações

Cada operação chama:

```python
criar_tabela_produtos()
```

Isso garante que a tabela exista, mas mistura a responsabilidade de criação estrutural do banco com as operações normais do serviço.

---

# O que o módulo não implementa

O arquivo não implementa:

- busca por nome;
- filtros por categoria;
- paginação;
- controle de estoque;
- código SKU;
- imagens;
- descontos;
- preço promocional;
- histórico de preço;
- auditoria;
- exclusão lógica;
- validação de empresa;
- chave estrangeira;
- tratamento de exceções;
- confirmação de operação;
- autenticação;
- controle de permissão;
- proteção multiempresa nas alterações;
- integração com pedidos;
- atualização automática de produtos relacionados.

---

# Possíveis evoluções

O serviço pode evoluir com:

- retorno do ID cadastrado;
- retorno booleano nas operações;
- validação de campos obrigatórios;
- validação de preço;
- validação das categorias;
- proteção por `empresa_id`;
- chave estrangeira para empresas;
- exclusão lógica;
- busca e filtros;
- paginação;
- controle de estoque;
- SKU;
- imagens;
- logs de auditoria;
- tratamento de erros;
- rollback;
- uso de migrations;
- separação entre estrutura do banco e serviço.

Essas possibilidades não fazem parte da implementação atual.

---

# Resumo

O módulo `produtos_service.py` implementa o CRUD básico de produtos do dashboard.

Ele permite:

- criar a tabela;
- listar produtos por empresa;
- cadastrar produtos;
- atualizar produtos;
- excluir produtos;
- utilizar categorias predefinidas.

A listagem respeita o `empresa_id`, mas atualização e exclusão utilizam apenas o identificador do produto.

As funções de cadastro, atualização e exclusão não retornam confirmação e não possuem validações internas ou tratamento de exceções.