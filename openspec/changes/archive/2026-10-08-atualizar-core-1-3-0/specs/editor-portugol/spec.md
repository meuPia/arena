## RENAMED Requirements

- FROM: `### Requirement: Realce de sintaxe do core 1.2.0`
- TO: `### Requirement: Realce de sintaxe`

## MODIFIED Requirements

### Requirement: Realce de sintaxe
O realce SHALL classificar os tokens assim, sem diferenciar maiúsculas de minúsculas nas palavras:
- Palavra-chave: exatamente as palavras reservadas do core: `algoritmo`, `var`, `inicio`, `fim_algoritmo`, `usar`, `se`, `entao`, `então`, `senao`, `senão`, `fim_se`, `enquanto`, `faca`, `faça`, `fim_enquanto`, `para`, `de`, `ate`, `até`, `passo`, `fim_para`, `escreva`, `leia`, `retorne`, `funcao`, `fim_funcao`, `classe`, `metodo`, `novo`, `fim_classe`, `interrompa`, `continue`, `e`, `ou`, `nao`, `não` e `mod`. `função` e `fim_função` MUST NOT ser realçados como palavra-chave.
- Tipo, em qualquer posição: `inteiro`, `real`, `float`, `string`, `cadeia`, `dicionario` e `filaPrioridade`. `fila`, `pilha` e `heap` MUST NOT ser realçados como tipo.
- Tipo contextual: `lista` e `logico` SHALL ser realçados como tipo somente quando o token significativo anterior for `:` ou `novo`. Espaços, quebras de linha e comentários não contam como token significativo. Em qualquer outra posição, eles MUST ser realçados como nome de variável.
- Operador: `<-`, `!=`, `<>`, `<=`, `>=` e `==`, cada um como um único token, além de `+ - * / % = < >`.
- Número: inteiros e decimais com ponto (`3.14`).
- String: entre aspas duplas, aceitando aspas escapadas (`\"`) e barra invertida escapada (`\\`).
- Atom: `verdadeiro`, `falso` e `pi`.

#### Scenario: Operadores de dois caracteres
- **WHEN** o editor contém `se x != 1 entao` e `y <- a >= b`
- **THEN** `!=` e `>=` são realçados cada um como um único token de operador

#### Scenario: Módulo
- **WHEN** o editor contém `r <- a mod b` e `r <- a % b`
- **THEN** `mod` é realçado como palavra-chave e `%` como operador

#### Scenario: Tipos válidos e removidos
- **WHEN** o editor contém `var q: filaPrioridade` e `var p: pilha`
- **THEN** `filaPrioridade` é realçado como tipo e `pilha` não

#### Scenario: Número decimal
- **WHEN** o editor contém `r <- 3.14`
- **THEN** `3.14` é realçado como um único número

#### Scenario: Strings com escapes
- **WHEN** o editor contém `escreva("diga \"oi\"")` e `s <- "a\\"`
- **THEN** cada literal é realçado como uma única string, do primeiro ao último caractere de aspas

#### Scenario: Atom pi
- **WHEN** o editor contém `area <- pi * r * r`
- **THEN** `pi` é realçado como atom

#### Scenario: lista como variável
- **WHEN** o editor contém `lista <- [1, 2]`
- **THEN** `lista` é realçado como nome de variável

#### Scenario: lista como tipo
- **WHEN** o editor contém `var l: lista` e `x <- novo lista()`
- **THEN** `lista` é realçado como tipo nas duas linhas

#### Scenario: logico como variável
- **WHEN** o editor contém `se logico entao`
- **THEN** `logico` é realçado como nome de variável

#### Scenario: Contexto atravessa linhas, mas só pelo último token
- **WHEN** uma linha termina em `var l:` e a linha seguinte começa com `lista`
- **THEN** `lista` é realçado como tipo
- **AND** quando a linha anterior é `var x: inteiro` e a linha seguinte começa com `lista <- [1]`, `lista` é realçado como nome de variável

#### Scenario: Formas acentuadas não aceitas pelo core
- **WHEN** o editor contém `função` ou `fim_função`
- **THEN** essas palavras não são realçadas como palavra-chave

### Requirement: Snippets de autocomplete
O autocomplete SHALL oferecer, além dos snippets existentes (`se`, `funcao`, `enquanto`, `classe`), os snippets abaixo:
- `escreva`: `escreva(<cursor>)`
- `leia`: `leia(<variavel>)`
- `metodo`: `metodo <nome>(<parametros>)`, corpo indentado e `fim_funcao`
- `para`: `para <variavel> de <inicio> ate <fim> faca`, corpo indentado e `fim_para`, sem `passo`
- `var`: `var <nome>: <tipo> <- <valor>`, com o detalhe "variável local"

#### Scenario: Snippet do para sem passo
- **WHEN** o aluno aceita o snippet `para`
- **THEN** o texto inserido não contém `passo`

#### Scenario: Snippet de metodo
- **WHEN** o aluno aceita o snippet `metodo`
- **THEN** o texto inserido começa com `metodo` e termina com `fim_funcao`

#### Scenario: Snippets de entrada e saída
- **WHEN** o aluno digita `esc` ou `lei` e abre o autocomplete
- **THEN** são oferecidos, respectivamente, os snippets `escreva` e `leia`

#### Scenario: Snippet de variável local
- **WHEN** o aluno digita `va` e aceita o snippet `var`
- **THEN** o texto inserido é `var nome: tipo <- valor`, com `nome`, `tipo` e `valor` como campos editáveis
