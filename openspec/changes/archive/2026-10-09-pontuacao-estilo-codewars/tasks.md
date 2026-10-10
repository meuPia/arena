## 1. Juiz: testes isolados e veredito novo

- [x] 1.1 Reescrever `api/_lib/shim/meupia_testes/plugin_testes.py` com `ATUAL`/`RESULTADOS` indexados (D2). Cada `esperar_*` captura exceções da comparação, e `esperar_verdadeiro`/`falso` usam truthiness. Verificar com um teste unitário do shim: chamada com `ATUAL=None` é ignorada, a última chamada no mesmo teste vale e a comparação que lança vira `False`.
- [x] 1.2 Reescrever `api/_lib/executor.py` (D1, D3). Ler o nonce e `N` do stdin, aplicar a transformação de AST em `main()` (testes viram `_arena_teste(k, lambda: …)` e o `inicio` vira `_arena_inicio`), usar `setitimer` de 1 s por teste, emitir uma linha assinada por teste e `{"fim": true}` no final, e devolver "montagem inválida" quando os últimos N comandos não forem `esperar_*`. Verificar rodando o executor à mão sobre um `main.py` gerado de S03 e conferindo as N linhas assinadas.
- [x] 1.3 Reescrever `juiz.julgar(fonte, exemplos, extras, detalhes=False)` em `api/_lib/juiz.py` (D3, D4). O tempo total passa a ser `min(15, 2 + N)`, o resultado sai das linhas com o nonce (inclusive de `TimeoutExpired.stdout` em bytes) e os status passam a ser `aceito`/`reprovado_exemplos`/`erro_compilacao`/`erro_execucao`, com `exemplos`, `extras`, `completo` e `falhaExemplo`. O mapeamento de linha do erro de compilação não muda. Verificar com `pytest tests/test_juiz.py`.
- [x] 1.4 Implementar `juiz.caracteres_significativos(fonte)` (D5) e incluir `caracteres` no retorno de todo julgamento que compila. Verificar com testes: comentários, indentação e linhas em branco não contam; espaço dentro de texto conta; `"http://x"` conta inteiro; aspas escapadas com `\"`; texto sem fechamento.
- [x] 1.5 Criar `tests/test_juiz.py`, trazendo os testes de juiz de `tests/test_arena.py` adaptados aos status novos (marcador forjado, segredo do ambiente, erro de compilação com linha, nome de função errado) e acrescentando: exceção em 1 teste não afeta os demais, laço infinito em 1 teste extra reprova só esse teste (em menos de 3 s), `esperar_igual(1, 1)` dentro da função do aluno não aprova, `inicio` com erro não impede os testes, estouro do tempo total mantém os testes concluídos, e `reprovado_exemplos` com exemplos 2/3. Verificar com `pytest tests/test_juiz.py`.

## 2. Dados dos desafios

- [x] 2.1 Criar `arena/extras_base/<COD>.txt` para os 9 desafios com as linhas atuais de `testesOcultos`, e renomear o campo para `testesExtras` em `arena/desafios/*.json` (o conteúdo continua o mesmo por enquanto). Verificar com `grep -r testesOcultos arena api scripts src tests` vazio, exceto em comentários de migração.
- [x] 2.2 Acrescentar `"pontuacao": {"modo": "proporcional"}` e `"desbloqueioConta": "aceito"` em `arena/config.json`, e fazer `arena.config()` validar os dois valores com padrões e erro para valor desconhecido (D7). Verificar com um teste que carrega uma config com modo inválido e espera erro.

## 3. Geração da bateria extra

- [x] 3.1 Criar `scripts/gerar_testes_extras.py` com o serializador Python → Portugol (que recusa `"` e `\` em textos), o leitor de literais Portugol das linhas base/públicas e o laço que regrava só `testesExtras` com `indent=2, ensure_ascii=False` (D9). Verificar rodando o script com um registro vazio: os JSON não mudam (`git diff` vazio).
- [x] 3.2 Escrever a referência em Python e o gerador (semente fixa, cerca de 15 casos) para B01, B02 e B03, conferindo antes a referência contra `testesPublicos` e `extras_base`. Verificar com o script rodando sem divergências e com a bateria de cada um entre 15 e 25 testes.
- [x] 3.3 Fazer o mesmo para S01, S02 e S03 (inclui rotas de até 120 passos em S03). Verificar como em 3.2.
- [x] 3.4 Fazer o mesmo para G01, G02 e X01 (listas de até 300 itens, matrizes de até 12×12 e números com até 80 dígitos). Verificar como em 3.2.
- [x] 3.5 Rodar o script duas vezes e confirmar que é determinístico: `git diff` vazio entre a 1ª e a 2ª execução.

## 4. Validação dos desafios

- [x] 4.1 Reescrever `scripts/validar_desafios.py` (D10): gabarito `aceito` e completo com `max(ms) ≤ 500`, código inicial não completo, 15–25 extras e nenhum `testesOcultos`, com uma linha `OK`/`ERRO` por desafio. Verificar com `npm run validar` terminando com "TUDO OK". Se algum gabarito falhar num extra, corrigir o gabarito ou a referência, e nunca afrouxar a validação.

## 5. Regras de pontuação e placar

- [x] 5.1 Implementar em `api/_lib/arena.py` as funções puras `pontos_submissao`, `melhor`, `melhores`, `tempo_ultima_melhoria`, `contagem_desbloqueio` e o novo `placar`, e adaptar `nivel_liberado`/`falta_para_liberar` (D7). Verificar com testes em `tests/test_arena.py`: 14/20 de 10 pts = 7, 19/20 de 35 pts = 33, modo `completo`, melhor mantida diante de uma submissão pior, empate de pontos resolvido por caracteres, desempate do placar por completos → caracteres → horário → nome, redução de caracteres que não muda o horário da última melhoria, freeze com melhoria pós-freeze, e desbloqueio com parcial nos modos `aceito` e `completo`.
- [x] 5.2 Em `api/_lib/store.py`, adicionar `k_aceitas(eid)` e remover `k_resolvidos` (D6). Verificar com um teste que grava duas aceitas pelo `Local` e lê a lista na ordem esperada.
- [x] 5.3 Reescrever `servico.submeter` (D8): sai o `ja_resolvido`, a tentativa continua sendo registrada antes de julgar, o resultado vai para `k_aceitas` quando aceito, o log ganha exemplos, extras, pontos, completo e caracteres, e a resposta traz `melhor`, `pontosModulo` e `caracteres`. Verificar com testes de fluxo: submissão parcial pontua, `reprovado_exemplos` não pontua e conta para o cooldown, nova submissão depois de completo é aceita e reduz os caracteres registrados.
- [x] 5.4 Adaptar `servico.missoes`, `servico.missao` e `servico.placar` para ler as aceitas (por equipe e de todas as equipes), devolver `melhor` e `completo` por módulo e calcular o placar congelado com `ate=freeze`. Verificar com testes: o painel mostra 7/10 em B01 parcial, a missão não contém `testesExtras`, o placar público não tem fonte nem participantes, e o placar congelado ignora a melhoria pós-freeze enquanto o admin a mostra.
- [x] 5.5 Remover de `tests/test_arena.py` os testes do modelo antigo (`validado`, `ja_resolvido`, `resolvidos`) e garantir que `test_todos_os_gabaritos_validam` use o veredito novo (aceito e completo). Verificar com `npm run test:py` passando.

## 6. Interface

- [x] 6.1 `src/arena/submissao.js`: mensagens novas da IDE (ACEITO / ACEITO PARCIAL / Passe primeiro nos exemplos), linha com a melhor pontuação e os caracteres, status `Melhor: p/P pts` com selo, e botão sem trava de "Recuperado". Verificar no `npm run local` submetendo o gabarito de B01, uma versão parcial e uma que falha num exemplo, e conferindo os três textos.
- [x] 6.2 `ide.html`: trocar o aviso do modal de submissão para testes de exemplo/extras e desempate por menor código. Verificar abrindo o modal no `npm run local`.
- [x] 6.3 `src/arena/painel.js` e `src/arena/arena.css`: card com `p/P pts`, selo ✅ e estados `completo`/`parcial`. Verificar no `npm run local` com um módulo parcial e outro completo.
- [x] 6.4 `placar.html` e `src/arena/placar.js`: ●/◐/○ por módulo, colunas Completos e Caracteres, e o log do admin com Exemplos, Extras, Pts e Car. Verificar em `/placar.html` e `/placar.html?admin=admin` no `npm run local`.

## 7. Enunciados, infraestrutura e documentação

- [x] 7.1 Acrescentar à `descricao` dos 9 desafios um bloco padrão "Como pontua" (exemplos obrigatórios, pontos proporcionais aos testes extras "N de M", desempate pelo menor código, sem contar comentários e indentação). Verificar com um teste que confere a presença do bloco em todos os desafios.
- [x] 7.2 `vercel.json`: `maxDuration` 30 (D12). Verificar com `python3 -c "import json; print(json.load(open('vercel.json'))['functions']['api/*.py']['maxDuration'])"`.
- [x] 7.3 Atualizar `CLAUDE.md` (regra de ouro com `testesExtras`, arquitetura do juiz isolado, nova seção "Pontuação", convenção "N de M" e `ARENA_PREFIXO` novo para os ensaios) e `README.md` (modelo Codewars, `gerar_testes_extras.py`). Verificar relendo as duas seções e confirmando que nenhuma menção a "testes ocultos" ficou desatualizada.

## 8. Verificação final

- [x] 8.1 Rodar `npm test` e `npm run validar`, os dois passando sem falhas.
- [x] 8.2 Ensaio ponta a ponta no `npm run local` com duas equipes (`TROQUE-ESTE-CODIGO-1`/`-2`): parcial → completo → redução de caracteres, reprovação nos exemplos entrando no cooldown, desbloqueio de Silver com um Bronze parcial e placar público vs. admin coerentes. Registrar o resultado no PR.
