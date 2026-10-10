## Context

O tokenizer de `src/editor/meupia-lang.js` é um `StreamLanguage` sem estado: cada palavra é classificada só pelo texto, comparando com `meuPiaKeywords`, `meuPiaTypes` e `meuPiaAtoms` em minúsculas. Por isso ele não consegue tratar `lista`/`logico` como tipos contextuais. Hoje `:` cai no `stream.next()` genérico e não recebe estilo.

O `StreamLanguage` do CodeMirror passa o mesmo objeto de estado de uma linha para a seguinte (e o copia com uma cópia rasa quando precisa). Então um campo no estado já basta para lembrar o último token entre linhas.

Já confirmei que o `node --test` consegue importar `meupia-lang.js` mesmo com os imports do CodeMirror. Os testes podem importar o módulo direto, sem precisar extrair um arquivo separado.

## Goals / Non-Goals

**Goals:**
- Realce de palavras igual ao lexer do core 1.3.0, com classificação testável sem DOM.

**Non-Goals:**
- Analisar a gramática de verdade (saber se o `:` é de uma declaração ou de um literal de dicionário). A regra é só "token significativo anterior".
- Marcar no editor o erro de `var` dentro de `se`/`enquanto`/`para`. Isso já é coberto pelo fluxo de erro de compilação atual.

## Decisions

### D1. Estado com o último token significativo
`startState()` devolve `{ anterior: null }`. Todo token significativo grava em `state.anterior`:
- palavras: o texto em minúsculas;
- `:`: a string `":"`;
- operadores e outros caracteres (`(`, `[`, `,`…): o próprio texto;
- strings e números: o marcador `"literal"`.

Espaços (`eatSpace`) e comentários (`//`) retornam sem mexer em `state.anterior`. Como o estado passa de uma linha para a outra, um `:` no fim de uma linha afeta a primeira palavra da linha seguinte, e uma linha que termina em `inteiro` não afeta.

*Alternativa:* olhar só a linha atual com `stream.string`. Foi descartada porque não cobre o `:` no fim da linha anterior, que a spec exige.

### D2. `:` como pontuação
Antes do teste de operadores: `if (stream.eat(":")) { state.anterior = ":"; return "punctuation"; }`. O `:` não entra na regex de operadores, para não mudar o realce dos operadores atuais.

### D3. Função pura `classificarPalavra(palavra, tokenAnterior)`
Exportada de `meupia-lang.js`. Compara em minúsculas e devolve `"keyword"`, `"atom"`, `"typeName"` ou `"variableName"`, nesta ordem:
1. está em `meuPiaKeywords` → `keyword`;
2. está em `meuPiaAtoms` → `atom`;
3. está em `meuPiaTypes` (os tipos fixos) → `typeName`;
4. está em `meuPiaTiposContextuais` (`lista`, `logico`) **e** `tokenAnterior` (em minúsculas) é `":"` ou `"novo"` → `typeName`;
5. nos demais casos → `variableName`.

O `token()` passa a usar essa função. `meuPiaKeywords` fica exatamente com as palavras reservadas do core (sem `função`/`fim_função`). `meuPiaTypes` fica com `inteiro`, `real`, `float`, `string`, `cadeia`, `dicionario` e `filaprioridade`.

### D4. Exportar a especificação do tokenizer para testes entre linhas
O objeto passado a `StreamLanguage.define` vira a constante exportada `meuPiaTokenizer`, e `meuPiaLanguage = StreamLanguage.define(meuPiaTokenizer)`. Os testes em `src/editor/meupia-lang.test.js` tokenizam várias linhas com `StringStream` (de `@codemirror/language`), usando um único estado vindo de `startState()`. Assim eles cobrem o caso de o contexto atravessar linhas, coisa que a função pura sozinha não mostra.

### D5. Snippet `var`
`snippetCompletion("var ${nome}: ${tipo} <- ${valor}", { label: "var", detail: "variável local", type: "keyword" })`, acrescentado à lista atual.

### D6. Cenário antigo da versão mantido
O OpenSpec não deixa um MODIFIED remover cenários existentes. Por isso o requisito "Versão do compilador" mantém o cenário "Recursos da linguagem do core 1.2.0" (`x=5` e `!=` continuam valendo no 1.3.0) e ganha o cenário "Recursos da linguagem do core 1.3.0".

## Risks / Trade-offs

- [`:` de literal de dicionário (`{"a": lista}`) faz `lista` aparecer como tipo] → Aceito. É raro, e o erro é só de cor.
- [Um comentário entre `:` e `lista` não quebra o contexto] → Esse é o comportamento desejado (comentários não são significativos), igual ao core.
- [Sem `:` nem `novo`, `lista` aparece com cor de variável mesmo em código antigo que usava `lista` como tipo em outra posição] → No core, isso já não é tipo, então a cor passa a dizer a verdade.

## Migration Plan

Deploy estático, como hoje. Para reverter, basta voltar `version` para `1.2.0` e reverter `meupia-lang.js`.
