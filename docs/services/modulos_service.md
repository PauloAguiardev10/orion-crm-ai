# Serviço – Módulos

## Arquivo

`dashboard/services/modulos_service.py`

---

# Objetivo

O módulo `modulos_service.py` administra os módulos adicionais disponíveis no sistema e a associação desses módulos às empresas.

Ele é responsável por:

- criar a tabela de módulos;
- criar a tabela de associação entre empresas e módulos;
- cadastrar módulos padrão;
- listar todos os módulos disponíveis;
- listar os módulos vinculados a uma empresa;
- substituir os módulos associados a uma empresa.

As operações utilizam:

```python
conectar()
```

importado de:

```python
database.db
```

---

# Dependências

O módulo importa:

```python
from database.db import conectar
import pandas as pd
```

O pandas é utilizado para retornar as consultas em formato de `DataFrame`.

---

# Tabelas administradas

O arquivo trabalha com duas tabelas:

```text
modulos
empresa_modulos
```

A tabela `modulos` armazena o catálogo de módulos disponíveis.

A tabela `empresa_modulos` registra quais módulos estão associados a cada empresa.

---

# Função criar_tabelas_modulos()

```python
def criar_tabelas_modulos():
```

Essa função:

1. cria a tabela `modulos`;
2. cria a tabela `empresa_modulos`;
3. cadastra os módulos padrão;
4. fecha a conexão com o banco.

---

# Tabela modulos

A estrutura criada é:

```sql
CREATE TABLE IF NOT EXISTS modulos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT UNIQUE,
    valor REAL DEFAULT 0
)
```

## Campos

| Campo | Finalidade |
|---|---|
| `id` | Identificador do módulo |
| `nome` | Nome do módulo |
| `valor` | Valor associado ao módulo |

O campo `nome` possui restrição:

```sql
UNIQUE
```

Isso impede módulos com nomes exatamente iguais.

O campo não possui `NOT NULL`.

---

# Tabela empresa_modulos

A estrutura criada é:

```sql
CREATE TABLE IF NOT EXISTS empresa_modulos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    empresa_id INTEGER,
    modulo_id INTEGER
)
```

## Campos

| Campo | Finalidade |
|---|---|
| `id` | Identificador da associação |
| `empresa_id` | Empresa vinculada |
| `modulo_id` | Módulo vinculado |

A tabela representa uma relação entre empresas e módulos.

Uma empresa pode possuir vários módulos.

Um mesmo módulo pode ser associado a várias empresas.

---

# Módulos padrão

A função define os seguintes módulos:

```python
modulos_padrao = [
    ("Instagram Direct", 80),
    ("Facebook Messenger", 80),
    ("IA Vendas", 200),
    ("PIX Automático", 100),
    ("Link de Pagamento", 100),
    ("Relatórios Avançados", 150),
    ("Multi IA", 200)
]
```

## Catálogo inicial

| Módulo | Valor |
|---|---:|
| Instagram Direct | 80 |
| Facebook Messenger | 80 |
| IA Vendas | 200 |
| PIX Automático | 100 |
| Link de Pagamento | 100 |
| Relatórios Avançados | 150 |
| Multi IA | 200 |

O código não informa moeda ou periodicidade desses valores.

---

# Inserção dos módulos padrão

Para cada item, a função executa:

```sql
INSERT OR IGNORE INTO modulos (
    nome,
    valor
)
VALUES (?, ?)
```

O comando:

```sql
INSERT OR IGNORE
```

evita erro quando já existe um módulo com o mesmo nome.

Como `nome` é `UNIQUE`, o módulo existente é mantido.

O valor de um módulo já existente não é atualizado automaticamente.

---

# Commits da criação

A função realiza um primeiro:

```python
conn.commit()
```

após criar as tabelas.

Depois realiza outro:

```python
conn.commit()
```

após inserir os módulos padrão.

Ao final:

```python
conn.close()
```

---

# Função listar_modulos()

```python
def listar_modulos():
```

Essa função retorna todos os módulos cadastrados.

Antes da consulta:

```python
criar_tabelas_modulos()
```

Isso garante que:

- as tabelas existam;
- os módulos padrão tenham sido cadastrados.

---

## Consulta

```sql
SELECT *
FROM modulos
ORDER BY nome
```

Os módulos são ordenados alfabeticamente pelo nome.

---

## Retorno

A função utiliza:

```python
pd.read_sql_query()
```

e retorna um:

```python
pandas.DataFrame
```

com todas as colunas da tabela.

---

# Função listar_modulos_empresa()

```python
def listar_modulos_empresa(
    empresa_id
):
```

Essa função retorna os módulos vinculados a uma empresa específica.

Antes da consulta:

```python
criar_tabelas_modulos()
```

---

## Consulta

```sql
SELECT
    modulos.id,
    modulos.nome,
    modulos.valor

FROM empresa_modulos

LEFT JOIN modulos
    ON modulos.id = empresa_modulos.modulo_id

WHERE empresa_modulos.empresa_id = ?
```

---

# Relacionamento utilizado

A consulta parte da tabela:

```text
empresa_modulos
```

e utiliza:

```sql
LEFT JOIN modulos
```

para recuperar:

- ID do módulo;
- nome;
- valor.

O filtro é aplicado por:

```text
empresa_id
```

---

# Retorno

A função retorna um:

```python
pandas.DataFrame
```

com as colunas:

- `id`;
- `nome`;
- `valor`.

Não existe uma cláusula `ORDER BY` nessa consulta.

Portanto, a ordem dos registros não é explicitamente garantida pelo código.

---

# Função salvar_modulos_empresa()

```python
def salvar_modulos_empresa(
    empresa_id,
    modulos_ids
):
```

Essa função substitui todos os módulos associados a uma empresa.

---

# Remoção das associações existentes

Primeiro, executa:

```sql
DELETE FROM empresa_modulos
WHERE empresa_id = ?
```

Todas as associações atuais da empresa são removidas.

---

# Inserção das novas associações

Depois, percorre:

```python
for modulo_id in modulos_ids:
```

Para cada ID, executa:

```sql
INSERT INTO empresa_modulos (
    empresa_id,
    modulo_id
)
VALUES (?, ?)
```

---

# Comportamento de substituição

A função não adiciona módulos de forma incremental.

Ela trabalha com substituição total:

```text
associações antigas
        │
        ▼
DELETE
        │
        ▼
insere somente os IDs recebidos
```

Se `modulos_ids` estiver vazio, a empresa ficará sem módulos associados.

---

# Finalização

Após as inserções:

```python
conn.commit()
conn.close()
```

A função não possui retorno explícito.

Seu retorno é:

```python
None
```

---

# Fluxo geral

```text
Dashboard
    │
    ▼
modulos_service
    │
    ├── criar_tabelas_modulos()
    ├── listar_modulos()
    ├── listar_modulos_empresa()
    └── salvar_modulos_empresa()
    │
    ▼
Banco de dados
```

---

# Fluxo de inicialização

```text
Abre conexão
     │
     ▼
Cria tabela modulos
     │
     ▼
Cria tabela empresa_modulos
     │
     ▼
Commit
     │
     ▼
Insere módulos padrão
     │
     ▼
Commit
     │
     ▼
Fecha conexão
```

---

# Fluxo de salvamento dos módulos da empresa

```text
Recebe empresa_id e lista de módulos
                │
                ▼
Exclui associações atuais da empresa
                │
                ▼
Percorre os IDs recebidos
                │
                ▼
Insere cada associação
                │
                ▼
Commit
                │
                ▼
Fecha conexão
```

---

# Controle por empresa

A tabela `empresa_modulos` utiliza o campo:

```text
empresa_id
```

As funções:

```python
listar_modulos_empresa()
salvar_modulos_empresa()
```

trabalham com esse identificador.

O catálogo da tabela `modulos` é global e não possui `empresa_id`.

Isso significa que os módulos disponíveis são compartilhados entre todas as empresas.

Somente as associações são específicas por empresa.

---

# Validações implementadas

O módulo não possui validações explícitas antes das operações.

A restrição:

```sql
nome TEXT UNIQUE
```

evita nomes exatamente duplicados na tabela `modulos`.

O comando:

```sql
INSERT OR IGNORE
```

evita falha ao cadastrar novamente os módulos padrão.

---

# Validações não implementadas

O código não verifica:

- se a empresa existe;
- se o módulo existe;
- se `modulos_ids` é uma lista;
- se existem IDs duplicados na lista;
- se o valor do módulo é negativo;
- se o nome do módulo está vazio;
- se uma associação já existe;
- se o módulo pertence a algum plano específico.

---

# Integridade dos dados

A tabela `empresa_modulos` não declara chaves estrangeiras.

Não existem comandos como:

```sql
FOREIGN KEY (empresa_id)
REFERENCES empresas(id)
```

ou:

```sql
FOREIGN KEY (modulo_id)
REFERENCES modulos(id)
```

Também não existe restrição única para a combinação:

```text
empresa_id + modulo_id
```

Assim, associações duplicadas podem ser inseridas caso `modulos_ids` contenha IDs repetidos.

---

# Tratamento de erros

O módulo não utiliza:

```python
try
except
```

Também não possui:

```python
rollback()
```

Erros de banco são propagados para a camada que chamou a função.

---

# Pontos de atenção

## Tecnologia de banco

Este código utiliza recursos típicos do SQLite:

```sql
AUTOINCREMENT
INSERT OR IGNORE
?
```

Por isso, sua implementação atual está alinhada ao SQLite.

---

## Catálogo global

Os módulos não pertencem individualmente a uma empresa.

A tabela `modulos` funciona como catálogo global.

---

## Valores não são atualizados

O uso de:

```sql
INSERT OR IGNORE
```

faz com que um módulo já existente seja ignorado.

Caso o valor definido no código seja alterado posteriormente, o banco não será atualizado automaticamente.

Exemplo:

```text
valor existente no banco: 80
novo valor no código: 100
```

O registro continuará com `80`, pois o `INSERT` será ignorado.

---

## Substituição completa

A função:

```python
salvar_modulos_empresa()
```

remove todas as associações antes de inserir as novas.

Se ocorrer um erro após o `DELETE` e antes do `commit`, o comportamento dependerá da transação e do encerramento da conexão.

Não há tratamento explícito com rollback.

---

## Ausência de criação preventiva no salvamento

Diferentemente das funções de listagem, `salvar_modulos_empresa()` não chama:

```python
criar_tabelas_modulos()
```

Portanto, ela pressupõe que as tabelas já existam.

Se for chamada antes da inicialização das tabelas, poderá gerar erro.

---

## IDs não convertidos

Os IDs recebidos em:

```python
modulos_ids
```

são inseridos diretamente.

Não existe conversão explícita para:

```python
int(modulo_id)
```

---

## Funções sem retorno de confirmação

A função:

```python
salvar_modulos_empresa()
```

não informa:

- quantos módulos foram salvos;
- se a empresa existia;
- se os módulos existiam;
- se a operação foi concluída.

---

# O módulo não implementa

Este arquivo não implementa:

- cadastro manual de novos módulos;
- edição de módulos;
- exclusão de módulos;
- atualização de valores;
- ativação ou desativação;
- cobrança automática;
- periodicidade;
- histórico de preços;
- autenticação;
- permissões;
- auditoria;
- chaves estrangeiras;
- proteção contra associações duplicadas;
- paginação;
- filtros;
- tratamento local de exceções.

---

# Possíveis evoluções

O módulo pode evoluir com:

- chaves estrangeiras;
- restrição única em `empresa_id` e `modulo_id`;
- validação da existência da empresa;
- validação dos módulos recebidos;
- conversão dos IDs para inteiro;
- controle transacional com rollback;
- atualização dos valores padrão;
- cadastro e edição administrativa de módulos;
- campo de status ativo;
- periodicidade de cobrança;
- retorno da quantidade de registros associados;
- criação preventiva das tabelas em `salvar_modulos_empresa()`.

Esses recursos não fazem parte da implementação atual.

---

# Resumo

O módulo `modulos_service.py` administra um catálogo global de módulos adicionais e os vínculos desses módulos com as empresas.

Ele cria as tabelas necessárias, cadastra sete módulos padrão, lista o catálogo completo, consulta os módulos de uma empresa e substitui todas as associações existentes por uma nova seleção.

A implementação utiliza SQLite, não possui chaves estrangeiras ou tratamento de exceções e pressupõe que as tabelas já estejam criadas quando `salvar_modulos_empresa()` for executada.