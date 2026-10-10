## Why

O meupia-core 1.2.0 já está na PyPI. Ele amplia a linguagem (`!=`, `%`/`mod`, `logico`, `lista`, `escreva` com vários argumentos) e passa a ter um contrato de erro estável: `main()` retorna um código, e a mensagem sai em uma linha em pt-BR com linha e coluna. Hoje o Lab fixa o core 1.1.20 e despeja no terminal todo o stdout do compilador, junto com o log do lexer. Em desafios, ele ainda mostra uma linha de erro deslocada em +1. Além disso, a execução reaproveita o `globals()` do Pyodide, então o código de uma execução vaza para a próxima.

## What Changes

- Instalar o meupia-core `1.2.0` em vez do `1.1.20`.
- Decidir sucesso ou falha da compilação pelo valor retornado por `main()` (0 = sucesso) e manter a checagem de `output/main.py` como segurança extra.
- Em erro de compilação, mostrar só o cabeçalho `[ERRO DE COMPILAÇÃO]` e a mensagem padronizada `Erro … na linha L, coluna C: …`, sem o log do lexer. Se a mensagem não seguir esse formato, mostrar o texto que vem depois de `[COMPILATION ERROR]:`.
- Em desafios, converter a linha do erro para a linha **do editor**, compensando o `usar "testes"` inserido. Erros dentro do `codigoTeste` anexado aparecem como `Erro nos testes automáticos do desafio`.
- Executar o Python gerado num namespace novo a cada execução (`{"__name__": "__main__"}`).
- Marcar no editor a linha e a coluna do último erro de compilação. A marca some na próxima edição ou na próxima compilação bem-sucedida.
- Alinhar o realce de sintaxe com o core 1.2.0: `mod`; os tipos exatos `inteiro`, `real`, `float`, `string`, `cadeia`, `logico`, `lista`, `dicionario` e `filaPrioridade`; remover `fila`, `pilha` e `heap`; operadores de dois caracteres; decimais; aspas escapadas; o atom `pi`.
- No autocomplete, adicionar snippets de `escreva`, `leia` e `metodo`, e tirar o `passo` do snippet do `para`.
- Quando o core acusa o erro no `fim_algoritmo` que o Lab anexou (sinal de que algum bloco do aluno ficou aberto), mostrar uma orientação sobre blocos não fechados em vez de "erro nos testes".
- Adicionar o script `npm test` com o test runner nativo do Node (`node:test`), sem dependências novas, com testes das funções puras de erro.
- **BREAKING** (para o aluno): variáveis e funções de uma execução deixam de existir na execução seguinte. Um programa que dependia sem querer desse vazamento agora falha, e esse é o comportamento correto.

## Capabilities

### New Capabilities
- `motor-de-execucao`: compilação e execução do código Portugol no Pyodide. Cobre a versão do core, a detecção de sucesso, a apresentação do erro de compilação, o mapeamento de linha em desafios e o isolamento entre execuções.
- `editor-portugol`: o editor CodeMirror para Portugol. Cobre o realce de sintaxe, o autocomplete e a marcação visual do erro de compilação.

### Modified Capabilities
<!-- Nenhuma: ainda não há specs em openspec/specs/. -->

## Impact

- `src/engine/wasm.js`: versão do core; a compilação passa a ser separada da execução; leitura do código de retorno; apresentação do erro; registro das informações da montagem do desafio; execução isolada.
- Novo módulo puro em `src/engine/` com a extração da mensagem e o mapeamento de linha. É usado pelo `wasm.js` e pelos testes.
- `src/editor/meupia-lang.js`: tokenizer, listas de palavras, snippets e a extensão de marcação de erro.
- `src/main.js`: registra a extensão de marcação de erro no `EditorView`.
- `src/style.css`: estilos da linha e da coluna com erro.
- `package.json`: script `test` (`node --test`). Nenhuma dependência nova.
- Sem mudança no plugin grid, no meupia-testes, nos JSON de desafios nem no fluxo de montagem do desafio.
