# Serviço – Autenticação

## Arquivo

`dashboard/services/auth_service.py`

---

# Objetivo

O módulo `auth_service.py` implementa funções de autenticação e recuperação de informações do usuário logado.

Ele é responsável por:

- gerar hash de senha;
- garantir a existência da empresa padrão Forway;
- garantir a existência de um administrador inicial;
- validar login por nome ou e-mail;
- registrar a data do último acesso;
- localizar a empresa vinculada ao usuário;
- retornar o identificador da empresa;
- retornar o nível de acesso do usuário.

O serviço utiliza PostgreSQL e trabalha diretamente com as tabelas:

```text
empresas
usuarios
```

---

# Dependências

O módulo importa:

```python
import hashlib

from database.db import conectar
from psycopg2.extras import RealDictCursor
```

## hashlib

A biblioteca padrão `hashlib` é utilizada para gerar o hash das senhas.

## conectar()

A função:

```python
conectar()
```

abre a conexão com o PostgreSQL.

## RealDictCursor

O cursor:

```python
RealDictCursor
```

faz com que os registros retornados pelo PostgreSQL sejam acessados como dicionários.

Exemplo:

```python
empresa["id"]
resultado["nome"]
resultado["nivel"]
```

---

# Credenciais administrativas padrão

O módulo define três constantes:

```python
EMAIL_ADMIN_PADRAO = "admin@forway.local"
NOME_ADMIN_PADRAO = "admin"
SENHA_ADMIN_PADRAO = "123456"
```

Elas são usadas para criar o administrador inicial da plataforma.

| Constante | Valor |
|---|---|
| `EMAIL_ADMIN_PADRAO` | `admin@forway.local` |
| `NOME_ADMIN_PADRAO` | `admin` |
| `SENHA_ADMIN_PADRAO` | `123456` |

Esses valores estão definidos diretamente no código.

---

# Função criptografar_senha()

```python
def criptografar_senha(senha: str) -> str:
```

Essa função recebe uma senha em texto e retorna seu hash SHA-256.

Implementação:

```python
return hashlib.sha256(
    senha.encode("utf-8")
).hexdigest()
```

---

## Fluxo

```text
Senha em texto
      │
      ▼
Conversão para UTF-8
      │
      ▼
Aplicação do SHA-256
      │
      ▼
Conversão hexadecimal
      │
      ▼
Hash retornado
```

---

## Exemplo conceitual

Entrada:

```text
123456
```

Saída:

```text
hash hexadecimal SHA-256
```

A função sempre gera o mesmo hash para a mesma senha.

---

# Função garantir_tabelas_auth()

```python
def garantir_tabelas_auth():
```

Apesar do nome, essa função não cria tabelas.

A documentação interna do código informa que a estrutura do banco já existe no PostgreSQL.

A função garante apenas:

- existência da empresa Forway;
- existência de um administrador padrão;
- vínculo do administrador com a empresa Forway;
- nível administrativo;
- status ativo.

---

# Criação da empresa padrão

A função executa:

```sql
INSERT INTO empresas (
    nome,
    slug,
    plano,
    nicho,
    status
)
VALUES (%s, %s, %s, %s, %s)
ON CONFLICT (slug) DO NOTHING
```

Valores utilizados:

```text
nome: Forway
slug: forway
plano: Premium
nicho: Agência de marketing
status: ativa
```

---

## Controle de duplicidade

O comando:

```sql
ON CONFLICT (slug) DO NOTHING
```

impede a criação de outra empresa com o mesmo `slug`, desde que exista uma restrição única compatível no banco.

A função não atualiza os dados da empresa caso ela já exista.

---

# Recuperação da empresa Forway

Depois da inserção, a função consulta:

```sql
SELECT id
FROM empresas
WHERE slug = %s
LIMIT 1
```

Parâmetro:

```text
forway
```

O resultado é acessado por:

```python
empresa["id"]
```

---

## Empresa não encontrada

Caso a empresa não seja localizada, a função lança:

```python
RuntimeError(
    "Não foi possível localizar a empresa Forway."
)
```

Isso interrompe a inicialização da autenticação.

---

# Criação do administrador padrão

Após localizar a empresa, a função executa:

```sql
INSERT INTO usuarios (
    empresa_id,
    nome,
    email,
    senha_hash,
    nivel,
    status
)
VALUES (%s, %s, %s, %s, %s, %s)
ON CONFLICT (email) DO NOTHING
```

Dados cadastrados:

```text
empresa_id: ID da Forway
nome: admin
email: admin@forway.local
senha_hash: SHA-256 de 123456
nivel: orion_admin
status: ativo
```

---

## Usuário já existente

Caso o e-mail já exista:

```sql
ON CONFLICT (email) DO NOTHING
```

impede uma nova inserção.

A senha do usuário existente não é redefinida por esse comando.

---

# Atualização obrigatória do administrador

Depois da tentativa de inserção, a função executa:

```sql
UPDATE usuarios
SET
    empresa_id = %s,
    nivel = %s,
    status = %s,
    atualizado_em = CURRENT_TIMESTAMP
WHERE email = %s
```

Esse comando garante que o usuário padrão fique:

- vinculado à empresa Forway;
- com nível `orion_admin`;
- com status `ativo`;
- com `atualizado_em` atualizado.

A senha e o nome não são alterados nesse `UPDATE`.

---

# Controle transacional

A função utiliza transação explícita.

Em caso de sucesso:

```python
conn.commit()
```

Em caso de falha:

```python
conn.rollback()
raise
```

Ao final:

```python
cursor.close()
conn.close()
```

---

# Função validar_login()

```python
def validar_login(
    usuario: str,
    senha: str
) -> bool:
```

Valida as credenciais informadas pelo usuário.

---

# Inicialização da autenticação

Antes de consultar o usuário, a função chama:

```python
garantir_tabelas_auth()
```

Isso significa que cada tentativa de login também verifica a existência:

- da empresa Forway;
- do administrador padrão.

---

# Normalização do login

O valor informado é tratado com:

```python
login = usuario.strip().lower()
```

Isso:

- remove espaços das extremidades;
- converte o login para letras minúsculas.

---

# Hash da senha

A senha recebida é processada por:

```python
senha_hash = criptografar_senha(senha)
```

A comparação no banco ocorre entre hashes.

---

# Consulta de autenticação

A função executa:

```sql
SELECT usuarios.id
FROM usuarios

INNER JOIN empresas
    ON empresas.id = usuarios.empresa_id

WHERE (
    LOWER(usuarios.email) = %s
    OR LOWER(usuarios.nome) = %s
)
  AND usuarios.senha_hash = %s
  AND usuarios.status = 'ativo'
  AND empresas.status = 'ativa'

LIMIT 1
```

---

## Condições exigidas

O login será considerado válido somente quando:

- o e-mail ou nome corresponder ao login;
- o hash da senha estiver correto;
- o usuário estiver ativo;
- a empresa estiver ativa.

---

# Login por nome ou e-mail

A autenticação aceita:

```text
e-mail
```

ou:

```text
nome do usuário
```

As comparações são feitas com:

```sql
LOWER(...)
```

Portanto, não diferenciam letras maiúsculas e minúsculas.

---

# Atualização do último login

Quando o usuário é encontrado, a função executa:

```sql
UPDATE usuarios
SET ultimo_login_em = CURRENT_TIMESTAMP
WHERE id = %s
```

Depois:

```python
conn.commit()
```

E retorna:

```python
True
```

---

# Login inválido

Caso nenhuma correspondência seja encontrada:

```python
return False
```

Nesse caso, não existe alteração no banco.

---

# Tratamento de erros do login

Em caso de exceção:

```python
conn.rollback()
raise
```

No bloco final:

```python
cursor.close()
conn.close()
```

---

# Função obter_empresa_usuario()

```python
def obter_empresa_usuario(
    usuario: str
):
```

Retorna o nome da empresa associada ao usuário.

---

## Preparação

A função:

1. chama `garantir_tabelas_auth()`;
2. remove espaços do login;
3. converte o login para minúsculas;
4. abre uma conexão com o PostgreSQL.

---

## Consulta

```sql
SELECT empresas.nome
FROM usuarios

INNER JOIN empresas
    ON empresas.id = usuarios.empresa_id

WHERE (
    LOWER(usuarios.email) = %s
    OR LOWER(usuarios.nome) = %s
)
  AND usuarios.status = 'ativo'
  AND empresas.status = 'ativa'

LIMIT 1
```

---

## Retorno

Quando encontra o registro:

```python
return resultado["nome"]
```

Caso contrário:

```python
return None
```

A função não valida senha.

---

# Função obter_empresa_id_usuario()

```python
def obter_empresa_id_usuario(
    usuario: str
):
```

Retorna o identificador da empresa associada ao usuário.

---

## Consulta

```sql
SELECT empresas.id
FROM usuarios

INNER JOIN empresas
    ON empresas.id = usuarios.empresa_id

WHERE (
    LOWER(usuarios.email) = %s
    OR LOWER(usuarios.nome) = %s
)
  AND usuarios.status = 'ativo'
  AND empresas.status = 'ativa'

LIMIT 1
```

---

## Retorno

Quando encontra o usuário:

```python
return resultado["id"]
```

Quando não encontra:

```python
return None
```

A função também não verifica senha.

---

# Função obter_nivel_usuario()

```python
def obter_nivel_usuario(
    usuario: str
):
```

Retorna o nível de acesso do usuário.

---

## Consulta

```sql
SELECT usuarios.nivel
FROM usuarios

INNER JOIN empresas
    ON empresas.id = usuarios.empresa_id

WHERE (
    LOWER(usuarios.email) = %s
    OR LOWER(usuarios.nome) = %s
)
  AND usuarios.status = 'ativo'
  AND empresas.status = 'ativa'

LIMIT 1
```

---

## Retorno

Quando o usuário é encontrado:

```python
return resultado["nivel"]
```

Quando não é encontrado:

```python
return "usuario"
```

Diferentemente das funções de empresa, essa função não retorna `None` em caso de ausência.

Ela utiliza o nível padrão:

```text
usuario
```

---

# Fluxo de autenticação

```text
Usuário informa login e senha
            │
            ▼
garantir_tabelas_auth()
            │
            ▼
Normaliza nome ou e-mail
            │
            ▼
Gera SHA-256 da senha
            │
            ▼
Consulta usuário e empresa
            │
            ├── Não encontrado → False
            │
            ▼
Atualiza ultimo_login_em
            │
            ▼
Commit
            │
            ▼
Retorna True
```

---

# Fluxo de inicialização administrativa

```text
garantir_tabelas_auth()
          │
          ▼
Insere empresa Forway
          │
          ▼
Consulta ID da empresa
          │
          ├── Não encontrada → RuntimeError
          │
          ▼
Insere administrador padrão
          │
          ▼
Atualiza empresa, nível e status
          │
          ▼
Commit
```

---

# Controle por empresa

Todas as consultas de autenticação utilizam:

```sql
INNER JOIN empresas
    ON empresas.id = usuarios.empresa_id
```

Além disso, exigem:

```sql
empresas.status = 'ativa'
```

Assim, mesmo que o usuário esteja ativo, ele não poderá autenticar quando sua empresa estiver inativa.

---

# Controle de status

Para autenticação e recuperação de dados, são exigidos:

```text
usuarios.status = ativo
empresas.status = ativa
```

Um usuário inativo ou pertencente a empresa inativa não é retornado pelas consultas.

---

# Níveis de acesso

O arquivo utiliza diretamente dois níveis:

```text
orion_admin
usuario
```

O administrador padrão recebe:

```text
orion_admin
```

Quando `obter_nivel_usuario()` não encontra o registro, retorna:

```text
usuario
```

O módulo não contém a lógica de autorização baseada nesses níveis.

---

# Validações implementadas

O serviço realiza:

- remoção de espaços do login;
- conversão do login para minúsculas;
- comparação sem distinção entre maiúsculas e minúsculas;
- hash da senha antes da consulta;
- verificação do status do usuário;
- verificação do status da empresa;
- prevenção de duplicidade por `ON CONFLICT`;
- atualização da data do último login;
- transação com commit e rollback nas funções de escrita.

---

# Validações não implementadas

O módulo não valida explicitamente:

- login vazio;
- senha vazia;
- tamanho mínimo da senha;
- complexidade da senha;
- número de tentativas;
- bloqueio por tentativas incorretas;
- tempo de sessão;
- autenticação em dois fatores;
- alteração obrigatória da senha padrão;
- unicidade do nome do usuário;
- formato do e-mail;
- expiração de senha.

---

# Segurança da senha

A senha é transformada com:

```python
hashlib.sha256()
```

A implementação não utiliza:

- salt individual;
- bcrypt;
- Argon2;
- PBKDF2;
- fator de custo;
- versionamento do algoritmo.

SHA-256 é uma função de hash genérica e rápida. O código atual não aplica um mecanismo específico para armazenamento seguro de senhas.

---

# Credenciais padrão no código

As credenciais iniciais estão expostas no próprio arquivo:

```text
admin@forway.local
admin
123456
```

Além disso, `garantir_tabelas_auth()` mantém o administrador padrão ativo.

A implementação não exige que a senha inicial seja alterada após o primeiro acesso.

Esse é um ponto crítico antes de disponibilizar o sistema em produção.

---

# Efeito colateral das consultas

As seguintes funções chamam:

```python
garantir_tabelas_auth()
```

- `validar_login()`;
- `obter_empresa_usuario()`;
- `obter_empresa_id_usuario()`;
- `obter_nivel_usuario()`.

Consequentemente, operações aparentemente apenas consultivas podem:

- inserir a empresa Forway;
- inserir o administrador padrão;
- atualizar nível, empresa, status e data do administrador;
- realizar `commit`.

---

# Recuperação por nome

As consultas aceitam login pelo campo:

```text
usuarios.nome
```

Como utilizam:

```sql
LIMIT 1
```

e o código não demonstra uma restrição única para o nome, dois usuários com o mesmo nome podem tornar a seleção ambígua.

O banco retornará apenas um dos registros correspondentes.

---

# Funções sem tratamento de exceção explícito

As funções:

- `obter_empresa_usuario()`;
- `obter_empresa_id_usuario()`;
- `obter_nivel_usuario()`;

possuem `try` e `finally`, mas não possuem:

```python
except
```

As exceções são propagadas naturalmente para a camada superior.

Como são funções somente de leitura, não executam rollback local.

---

# Retornos das funções

| Função | Retorno |
|---|---|
| `criptografar_senha()` | hash em texto |
| `garantir_tabelas_auth()` | `None` |
| `validar_login()` | `True` ou `False` |
| `obter_empresa_usuario()` | nome da empresa ou `None` |
| `obter_empresa_id_usuario()` | ID da empresa ou `None` |
| `obter_nivel_usuario()` | nível encontrado ou `"usuario"` |

---

# O módulo não implementa

Este arquivo não implementa:

- criação de sessão;
- token JWT;
- cookie de autenticação;
- logout;
- recuperação de senha;
- troca de senha;
- cadastro comum de usuários;
- autenticação em dois fatores;
- bloqueio por tentativas;
- permissões por página;
- auditoria detalhada;
- logs de falhas;
- expiração de sessão;
- revogação de acesso;
- criptografia reversível;
- gestão de papéis e permissões.

---

# Possíveis evoluções

Possíveis melhorias futuras incluem:

- substituir SHA-256 por algoritmo próprio para senhas;
- remover a senha padrão do código;
- utilizar variáveis de ambiente;
- exigir troca da senha no primeiro acesso;
- separar inicialização administrativa da validação de login;
- impedir nomes de usuário duplicados;
- adicionar controle de tentativas;
- registrar falhas de autenticação;
- adicionar recuperação segura de senha;
- implementar autenticação em dois fatores;
- criar sessões com expiração;
- adicionar autorização por nível;
- retornar um objeto com dados completos do usuário autenticado.

Esses recursos não fazem parte da implementação atual.

---

# Resumo

O módulo `auth_service.py` implementa a autenticação básica do dashboard utilizando PostgreSQL.

Ele garante a existência da empresa Forway e de um administrador padrão, valida o login por nome ou e-mail, compara hashes de senha, registra o último acesso e recupera a empresa e o nível do usuário.

A implementação possui controle transacional nas operações de escrita e valida o status do usuário e da empresa. Entretanto, utiliza SHA-256 sem salt e mantém credenciais administrativas padrão diretamente no código, aspectos que precisam ser tratados antes de uma implantação segura em produção.