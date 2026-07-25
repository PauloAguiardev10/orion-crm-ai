# Serviço – Leads

## Arquivo

`dashboard/services/leads_service.py`

---

# Objetivo

O módulo `leads_service.py` implementa a camada de serviços responsável pela consulta, atualização e análise automática das leads cadastradas no Orion CRM AI.

Este serviço atua como ponte entre:

- Dashboard Streamlit;
- Banco de dados PostgreSQL;
- Serviço de análise de intenção (`intencao_service.py`).

Suas responsabilidades incluem:

- carregar leads do banco;
- preparar os dados para exibição no dashboard;
- atualizar informações comerciais;
- executar a classificação automática de novas leads.

---

# Dependências

O módulo importa:

```python
import pandas as pd
from datetime import datetime
```

e utiliza:

```python
from database.db import conectar
```

Também depende diretamente do módulo:

```python
services.intencao_service
```

Importando as funções:

```python
detectar_intencao()
calcular_score()
definir_temperatura()
gerar_resumo()
```

Essas funções são responsáveis pela análise automática da conversa.

---

# STATUS_LISTA

O módulo define os possíveis estados comerciais da lead:

```python
STATUS_LISTA = [
    "Aguardando atendimento",
    "Em atendimento",
    "Proposta enviada",
    "Negócio fechado",
    "Não fechado",
]
```

Essa constante pode ser utilizada pela interface para preencher listas de seleção.

O serviço não valida se o status informado pertence a essa lista.

---

# Função garantir_colunas_leads()

```python
garantir_colunas_leads()
```

Nesta versão do projeto a função não executa nenhuma alteração estrutural.

Seu conteúdo é apenas:

```python
return None
```

O comentário do código informa que:

- o banco utilizado é PostgreSQL;
- a estrutura das tabelas já existe;
- o Dashboard não deve criar nem alterar tabelas.

Essa função permanece apenas por compatibilidade com versões anteriores do sistema.

---

# Função carregar_leads()

```python
carregar_leads(empresa_id=1)
```

É a principal função do serviço.

Ela consulta todas as leads pertencentes a uma empresa e prepara os dados para exibição no Dashboard.

---

## Consulta SQL

A consulta utiliza:

```sql
SELECT
...
FROM leads

LEFT JOIN clientes
ON clientes.id = leads.cliente_id

WHERE leads.empresa_id = %s

ORDER BY leads.id DESC
```

O filtro é realizado pelo:

```text
empresa_id
```

---

## Histórico da conversa

A consulta possui uma subconsulta responsável por localizar o histórico mais recente do cliente:

```sql
SELECT conversas.historico
FROM conversas
...
ORDER BY conversas.id DESC
LIMIT 1
```

A busca considera:

- canal;
- telefone;
- nome;
- empresa.

Dessa forma, cada lead recebe automaticamente o último histórico registrado.

---

# Campos retornados

A consulta retorna:

- dados da lead;
- dados do cliente;
- histórico da conversa;
- classificação comercial;
- informações financeiras;
- resumo do vendedor;
- datas.

---

# Tratamento dos dados

Após a consulta, o serviço normaliza diversos campos utilizando `fillna()`.

## Status

Quando vazio:

```text
Aguardando atendimento
```

---

## Responsável

Quando vazio:

```text
Não atribuído
```

---

## Temperatura

Quando vazia:

```text
fria
```

---

## Prioridade

Quando vazia:

```text
baixa
```

---

## Produto

Quando vazio:

```text
Não identificado
```

---

## Canal

Quando vazio:

```text
WhatsApp
```

Depois ocorre uma padronização dos nomes:

| Valor recebido | Valor exibido |
|----------------|---------------|
| Facebook | Facebook Messenger |
| Messenger | Facebook Messenger |
| Instagram | Instagram Direct |

---

## Valores financeiros

Quando nulos:

```python
valor_negocio = 0
mensalidade = 0
```

---

## Campos de texto

São preenchidos com string vazia:

- motivo_perda;
- observacao_comercial.

---

# Conversão da data

O campo:

```python
criado_em
```

é convertido utilizando:

```python
pd.to_datetime()
```

com:

```python
errors="coerce"
```

Datas inválidas tornam-se valores nulos (`NaT`).

---

# Cálculo das horas desde a entrada

Após converter a data, o serviço calcula automaticamente:

```text
horas_desde_entrada
```

O cálculo utiliza:

```python
datetime.now()
```

e:

```python
total_seconds() / 3600
```

O resultado é arredondado para uma casa decimal.

Exemplo:

```text
4.3 horas
18.7 horas
52.1 horas
```

Essa informação é utilizada para acompanhamento operacional das leads.

---

# Retorno

A função retorna um:

```python
pandas.DataFrame
```

já tratado e pronto para utilização pelo Dashboard.

---

# Função atualizar_lead()

```python
atualizar_lead(...)
```

Atualiza os dados comerciais de uma lead existente.

Campos alterados:

- status;
- responsável;
- valor do negócio;
- mensalidade;
- motivo da perda;
- observação comercial;
- atualizado_em.

---

## Consulta SQL

```sql
UPDATE leads
SET
    status = %s,
    responsavel = %s,
    valor_negocio = %s,
    mensalidade = %s,
    motivo_perda = %s,
    observacao_comercial = %s,
    atualizado_em = CURRENT_TIMESTAMP
WHERE id = %s
```

---

## Conversão dos valores

Os campos monetários são convertidos utilizando:

```python
float(valor_negocio or 0)
float(mensalidade or 0)
```

O identificador é convertido por:

```python
int(lead_id)
```

---

## Controle transacional

Diferentemente de outros serviços, esta função utiliza transação explícita.

Em caso de sucesso:

```python
conn.commit()
```

Em caso de erro:

```python
conn.rollback()
```

Depois a exceção é propagada novamente através de:

```python
raise
```

Essa implementação evita alterações parciais no banco.

---

# Função analisar_lead_automaticamente()

```python
analisar_lead_automaticamente(
    nome,
    mensagem
)
```

Executa a classificação automática de uma conversa.

---

## Fluxo

Primeiro:

```python
detectar_intencao()
```

Depois:

```python
calcular_score()
```

Em seguida:

```python
definir_temperatura()
```

Por fim:

```python
gerar_resumo()
```

Cada etapa utiliza o resultado da etapa anterior.

---

# Resultado

A função retorna um dicionário contendo:

```python
{
    "intencao": ...,
    "score": ...,
    "temperatura": ...,
    "resumo": ...
}
```

Esses dados podem ser utilizados diretamente pelo Dashboard ou pelo agente SDR.

---

# Fluxo geral

```text
Dashboard
      │
      ▼
Leads Service
      │
      ├── Consulta PostgreSQL
      │
      ├── Trata valores nulos
      │
      ├── Padroniza canais
      │
      ├── Calcula horas da lead
      │
      └── Retorna DataFrame
```

---

# Fluxo da análise automática

```text
Mensagem do cliente
        │
        ▼
detectar_intencao()
        │
        ▼
calcular_score()
        │
        ▼
definir_temperatura()
        │
        ▼
gerar_resumo()
        │
        ▼
Retorna classificação completa
```

---

# Controle transacional

Entre todos os serviços documentados até o momento, este é o primeiro que implementa controle transacional explícito.

Operações realizadas:

- commit em caso de sucesso;
- rollback em caso de erro;
- propagação da exceção para a camada superior.

Esse comportamento aumenta a segurança das atualizações realizadas no PostgreSQL.

---

# Validações implementadas

O serviço realiza:

- preenchimento automático de campos nulos;
- padronização dos canais;
- conversão de datas;
- cálculo automático das horas da lead;
- conversão de valores monetários;
- rollback em caso de falha.

---

# Validações não implementadas

O módulo não verifica explicitamente:

- existência da lead antes da atualização;
- validade do status informado;
- existência do responsável;
- existência da empresa;
- limite mínimo ou máximo dos valores financeiros.

Essas verificações devem ser realizadas em outras camadas do sistema.

---

# Pontos de atenção

## Compatibilidade com PostgreSQL

O código utiliza parâmetros no formato:

```sql
%s
```

compatíveis com PostgreSQL, diferentemente dos serviços baseados em SQLite que utilizam `?`.

---

## Compatibilidade mantida

A função `garantir_colunas_leads()` permanece apenas para manter compatibilidade arquitetural com versões anteriores do projeto.

---

## Histórico automático

Cada lead recebe automaticamente o histórico mais recente da conversa por meio de uma subconsulta SQL.

Isso evita consultas adicionais pelo Dashboard.

---

## Integração com IA

A função `analisar_lead_automaticamente()` não implementa a inteligência diretamente.

Ela delega a classificação ao módulo `intencao_service.py`, mantendo a separação de responsabilidades.

---

# O módulo não implementa

Este arquivo não implementa:

- criação de leads;
- exclusão de leads;
- alteração do cliente;
- alteração do produto;
- filtros avançados;
- paginação;
- auditoria;
- autenticação;
- controle de permissões.

---

# Resumo

O módulo `leads_service.py` é responsável pela camada de serviços das leads no Orion CRM AI.

Ele consulta dados do PostgreSQL, prepara as informações para o Dashboard, atualiza o acompanhamento comercial e integra a classificação automática através do `intencao_service.py`.

Além disso, diferencia-se dos demais serviços por utilizar controle transacional (`commit`/`rollback`) e por calcular automaticamente indicadores operacionais, como o tempo de permanência da lead no funil.