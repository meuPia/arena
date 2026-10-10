## Context

Hoje `runWasmCode` (`src/engine/wasm.js`) faz tudo num único bloco `runPythonAsync`: grava `main.por`, chama `main()` com o stdout redirecionado para `limbo`, decide o erro pela existência de `output/main.py`, imprime o `limbo` inteiro em caso de erro e, em caso de sucesso, roda `exec(codigo, globals())`. Toda a lógica de decisão fica dentro de Python e não pode ser testada sem o Pyodide.

Outros pontos que limitam o desenho:
- O stdout do Pyodide é ligado a `term.writeln`, que `main.js` envolve com `parseTestLine` (resultados do meupia-testes). O caminho de execução não pode mudar.
- A montagem do desafio faz três coisas: (1) remove `fim_algoritmo` sem tirar linhas, porque troca o texto por string vazia; (2) troca a primeira ocorrência de `algoritmo "..."` por `$1\nusar "testes"`, o que acrescenta uma linha; (3) anexa `"\n\n// --- TESTES AUTOMATIZADOS ---\n" + codigoTeste + "\nfim_algoritmo"`. Só (2) desloca as linhas que vieram do editor.
- O projeto ainda não tem testes nem `node_modules` instalado. O Vite está em `8.0.0-beta`, forçado por `overrides`. `@codemirror/lint` já vem como dependência transitiva de `codemirror`.

## Goals / Non-Goals

**Goals:**
- Tirar de Python a lógica de decisão e formatação do erro e colocá-la em funções JS puras, testáveis com `node:test`.
- Calcular o deslocamento de linhas sem mexer no texto montado do desafio.

**Non-Goals:**
- Realce contextual de `logico`/`lista` (só como tipo depois de `:` ou `novo`). O tokenizer realça essas palavras como tipo em qualquer posição.
- Tooltip ou painel de diagnósticos no editor. A mensagem fica só no terminal.
- Mapear a coluna em linhas deslocadas. A inserção acrescenta uma linha inteira, então a coluna não muda.

## Decisions

### D1. Módulo puro `src/engine/erros.js`
Novo módulo sem imports de DOM, Pyodide ou estado global, com:
- `extrairMensagemErro(saida)` → `{ tipo, linha, coluna, descricao, texto }` quando a mensagem segue o formato padronizado, ou `{ linha: null, texto }` no fallback. Regex: `/^Erro (léxico|sintático|semântico) na linha (\d+), coluna (\d+): (.*)$/m`. Fallback 1: o texto depois de `[COMPILATION ERROR]:`, sem espaços nas pontas e sem as linhas do log do lexer. Fallback 2: a saída inteira.
- `mapearLinhaErro(linhaMontada, info)` → `{ origem: "editor", linha }` | `{ origem: "bloco-aberto" }` | `{ origem: "testes" }`. Quando `info` é `null` (modo livre), a linha não muda e a origem é sempre `editor`. Regras, nesta ordem:
  1. `linhaMontada === info.linhaFimAnexado` → `bloco-aberto`;
  2. `linhaMontada >= info.inicioAnexo` → `testes`;
  3. `linhaMontada === info.linhaUsarTestes` → `testes`;
  4. `info.linhaUsarTestes !== null && linhaMontada > info.linhaUsarTestes` → `editor`, com `linhaMontada - 1`;
  5. nos demais casos → `editor`, com a mesma linha.
- `formatarMensagemErro(erro, mapeado)` → a string final do terminal. Na origem `editor`, troca o número da linha. Na origem `testes`, monta `Erro nos testes automáticos do desafio: <descricao>`. Na origem `bloco-aberto`, devolve a orientação fixa sobre blocos não fechados (texto da spec `motor-de-execucao`).

Linhas e colunas do core começam em 1 (confirmado no core 1.2.0). Nenhuma função faz `±1` na coluna. Erros no fim do arquivo apontam para o último token lido, então a linha sempre existe no programa montado. Um arquivo vazio gera `linha 1, coluna 1`.

*Alternativa:* deixar o parse em Python. Foi descartada porque não pode ser testada com `node:test` sem o Pyodide, e o pedido exige testes dessas funções.

### D2. Informações da montagem coletadas junto da montagem, sem mudar o texto
Dentro do `if (desafioAtual && desafioAtual.codigoTeste)` atual, sem alterar nenhuma das três operações:
- Antes do `replace` de `regexAlgoritmo`, se o `usar "testes"` for mesmo inserido, calcular `linhaUsarTestes` = (número de linhas do trecho até o fim do match) + 1, usando o `match.index` da mesma regex.
- `inicioAnexo` = número de linhas do `codigoFinal` logo antes do `+=` do cabeçalho, mais 1. É a primeira linha que não veio do editor. Daí para baixo, tudo é anexo (linha em branco, comentário, `codigoTeste`, `fim_algoritmo`).
- `linhaFimAnexado` = número de linhas do `codigoFinal` depois do último `+=` (o `\nfim_algoritmo`). É a última linha do programa montado.
- Fora de desafio, `info = null`.

*Alternativa:* extrair a montagem para uma função pura `montarPrograma()`. Seria mais testável, mas a restrição é não alterar o fluxo de montagem.

### D3. Separar compilação e execução em duas chamadas ao Pyodide
1. **Compilar:** o bloco Python grava `main.por`, chama `main()` com o stdout redirecionado, guarda `codigo_retorno` (o valor retornado; `None` vira `-1`), `saida_compilador = limbo.getvalue()` e `gerou_py = os.path.exists("output/main.py")`. O JS lê esses três valores com `pyodide.globals.get(...)`.
2. **Decidir no JS:** sucesso = `codigo_retorno === 0 && gerou_py`. Em erro: `term.writeln` com o cabeçalho vermelho `[ERRO DE COMPILAÇÃO]`, depois `formatarMensagemErro(...)`, depois `marcarErroCompilacao(view, linha, coluna)` se a origem for o editor. Em sucesso: `limparErroCompilacao(view)` e passa para o passo 3.
3. **Executar:** um segundo `runPythonAsync` imprime `[EXECUTANDO]` e roda `exec(codigo_python_gerado, {"__name__": "__main__"})`, ainda ignorando `SystemExit`. O `catch` JS de `[ERRO DO SISTEMA]` continua cobrindo os dois passos.

`exec` com um dicionário novo coloca `__builtins__` sozinho. Funções definidas no programa usam esse dicionário como globals, então a recursão e as variáveis globais do Portugol continuam funcionando.

*Alternativa:* `exec` com uma cópia de `globals()`. Foi descartada porque copiaria o estado sujo da execução anterior.

### D4. Marcação no editor com um `StateField` próprio
Em `src/editor/meupia-lang.js`:
- `StateEffect` `definirErro` (com `{linha, coluna}` ou `null`).
- `StateField` com um `DecorationSet`: `Decoration.line({class: "cm-linha-erro"})` e, se a coluna estiver dentro da linha, `Decoration.mark({class: "cm-coluna-erro"})` sobre o caractere da coluna (ou até o fim da palavra). O field fica vazio quando `tr.docChanged` ou quando recebe o efeito com `null`. A linha é limitada a `[1, doc.lines]`.
- Exports: `meuPiaErroCompilacao` (a extensão), `marcarErroCompilacao(view, linha, coluna)` e `limparErroCompilacao(view)`.
- `main.js` acrescenta a extensão no `EditorView`. `style.css` define as duas classes (fundo vermelho translúcido na linha e sublinhado ondulado `#f44336` na coluna).

*Alternativa:* `@codemirror/lint` com `setDiagnostics`. Daria tooltip e marcador no gutter, mas os diagnósticos são remapeados nas edições em vez de sumir, o que exigiria um listener extra para apagá-los. Também seria preciso declarar a dependência direta. Para "some na próxima edição", o `StateField` é mais simples.

### D5. Tokenizer
Ordem dentro de `token()`: comentário → string `/^"(?:[^"\\]|\\.)*"/` → número `/^\d+(?:\.\d+)?/` → operador `/^(?:<-|<>|<=|>=|==|!=|[+\-*\/%=<>])/` → palavra. As listas são comparadas em minúsculas, então `meuPiaTypes` guarda `"filaprioridade"`. O atom `pi` entra em `meuPiaAtoms`, e `mod` entra em `meuPiaKeywords`.

### D6. Test runner nativo do Node (`node:test`)
O script fica `"test": "node --test 'src/**/*.test.js'"`. As aspas fazem o Node expandir o glob, já que o `sh` do npm não tem `**`. Os testes ficam em `src/engine/erros.test.js` e usam `node:test` + `node:assert/strict`. Eles importam só `erros.js`, que é ESM puro (o `package.json` já tem `"type": "module"`). O Vite não empacota esse arquivo porque ninguém o importa.

*Alternativa:* vitest. Foi descartada porque a peer `vite ^6.4.0 || ^7.0.0 || ^8.0.0` não aceita o pré-lançamento `8.0.0-beta.15` instalado, e o npm acusaria `ERESOLVE`. As funções são puras e não precisam de DOM nem de transformação do Vite, então o runner nativo basta e não traz nenhuma dependência.

## Risks / Trade-offs

- [Um `codigoTeste` com bloco desbalanceado também cairia no `fim_algoritmo` anexado e seria mostrado como "bloco não fechado" ao aluno] → Pouco provável, porque os desafios são mantidos pelo projeto. A correção dos JSON é de outro change.
- [A orientação de bloco não fechado não diz qual bloco] → Limitação do core atual. Ver Follow-ups.
- [`codigo_retorno` pode vir `None` se o core instalado não for o 1.2.0] → Normalizar para `-1` e tratar como erro. A checagem de `gerou_py` evita um falso positivo.
- [`logico`/`lista` realçados como tipo também quando usados como identificador] → Trade-off aceito (ver Non-Goals).
- [O wrapper de `term.writeln` em `main.js` chama `parseTestLine` também para as mensagens de erro] → Igual a hoje. As mensagens de erro não seguem o formato das linhas de teste.

## Migration Plan

Deploy estático, como hoje. Para reverter, basta voltar `version` para `1.1.20` e reverter os arquivos alterados. Não há dados persistidos envolvidos.

## Follow-ups (fora deste change)

- **meupia-core:** apontar a linha do bloco que ficou aberto (ex.: "o `se` da linha 4 não foi fechado com `fim_se`") em vez de acusar o `fim_algoritmo`. Isso ajuda também fora dos desafios e combina com o change do Tutor Socrático. Quando existir, a origem `bloco-aberto` poderá usar essa linha.
