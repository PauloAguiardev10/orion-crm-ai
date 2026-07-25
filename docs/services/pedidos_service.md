# Serviço – Pedidos

## Arquivo

`dashboard/services/pedidos_service.py`

---

# Objetivo

O módulo `pedidos_service.py` implementa a camada de persistência dos pedidos do Orion CRM AI.

Ele é responsável por:

- definir os status dos pedidos;
- definir os status de pagamento;
- definir as formas de pagamento;
- criar e atualizar a estrutura da tabela `pedidos`;
- listar pedidos por empresa;
- cadastrar pedidos;
- salvar pedidos;
- atualizar pedidos;
- excluir pedidos.

Todas as operações utilizam a função:

```python
conectar()
```

do módulo:

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

O pandas é utilizado para retornar as consultas em formato `DataFrame`.

---

# Constantes do módulo

## STATUS_PAGAMENTO

```python
STATUS_PAGAMENTO = [
    "Pendente",
    "Pago",
    "Atrasado",
    "Cancelado"
]
```

Representa os possíveis estados do pagamento de um pedido.

---

## STATUS_PEDIDO

```python
STATUS_PEDIDO = [
    "Pendente",
    "Em andamento",
    "Concluído",
    "Cancelado"
]
```

Representa os possíveis estados operacionais do pedido.

---

## FORMAS_PAGAMENTO

```python
FORMAS_PAGAMENTO = [
    "Pix",
    "Cartão",
    "Boleto",
    "Dinheiro",
    "Transferência"
]
```

Define as formas de pagamento disponíveis.

O serviço apenas disponibiliza essas listas. Ele não valida se os valores recebidos pertencem a elas.

---

# Estrutura da tabela

A função:

```python
criar_tabela_pedidos()
```

garante a existência da tabela:

```sql
pedidos
```

Estrutura criada:

```sql
CREATE TABLE IF NOT EXISTS pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    empresa_id INTEGER DEFAULT 1,
    cliente TEXT,
    produto TEXT,
    quantidade INTEGER DEFAULT 1,
    valor_total REAL DEFAULT 0,
    status TEXT DEFAULT 'Pendente',
    status_pagamento TEXT DEFAULT 'Pendente',
    forma_pagamento TEXT DEFAULT 'Pix',
    criado_em TEXT DEFAULT CURRENT_TIMESTAMP
)
```

---

# Campos da tabela

| Campo | Finalidade |
|--------|------------|
| id | Identificador do pedido |
| empresa_id | Empresa proprietária |
| cliente | Nome do cliente |
| produto | Produto ou serviço |
| quantidade | Quantidade |
| valor_total | Valor total do pedido |
| status | Situação operacional |
| status_pagamento | Situação financeira |
| forma_pagamento | Forma utilizada |
| criado_em | Data e hora da criação |

---

# Migração automática da tabela

Após criar a tabela, a função executa:

```sql
PRAGMA table_info(pedidos)
```

para obter todas as colunas existentes.

Caso alguma coluna esteja ausente, ela é criada automaticamente utilizando:

```sql
ALTER TABLE pedidos
ADD COLUMN ...
```

São verificadas:

- status_pagamento
- forma_pagamento
- status

Esse comportamento funciona como uma migração simples da estrutura do banco.

---

# Função listar_pedidos()

```python
listar_pedidos(empresa_id=1)
```

Fluxo:

1. garante a existência da tabela;
2. abre conexão;
3. executa a consulta;
4. fecha conexão;
5. retorna um DataFrame.

Consulta:

```sql
SELECT *
FROM pedidos
WHERE empresa_id = ?
ORDER BY id DESC
```

A listagem é filtrada pelo `empresa_id`.

---

# Retorno

A função retorna:

```python
pandas.DataFrame
```

contendo todas as colunas da tabela.

---

# Função carregar_pedidos()

```python
carregar_pedidos(empresa_id=1)
```

Implementação:

```python
return listar_pedidos(empresa_id)
```

Ela funciona apenas como um alias para `listar_pedidos()`.

Não adiciona nenhuma regra de negócio.

---

# Função cadastrar_pedido()

```python
cadastrar_pedido(...)
```

Responsável pela inserção de novos pedidos.

Recebe:

- empresa_id
- cliente
- produto
- quantidade
- valor_total
- status
- status_pagamento
- forma_pagamento

Os parâmetros opcionais possuem os seguintes padrões:

```python
status="Pendente"
status_pagamento="Pendente"
forma_pagamento="Pix"
```

---

## Consulta SQL

```sql
INSERT INTO pedidos (
    empresa_id,
    cliente,
    produto,
    quantidade,
    valor_total,
    status,
    status_pagamento,
    forma_pagamento
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
```

Após a inserção:

```python
conn.commit()
conn.close()
```

A função não possui retorno explícito.

---

# Função salvar_pedido()

```python
salvar_pedido(...)
```

Esta função apenas encapsula:

```python
cadastrar_pedido(...)
```

Implementação:

```python
cadastrar_pedido(...)
```

Não existe lógica adicional.

---

# Função atualizar_pedido()

```python
atualizar_pedido(...)
```

Atualiza:

- cliente;
- produto;
- quantidade;
- valor_total;
- status;
- status_pagamento;
- forma_pagamento.

Consulta utilizada:

```sql
UPDATE pedidos
SET
    cliente = ?,
    produto = ?,
    quantidade = ?,
    valor_total = ?,
    status = ?,
    status_pagamento = ?,
    forma_pagamento = ?
WHERE id = ?
```

O identificador do pedido é convertido utilizando:

```python
int(pedido_id)
```

Após a atualização:

```python
conn.commit()
conn.close()
```

A função não retorna confirmação da operação.

Também não verifica:

```python
cursor.rowcount
```

---

# Função excluir_pedido()

```python
excluir_pedido(pedido_id)
```

Executa:

```sql
DELETE FROM pedidos
WHERE id = ?
```

O identificador recebido é convertido para inteiro:

```python
int(pedido_id)
```

Após a exclusão:

```python
conn.commit()
conn.close()
```

Não existe retorno indicando sucesso ou falha.

---

# Fluxo do módulo

```text
Dashboard
     │
     ▼
Pedidos Service
     │
     ├── listar_pedidos()
     ├── cadastrar_pedido()
     ├── salvar_pedido()
     ├── atualizar_pedido()
     └── excluir_pedido()
     │
     ▼
SQLite
```

---

# Fluxo de cadastro

```text
Recebe os dados
      │
      ▼
Garante tabela
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
Recebe pedido_id
      │
      ▼
Converte para inteiro
      │
      ▼
Executa UPDATE
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
Recebe pedido_id
      │
      ▼
Converte para inteiro
      │
      ▼
Executa DELETE
      │
      ▼
Commit
      │
      ▼
Fecha conexão
```

---

# Controle por empresa

A listagem utiliza:

```sql
WHERE empresa_id = ?
```

Entretanto:

- atualização;
- exclusão;

utilizam apenas:

```sql
WHERE id = ?
```

Assim, a proteção contra acesso entre empresas depende da camada que chama essas funções.

---

# Validações implementadas

O módulo não valida:

- cliente vazio;
- produto vazio;
- quantidade negativa;
- quantidade zero;
- valor negativo;
- forma de pagamento;
- status;
- status de pagamento;
- existência do produto;
- existência da empresa;
- existência do pedido.

---

# Tratamento de erros

O módulo não implementa:

```python
try
except
```

Qualquer exceção é propagada para a camada superior.

Também não existe rollback explícito.

---

# Integridade dos dados

O campo:

```text
empresa_id
```

não possui chave estrangeira declarada.

Também não existem relacionamentos explícitos para:

- clientes;
- produtos.

O arquivo apenas armazena os valores recebidos.

---

# Pontos de atenção

## Migração automática

A função `criar_tabela_pedidos()` atua também como uma migração simples da tabela, adicionando colunas ausentes quando necessário.

---

## salvar_pedido()

A função:

```python
salvar_pedido()
```

não implementa lógica própria.

Ela apenas reutiliza `cadastrar_pedido()`.

---

## Atualização

A atualização utiliza apenas:

```sql
WHERE id = ?
```

Não verifica:

```sql
empresa_id
```

---

## Exclusão

A exclusão também utiliza apenas:

```sql
WHERE id = ?
```

---

## Retorno das funções

As funções:

- cadastrar_pedido()
- salvar_pedido()
- atualizar_pedido()
- excluir_pedido()

não retornam confirmação da operação.

---

# O módulo não implementa

Este arquivo não implementa:

- estoque;
- cálculo automático do valor total;
- relacionamento com produtos;
- relacionamento com clientes;
- desconto;
- parcelamento;
- emissão de nota fiscal;
- geração de recibo;
- auditoria;
- exclusão lógica;
- paginação;
- filtros;
- busca;
- autenticação;
- controle de permissões;
- validação de status;
- validação das formas de pagamento;
- validação do valor.

---

# Possíveis evoluções

O serviço pode evoluir com:

- retorno booleano;
- retorno do ID do pedido;
- validação dos dados;
- relacionamento por chave estrangeira;
- cálculo automático do valor total;
- validação dos status;
- proteção multiempresa;
- logs;
- tratamento de exceções;
- rollback;
- exclusão lógica;
- filtros;
- paginação.

Esses recursos não fazem parte da implementação atual.

---

# Resumo

O módulo `pedidos_service.py` implementa o CRUD básico de pedidos do Orion CRM AI.

Ele permite:

- criar e atualizar a estrutura da tabela;
- listar pedidos por empresa;
- cadastrar pedidos;
- atualizar pedidos;
- excluir pedidos;
- disponibilizar listas de status e formas de pagamento.

Além do CRUD, ele possui um mecanismo simples de migração da tabela utilizando `PRAGMA table_info` e `ALTER TABLE`, garantindo compatibilidade com versões anteriores do banco de dados.