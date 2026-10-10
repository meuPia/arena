## Why

O meupia-core 1.3.0 já está na PyPI e permite declarar variáveis locais com `var` dentro de `funcao`, `metodo` e `inicio`. O Lab ainda instala o 1.2.0, então os alunos não conseguem usar esse recurso. Uma comparação entre o lexer do core e o realce do editor também achou dois desvios que enganam o aluno:
- `função` e `fim_função` aparecem coloridos como palavra-chave, mas o core rejeita essas formas.
- `lista` e `logico` aparecem como tipo em qualquer posição, mas no core só são tipo depois de `:` ou de `novo`.

## What Changes

- Instalar o meupia-core `1.3.0` em vez do `1.2.0`.
- Realce de palavras-chave igual às palavras reservadas do core. `função` e `fim_função` deixam de ser realçadas.
- `lista` e `logico` passam a ser realçados como tipo só quando o token significativo anterior for `:` ou `novo`. Em qualquer outra posição, são realçados como nome de variável.
- O requisito de realce perde a versão no nome (`Realce de sintaxe do core 1.2.0` → `Realce de sintaxe`).
- Novo snippet `var` para declarar variável local.
- Testes `node:test` para a classificação de palavras e para o realce contextual.

## Capabilities

### New Capabilities
<!-- Nenhuma. -->

### Modified Capabilities
- `motor-de-execucao`: o requisito "Versão do compilador" passa para o 1.3.0, com um cenário de variável local.
- `editor-portugol`: "Realce de sintaxe do core 1.2.0" é renomeado para "Realce de sintaxe" e ganha a lista exata de palavras-chave e os tipos contextuais. "Snippets de autocomplete" ganha o snippet `var`.

## Impact

- `src/engine/wasm.js`: `version = "1.3.0"`.
- `src/editor/meupia-lang.js`: listas de palavras, estado do tokenizer com o último token significativo, a função pura exportada `classificarPalavra` e o snippet `var`.
- Novo `src/editor/meupia-lang.test.js`.
- Sem mudança no motor de erros, no mapeamento de linhas, na montagem dos desafios nem em dependências.
