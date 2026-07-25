# Dashboard – Pedidos

## Arquivo

`dashboard/app_pages/pedidos.py`

---

# Objetivo

O módulo `pedidos.py` implementa a página de gerenciamento de pedidos e vendas do Dashboard Orion CRM AI.

A página permite:

- cadastrar novos pedidos;
- visualizar pedidos existentes;
- atualizar o status de um pedido;
- excluir pedidos cadastrados.

Todo pedido é associado à empresa autenticada através do `empresa_id` armazenado na sessão do Streamlit.

---

# Função Principal

```python
def render_pedidos():
```

Esta função é responsável por construir toda a interface da página de pedidos.

Seu fluxo consiste em:

1. identificar a empresa autenticada;
2. carregar produtos cadastrados;
3. carregar pedidos existentes;
4. permitir cadastrar um novo pedido;
5. listar todos os pedidos;
6. permitir alterar ou excluir um pedido.

---

# Identificação da Empresa

A página utiliza:

```python
empresa_id = st.session_state.empresa_id
```

Esse identificador é utilizado nas chamadas:

```python
listar_produtos(empresa_id)

listar_pedidos(empresa_id)

cadastrar_pedido(...)
```

Assim, produtos e pedidos pertencem à empresa atualmente logada.

---

# Carregamento dos Produtos

Antes de permitir um novo pedido, o sistema executa:

```python
produtos = listar_produtos(empresa_id)
```

Caso não existam produtos cadastrados:

```python
if produtos.empty:
```

é exibida a mensagem:

```text
Cadastre produtos antes de criar pedidos.
```

e a função é encerrada.

Não é possível criar pedidos sem produtos cadastrados.

---

# Carregamento dos Pedidos

Após carregar os produtos:

```python
pedidos = listar_pedidos(empresa_id)
```

Os pedidos são tratados como DataFrame do pandas.

O código utiliza:

```python
pedidos.empty

pedidos.iterrows()
```

---

# Cadastro de Pedido

A página apresenta:

```text
Novo pedido
```

---

## Produto

O usuário escolhe um produto através de:

```python
selectbox()
```

As opções possuem o formato:

```text
Nome do Produto - R$ Valor
```

Cada opção mantém internamente todo o registro do produto.

---

## Dados do Cliente

São coletados:

- nome do cliente;
- telefone;
- quantidade.

A quantidade possui valor mínimo igual a 1.

---

## Dados da Venda

Também são informados:

Forma de pagamento:

```python
FORMAS_PAGAMENTO
```

Origem da venda:

```text
WhatsApp

Instagram

Facebook

Manual
```

Responsável pela venda:

```text
IA

Humano
```

Observações:

```python
text_area()
```

---

# Cálculo do Valor

O valor do pedido é calculado automaticamente.

O código realiza:

```python
valor_total = (
    float(produto["preco"])
    * quantidade
)
```

Em seguida apresenta:

```python
st.metric(
    "Valor total",
    formatar_moeda(valor_total)
)
```

A página não permite edição manual do valor total.

---

# Cadastro

Ao clicar em:

```text
Cadastrar pedido
```

é executado:

```python
cadastrar_pedido(...)
```

Os valores enviados são:

- empresa;
- cliente;
- telefone;
- id do produto;
- nome do produto;
- quantidade;
- valor total;
- forma de pagamento;
- status pagamento;
- status pedido;
- origem;
- vendido por;
- observações.

Os valores iniciais definidos pela própria página são:

Status pagamento

```text
Aguardando pagamento
```

Status pedido

```text
Novo pedido
```

Após o cadastro:

```python
st.success()

st.rerun()
```

O retorno da função `cadastrar_pedido()` não é validado nesta página.

---

# Listagem

Após o cadastro é exibida:

```text
Pedidos cadastrados
```

Caso não existam pedidos:

```python
pedidos.empty
```

é apresentada:

```text
Nenhum pedido cadastrado.
```

Caso existam registros:

```python
st.dataframe()
```

é utilizado para apresentar todos os pedidos.

A tabela ocupa toda a largura disponível.

O índice não é exibido.

---

# Gerenciamento

A página permite selecionar um pedido.

As opções possuem formato:

```text
Pedido #ID - Nome Cliente
```

Após selecionar um pedido, são disponibilizados:

## Status do pagamento

As opções são obtidas de:

```python
STATUS_PAGAMENTO
```

A página utiliza o valor salvo no pedido para definir a opção inicialmente selecionada.

Caso o valor salvo não exista na lista, é utilizada a primeira opção.

---

## Status do pedido

As opções são obtidas de:

```python
STATUS_PEDIDO
```

O comportamento é equivalente ao status de pagamento.

---

## Observações

As observações atuais são carregadas para edição:

```python
text_area()
```

Caso estejam vazias:

```python
""
```

é utilizado como valor padrão.

---

# Atualização

Ao clicar em:

```text
Salvar alterações pedido
```

é chamada:

```python
atualizar_pedido(
    pedido["id"],
    novo_status_pagamento,
    novo_status_pedido,
    nova_observacao
)
```

Após isso:

```python
st.success()

st.rerun()
```

O código da página não verifica o retorno da função.

---

# Exclusão

Ao clicar em:

```text
Excluir pedido
```

é executado:

```python
excluir_pedido(
    pedido["id"]
)
```

Depois:

```python
st.warning()

st.rerun()
```

Nesta página:

- não existe confirmação antes da exclusão;
- não existe tratamento local de exceções;
- não existe validação do retorno da função.

A proteção de integridade depende do serviço responsável.

---

# Formatação Monetária

O módulo implementa:

```python
formatar_moeda(valor)
```

Essa função converte valores para o padrão brasileiro.

Exemplo:

```text
R$ 1.250,00
```

Ela é utilizada para:

- exibir o preço dos produtos no SelectBox;
- exibir o valor total do pedido.

---

# Serviços Utilizados

O módulo depende de:

## pedidos_service

- listar_pedidos()
- cadastrar_pedido()
- atualizar_pedido()
- excluir_pedido()

Além das listas:

```python
STATUS_PAGAMENTO

STATUS_PEDIDO

FORMAS_PAGAMENTO
```

---

## produtos_service

O módulo utiliza:

```python
listar_produtos()
```

para disponibilizar produtos durante o cadastro.

---

# Dependências

O módulo utiliza:

```python
streamlit
```

e os serviços internos:

```text
services.pedidos_service

services.produtos_service
```

---

# Fluxo da Página

```text
Carrega empresa

↓

Lista produtos

↓

Existem produtos?

↓

Não

↓

Encerra

↓

Sim

↓

Novo pedido

↓

Calcula valor automaticamente

↓

Cadastrar

↓

Lista pedidos

↓

Seleciona pedido

↓

Atualizar

ou

Excluir
```

---

# Limitações Observadas

O código atual não implementa:

- pesquisa de pedidos;
- filtros por status;
- filtros por período;
- pesquisa por cliente;
- paginação;
- confirmação antes da exclusão;
- emissão de nota fiscal;
- geração de comprovantes;
- integração com gateway de pagamento;
- baixa automática de estoque;
- tratamento local de exceções;
- validação do retorno das funções de atualização e exclusão.

Esses recursos não devem ser considerados implementados apenas por serem possibilidades futuras.

---

# Pontos de Atenção

A página recebe apenas o identificador do pedido para atualização e exclusão.

A verificação de pertencimento à empresa deve estar implementada em:

```text
atualizar_pedido()

excluir_pedido()
```

A documentação não deve afirmar que essa proteção existe sem analisar esses serviços.

---

# Evoluções Futuras

O módulo pode ser expandido com:

- pesquisa de pedidos;
- filtros por cliente;
- filtros por período;
- impressão;
- PDF;
- integração PIX;
- integração com gateways;
- geração automática de nota fiscal;
- baixa automática de estoque;
- envio para WhatsApp;
- histórico de alterações;
- confirmação antes da exclusão;
- tratamento de exceções.

Essas funcionalidades representam possibilidades futuras e não fazem parte da implementação atual.

---

# Resumo

O módulo `pedidos.py` implementa o gerenciamento de pedidos do Orion CRM AI.

Ele permite cadastrar pedidos utilizando produtos previamente cadastrados, calcula automaticamente o valor total, lista os pedidos existentes e disponibiliza operações de atualização e exclusão.

Toda a lógica de persistência é delegada aos serviços internos, enquanto a página é responsável exclusivamente pela interface construída em Streamlit.