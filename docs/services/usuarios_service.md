# Serviço – Usuários

## Arquivo

`dashboard/services/usuarios_service.py`

---

# Objetivo

O módulo `usuarios_service.py` implementa as operações relacionadas aos usuários do Orion CRM AI.

Ele é responsável por:

- criação da tabela de usuários;
- listagem de usuários;
- criação de novos usuários;
- atualização automática de usuários existentes;
- criação do administrador de uma empresa;
- alteração de senha;
- geração do hash das senhas.

Todas as operações utilizam SQLite através da função:

```python
conectar()
```

---

# Dependências

O módulo importa:

```python
import hashlib
import pandas as pd
```

Também utiliza:

```python
from database.db import conectar
```

---

# Estrutura da tabela

A função:

```python
criar_tabela_usuarios()
```

garante a existência da tabela:

```sql
usuarios
```

Caso ela não exista, executa:

```sql
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    empresa_id INTEGER,
    empresa TEXT NOT NULL,
    usuario TEXT UNIQUE NOT NULL,
    senha TEXT NOT NULL,
    nivel TEXT DEFAULT 'usuario'
)
```

---

# Campos da tabela

| Campo | Finalidade |
|--------|------------|
| id | Identificador do usuário |
| empresa_id | ID da empresa vinculada |
| empresa | Nome da empresa |
| usuario | Login do usuário |
| senha | Hash SHA-256 da senha |
| nivel | Nível de acesso |

---

# Função hash_senha()

```python
def hash_senha(senha):
```

Esta função gera o hash SHA-256 da senha.

Implementação:

```python
hashlib.sha256(
    senha.encode()
).hexdigest()
```

O retorno é uma string hexadecimal contendo o hash da senha.

O módulo nunca grava a senha em texto puro.

---

# Função criar_tabela_usuarios()

```python
def criar_tabela_usuarios():
```

Responsabilidades:

- abre conexão;
- cria a tabela caso não exista;
- realiza commit;
- encerra a conexão.

Ela pode ser chamada diversas vezes sem provocar erro devido ao uso de:

```sql
CREATE TABLE IF NOT EXISTS
```

---

# Função listar_usuarios()

```python
def listar_usuarios():
```

Antes da consulta:

```python
criar_tabela_usuarios()
```

Depois executa:

```sql
SELECT
    id,
    empresa_id,
    empresa,
    usuario,
    nivel
FROM usuarios
ORDER BY id
```

Importante:

O campo:

```text
senha
```

não é retornado.

A função devolve um:

```python
pandas.DataFrame
```

---

# Função criar_usuario()

```python
def criar_usuario(
    usuario,
    senha,
    empresa,
    nivel,
    empresa_id=None
)
```

Esta é a principal função do módulo.

Ela possui comportamento de:

```text
UPSERT
```

Ou seja:

- cria um novo usuário quando ele não existe;
- atualiza o usuário existente quando já existe.

---

## Validação inicial

A função verifica:

```python
if not usuario.strip()
```

```python
if not senha.strip()
```

```python
if not empresa.strip()
```

Caso algum esteja vazio:

```python
return False
```

Não existe validação para:

- tamanho mínimo;
- força da senha;
- caracteres especiais;
- nível informado;
- empresa_id.

---

## Criação da tabela

Antes de qualquer operação:

```python
criar_tabela_usuarios()
```

---

## Hash da senha

A senha recebida é convertida utilizando:

```python
senha_hash = hash_senha(senha)
```

A senha original nunca é gravada.

---

## Verificação do usuário

A consulta utilizada:

```sql
SELECT id
FROM usuarios
WHERE usuario = ?
```

O campo:

```text
usuario
```

é tratado como identificador único.

---

## Usuário existente

Quando encontrado:

```python
cursor.execute(
    UPDATE ...
)
```

São atualizados:

- empresa_id;
- empresa;
- senha;
- nível.

O nome do usuário não pode ser alterado.

A consulta:

```sql
UPDATE usuarios
SET empresa_id = ?,
    empresa = ?,
    senha = ?,
    nivel = ?
WHERE usuario = ?
```

---

## Novo usuário

Caso não exista:

```python
INSERT INTO usuarios (...)
```

São gravados:

- empresa_id;
- empresa;
- usuário;
- hash da senha;
- nível.

---

## Finalização

Após inserir ou atualizar:

```python
conn.commit()
conn.close()
```

Retorno:

```python
True
```

---

# Comportamento observado

A função sempre retorna:

```python
True
```

quando a execução chega ao final.

Ela não diferencia:

- inserção;
- atualização.

Também não verifica:

```python
cursor.rowcount
```

---

# Função criar_admin_empresa()

```python
def criar_admin_empresa(...)
```

Esta função apenas encapsula:

```python
criar_usuario(...)
```

Passando automaticamente:

```python
nivel="admin_empresa"
```

Parâmetros:

- empresa_id;
- empresa_nome;
- usuário;
- senha.

Não possui lógica adicional.

---

# Função alterar_senha()

```python
def alterar_senha(
    usuario,
    nova_senha
)
```

Responsável por atualizar somente a senha.

---

## Validação

Verifica:

```python
if not nova_senha.strip():
```

Caso esteja vazia:

```python
False
```

---

## Hash

A nova senha recebe:

```python
hash_senha(nova_senha)
```

---

## Atualização

Consulta:

```sql
UPDATE usuarios
SET senha = ?
WHERE usuario = ?
```

A busca utiliza:

```text
usuario
```

e não:

```text
id
```

---

## Retorno

Após o commit:

```python
alterado = cursor.rowcount > 0
```

Retorno:

```python
True
```

quando algum registro foi atualizado.

Caso contrário:

```python
False
```

---

# Fluxo do módulo

```text
Criar usuário
      │
      ▼
Validar campos
      │
      ▼
Criar tabela
      │
      ▼
Gerar hash SHA-256
      │
      ▼
Usuário existe?
      │
 ┌────┴────┐
 │         │
 ▼         ▼
UPDATE   INSERT
 │         │
 └────┬────┘
      ▼
 Commit
      │
      ▼
 Retorna True
```

---

# Segurança implementada

O módulo implementa:

- armazenamento de senha apenas em hash SHA-256;
- usuário único;
- validação básica de campos obrigatórios.

---

# O que este módulo NÃO implementa

Não existe implementação para:

- autenticação;
- login;
- geração de token;
- JWT;
- recuperação de senha;
- redefinição por e-mail;
- confirmação de senha;
- política de senha forte;
- expiração de senha;
- histórico de senhas;
- bloqueio por tentativas;
- controle de sessões;
- auditoria;
- permissões detalhadas;
- exclusão de usuários;
- alteração de nome de usuário;
- alteração de empresa;
- validação de nível informado;
- tratamento local de exceções.

---

# Pontos de atenção

## UPSERT manual

O módulo implementa um comportamento semelhante ao UPSERT através de:

```text
SELECT
```

seguido por:

```text
UPDATE
```

ou

```text
INSERT
```

Não utiliza recursos específicos do SQLite como:

```sql
INSERT ... ON CONFLICT
```

---

## Identificador utilizado

Toda atualização utiliza:

```text
usuario
```

como chave.

O campo:

```text
id
```

não é utilizado para localizar registros.

---

## SHA-256

O algoritmo utilizado é:

```text
SHA-256
```

Não há utilização de:

- salt;
- pepper;
- bcrypt;
- Argon2;
- PBKDF2.

O módulo apenas gera o hash direto da senha.

---

## empresa_id

O parâmetro:

```python
empresa_id=None
```

é opcional.

Portanto, o módulo permite criar usuários sem empresa vinculada.

---

## Retorno de criar_usuario()

Independentemente de ter ocorrido:

- INSERT
- UPDATE

o retorno é:

```python
True
```

Não existe indicação do tipo de operação realizada.

---

# Possíveis evoluções

O módulo pode evoluir com:

- bcrypt ou Argon2;
- autenticação JWT;
- redefinição de senha;
- confirmação de senha;
- política de senha forte;
- auditoria;
- logs;
- bloqueio por tentativas;
- controle de sessões;
- exclusão segura;
- alteração de login;
- permissões mais detalhadas;
- tratamento completo de exceções;
- utilização de UPSERT nativo do SQLite.

Esses recursos não fazem parte da implementação atual.

---

# Resumo

O módulo `usuarios_service.py` fornece a camada de persistência para usuários do Orion CRM AI.

Ele implementa:

- criação da tabela;
- hash SHA-256 das senhas;
- criação de usuários;
- atualização automática de usuários existentes;
- criação do administrador da empresa;
- alteração de senha;
- listagem de usuários.

A implementação atual é simples e objetiva, servindo como base para o gerenciamento de usuários do sistema, sem incluir autenticação ou controle avançado de segurança.