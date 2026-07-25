# Serviço – Configurações

## Arquivo

`dashboard/services/configuracoes_service.py`

---

# Objetivo

O módulo `configuracoes_service.py` implementa as operações de persistência utilizadas na área de configurações do dashboard.

Ele administra:

- serviços cadastrados por empresa;
- especialistas cadastrados por empresa;
- associação entre especialistas e serviços;
- remoção de especialistas;
- remoção de serviços;
- correção de especialistas duplicados;
- remoção de associações duplicadas;
- criação e atualização das tabelas relacionadas.

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

O pandas é utilizado para retornar serviços e especialistas em formato de `DataFrame`.

---

# Tabelas administradas

O módulo trabalha com três tabelas:

```text
especialistas
servicos
especialista_servicos
```

A tabela `especialista_servicos` representa o relacionamento entre especialistas e serviços.

---

# Função garantir_tabelas_config()

```python
def garantir_tabelas_config():
```

Essa função garante que as três tabelas necessárias existam.

Ela também verifica se cada uma delas possui a coluna:

```text
empresa_id
```

---

## Tabela especialistas

A estrutura definida é:

```sql
CREATE TABLE IF NOT EXISTS especialistas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    empresa_id INTEGER DEFAULT 1,
    nome TEXT NOT NULL
)
```

### Campos

| Campo | Finalidade |
|---|---|
| `id` | Identificador do especialista |
| `empresa_id` | Empresa à qual o especialista pertence |
| `nome` | Nome do especialista |

O campo `nome` é obrigatório no banco devido a:

```sql
NOT NULL
```

---

## Tabela servicos

A estrutura definida é:

```sql
CREATE TABLE IF NOT EXISTS servicos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    empresa_id INTEGER DEFAULT 1,
    nome TEXT NOT NULL
)
```

### Campos

| Campo | Finalidade |
|---|---|
| `id` | Identificador do serviço |
| `empresa_id` | Empresa proprietária do serviço |
| `nome` | Nome do serviço |

O campo `nome` também é obrigatório.

---

## Tabela especialista_servicos

A estrutura definida é:

```sql
CREATE TABLE IF NOT EXISTS especialista_servicos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    empresa_id INTEGER DEFAULT 1,
    especialista_id INTEGER NOT NULL,
    servico_id INTEGER NOT NULL
)
```

### Campos

| Campo | Finalidade |
|---|---|
| `id` | Identificador da associação |
| `empresa_id` | Empresa proprietária da associação |
| `especialista_id` | ID do especialista |
| `servico_id` | ID do serviço |

Essa tabela permite associar um especialista a vários serviços.

Também permite que um mesmo serviço seja associado a vários especialistas.

---

# Migração automática de empresa_id

Após criar as tabelas, a função percorre:

```python
[
    "especialistas",
    "servicos",
    "especialista_servicos"
]
```

Para cada tabela, executa:

```sql
PRAGMA table_info(nome_da_tabela)
```

Depois verifica se existe a coluna:

```text
empresa_id
```

Caso a coluna não exista, executa:

```sql
ALTER TABLE nome_da_tabela
ADD COLUMN empresa_id INTEGER DEFAULT 1
```

Esse comportamento funciona como uma migração simples para tabelas criadas em versões anteriores do sistema.

---

# Função limpar_especialistas_duplicados()

```python
def limpar_especialistas_duplicados(empresa_id=1):
```

Essa função identifica especialistas duplicados dentro de uma empresa e consolida seus relacionamentos.

O parâmetro possui valor padrão:

```python
empresa_id=1
```

---

## Identificação de nomes duplicados

A consulta utilizada é:

```sql
SELECT nome
FROM especialistas
WHERE empresa_id = ?
GROUP BY LOWER(TRIM(nome))
HAVING COUNT(*) > 1
```

Os nomes são comparados utilizando:

```sql
LOWER(TRIM(nome))
```

Isso significa que diferenças de:

- letras maiúsculas e minúsculas;
- espaços no início;
- espaços no final;

são ignoradas.

Exemplos tratados como equivalentes:

```text
Luciano
luciano
 Luciano
Luciano 
```

---

## Compatibilidade com tipos de linha

Ao ler o resultado, o código verifica:

```python
hasattr(item, "keys")
```

Isso permite acessar registros retornados como:

- objetos semelhantes a `sqlite3.Row`;
- tuplas comuns.

Para registros com chaves:

```python
item["nome"]
```

Para tuplas:

```python
item[0]
```

O mesmo padrão é utilizado em outras funções do módulo.

---

## Seleção do registro principal

Para cada nome duplicado, a função consulta todos os IDs:

```sql
SELECT id
FROM especialistas
WHERE empresa_id = ?
AND LOWER(TRIM(nome)) = LOWER(TRIM(?))
ORDER BY id ASC
```

O primeiro ID é mantido:

```python
id_principal = ids[0]
```

Os demais são considerados duplicados:

```python
ids_duplicados = ids[1:]
```

Portanto, o registro mais antigo, considerando o menor ID, é preservado.

---

## Transferência das associações

Antes de excluir um especialista duplicado, a função atualiza as associações existentes:

```sql
UPDATE especialista_servicos
SET especialista_id = ?
WHERE especialista_id = ?
AND empresa_id = ?
```

As associações do ID duplicado passam a apontar para o ID principal.

---

## Exclusão do especialista duplicado

Depois da transferência:

```sql
DELETE FROM especialistas
WHERE id = ?
AND empresa_id = ?
```

Somente o registro duplicado pertencente à empresa informada é removido.

---

## Remoção de associações duplicadas

Após consolidar os especialistas, a função executa:

```sql
DELETE FROM especialista_servicos
WHERE id NOT IN (
    SELECT MIN(id)
    FROM especialista_servicos
    WHERE empresa_id = ?
    GROUP BY empresa_id, especialista_id, servico_id
)
AND empresa_id = ?
```

Para cada combinação de:

```text
empresa_id
especialista_id
servico_id
```

é mantida a associação com o menor ID.

As associações repetidas são excluídas.

---

## Finalização

Ao final:

```python
conn.commit()
conn.close()
```

A função não possui retorno explícito.

Seu retorno em Python é:

```python
None
```

---

# Função carregar_servicos()

```python
def carregar_servicos(empresa_id=1):
```

Essa função retorna os serviços cadastrados para uma empresa.

Antes da consulta:

```python
garantir_tabelas_config()
```

---

## Consulta

```sql
SELECT *
FROM servicos
WHERE empresa_id = ?
ORDER BY id
```

A consulta é filtrada por:

```text
empresa_id
```

Os registros são ordenados por ID crescente.

---

## Retorno

A função retorna:

```python
pandas.DataFrame
```

com todas as colunas da tabela `servicos`.

---

# Função carregar_especialistas()

```python
def carregar_especialistas(empresa_id=1):
```

Essa função carrega os especialistas e reúne os serviços associados a cada um.

Antes da consulta, executa:

```python
garantir_tabelas_config()
limpar_especialistas_duplicados(empresa_id)
```

Portanto, a leitura dos especialistas também aciona a limpeza de duplicidades.

---

## Consulta

```sql
SELECT
    especialistas.id,
    especialistas.empresa_id,
    especialistas.nome,
    GROUP_CONCAT(servicos.nome, ', ') AS especialidades
FROM especialistas
LEFT JOIN especialista_servicos
    ON especialista_servicos.especialista_id = especialistas.id
    AND especialista_servicos.empresa_id = especialistas.empresa_id
LEFT JOIN servicos
    ON servicos.id = especialista_servicos.servico_id
    AND servicos.empresa_id = especialistas.empresa_id
WHERE especialistas.empresa_id = ?
GROUP BY especialistas.id, especialistas.empresa_id, especialistas.nome
ORDER BY especialistas.id
```

---

## Relacionamentos utilizados

O primeiro `LEFT JOIN` conecta:

```text
especialistas
```

com:

```text
especialista_servicos
```

O segundo conecta:

```text
especialista_servicos
```

com:

```text
servicos
```

Os relacionamentos também verificam o `empresa_id`.

---

## GROUP_CONCAT

A função utiliza:

```sql
GROUP_CONCAT(servicos.nome, ', ')
```

Os nomes dos serviços associados são reunidos em uma única string.

Exemplo:

```text
Tráfego Pago, Social Media, Web Design
```

Essa string é retornada na coluna:

```text
especialidades
```

Caso um especialista não possua serviços associados, o valor poderá ser nulo.

---

## Retorno

A função retorna um:

```python
pandas.DataFrame
```

com as colunas:

- `id`;
- `empresa_id`;
- `nome`;
- `especialidades`.

---

# Função carregar_ids_servicos_especialista()

```python
def carregar_ids_servicos_especialista(
    nome,
    empresa_id=1
):
```

Essa função retorna os IDs dos serviços associados ao especialista identificado pelo nome.

---

## Busca do especialista

A consulta é:

```sql
SELECT id
FROM especialistas
WHERE empresa_id = ?
AND LOWER(TRIM(nome)) = LOWER(TRIM(?))
ORDER BY id ASC
LIMIT 1
```

A comparação ignora:

- diferença entre maiúsculas e minúsculas;
- espaços no início e no final.

O nome recebido é tratado com:

```python
nome.strip()
```

---

## Especialista não encontrado

Caso nenhum registro seja localizado:

```python
if not especialista:
    conn.close()
    return []
```

O retorno é uma lista vazia.

---

## Busca das associações

Após obter o ID:

```sql
SELECT servico_id
FROM especialista_servicos
WHERE empresa_id = ?
AND especialista_id = ?
```

---

## Retorno

A função retorna uma lista contendo os IDs dos serviços.

Exemplo:

```python
[1, 3, 5]
```

Não retorna os nomes dos serviços.

---

# Função cadastrar_servico()

```python
def cadastrar_servico(
    nome,
    empresa_id=1
):
```

Essa função cadastra um serviço para uma empresa.

---

## Validação inicial

A função verifica:

```python
if not nome.strip():
    return False
```

Nomes vazios ou compostos apenas por espaços não são aceitos.

---

## Verificação de duplicidade

Antes da inserção:

```sql
SELECT id
FROM servicos
WHERE empresa_id = ?
AND LOWER(TRIM(nome)) = LOWER(TRIM(?))
```

A duplicidade é verificada dentro da mesma empresa.

A comparação ignora letras maiúsculas, minúsculas e espaços externos.

---

## Serviço já existente

Se o serviço já estiver cadastrado:

```python
conn.close()
return True
```

A função considera a operação bem-sucedida, mas não cria um novo registro.

Esse comportamento torna a função idempotente para nomes equivalentes dentro da mesma empresa.

---

## Inserção

Quando não existe:

```sql
INSERT INTO servicos (
    empresa_id,
    nome
)
VALUES (?, ?)
```

O nome é salvo após:

```python
nome.strip()
```

---

## Retorno

A função retorna:

```python
True
```

quando:

- o serviço já existe;
- o serviço é cadastrado com sucesso.

Retorna:

```python
False
```

somente quando o nome está vazio.

Não retorna o ID criado.

---

# Função cadastrar_especialista()

```python
def cadastrar_especialista(
    nome,
    servicos_ids,
    empresa_id=1
):
```

Essa função cria ou atualiza um especialista e substitui suas associações com serviços.

---

## Validação do nome

```python
if not nome.strip():
    return False
```

Nomes vazios não são aceitos.

Depois:

```python
nome = nome.strip()
```

---

## Busca de especialista existente

```sql
SELECT id
FROM especialistas
WHERE empresa_id = ?
AND LOWER(TRIM(nome)) = LOWER(TRIM(?))
ORDER BY id ASC
LIMIT 1
```

A busca considera a empresa e compara o nome sem diferenciar maiúsculas, minúsculas ou espaços externos.

---

## Especialista existente

Quando encontrado, o nome é atualizado:

```sql
UPDATE especialistas
SET nome = ?
WHERE id = ?
AND empresa_id = ?
```

O registro existente é reutilizado.

---

## Novo especialista

Quando não encontrado:

```sql
INSERT INTO especialistas (
    empresa_id,
    nome
)
VALUES (?, ?)
```

Depois da inserção:

```python
conn.commit()
especialista_id = cursor.lastrowid
```

O ID gerado é armazenado para criar as associações.

---

# Substituição das associações

Antes de inserir os serviços selecionados, a função remove todas as associações anteriores:

```sql
DELETE FROM especialista_servicos
WHERE empresa_id = ?
AND especialista_id = ?
```

Isso significa que a função não adiciona serviços incrementalmente.

Ela substitui a lista anterior pela nova lista recebida em:

```python
servicos_ids
```

---

## Inserção dos serviços

Para cada ID:

```python
for servico_id in servicos_ids:
```

é executado:

```sql
INSERT INTO especialista_servicos (
    empresa_id,
    especialista_id,
    servico_id
)
VALUES (?, ?, ?)
```

O ID do serviço é convertido para inteiro:

```python
int(servico_id)
```

---

## Limpeza posterior

Após concluir e fechar a conexão:

```python
limpar_especialistas_duplicados(empresa_id)
```

Isso consolida eventuais especialistas e associações duplicadas.

---

## Retorno

A função retorna:

```python
True
```

quando chega ao final.

Retorna:

```python
False
```

somente quando o nome está vazio.

---

# Função excluir_especialista_por_nome()

```python
def excluir_especialista_por_nome(
    nome,
    empresa_id=1
):
```

Essa função exclui todos os especialistas de uma empresa que possuam o nome informado, considerando a normalização por letras e espaços.

---

## Busca dos especialistas

```sql
SELECT id
FROM especialistas
WHERE empresa_id = ?
AND LOWER(TRIM(nome)) = LOWER(TRIM(?))
```

O nome é enviado como:

```python
nome.strip()
```

Diferentemente de outras consultas, não existe:

```sql
LIMIT 1
```

Portanto, todos os registros correspondentes são recuperados.

---

## Exclusão das associações

Para cada ID encontrado:

```sql
DELETE FROM especialista_servicos
WHERE empresa_id = ?
AND especialista_id = ?
```

As associações são removidas antes do especialista.

---

## Exclusão do especialista

Depois:

```sql
DELETE FROM especialistas
WHERE empresa_id = ?
AND id = ?
```

---

## Retorno

Ao final, a função retorna:

```python
True
```

Esse retorno ocorre mesmo quando nenhum especialista é encontrado.

A função não informa quantos registros foram excluídos.

---

# Função excluir_servico()

```python
def excluir_servico(
    servico_id,
    empresa_id=1
):
```

Essa função exclui um serviço e remove primeiro suas associações com especialistas.

---

## Exclusão das associações

```sql
DELETE FROM especialista_servicos
WHERE servico_id = ?
AND empresa_id = ?
```

---

## Exclusão do serviço

```sql
DELETE FROM servicos
WHERE id = ?
AND empresa_id = ?
```

O ID é convertido para inteiro nas duas consultas:

```python
int(servico_id)
```

---

## Retorno

A função sempre retorna:

```python
True
```

quando chega ao final.

Ela não verifica:

```python
cursor.rowcount
```

Portanto, não diferencia entre:

- serviço excluído;
- serviço inexistente;
- serviço pertencente a outra empresa.

---

# Fluxo de cadastro do especialista

```text
Recebe nome e IDs dos serviços
             │
             ▼
Valida o nome
             │
             ▼
Busca especialista equivalente
             │
       ┌─────┴─────┐
       │           │
       ▼           ▼
   Encontrado   Não encontrado
       │           │
       ▼           ▼
Atualiza nome    Insere registro
       │           │
       └─────┬─────┘
             ▼
Remove associações anteriores
             │
             ▼
Insere as novas associações
             │
             ▼
Commit e fechamento
             │
             ▼
Limpa duplicidades
             │
             ▼
Retorna True
```

---

# Fluxo da limpeza de duplicados

```text
Localiza nomes repetidos na empresa
             │
             ▼
Mantém o especialista de menor ID
             │
             ▼
Transfere associações dos duplicados
             │
             ▼
Exclui especialistas duplicados
             │
             ▼
Remove associações repetidas
```

---

# Controle multiempresa

As funções utilizam o parâmetro:

```python
empresa_id
```

com valor padrão:

```python
1
```

O filtro por empresa aparece nas operações de:

- listagem de serviços;
- listagem de especialistas;
- busca de especialista;
- cadastro de serviço;
- cadastro de especialista;
- exclusão de especialista;
- exclusão de serviço;
- limpeza de duplicidades;
- associações entre especialista e serviço.

Isso oferece um isolamento por empresa mais completo do que os serviços de produtos e pedidos analisados anteriormente.

---

# Validações implementadas

O módulo valida diretamente:

- nome vazio no cadastro de serviço;
- nome vazio no cadastro de especialista;
- duplicidade de serviço por empresa;
- duplicidade de especialista por nome normalizado;
- empresa nas consultas e alterações;
- conversão dos IDs dos serviços para inteiro;
- conversão do ID do serviço excluído para inteiro.

---

# Validações não implementadas

O módulo não verifica explicitamente:

- se `empresa_id` existe;
- se os IDs de serviços recebidos existem;
- se os serviços pertencem à mesma empresa;
- se `servicos_ids` é uma lista válida;
- se existem IDs repetidos na lista antes da inserção;
- tamanho máximo do nome;
- caracteres permitidos;
- relacionamento por chave estrangeira;
- existência do serviço antes da exclusão;
- existência do especialista antes da exclusão.

---

# Integridade dos relacionamentos

As tabelas não declaram chaves estrangeiras.

Não existem comandos como:

```sql
FOREIGN KEY (especialista_id)
REFERENCES especialistas(id)
```

ou:

```sql
FOREIGN KEY (servico_id)
REFERENCES servicos(id)
```

A consistência dos relacionamentos é mantida manualmente pelo código.

---

# Tratamento de erros

O módulo não utiliza:

```python
try
except
```

Erros do banco, erros de conversão ou valores inválidos são propagados para a camada chamadora.

Não existe rollback explícito em caso de falha.

---

# Pontos de atenção

## Limpeza durante a leitura

A função:

```python
carregar_especialistas()
```

não apenas consulta dados.

Ela também chama:

```python
limpar_especialistas_duplicados()
```

Portanto, uma operação de leitura pode alterar o banco de dados ao remover duplicidades.

---

## Substituição total de serviços

Ao cadastrar um especialista já existente, todas as associações anteriores são excluídas antes da criação das novas.

Assim, os IDs enviados representam a lista completa de serviços desejada.

---

## Serviço duplicado

`cadastrar_servico()` retorna `True` mesmo quando o serviço já existe.

A camada chamadora não consegue distinguir entre:

- serviço recém-cadastrado;
- serviço que já estava cadastrado.

---

## Exclusões retornam True

As funções:

```python
excluir_especialista_por_nome()
excluir_servico()
```

retornam `True` mesmo quando nenhuma linha é afetada.

---

## Especialistas identificados pelo nome

Algumas operações localizam especialistas pelo nome, e não pelo ID.

O nome é comparado com:

```sql
LOWER(TRIM(nome))
```

Essa regra reduz duplicidades de capitalização e espaçamento, mas nomes iguais na mesma empresa são tratados como o mesmo especialista.

---

## Associação sem validação prévia

`cadastrar_especialista()` insere os IDs recebidos sem consultar previamente a tabela `servicos`.

O arquivo não garante que cada ID:

- exista;
- pertença à empresa informada.

---

## Commit intermediário

Quando um novo especialista é criado, a função executa um `commit` logo após o `INSERT` para então obter e utilizar:

```python
cursor.lastrowid
```

Depois realiza outro `commit` após inserir as associações.

As duas partes não estão protegidas por uma transação única com tratamento de rollback.

---

# O módulo não implementa

Este arquivo não implementa:

- autenticação;
- controle de permissão;
- paginação;
- busca textual específica;
- edição separada do nome do serviço;
- edição por ID do especialista;
- chave estrangeira;
- exclusão em cascata definida no banco;
- logs de auditoria;
- histórico de alterações;
- tratamento local de exceções;
- rollback;
- retorno do ID cadastrado;
- confirmação da quantidade de registros alterados;
- validação da existência da empresa;
- validação da existência dos serviços associados.

---

# Possíveis evoluções

O módulo pode evoluir com:

- chaves estrangeiras;
- índice único para serviço por empresa;
- índice único para especialista por empresa;
- restrição única para associações;
- validação dos IDs dos serviços;
- uso do ID do especialista nas operações;
- retorno dos IDs criados;
- retorno da quantidade de registros alterados;
- transações atômicas;
- rollback em caso de erro;
- tratamento de exceções;
- separação entre migrações e operações normais;
- limpeza de duplicados executada fora da consulta;
- logs de auditoria.

Essas possibilidades não fazem parte da implementação atual.

---

# Resumo

O módulo `configuracoes_service.py` administra serviços, especialistas e seus relacionamentos no dashboard.

Ele permite:

- garantir a criação das tabelas necessárias;
- adicionar a coluna `empresa_id` em tabelas antigas;
- cadastrar serviços;
- cadastrar ou atualizar especialistas;
- associar especialistas a serviços;
- listar serviços por empresa;
- listar especialistas e suas especialidades;
- carregar os IDs dos serviços associados;
- excluir especialistas;
- excluir serviços;
- consolidar especialistas duplicados;
- remover associações duplicadas.

O módulo aplica filtros de `empresa_id` em praticamente todas as operações e possui uma rotina de limpeza de duplicidades. Entretanto, não utiliza chaves estrangeiras, não valida a existência dos IDs associados e não possui tratamento local de exceções.