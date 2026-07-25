# Serviço – Configuração do Agente

## Arquivo

`dashboard/services/agente_service.py`

---

# Objetivo

O módulo `agente_service.py` é responsável por armazenar e gerenciar as configurações do agente SDR associadas a cada empresa.

Ele permite que cada empresa possua sua própria configuração operacional, definindo características como:

- nome do agente;
- tom de comunicação;
- nicho de atuação;
- objetivo principal;
- permissões de venda;
- integração com canais de atendimento.

Este serviço utiliza banco de dados SQLite e trabalha exclusivamente com a tabela:

```text
agente_config
```

---

# Dependências

O módulo importa:

```python
from database.db import conectar
import pandas as pd
```

A função:

```python
conectar()
```

é utilizada para abrir conexões com o banco de dados.

O pandas é utilizado para retornar consultas em formato de `DataFrame`.

---

# Tabela administrada

O módulo trabalha com uma única tabela:

```text
agente_config
```

Essa tabela possui uma configuração única para cada empresa.

O relacionamento é controlado pelo campo:

```text
empresa_id
```

que possui restrição:

```sql
UNIQUE
```

Assim, cada empresa pode possuir apenas um registro de configuração.

---

# Função criar_tabela_agente()

```python
def criar_tabela_agente():
```

Cria a tabela de configuração do agente caso ela ainda não exista.

---

## Estrutura da tabela

```sql
CREATE TABLE IF NOT EXISTS agente_config (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    empresa_id INTEGER UNIQUE,

    nome_agente TEXT DEFAULT 'Sofia',

    tom TEXT DEFAULT 'Humanizado',

    nicho TEXT,

    objetivo TEXT,

    ia_pode_vender BOOLEAN DEFAULT 0,

    ia_envia_pix BOOLEAN DEFAULT 0,

    ia_envia_link BOOLEAN DEFAULT 0,

    whatsapp BOOLEAN DEFAULT 1,

    instagram BOOLEAN DEFAULT 0,

    facebook BOOLEAN DEFAULT 0

)
```

---

# Campos

| Campo | Finalidade |
|--------|------------|
| id | Identificador interno |
| empresa_id | Empresa proprietária da configuração |
| nome_agente | Nome exibido pelo agente |
| tom | Estilo de comunicação |
| nicho | Nicho da empresa |
| objetivo | Objetivo comercial |
| ia_pode_vender | Permite venda automática |
| ia_envia_pix | Permite envio automático de PIX |
| ia_envia_link | Permite envio de link de pagamento |
| whatsapp | Atendimento via WhatsApp |
| instagram | Atendimento via Instagram |
| facebook | Atendimento via Facebook |

---

# Valores padrão

Quando uma configuração é criada automaticamente, os seguintes valores são utilizados:

| Campo | Valor |
|--------|-------|
| nome_agente | Sofia |
| tom | Humanizado |
| ia_pode_vender | False |
| ia_envia_pix | False |
| ia_envia_link | False |
| whatsapp | True |
| instagram | False |
| facebook | False |

Os campos:

```text
nicho
objetivo
```

não possuem valor padrão.

---

# Função carregar_config_agente()

```python
carregar_config_agente(
    empresa_id
)
```

Retorna a configuração do agente pertencente à empresa informada.

Antes da consulta, executa:

```python
criar_tabela_agente()
```

garantindo que a tabela exista.

---

## Consulta

```sql
SELECT *
FROM agente_config
WHERE empresa_id = ?
```

O resultado é carregado em um `DataFrame`.

---

# Configuração inexistente

Quando nenhuma configuração é encontrada:

```python
if config.empty:
```

o serviço executa:

```python
criar_config_padrao(
    empresa_id
)
```

Depois realiza novamente a consulta utilizando:

```python
return carregar_config_agente(
    empresa_id
)
```

Essa chamada recursiva garante que sempre exista um registro para a empresa antes do retorno.

---

# Retorno

Quando existe configuração:

```python
return config.iloc[0]
```

O retorno é uma única linha do DataFrame, representada como uma `Series` do pandas.

---

# Função criar_config_padrao()

```python
criar_config_padrao(
    empresa_id
)
```

Cria a configuração inicial de uma empresa.

---

## Inserção

A função executa:

```sql
INSERT INTO agente_config (

    empresa_id

)
VALUES (?)
```

Somente o campo:

```text
empresa_id
```

é informado.

Todos os demais valores são preenchidos pelos valores padrão definidos na tabela.

---

# Finalização

Após a inserção:

```python
conn.commit()
conn.close()
```

A função não possui retorno.

---

# Função salvar_config_agente()

```python
salvar_config_agente(...)
```

Atualiza a configuração existente de uma empresa.

---

## Campos atualizados

A função altera:

- nome do agente;
- tom;
- nicho;
- objetivo;
- IA pode vender;
- IA envia PIX;
- IA envia link;
- WhatsApp;
- Instagram;
- Facebook.

---

## Consulta

```sql
UPDATE agente_config

SET

    nome_agente = ?,

    tom = ?,

    nicho = ?,

    objetivo = ?,

    ia_pode_vender = ?,

    ia_envia_pix = ?,

    ia_envia_link = ?,

    whatsapp = ?,

    instagram = ?,

    facebook = ?

WHERE empresa_id = ?
```

A atualização é feita utilizando:

```text
empresa_id
```

---

# Fluxo geral

```text
Dashboard
      │
      ▼
agente_service
      │
      ├── criar_tabela_agente()
      ├── carregar_config_agente()
      ├── criar_config_padrao()
      └── salvar_config_agente()
      │
      ▼
Banco de Dados
```

---

# Fluxo de carregamento

```text
Recebe empresa_id
        │
        ▼
Cria tabela (se necessário)
        │
        ▼
Consulta configuração
        │
        ├── Existe
        │      │
        │      ▼
        │   Retorna configuração
        │
        ▼
Não existe
        │
        ▼
Cria configuração padrão
        │
        ▼
Executa nova consulta
        │
        ▼
Retorna configuração criada
```

---

# Controle por empresa

Cada empresa possui apenas uma configuração.

Isso é garantido pela restrição:

```sql
empresa_id UNIQUE
```

Todas as consultas e atualizações utilizam:

```text
WHERE empresa_id = ?
```

---

# Configuração inicial

A criação automática garante que o sistema nunca trabalhe com uma empresa sem configuração.

Esse comportamento simplifica a lógica do Dashboard, pois elimina a necessidade de tratar ausência de registros.

---

# Validações implementadas

O módulo implementa:

- criação automática da tabela;
- criação automática da configuração padrão;
- atualização por empresa;
- uso de valores padrão definidos na estrutura da tabela.

---

# Validações não implementadas

O código não verifica:

- existência da empresa;
- validade do tom informado;
- tamanho do nome do agente;
- campos obrigatórios;
- tipos booleanos;
- limite de caracteres;
- duplicidade de empresa antes da inserção;
- existência da configuração antes do UPDATE.

---

# Tratamento de erros

O módulo não utiliza:

```python
try
except
```

Nem:

```python
rollback()
```

Qualquer exceção é propagada para a camada superior.

---

# Integridade dos dados

A tabela não declara chave estrangeira para:

```text
empresa_id
```

Assim, o banco não impede que uma configuração seja criada para uma empresa inexistente.

---

# Recursividade controlada

A função:

```python
carregar_config_agente()
```

utiliza uma chamada recursiva apenas quando a configuração ainda não existe.

Após criar o registro padrão, a nova consulta retorna normalmente.

Esse comportamento evita duplicação de código.

---

# Configuração padrão

O comportamento padrão do agente recém-criado é:

- nome: Sofia;
- comunicação humanizada;
- atendimento apenas pelo WhatsApp;
- sem vendas automáticas;
- sem envio automático de PIX;
- sem envio automático de links de pagamento.

Essas permissões podem ser alteradas posteriormente pela função `salvar_config_agente()`.

---

# O módulo não implementa

Este arquivo não implementa:

- múltiplas configurações por empresa;
- histórico de alterações;
- auditoria;
- versionamento;
- permissões por usuário;
- autenticação;
- exclusão da configuração;
- restauração para valores padrão;
- validações de negócio;
- sincronização com outros serviços;
- tratamento de exceções.

---

# Possíveis evoluções

O módulo pode evoluir com:

- chave estrangeira para `empresa_id`;
- validação da existência da empresa;
- controle transacional com rollback;
- histórico de alterações;
- registro do usuário responsável pela alteração;
- múltiplos perfis de agente;
- configuração por canal de atendimento;
- personalização do prompt do agente;
- horários de funcionamento;
- configuração de modelos de IA;
- retorno indicando sucesso da operação.

Esses recursos não fazem parte da implementação atual.

---

# Resumo

O módulo `agente_service.py` gerencia as configurações operacionais do agente SDR para cada empresa.

Ele garante que exista uma configuração única por empresa, cria automaticamente um registro padrão quando necessário e permite atualizar informações como nome do agente, tom de comunicação, objetivo comercial, canais habilitados e permissões de automação.

Sua implementação é simples e centraliza toda a configuração comportamental do agente em uma única tabela.