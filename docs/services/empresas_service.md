# Serviço – Empresas

## Arquivo

`dashboard/services/empresas_service.py`

---

# Objetivo

O módulo `empresas_service.py` implementa a camada de persistência responsável pelo cadastro básico das empresas do Orion CRM AI.

Ele é responsável por:

- criar a tabela de empresas;
- listar empresas;
- cadastrar empresas;
- definir automaticamente os módulos habilitados conforme o plano contratado.

Todas as operações utilizam:

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
import pandas as pd
```

e:

```python
from database.db import conectar
```

O pandas é utilizado para retornar consultas em formato de `DataFrame`.

---

# Planos disponíveis

O módulo define a constante:

```python
PLANOS = [
    "Lite",
    "Pro",
    "Premium"
]
```

Esses valores representam os planos aceitos pela aplicação.

O serviço não valida se o plano recebido pertence obrigatoriamente a essa lista.

---

# Estrutura da tabela

A função:

```python
criar_tabela_empresas()
```

garante a existência da tabela:

```sql
empresas
```

Estrutura criada:

```sql
CREATE TABLE IF NOT EXISTS empresas (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    nome TEXT UNIQUE NOT NULL,

    plano TEXT DEFAULT 'Lite',

    nicho TEXT,

    nome_agente TEXT DEFAULT 'Sofia',

    status TEXT DEFAULT 'ativa',

    whatsapp BOOLEAN DEFAULT 1,

    instagram BOOLEAN DEFAULT 0,

    facebook BOOLEAN DEFAULT 0,

    crm BOOLEAN DEFAULT 0,

    funil BOOLEAN DEFAULT 0,

    analytics BOOLEAN DEFAULT 0,

    vendas_ia BOOLEAN DEFAULT 0,

    criado_em TEXT DEFAULT CURRENT_TIMESTAMP
)
```

---

# Campos da tabela

| Campo | Finalidade |
|--------|------------|
| id | Identificador da empresa |
| nome | Nome da empresa |
| plano | Plano contratado |
| nicho | Segmento da empresa |
| nome_agente | Nome do agente virtual |
| status | Situação da empresa |
| whatsapp | Módulo WhatsApp |
| instagram | Módulo Instagram |
| facebook | Módulo Facebook |
| crm | CRM |
| funil | Funil Comercial |
| analytics | Analytics |
| vendas_ia | IA de vendas |
| criado_em | Data de criação |

---

# Valores padrão

A tabela define os seguintes padrões:

| Campo | Valor |
|--------|-------|
| plano | Lite |
| nome_agente | Sofia |
| status | ativa |
| whatsapp | 1 |
| instagram | 0 |
| facebook | 0 |
| crm | 0 |
| funil | 0 |
| analytics | 0 |
| vendas_ia | 0 |

---

# Função criar_tabela_empresas()

```python
def criar_tabela_empresas():
```

Fluxo:

1. abre conexão;
2. cria cursor;
3. executa `CREATE TABLE IF NOT EXISTS`;
4. realiza `commit`;
5. fecha conexão.

Como utiliza:

```sql
CREATE TABLE IF NOT EXISTS
```

a função pode ser executada diversas vezes sem recriar a tabela.

---

# Função listar_empresas()

```python
def listar_empresas():
```

Antes da consulta:

```python
criar_tabela_empresas()
```

Consulta executada:

```sql
SELECT *
FROM empresas
ORDER BY id DESC
```

Não existe filtro por empresa.

A função retorna:

```python
pandas.DataFrame
```

contendo todas as colunas.

---

# Função criar_empresa()

```python
def criar_empresa(
    nome,
    plano,
    nicho,
    nome_agente
)
```

Responsável pelo cadastro de uma empresa.

Além da inserção, define automaticamente quais módulos ficarão habilitados.

---

# Configuração inicial dos módulos

Inicialmente:

```python
whatsapp = True

instagram = False
facebook = False

crm = False
funil = False
analytics = False

vendas_ia = False
```

Ou seja:

| Módulo | Estado inicial |
|---------|----------------|
| WhatsApp | Ativado |
| Instagram | Desativado |
| Facebook | Desativado |
| CRM | Desativado |
| Funil | Desativado |
| Analytics | Desativado |
| IA Vendas | Desativado |

---

# Plano Lite

Quando o plano é:

```text
Lite
```

Nenhuma alteração é realizada.

A empresa permanece apenas com:

- WhatsApp habilitado.

---

# Plano Pro

Quando:

```python
plano in ["Pro", "Premium"]
```

são ativados:

```python
crm = True
funil = True
analytics = True
```

O plano Pro passa a possuir:

- WhatsApp
- CRM
- Funil
- Analytics

---

# Plano Premium

Quando:

```python
plano == "Premium"
```

também são ativados:

```python
instagram = True
facebook = True
vendas_ia = True
```

O Premium possui:

- WhatsApp
- Instagram
- Facebook
- CRM
- Funil
- Analytics
- IA de vendas

---

# Inserção

Após definir os módulos, executa:

```sql
INSERT INTO empresas (

    nome,
    plano,
    nicho,
    nome_agente,

    whatsapp,
    instagram,
    facebook,

    crm,
    funil,
    analytics,

    vendas_ia

)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```

Os valores enviados são exatamente os calculados anteriormente.

---

# Finalização

Após a inserção:

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

# Fluxo do cadastro

```text
Recebe dados da empresa
        │
        ▼
Define módulos padrão
        │
        ▼
Plano Lite?
        │
        ├── Sim
        │      │
        │      ▼
        │   Mantém apenas WhatsApp
        │
        ▼
Plano Pro ou Premium?
        │
        ▼
Ativa CRM
Ativa Funil
Ativa Analytics
        │
        ▼
É Premium?
        │
        ├── Não
        │
        ▼
Sim
        │
        ▼
Ativa Instagram
Ativa Facebook
Ativa IA Vendas
        │
        ▼
INSERT
        │
        ▼
Commit
```

---

# Módulos por plano

| Módulo | Lite | Pro | Premium |
|---------|:---:|:---:|:---:|
| WhatsApp | ✅ | ✅ | ✅ |
| CRM | ❌ | ✅ | ✅ |
| Funil | ❌ | ✅ | ✅ |
| Analytics | ❌ | ✅ | ✅ |
| Instagram | ❌ | ❌ | ✅ |
| Facebook | ❌ | ❌ | ✅ |
| IA de Vendas | ❌ | ❌ | ✅ |

---

# Validações implementadas

O serviço não implementa validações para:

- nome vazio;
- nicho vazio;
- plano inválido;
- nome do agente vazio;
- empresa duplicada antes do INSERT.

A única proteção existente é:

```sql
nome TEXT UNIQUE
```

definida na estrutura da tabela.

---

# Tratamento de erros

O módulo não utiliza:

```python
try
except
```

Erros de banco são propagados para a camada chamadora.

Também não existe rollback explícito.

---

# Integridade

O módulo não utiliza:

- chave estrangeira;
- relacionamento com usuários;
- relacionamento com parceiros;
- relacionamento com módulos.

Ele apenas grava os dados da empresa.

---

# Pontos de atenção

## Ativação automática

A principal responsabilidade deste serviço é ativar automaticamente os módulos conforme o plano informado.

Essa regra está totalmente implementada dentro da função `criar_empresa()`.

---

## WhatsApp sempre habilitado

Independentemente do plano:

```python
whatsapp = True
```

Sempre permanece ativo.

---

## Premium herda o Pro

Como o código primeiro executa:

```python
if plano in ["Pro", "Premium"]
```

e depois:

```python
if plano == "Premium"
```

o Premium herda automaticamente todos os recursos do plano Pro.

---

## Ausência de atualização

Este arquivo não implementa:

- atualização da empresa;
- alteração do plano;
- alteração dos módulos;
- exclusão.

Essas operações pertencem a outras partes do sistema.

---

# O módulo não implementa

O arquivo não implementa:

- edição;
- exclusão;
- filtros;
- busca;
- paginação;
- parceiro responsável;
- cobrança;
- mensalidade;
- serviços adicionais;
- bloqueio financeiro;
- upload de logo;
- autenticação;
- permissões;
- auditoria.

---

# Possíveis evoluções

O módulo pode evoluir com:

- atualização de empresa;
- exclusão;
- alteração automática de módulos após troca de plano;
- integração com cobrança;
- histórico de planos;
- parceiros;
- serviços adicionais;
- logs;
- tratamento de exceções;
- rollback;
- retorno do ID criado.

Esses recursos não fazem parte da implementação atual.

---

# Resumo

O módulo `empresas_service.py` implementa o cadastro básico das empresas do Orion CRM AI.

Sua principal responsabilidade é criar empresas e habilitar automaticamente os módulos correspondentes ao plano contratado.

Ele também fornece a listagem das empresas cadastradas e garante a criação da tabela `empresas`, mas não implementa atualização, exclusão ou controle financeiro.