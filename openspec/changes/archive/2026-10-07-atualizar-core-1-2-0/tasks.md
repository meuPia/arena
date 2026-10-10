## 1. Setup de testes

- [x] 1.1 Rodar `npm install` (para o build) e adicionar o script `"test": "node --test 'src/**/*.test.js'"` no `package.json`, sem dependências novas (D6). Verificar que `npm test` roda depois de criado o primeiro arquivo de teste na tarefa 2.1.

## 2. Funções puras de erro (`src/engine/erros.js`)

- [x] 2.1 Implementar `extrairMensagemErro(saida)` (formato padronizado → `{tipo, linha, coluna, descricao, texto}`; fallback com o texto depois de `[COMPILATION ERROR]:`, sem o log do lexer; fallback com a saída inteira). Verificar com testes `node:test` em `src/engine/erros.test.js` cobrindo: erro léxico com o log `(Lexer started)`/`Scanning line` ao redor (`linha 4, coluna 8` extraídos como estão, sem ajuste de base), erros sintático e semântico, arquivo vazio (`linha 1, coluna 1`), texto fora do formato depois do marcador e saída sem marcador.
- [x] 2.2 Implementar `mapearLinhaErro(linhaMontada, info)` com as três origens de D1. Verificar com testes de: `info = null` (sempre `editor`, mesma linha); `usar "testes"` inserido depois da linha 1 (montado 6 → editor 5; montado 1 → 1; montado 2 → `testes`); `usar "testes"` já presente (`linhaUsarTestes = null`; montado 5 → 5); linha dentro do `codigoTeste` → `testes`; linha igual a `linhaFimAnexado` (ex.: 11) → `bloco-aberto`.
- [x] 2.3 Implementar `formatarMensagemErro(erro, mapeado)`. Verificar com testes de que a linha é trocada pela do editor (`Erro léxico na linha 5, coluna …`), de que a origem `testes` gera `Erro nos testes automáticos do desafio: <descricao>`, de que a origem `bloco-aberto` gera a orientação de bloco não fechado sem número de linha e de que o fallback devolve o texto sem alteração. `npm test` passa.

## 3. Motor de execução (`src/engine/wasm.js`)

- [x] 3.1 Trocar `version` para `"1.2.0"`. Verificar no `npm run dev` que o terminal anuncia `v1.2.0` e o motor fica pronto.
- [x] 3.2 Coletar `info = { linhaUsarTestes, inicioAnexo, linhaFimAnexado }` na montagem do desafio (D2), sem alterar o texto montado. Verificar com um `git diff` de que as três operações de montagem continuam idênticas e de que, num desafio, o erro na linha 5 do editor aparece como linha 5.
- [x] 3.3 Separar o bloco Python em compilação (expondo `codigo_retorno`, `saida_compilador` e `gerou_py`) e decisão no JS (D3). Em erro, escrever `[ERRO DE COMPILAÇÃO]` + `formatarMensagemErro(...)`. Verificar no navegador de que `x <- 7 $ 2` mostra só `Erro léxico na linha …`, sem o log do lexer.
- [x] 3.4 Executar o programa gerado em `exec(codigo, {"__name__": "__main__"})`, mantendo `[EXECUTANDO]`, `[FIM DO PROGRAMA]`, `SystemExit` ignorado e `[ERRO DO SISTEMA]`. Verificar no navegador de que apagar uma função e rodar de novo faz a chamada falhar.

## 4. Editor (`src/editor/meupia-lang.js`, `src/main.js`, `src/style.css`)

- [x] 4.1 Criar o `StateField`/`StateEffect` de erro e os exports `meuPiaErroCompilacao`, `marcarErroCompilacao` e `limparErroCompilacao` (D4), limitando a linha a `[1, doc.lines]`. Registrar a extensão em `main.js` e criar as classes `cm-linha-erro`/`cm-coluna-erro` em `style.css`. Verificar que `npm run build` passa.
- [x] 4.2 Ligar a marcação ao motor: `marcarErroCompilacao` quando a origem for o editor, `limparErroCompilacao` no sucesso. Verificar no navegador de que a linha certa é marcada, a marca some ao digitar e some ao compilar com sucesso, e erros de origem `testes` ou `bloco-aberto` não marcam nada.
- [x] 4.3 Atualizar o tokenizer e as listas (D5): `mod`; os tipos exatos sem `fila`/`pilha`/`heap`; operadores de dois caracteres e `%`; decimais; strings com escapes; o atom `pi`. Verificar no navegador com as linhas dos cenários de realce da spec `editor-portugol`.
- [x] 4.4 Adicionar os snippets `escreva`, `leia` e `metodo`, e tirar o `passo` do snippet `para`. Verificar no navegador aceitando cada snippet.

## 5. Verificação integrada

- [x] 5.1 `npm test` e `npm run build` passam sem erros.
- [x] 5.2 Fazer o roteiro manual no `npm run dev`: programa válido executa; `x <- 7 $ 2` mostra só o erro léxico e marca a linha; num desafio (`?desafio=<id>`), um erro na linha 5 aparece como 5; `escreva("x=", 5)` imprime `x=5`; `se x != 1 entao` funciona; a função apagada falha na segunda execução; num desafio, apagar um `fim_se` mostra a orientação de bloco não fechado, sem marcar linha; sem desafio, apagar um `fim_se` marca a linha do `fim_algoritmo`. Confirmar visualmente que `x <- 7 $ 2` marca a coluna do `$`.
- [x] 5.3 Confirmar que nenhum commit foi feito (`git status` mostra só alterações na árvore de trabalho).
