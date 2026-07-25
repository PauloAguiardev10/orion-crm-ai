# Dashboard – Produtos

## Arquivo

`dashboard/app_pages/produtos.py`

---

## Objetivo

O módulo `produtos.py` implementa a página de gerenciamento de produtos do dashboard.

A página permite que a empresa autenticada:

- cadastre produtos;
- visualize os produtos existentes;
- altere informações de um produto;
- exclua produtos.

O acesso à página é restrito de acordo com a permissão do plano da empresa.

---

## Função principal

```python
def render_produtos():
```

A função `render_produtos()` é responsável por construir e controlar toda a interface da página de produtos.

Ela executa as seguintes etapas:

1. obtém o identificador da empresa autenticada;
2. verifica se a empresa possui permissão para acessar o recurso;
3. carrega os produtos da empresa;
4. exibe o formulário de cadastro;
5. apresenta a listagem dos produtos;
6. disponibiliza as ações de atualização e exclusão.

---

## Identificação da empresa

A página utiliza o identificador armazenado na sessão do Streamlit:

```python
empresa_id = st.session_state.empresa_id
```

Esse valor é enviado ao serviço de produtos para listar e cadastrar registros vinculados à empresa autenticada.

A listagem e o cadastro são, portanto, realizados utilizando `empresa_id`.

---

## Controle de acesso

Antes de exibir a página, o módulo verifica se a empresa possui permissão para o recurso `Premium`:

```python
if not verificar_permissao("Premium"):
```

Quando a permissão não é concedida, a função apresenta a tela de upgrade:

```python
tela_upgrade(
    "Produtos",
    "Premium"
)
```

Em seguida, a execução da página é interrompida:

```python
return
```

No código atual, o acesso à página de produtos depende diretamente do resultado de:

```python
verificar_permissao("Premium")
```

---

## Carregamento dos produtos

Os produtos da empresa são obtidos por meio da função:

```python
produtos = listar_produtos(empresa_id)
```

O retorno é tratado como um DataFrame do pandas, pois o código utiliza recursos como:

```python
produtos.empty
produtos.iterrows()
produtos["id"]
produtos.iloc[0]
```

---

## Cadastro de produto

A página apresenta a seção:

```text
Cadastrar produto
```

O formulário é dividido em duas colunas.

### Primeira coluna

São coletados os seguintes campos:

- nome do produto;
- categoria;
- preço.

```python
nome = st.text_input("Nome do produto")
categoria = st.text_input("Categoria")
preco = st.number_input(
    "Preço",
    min_value=0.0,
    value=0.0
)
```

O preço não pode ser inferior a zero.

### Segunda coluna

São coletados:

- estoque;
- status;
- link da imagem.

```python
estoque = st.number_input(
    "Estoque",
    min_value=0,
    value=0
)

status = st.selectbox(
    "Status",
    ["ativo", "inativo"]
)

imagem_url = st.text_input("Link da imagem")
```

O estoque não pode ser inferior a zero.

O status pode assumir os valores:

```text
ativo
inativo
```

### Descrição

A descrição é informada em uma área de texto:

```python
descricao = st.text_area("Descrição do produto")
```

---

## Processamento do cadastro

Ao clicar no botão:

```text
Cadastrar produto
```

a página chama:

```python
cadastrar_produto(
    empresa_id,
    nome,
    categoria,
    descricao,
    preco,
    estoque,
    imagem_url,
    status,
)
```

A função de serviço retorna um valor utilizado como indicação de sucesso ou falha.

### Cadastro bem-sucedido

Quando o retorno é verdadeiro:

```python
st.success("Produto cadastrado com sucesso.")
st.rerun()
```

A página apresenta a mensagem de sucesso e é recarregada.

### Cadastro não realizado

Quando o retorno é falso:

```python
st.warning("Informe o nome do produto.")
```

O código da página associa esse retorno à ausência ou invalidade do nome do produto.

A validação efetiva é realizada pela função `cadastrar_produto()` no módulo de serviço.

---

## Listagem dos produtos

A página apresenta a seção:

```text
Produtos cadastrados
```

Quando não existem produtos:

```python
if produtos.empty:
    st.info("Nenhum produto cadastrado.")
    return
```

A execução é encerrada e a área de gerenciamento não é exibida.

Quando existem registros, o DataFrame é apresentado por meio de:

```python
st.dataframe(
    produtos,
    use_container_width=True,
    hide_index=True,
)
```

A tabela:

- ocupa a largura disponível;
- não exibe o índice do DataFrame;
- mostra as colunas retornadas por `listar_produtos()`.

---

## Gerenciamento de produto

Quando existem produtos cadastrados, a página apresenta a seção:

```text
Gerenciar produto
```

### Seleção do produto

O código cria um dicionário no formato:

```python
{
    "ID - Nome": id_do_produto
}
```

A construção é feita com:

```python
produto_opcoes = {
    f"{row['id']} - {row['nome']}": row["id"]
    for _, row in produtos.iterrows()
}
```

O usuário seleciona um produto:

```python
produto_escolhido = st.selectbox(
    "Selecionar produto",
    list(produto_opcoes.keys()),
)
```

O identificador é obtido a partir da opção escolhida:

```python
produto_id = produto_opcoes[produto_escolhido]
```

Depois, o registro correspondente é localizado no DataFrame:

```python
produto = produtos[
    produtos["id"] == produto_id
].iloc[0]
```

---

## Campos de atualização

Os campos são preenchidos inicialmente com os dados atuais do produto.

### Primeira coluna

Permite alterar:

- nome;
- categoria;
- preço.

```python
novo_nome = st.text_input(
    "Nome atualizado",
    value=produto["nome"],
)
```

Quando a categoria é nula ou vazia, o campo recebe uma string vazia:

```python
value=produto["categoria"]
if produto["categoria"]
else ""
```

O preço é convertido para `float`:

```python
value=float(produto["preco"])
```

### Segunda coluna

Permite alterar:

- estoque;
- status;
- link da imagem.

O estoque é convertido para inteiro:

```python
value=int(produto["estoque"])
```

O status atual é usado para definir a opção selecionada.

Quando o status salvo não pertence à lista:

```text
ativo
inativo
```

o código utiliza a primeira opção como padrão.

Para a imagem, uma string vazia é usada quando não existe URL cadastrada.

### Descrição atualizada

A descrição é exibida em uma área de texto:

```python
nova_descricao = st.text_area(
    "Descrição atualizada",
    value=produto["descricao"]
    if produto["descricao"]
    else "",
)
```

---

## Atualização do produto

Ao clicar em:

```text
Salvar alterações
```

a página chama:

```python
atualizar_produto(
    produto_id,
    novo_nome,
    nova_categoria,
    nova_descricao,
    novo_preco,
    novo_estoque,
    nova_imagem,
    novo_status,
)
```

Depois da chamada, o código apresenta:

```python
st.success("Produto atualizado.")
st.rerun()
```

No módulo da página, não existe verificação do valor retornado por `atualizar_produto()`.

A interface considera a operação concluída após executar a função de serviço, desde que não seja lançada uma exceção.

---

## Exclusão do produto

Ao clicar em:

```text
Excluir produto
```

a página executa:

```python
excluir_produto(produto_id)
```

Em seguida, apresenta:

```python
st.warning("Produto excluído.")
st.rerun()
```

No código atual:

- não existe confirmação antes da exclusão;
- não existe tratamento local de exceção;
- não existe verificação de retorno da função;
- a exclusão utiliza somente o identificador do produto.

A validação de vínculo com a empresa, caso exista, deve estar implementada no serviço responsável.

---

## Formatação monetária

O módulo possui a função:

```python
def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
```

Essa função converte um valor para o formato monetário brasileiro.

Exemplo:

```text
R$ 1.250,00
```

Entretanto, na versão atual de `produtos.py`, a função `formatar_moeda()` está declarada, mas não é chamada dentro de `render_produtos()`.

O preço é exibido diretamente no DataFrame e nos componentes numéricos do Streamlit.

---

## Funções importadas

### Serviço de produtos

O módulo importa de `services.produtos_service`:

```python
listar_produtos
cadastrar_produto
atualizar_produto
excluir_produto
```

Responsabilidades utilizadas pela página:

| Função | Uso no módulo |
|---|---|
| `listar_produtos()` | Carrega os produtos vinculados à empresa |
| `cadastrar_produto()` | Envia os dados de um novo produto |
| `atualizar_produto()` | Atualiza os dados do produto selecionado |
| `excluir_produto()` | Exclui o produto selecionado |

### Serviço de permissões

O módulo importa de `utils.permissoes`:

```python
verificar_permissao
tela_upgrade
```

| Função | Uso no módulo |
|---|---|
| `verificar_permissao()` | Verifica se o recurso está liberado |
| `tela_upgrade()` | Apresenta a tela de upgrade quando o acesso é negado |

---

## Dependências

O módulo utiliza diretamente:

```python
import streamlit as st
```

Também depende dos módulos internos:

```text
services.produtos_service
utils.permissoes
```

Embora o retorno de `listar_produtos()` seja manipulado como DataFrame, o pandas não é importado diretamente nesta página.

---

## Fluxo da página

```text
Acesso à página
       │
       ▼
Obtém empresa_id da sessão
       │
       ▼
Verifica permissão "Premium"
       │
       ├── Sem permissão
       │      │
       │      ▼
       │  Exibe tela de upgrade
       │      │
       │      ▼
       │  Encerra a função
       │
       ▼
Carrega produtos da empresa
       │
       ▼
Exibe formulário de cadastro
       │
       ▼
Permite cadastrar produto
       │
       ▼
Verifica se existem produtos
       │
       ├── Não existem
       │      │
       │      ▼
       │  Exibe mensagem e encerra
       │
       ▼
Exibe tabela de produtos
       │
       ▼
Permite selecionar um produto
       │
       ├── Atualizar
       │
       └── Excluir
```

---

## Limitações observadas no código atual

A página não implementa diretamente:

- pesquisa de produtos;
- filtro por categoria;
- filtro por status;
- paginação;
- upload de imagem;
- pré-visualização da imagem;
- validação local completa dos campos;
- confirmação antes da exclusão;
- tratamento local de exceções;
- controle de estoque após uma venda;
- formatação monetária na tabela;
- ordenação configurável pela interface.

Esses recursos não devem ser considerados implementados apenas por estarem previstos como possíveis evoluções.

---

## Pontos de atenção

### Permissão denominada Premium

A página usa:

```python
verificar_permissao("Premium")
```

Portanto, a documentação deve registrar que o acesso depende dessa verificação.

Não é possível concluir, apenas por este arquivo, se:

- somente empresas do plano Premium têm acesso;
- empresas de outros planos podem contratar o recurso adicionalmente;
- a função considera plano e serviços adicionais.

Essa regra está localizada em `utils.permissoes`.

### Escopo da empresa

A listagem e o cadastro recebem `empresa_id`.

Por outro lado, as chamadas de atualização e exclusão recebem somente `produto_id`.

A proteção multiempresa dessas duas operações depende da implementação de:

```text
atualizar_produto()
excluir_produto()
```

### Retornos dos serviços

Somente `cadastrar_produto()` tem seu retorno verificado pela página.

As funções de atualização e exclusão são executadas sem validação de retorno.

---

## Possíveis evoluções

As seguintes melhorias podem ser implementadas futuramente:

- confirmação antes de excluir;
- tratamento de erros com `try/except`;
- validação obrigatória de nome e preço;
- pesquisa por nome;
- filtros por categoria e status;
- upload de imagens;
- visualização da imagem do produto;
- alerta de estoque baixo;
- histórico de movimentação;
- paginação da tabela;
- vínculo com os pedidos;
- verificação explícita do retorno das operações;
- reforço da validação multiempresa nos serviços.

Essas funcionalidades são possibilidades de evolução e não fazem parte da implementação atual desta página.

---

## Resumo

O módulo `produtos.py` fornece uma interface Streamlit para cadastro, visualização, atualização e exclusão de produtos.

A página:

- utiliza o `empresa_id` da sessão;
- exige a permissão identificada como `Premium`;
- delega as operações aos serviços de produtos;
- apresenta os registros em um DataFrame;
- permite selecionar um produto para edição ou exclusão.

A implementação atual concentra-se nas operações básicas de gerenciamento, sem pesquisa, filtros avançados, upload de imagens, confirmação de exclusão ou tratamento local de exceções.