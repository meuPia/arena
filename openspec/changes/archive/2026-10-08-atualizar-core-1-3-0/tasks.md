## 1. Motor

- [x] 1.1 Trocar `version` para `"1.3.0"` em `src/engine/wasm.js`. Verificar no `npm run dev` que o terminal anuncia `Baixando Compilador meuPiá v1.3.0` e o motor fica pronto.

## 2. Classificação de palavras (`src/editor/meupia-lang.js`)

- [x] 2.1 Ajustar `meuPiaKeywords` para exatamente as palavras reservadas do core (sem `função`/`fim_função`), deixar `meuPiaTypes` só com os tipos fixos e criar `meuPiaTiposContextuais = ["lista", "logico"]`. Verificar com `npm test` (tarefa 2.3).
- [x] 2.2 Implementar e exportar `classificarPalavra(palavra, tokenAnterior)` conforme D3. Verificar com `npm test` (tarefa 2.3).
- [x] 2.3 Criar `src/editor/meupia-lang.test.js` com testes de `classificarPalavra`: cada palavra-chave da lista da spec → `keyword` (inclusive em maiúsculas); `função`/`fim_função` → `variableName`; os tipos fixos → `typeName` com qualquer token anterior; `lista`/`logico` depois de `":"` e de `"novo"`/`"NOVO"` → `typeName`; depois de `null`, `"<-"`, `"se"` e `"literal"` → `variableName`; `pi` → `atom`. `npm test` passa.

## 3. Tokenizer com estado

- [x] 3.1 Extrair a especificação do tokenizer para a constante exportada `meuPiaTokenizer`, com `startState()` → `{ anterior: null }`, gravando o último token significativo (D1), tratando `:` como `punctuation` (D2) e usando `classificarPalavra` para as palavras. Verificar com `npm test` (tarefa 3.2) e que `npm run build` passa.
- [x] 3.2 Acrescentar ao teste um helper que tokeniza várias linhas com `StringStream` e um estado compartilhado. Verificar: `lista <- [1, 2]` → variável; `var l: lista` e `x <- novo lista()` → tipo; `se logico entao` → variável; `var l:` + quebra de linha + `lista` → tipo; `var x: inteiro` + quebra de linha + `lista <- [1]` → variável; `:` + comentário + quebra de linha + `lista` → tipo; os cenários atuais de realce (`!=`, `>=`, `mod`, `%`, `3.14`, strings com escape, `pi`, `filaPrioridade`/`pilha`) continuam com o mesmo estilo. `npm test` passa.

## 4. Autocomplete

- [x] 4.1 Acrescentar o snippet `var` (D5). Verificar no navegador que digitar `va` oferece `var` (detalhe "variável local") e aceitá-lo insere `var nome: tipo <- valor`.

## 5. Verificação integrada

- [x] 5.1 `npm test` e `npm run build` passam sem erros.
- [x] 5.2 Fazer o roteiro manual no `npm run dev`: o terminal anuncia v1.3.0; o programa com `funcao dobro(a)` / `var r: inteiro <- a * 2` / `retorne r` e `escreva(dobro(4))` imprime `8`; `escreva("x=", 5)` e `se x != 1 entao` continuam funcionando; `var` dentro de um `se` mostra `Erro sintático na linha …` com a linha certa do editor e marca essa linha; no editor, `lista <- [1]` aparece com a cor de variável, `var l: lista` com a cor de tipo, e `função` não fica com a cor de palavra-chave.
- [x] 5.3 Confirmar que nenhum commit foi feito (`git status` mostra só alterações na árvore de trabalho).
