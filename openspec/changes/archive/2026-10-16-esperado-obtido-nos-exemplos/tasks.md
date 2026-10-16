## 1. Funções puras em JavaScript (sem DOM)

- [x] 1.1 Criar `src/arena/testes-exemplo.js` com `linhasDeTeste(testesPublicos)` (linhas que começam com `esperar_` depois de `trim`, como `juiz._linhas_de_teste`) e `argumentosDaLinha(linha)` (D7). Cobrir em `src/arena/testes-exemplo.test.js`:
  - `esperar_igual(dobro(2), 4, "Exemplo 1")` → entrada `dobro(2)`;
  - vírgulas dentro de `()`, `[]`, `{}` e de cadeias (`"a, b"`, com `\"`) não separam argumentos;
  - linha com parênteses desbalanceados → entrada = linha inteira;
  - linhas vazias e comentários `//` não contam.

  Verificar com `npm run test:js` passando.
- [x] 1.2 Implementar `trechoDiferente(a, b)` e `janela(texto, inicio, 300)` (D5) e cobrir: `"ok"` × `"ok·"` destaca só o `·`; `"Ola"` × `"ola"` destaca o primeiro caractere; um lado sem meio (caractere faltando); emoji não é partido; valor de 1.000 caracteres com a diferença no fim mantém a diferença visível, com `…` no começo. Verificar com `npm run test:js`.
- [x] 1.3 Implementar `dica(resultado)` com as 8 regras na ordem do requisito "Destaque das diferenças e dicas" (D5) e cobrir uma regra por caso, mais um caso sem dica (`3` × `7`) e um caso em que duas regras se aplicariam (vence a primeira). Verificar com `npm run test:js`.

## 2. Plugin da Arena em Python

- [x] 2.1 Criar `src/arena/plugin_testes_arena.py` (D1–D4): guarda as funções originais de `meupia_testes.plugin_testes`, define as versões da Arena (frame do chamador, mapa `linha → k` pelo AST de `output/main.py` com N vindo do JS, comparação igual à do shim do juiz, `formatar(valor)`), envia `json.dumps(...)` para `arena_testes.registrar` e imprime no terminal `[TESTE_OK] <rótulo>` ou `[TESTE_FALHA] <rótulo>: esperado <texto> (<tipo>), obtido <texto> (<tipo>)`. Chamadas fora do mapa vão para a função original.
- [x] 2.2 Criar `tests/test_plugin_testes_arena.py`: com módulos falsos em `sys.modules` (`meupia_testes.plugin_testes` com funções originais que só anotam a chamada, e `arena_testes` que coleta o JSON), compilar com o `meupia-core` 1.3.0 o código montado como no `wasm.js` (código do aluno + `usar "testes"` + `testesPublicos` de `arena/exemplos/B91.json`) e executar o `output/main.py`. Cobrir:
  - gabarito: 3 resultados, `k` 0, 1, 2, todos `ok`;
  - função que devolve `"" + n * 2`: `esperado` inteiro `4`, `obtido` cadeia `"4"`, `ok` falso;
  - `inicio` do aluno chamando `esperar_igual(1, 1)`: vai para a função original e não gera resultado;
  - `esperar_maior` entre cadeia e inteiro: `ok` falso, `erro = "comparar"`, e o teste seguinte roda;
  - `formatar`: `None`, `True`, `4`, `4.0`, `"a b\n"` (com `·` e `↵`), lista aninhada, dicionário, corte em 2.000 caracteres;
  - um `escreva("[TESTE_OK] ...")` do aluno não gera resultado.

  Verificar com `npm run test:py` passando.

## 3. Painel na aba Missão

- [x] 3.1 Em `src/arena/testes-exemplo.js`, implementar `ativarTestesArena`, `iniciarRodada`, `registrar` e `concluirRodada` (D6), e a renderização dos cartões com `createElement`/`textContent` (D8): resumo com `aria-live="polite"`, cartão aprovado compacto, reprovado com esperado/obtido/tipos/destaque/dica, "não executado", e a classe `test-item` em todos. Criar `src/arena/testes-plugin.js`, que só importa o `.py` com `?raw` (fora do caminho dos testes de `node --test`). Verificar com `npm run test:js` (os imports não quebram) e `npm run build` sem erro.
- [x] 3.2 Em `src/main.js`: trocar a chamada final por `initWasmEngine(term, runBtn).then(() => ativarTestesArena(getPyodide()))`; no handler do Rodar, chamar `iniciarRodada` antes e `concluirRodada` depois de `runWasmCode`; na interceptação de `term.writeln`, chamar `parseTestLine` só quando o plugin da Arena não está ativo. Conferir com `git diff` que `src/engine/wasm.js` e `src/ui/instructions.js` não mudaram.
- [x] 3.3 Em `src/arena/arena.css`, sob `body.arena-ide`, estilizar `.arena-teste` (cabeçalho, grid de dois lados com container query em `#test-results`, rótulo do tipo, `mark` com sublinhado, marcadores de espaço em `--a-muted`, dica, pendente) só com tokens (D9). Verificar com `grep` que não há cor fixa nas regras novas e, com `contraste()` de `editor-cores.js`, que `--a-text` sobre `--a-gold-bg`, `--a-fail` sobre `--a-fail-bg` e `--a-muted` sobre `--a-fail-bg` ficam ≥ 4,5:1 nos dois temas (se algum par não passar, usar outro token existente e registrar no design).

## 4. Verificação na IDE

- [x] 4.1 Com `npm run local`, entrar com `TROQUE-ESTE-CODIGO-1`, abrir B91 e conferir no navegador (preview), nos temas escuro e claro:
  - gabarito → `3 de 3 exemplos aprovados`, três cartões compactos;
  - `retorne "" + n * 2` → cartões com `4` (inteiro) × `"4"` (cadeia), rótulos destacados e a dica de tipos;
  - função sem `retorne` → obtido `sem valor` e a dica do `retorne`;
  - `escreva("[TESTE_OK] Sucesso: x")` no `inicio` → nenhum cartão extra;
  - retorno `"<b>oi</b>"` → aparece como texto;
  - erro de execução no 2º exemplo (por exemplo, índice fora da lista) → 1º com resultado, 2º e 3º "não executado", terminal com `[ERRO DO SISTEMA]`;
  - erro de compilação → área de resultados vazia;
  - terminal com as linhas `[TESTE_OK] Exemplo 1` / `[TESTE_FALHA] Exemplo 1: esperado 4 (inteiro), obtido "4" (cadeia)`.

  Registrar com captura de tela de um cartão reprovado em cada tema.
- [x] 4.2 Na largura de celular (`resize_window` mobile), rodar B91 com um exemplo reprovado: a aba Missão ganha a marca de novidade, e o cartão mostra esperado e obtido um embaixo do outro, sem rolagem horizontal da página.
- [x] 4.3 Fallback: com `ativarTestesArena` forçada a devolver `false` (por exemplo, renomeando temporariamente o módulo `arena_testes` no trecho Python), Rodar volta a mostrar as linhas antigas `✅`/`❌` e Submeter continua funcionando. Desfazer a alteração temporária depois.
- [x] 4.4 Rodar `npm test` completo e `npm run validar` (sem banco: os exemplos) e confirmar que passam, para garantir que o juiz e os desafios não foram afetados.

## 5. Documentação

- [x] 5.1 No `CLAUDE.md`, na linha de `ide.html` da Arquitetura, citar que o Rodar mostra esperado × obtido dos exemplos (`src/arena/testes-exemplo.js` + `plugin_testes_arena.py`, troca das funções do plugin no Pyodide, fallback para o painel do Lab). No `docs/cartao-dialeto.md`, seção "Na Arena", acrescentar uma frase dizendo que, ao rodar, cada exemplo reprovado mostra o esperado e o obtido com o tipo. Rodar `npm run test:py` (o `test_cartao_dialeto.py` continua passando) e `npm run test:js` (a busca da ajuda continua passando com o cartão novo).
