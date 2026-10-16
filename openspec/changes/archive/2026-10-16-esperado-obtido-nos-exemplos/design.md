## Context

Motivação em `proposal.md`; comportamento em `specs/arena-interface/spec.md`. O que existe hoje e define a abordagem:

- **Montagem e execução** (`src/engine/wasm.js`, herdado do Lab): o Rodar monta o programa (`usar "testes"` + `testesPublicos` + `fim_algoritmo`), compila com o `meupia-core` no Pyodide e executa `output/main.py` com `exec(..., {"__name__": "__main__"})`. Antes de compilar, ele apaga `output/main.py`; depois da compilação, deixa `codigo_retorno` e `gerou_py` nos globais do Pyodide. Um erro de execução derruba o programa inteiro (`[ERRO DO SISTEMA]`), e os testes seguintes não rodam.
- **Código gerado**: o `meupia-core` 1.3.0 gera `from meupia_testes.plugin_testes import *` no topo e põe cada linha de teste como uma instrução de `main()`, por exemplo `esperar_igual(dobro(2), 4, _S("Exemplo 1"))`. Cadeias viram `_S`, uma subclasse de `str`; `escreva` usa `_texto`, que mostra lógicos como `verdadeiro`/`falso`.
- **Plugin `meupia-testes` 1.0.0** (PyPI, instalado pelo `micropip`): cada `esperar_*` compara e imprime `[TESTE_OK] Sucesso: …` ou `[TESTE_FALHA] Falhou: Esperava '{esperado}', mas recebeu '{recebido}' - {mensagem}`, com `str()` nos dois valores. É daí que vem o "esperava '4', recebeu '4'". Uma comparação que lança erro derruba o programa.
- **Painel atual**: `src/main.js` intercepta `term.writeln` e chama `parseTestLine` (`src/ui/instructions.js`, do Lab), que procura os marcadores no texto e faz `innerHTML +=` em `#test-results`. Qualquer `escreva("[TESTE_OK] …")` do aluno vira um cartão, e o valor entra como HTML.
- **Juiz** (`api/_lib/executor.py`): identifica os testes como as N últimas instruções `esperar_*` de `main()`, sendo N o número de linhas `esperar_*` da bateria (`juiz._linhas_de_teste`). Chamadas `esperar_*` fora delas são ignoradas, e a comparação que lança erro reprova só o teste (`shim/meupia_testes/plugin_testes.py`).
- **Celular** (`src/arena/ide-mobile.js`): um `MutationObserver` em `#test-content` marca a aba Missão como "nova" quando entra um nó com a classe `test-item`.
- O `CLAUDE.md` pede mexer o mínimo em `src/engine/wasm.js` e `src/ui/*`, para continuar trazendo melhorias do `upstream`.

## Goals / Non-Goals

**Goals:**
- Resultado estruturado (tipo e valor) de cada linha de teste de exemplo, sem depender do stdout do aluno.
- Mesmo critério de aprovação do juiz e a mesma regra de "o que é um teste".
- Nenhuma mudança em `wasm.js`, `instructions.js`, no juiz ou no pacote do PyPI.
- Formatação, diferença e dicas em funções puras testáveis com `node --test`; o trecho Python testável com `pytest` contra o `meupia-core` 1.3.0 real.
- Volta automática ao comportamento antigo se o plugin da Arena não puder ser ativado.

**Non-Goals:**
- Não isolar os testes no navegador (limite de tempo por teste, seguir depois de uma exceção no cálculo da entrada). O navegador continua parando no primeiro erro de execução, como hoje.
- Não mudar o terminal além das linhas dos testes de exemplo.
- Não usar algoritmo de diff completo (LCS/Myers): um trecho diferente por valor basta para os casos que geram "mas está igual!".

## Decisions

### D1. Trocar as funções do plugin no Pyodide, depois da inicialização
Um trecho Python da Arena (`src/arena/plugin_testes_arena.py`, embutido no build com `?raw` por um módulo pequeno, como `src/arena/cartao.js`) é executado uma vez com `pyodide.runPython`, logo depois que `initWasmEngine` termina. Ele guarda as funções originais de `meupia_testes.plugin_testes` e põe no lugar versões da Arena com a mesma assinatura. Como o código gerado faz `from meupia_testes.plugin_testes import *` a cada execução, ele já pega as versões novas.

Em `src/main.js`, a chamada final vira `initWasmEngine(term, runBtn).then(() => ativarTestesArena(getPyodide()))`. O `initWasmEngine` habilita o botão Rodar no fim e o `.then` roda numa microtarefa logo em seguida, antes de qualquer clique; o `runPython` é síncrono. Se `getPyodide()` for `null` (falha no motor) ou o trecho lançar erro, `ativarTestesArena` devolve `false` e nada muda.

- *Alternativa: publicar um `meupia-testes` novo no PyPI*. Mudaria o Lab e o pacote de todo mundo, e o prazo do evento não comporta.
- *Alternativa: mudar a montagem em `wasm.js` (por exemplo, embrulhar cada linha de teste)*. Mexe no arquivo do Lab e quebra a regra "montagem igual à do Lab" que o juiz replica.
- *Alternativa: continuar lendo o stdout com um formato mais rico*. Mantém o problema do marcador forjado e mistura a saída do aluno com o resultado.

### D2. Saber qual linha de teste chamou: frame do chamador + AST do `main.py`
A versão da Arena de cada `esperar_*` olha o frame do chamador (`sys._getframe(1)`). Só conta como teste a chamada feita diretamente de `main()` numa linha que pertence a uma das N últimas instruções `esperar_*` de `main()`, a mesma regra do `executor.transformar`. O mapa `linha do main.py → k` é montado na primeira chamada de cada Rodar: o trecho lê `output/main.py` (que o `wasm.js` acabou de gerar), faz `ast.parse` e cobre de `lineno` a `end_lineno` de cada instrução, para aguentar uma linha de teste que vire várias linhas Python. N vem do JavaScript, contado como no juiz (linhas de `testesPublicos` que começam com `esperar_` depois de `trim`).

Chamadas fora do mapa (o aluno chamando `esperar_*` no `inicio` ou dentro de uma função) seguem para a função **original** do plugin, com o mesmo efeito de hoje no terminal, e não geram cartão. Se as N últimas instruções não forem todas `esperar_*` (montagem inesperada), o mapa fica vazio, nenhuma chamada vira cartão e a rodada termina como em D6, com todos "não executado". Esse caso só acontece com um desafio malformado, que o `npm run validar` já recusa no juiz.

- *Alternativa: contar as chamadas em ordem (a k-ésima chamada é o teste k)*. Quebra assim que o aluno chama `esperar_*` por conta própria ou uma função chamada no teste também chama.

### D3. Comparação idêntica à do juiz, com erro reprovando só o teste
Para as chamadas mapeadas, a comparação é a mesma do shim do juiz: `recebido == esperado`, `!=`, `>`, `<`, `item in colecao`, `bool(condicao)` e `not condicao`. Uma exceção na comparação vira `ok = False` com `erro = "comparar"`, sem propagar, como no juiz. O valor devolvido continua sendo o booleano do resultado, para não mudar programas que usam o retorno.

### D4. Valores formatados em Python; diferença e dicas em JavaScript
O Python conhece o tipo real; o JavaScript é onde fica fácil testar e renderizar. O trecho Python entrega, por teste:

```
{ "k": 0, "funcao": "igual", "ok": false, "mensagem": "Exemplo 1", "erro": null,
  "esperado": {"tipo": "inteiro", "texto": "4", "bruto": 4},
  "obtido":   {"tipo": "cadeia",  "texto": "\"4\"", "bruto": "4"} }
```

Regras de `formatar(valor)`, nesta ordem: `None` → `sem valor`; `bool` → `logico` (`verdadeiro`/`falso`, antes de `int`, que é a classe-mãe); `int` → `inteiro`; `float` → `real` com `repr` (`4.0`, `0.30000000000000004`); `str` (inclui `_S`) → `cadeia`, entre aspas duplas, com `·` no lugar de espaço, `→` no de tabulação e `↵` no de quebra de linha; `list`/`tuple`/`deque` → `lista` `[a, b]`; `dict` → `dicionario` `{"a": 1}`; o resto → o `str()` com o tipo `valor`. Listas e dicionários formatam os elementos com as mesmas regras, até a profundidade 4, e o texto é cortado em 2.000 caracteres (o JavaScript encurta para 300 na tela, D5). `bruto` só vai para cadeia, inteiro e real de nível superior, que é o que as dicas usam; ele é truncado nos mesmos 2.000 caracteres.

Os marcadores entram já no Python porque só ele sabe quais espaços estão dentro de uma cadeia (o espaço de `, ` numa lista não é marcado). Um `·` literal na cadeia do aluno fica igual a um espaço marcado; é um caso raro e aceitável.

### D5. Trecho diferente: prefixo e sufixo comuns
`trechoDiferente(a, b)` compara os textos formatados por código de caractere (`Array.from`, para não partir emoji) e devolve o maior prefixo comum e o maior sufixo comum que não se sobrepõem; o meio de cada lado é o destaque. Quando um lado não tem meio (o caso "faltou um caractere"), o outro lado mostra o destaque e o lado curto ganha um marcador de posição. Com tipos diferentes, o destaque vai para o rótulo do tipo, não para o texto. Para encurtar valores longos, a janela de 300 caracteres é centrada no início do trecho diferente, com `…` nas pontas cortadas.

As dicas seguem a ordem do requisito "Destaque das diferenças e dicas". As comparações de cadeia usam `bruto`: `trim()`, remoção de `\s`, `toLowerCase()` e remoção de acentos (`normalize("NFD")` + `\p{M}`, como em `ajuda.js`). "Reais muito próximos" = os dois reais com `|a − b| ≤ 1e-9 × max(1, |a|, |b|)`.

### D6. Ciclo da rodada no JavaScript
`src/arena/testes-exemplo.js` exporta as funções puras e um pequeno controlador:
- `ativarTestesArena(pyodide)`: registra o módulo JS `arena_testes` (`pyodide.registerJsModule`) com `registrar(json)`, roda o trecho Python e liga a flag `ativo`.
- `iniciarRodada(pyodide, testesPublicos)`: lê as linhas de teste, guarda a entrada de cada uma, define N no Python, zera o mapa e os resultados, apaga `codigo_retorno`/`gerou_py` dos globais e desenha o resumo vazio.
- `registrar(json)`: guarda o resultado do teste k e desenha o cartão dele na hora (o aluno vê o progresso mesmo se o programa travar depois).
- `concluirRodada(pyodide)`: se `codigo_retorno !== 0` ou `!gerou_py`, foi erro de compilação e a área fica vazia; senão, os testes sem resultado viram "não executado" e o resumo é fechado.

O handler do Rodar em `main.js` chama `iniciarRodada` antes e `concluirRodada` depois de `await runWasmCode(view, term)`. A interceptação de `term.writeln` só chama `parseTestLine` quando `ativo` é falso, que é o fallback.

`registrar` recebe uma string JSON (`json.dumps`) em vez de um `dict`, para não lidar com `PyProxy` e não vazar memória no Pyodide.

### D7. Entrada lida da linha do desafio, em Portugol
A entrada vem da linha de teste do `testesPublicos`, não do Python (que só tem `dobro(2)` já traduzido e, em cadeias, `_S("…")`). `argumentosDaLinha(linha)` acha o parêntese da chamada `esperar_*` e separa os argumentos pelas vírgulas de nível zero, respeitando `()`, `[]`, `{}` e cadeias entre aspas duplas com `\"`. A entrada é o primeiro argumento, sem espaços nas pontas. Se a separação falhar (parênteses desbalanceados), a entrada é a linha inteira. O rótulo vem da `mensagem` que o Python recebeu; vazia, vira `Exemplo <k+1>`.

### D8. Renderização com DOM e só texto
Os cartões são montados com `createElement` e `textContent`; nenhum dado do aluno passa por `innerHTML`. Estrutura de um cartão reprovado:

```
div.test-item.fail.arena-teste
  div.arena-teste-cabecalho   ❌ Exemplo 1 · entrada: dobro(2)
  div.arena-teste-lados       (grid de 2 colunas; 1 coluna abaixo de ~420 px de largura do painel)
    div  Esperado  [inteiro]  4
    div  Obtido    [cadeia]   "4"
  p.arena-teste-dica          O esperado é inteiro e o obtido é cadeia.
```

Aprovado: só o cabeçalho (`div.test-item.success.arena-teste`). Não executado: `div.test-item.arena-teste.pendente`. A classe `test-item` fica em todos, para o `ide-mobile.js` continuar marcando a aba Missão. O resumo (`N de M exemplos aprovados`) fica num elemento com `aria-live="polite"`. O destaque usa `<mark>` com sublinhado, e os marcadores de espaço fora do destaque ficam num `span` com cor `--a-muted`.

A largura de uma coluna é decidida por container query (`container-type: inline-size` em `#test-results`), porque o painel lateral muda de largura com o Split.js e no celular, independentemente da janela.

### D9. Estilo só com tokens
Em `src/arena/arena.css`, sob `body.arena-ide`: o cartão reprovado reusa `--a-fail`/`--a-fail-bg`, o aprovado `--a-accent-*`, o pendente `--a-surface-3`/`--a-muted`, e o destaque `--a-gold-bg` com texto `--a-text` e contorno `--a-gold-borda` (o mesmo `mark` da busca da ajuda, `.arena-modal-ajuda mark`) + `text-decoration: underline`. Dentro do cartão reprovado, o texto do `mark` volta para `--a-text`, para não herdar `--a-fail` sobre o fundo dourado. Valores em `--a-font-mono`, com `white-space: pre-wrap` e `overflow-wrap: anywhere`. Nenhuma cor fixa. A tarefa de verificação confere com `contraste()` (de `editor-cores.js`) os pares de texto/fundo novos nos dois temas.

## Risks / Trade-offs

- [O `meupia-core` mudar a forma de gerar o import ou os testes] → o teste Python (tarefa 2) compila um desafio de exemplo com a versão fixada e falha se o mapa não achar as N linhas. A versão só muda junto com `wasm.js` e `requirements.txt`, e o `CLAUDE.md` já manda rodar os testes nessa hora.
- [O PyPI publicar um `meupia-testes` com outra estrutura] → o `micropip` instala a versão mais nova sem fixar. Se `meupia_testes.plugin_testes` não existir ou não tiver as funções, `ativarTestesArena` devolve `false` e volta o painel antigo. Fixar `meupia-testes==1.0.0` no `wasm.js` evitaria a surpresa, mas mexe no arquivo do Lab; fica registrado como melhoria para o `upstream`.
- [Diferença de comportamento entre Rodar e juiz quando a entrada de um teste lança erro] → no navegador, o programa para e os testes seguintes viram "não executado"; no juiz, só aquele teste reprova. Já é assim hoje; o texto do cartão diz "o programa parou antes de concluir este teste" e o terminal mostra o erro.
- [Laço infinito no Rodar continua travando a aba] → fora do escopo (Non-Goals); os cartões já desenhados continuam na tela porque `registrar` desenha na hora.
- [Valores enormes (listas de milhares de itens)] → corte em 2.000 caracteres no Python e janela de 300 na tela.
- [`·` literal ambíguo com espaço marcado] → aceito (D4).
- [Prazo: evento em 21/10] → a mudança não toca juiz, API nem submissão, e o fallback devolve o painel antigo. Se não for conferida no laboratório antes do evento, fica para depois sem prejuízo.

## Migration Plan

Só frontend: entra no próximo deploy da Vercel, sem migração de dados. Rollback: reverter o commit, ou fazer `ativarTestesArena` não ser chamada em `main.js`, o que volta o painel antigo sem mexer em mais nada.
