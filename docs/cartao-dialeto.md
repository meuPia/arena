# Cartão de referência rápida: Portugol meuPiá

Dialeto do **meupia-core 1.3.0**, o mesmo da IDE e do juiz da Code Arena. Tudo o que está aqui foi conferido
com o compilador real (`tests/test_cartao_dialeto.py`).

## Estrutura

```
algoritmo "Missao"

var                         // variáveis globais (opcional)
    contador : inteiro

funcao dobro(n)             // parâmetros sem tipo
    var r : inteiro         // variável local: "var" dentro da função
    r <- n * 2
    retorne r
fim_funcao

inicio
    escreva(dobro(21))
fim_algoritmo
```

- As funções vêm **antes** do `inicio`.
- Os testes chamam a sua função: **não mude o nome nem os parâmetros** que vêm no código inicial.

## Variáveis

| Tipo | Começa com | Exemplo |
|---|---|---|
| `inteiro` | `0` | `var i, j : inteiro` |
| `real` | `0.0` | `var media : real` |
| `cadeia` (ou `string`) | `""` | `var nome : cadeia` |
| `logico` | `falso` | `var achou : logico` |
| `lista` | `[]` | `var v : lista` |
| `dicionario` | `{}` | `var conta : dicionario` |

- **Toda variável precisa estar num `var`, inclusive o contador do `para`.**
- Atribuição: `x <- 10`. Dentro de função dá para declarar com valor: `var total : inteiro <- 0`.

## Operadores

| | |
|---|---|
| Aritméticos | `+  -  *  /` e resto: `%` ou `mod` |
| Comparação | `=` ou `==` · `<>` ou `!=` · `<  >  <=  >=` |
| Lógicos | `e  ou  nao` · valores `verdadeiro` e `falso` |

- **`/` sempre dá real:** `7 / 2` é `3.5`. Divisão inteira: `piso(7 / 2)` é `3` (e `piso(-7 / 2)` é `-4`).
- Textos comparam em ordem alfabética: `c >= "a" e c <= "z"`.
- Os dois lados de uma comparação aceitam expressões: `se i % 2 = 0 entao`.

## Decisão

```
se n < 0 entao
    retorne "negativo"
senao
    se n = 0 entao
        retorne "zero"
    senao
        retorne "positivo"
    fim_se
fim_se
```

Não existe `senao se` com um `fim_se` só: cada `se` fecha o seu.

Os acentos são opcionais: `então`, `senão`, `faça`, `até` e `não` também valem.

## Repetição

```
para i de 1 ate n faca              // inclui o n
para i de n ate 1 passo -1 faca     // contagem regressiva
para i de 0 ate tamanho(v) - 1 faca // percorre lista ou texto
    ...
fim_para

enquanto x > 0 faca
    ...
fim_enquanto
```

`interrompa` sai do laço. `continue` pula para a próxima volta.

## Texto

| | |
|---|---|
| Tamanho | `tamanho(t)` |
| Um caractere | `t[0]` é o primeiro, `t[tamanho(t) - 1]` é o último |
| Juntar | `"total: " + n`; número e lógico viram texto (`"" + 42` é `"42"`) |
| Montar texto | `r <- ""` e depois `r <- r + t[i]` |

- Não há fatia: `t[1:3]` dá erro. Monte o pedaço com um `para`.
- `escreva("a", n)` junta os valores **sem** espaço entre eles.

## Lista

```
var v : lista
v <- [5, 6, 7]       // ou v <- [] para começar vazia
v[0] <- 9            // índices começam em 0
v.adicionar(8)       // põe no fim
x <- v.removerFim()  // tira o último e devolve
n <- tamanho(v)
m[1][0]              // lista de listas
```

Também existem `v.expandir(outra)` (junta outra lista no fim) e `v.limpar()` (esvazia).

## Dicionário

```
var conta : dicionario
conta["a"] <- 1
x <- conta.pegar("a", 0)   // valor da chave, ou 0 se ela não existe
```

## Matemática

| | |
|---|---|
| Arredondar | `piso(x)` (para baixo) e `teto(x)` (para cima) |
| Outras | `absoluto(x)`, `raiz(x)`, `potencia(b, e)` |
| Trigonometria | `seno(x)`, `cosseno(x)`, `tangente(x)` |
| Constante | `pi` |

`raiz` e `potencia` devolvem **real**: `potencia(2, 3)` é `8.0`.

## Na Arena

- **Rodar** executa só os testes de exemplo, no seu navegador. **Submeter** manda para o juiz, que roda os
  exemplos e os testes extras.
- Exemplo reprovado no Rodar: a aba Missão mostra a entrada, o esperado e o obtido com o tipo (`"5"` é cadeia,
  `5` é inteiro) e destaca a diferença. Espaço aparece como `·` e quebra de linha como `↵`.
- O juiz confere o que a função **devolve** (`retorne`). O que vai para o `escreva` é ignorado.
- **Não use `leia`:** ninguém digita nada durante os testes.
- Cada teste tem **1 segundo**. Um laço que não termina reprova o teste.
- No empate de pontos, ganha quem tem **menos caracteres**. Comentários `//` e espaços fora de textos não
  contam, então comente à vontade.

### Mensagens comuns

| Mensagem | O que fazer |
|---|---|
| a variável "k" não foi declarada no bloco var | Declare `k` num `var` (contador do `para` também) |
| um exemplo deu erro durante a execução | Confira o nome e os parâmetros da função pedida, índice fora da lista ou do texto e divisão por zero |
| esperado "]", encontrado ":" | Fatia `t[1:3]` não existe: use um `para` |
| a variável "x" já foi declarada neste bloco | Tire a declaração repetida |
