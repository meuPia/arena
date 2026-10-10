## Purpose

Oferecer ao aluno um editor de Portugol cujo realce de sintaxe e autocomplete correspondam à linguagem aceita pelo meupia-core, e que aponte visualmente onde está o último erro de compilação.

## ADDED Requirements

### Requirement: Marcação do erro de compilação
Quando uma compilação falhar com um erro localizado no código do editor, o editor SHALL destacar a linha do erro e, se a coluna for conhecida e estiver dentro da linha, também a posição da coluna. Só o último erro fica marcado. A marcação MUST sumir na próxima edição do documento ou na próxima compilação bem-sucedida.

#### Scenario: Erro léxico marca a linha
- **WHEN** a compilação falha com `Erro léxico na linha 4, coluna 12: …` (linha já convertida para a do editor)
- **THEN** a linha 4 do editor fica destacada
- **AND** a posição da coluna 12 fica indicada

#### Scenario: Marca some ao editar
- **WHEN** há uma linha marcada e o aluno digita qualquer caractere no editor
- **THEN** a marcação desaparece

#### Scenario: Marca some ao compilar com sucesso
- **WHEN** há uma linha marcada e o aluno executa um programa que compila sem erro
- **THEN** a marcação desaparece

#### Scenario: Novo erro substitui o anterior
- **WHEN** a linha 4 está marcada e uma nova compilação falha na linha 7
- **THEN** só a linha 7 fica marcada

#### Scenario: Erro nos testes do desafio
- **WHEN** a compilação falha numa linha do código de teste anexado pelo desafio
- **THEN** nenhuma linha do editor é marcada

#### Scenario: Arquivo vazio
- **WHEN** o editor está vazio e a compilação falha com `linha 1, coluna 1`
- **THEN** a linha 1 é marcada e o Lab não lança erro, mesmo sem caractere na coluna 1

#### Scenario: Linha fora do documento
- **WHEN** a linha reportada é maior que o número de linhas do editor
- **THEN** a última linha do editor é marcada e o Lab não lança erro

### Requirement: Realce de sintaxe do core 1.2.0
O realce SHALL classificar os tokens assim, sem diferenciar maiúsculas de minúsculas nas palavras:
- Palavra-chave: as palavras-chave existentes mais `mod`.
- Tipo: exatamente `inteiro`, `real`, `float`, `string`, `cadeia`, `logico`, `lista`, `dicionario` e `filaPrioridade`. `fila`, `pilha` e `heap` MUST NOT ser realçados como tipo.
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

### Requirement: Snippets de autocomplete
O autocomplete SHALL oferecer, além dos snippets existentes (`se`, `funcao`, `enquanto`, `classe`), os snippets abaixo:
- `escreva`: `escreva(<cursor>)`
- `leia`: `leia(<variavel>)`
- `metodo`: `metodo <nome>(<parametros>)`, corpo indentado e `fim_funcao`
- `para`: `para <variavel> de <inicio> ate <fim> faca`, corpo indentado e `fim_para`, sem `passo`

#### Scenario: Snippet do para sem passo
- **WHEN** o aluno aceita o snippet `para`
- **THEN** o texto inserido não contém `passo`

#### Scenario: Snippet de metodo
- **WHEN** o aluno aceita o snippet `metodo`
- **THEN** o texto inserido começa com `metodo` e termina com `fim_funcao`

#### Scenario: Snippets de entrada e saída
- **WHEN** o aluno digita `esc` ou `lei` e abre o autocomplete
- **THEN** são oferecidos, respectivamente, os snippets `escreva` e `leia`
