## Context

Hoje (ver proposal.md, "Why"):
- `juiz.julgar(fonte, testes)` concatena `testesPublicos` + `testesOcultos`, compila uma vez e roda `executor.py`, que faz `exec` do `main.py` gerado. O shim `plugin_testes` acumula booleanos em `RESULTADOS`. Uma exceção ou um laço infinito interrompe todos os testes seguintes, e o estouro de `TEMPO_EXECUCAO` (5 s) devolve `tempo_esgotado` sem nenhum resultado.
- `servico.submeter` grava a solução em `k_resolvidos(eid)` com `HSETNX`, só quando o status é `validado`. O placar, o desbloqueio e o painel leem esse hash. O freeze filtra os timestamps desse hash.
- Verifiquei o `main.py` que o meupia-core 1.3.0 gera para um desafio montado. `def main():` tem `global ...`, depois os comandos do `inicio` do aluno e por último **uma linha `Expr(Call(Name("esperar_*")))` por teste**, na ordem anexada. Medi também que compilar e rodar uma bateria de 25 testes com rotas de 120 passos ou 15 matrizes 12×12 leva cerca de 0,2 s.
- No macOS e no Linux, `subprocess.run(..., timeout=...)` devolve em `TimeoutExpired.stdout` (em **bytes**) a saída produzida até a morte do processo.
- O lexer do meupia-core trata `//` como comentário até o fim da linha, textos só com `"` (escapada por um número ímpar de `\`) e espaços via `isspace()`. Não há comentário de bloco.
- `vercel.json` tem `maxDuration: 20`. A compilação pode levar até 10 s e a nova execução até 15 s.

## Goals / Non-Goals

**Goals:**
- Resultado por teste confiável mesmo com código hostil ou travado, sem mudar o meupia-core.
- Uma única fonte de verdade para pontos, desbloqueio e placar (vivo e congelado), gravada só com operações atômicas de inserção.
- Funções puras e testáveis para pontuação, melhor submissão, ordem do placar e contagem de caracteres.

**Non-Goals:**
- Impedir fraudes elaboradas via Python injetado (por exemplo, inspecionar frames para achar o nonce). Isso continua sendo tratado pelo sorteio de explicação e pelo log do admin.
- Migrar dados de ensaio gravados no formato antigo.
- Mudar o botão Rodar, `src/engine/*`, `src/editor/*` ou `src/ui/*`.

## Decisions

### D1. Isolamento por transformação de AST no executor
O `juiz` passa ao executor, pela entrada padrão, o nonce e `N` (o total de linhas de teste). O executor:
1. faz `ast.parse` do `main.py`, acha `def main()` e confere que os **últimos N comandos** são `Expr(Call(Name))` com nome `esperar_*`. Se não forem, devolve um relatório de "montagem inválida", que o juiz transforma em `erro_compilacao` com a mensagem amigável de hoje ("O código não conversa com os testes…");
2. troca cada teste `k` por `_arena_teste(k, lambda: <chamada original>)`;
3. move os comandos do `inicio` do aluno (entre o `global` e os testes) para uma função aninhada `_arena_inicio()`, com o mesmo `global`, e chama `_arena_teste(-1, _arena_inicio)`;
4. compila com `ast.unparse`/`compile` e faz `exec` como hoje.

`_arena_teste(k, fn)` define `plugin_testes.ATUAL = k`, arma `signal.setitimer(ITIMER_REAL, 1.0)` com um handler que levanta `_TempoDoTeste(BaseException)`, chama `fn()` e captura `BaseException`, inclusive `SystemExit`. No `finally`, desarma o timer e `ATUAL` volta a `None`. Em exceção ou tempo esgotado, o resultado do teste `k` é `False`. Para `k ≥ 0`, escreve uma linha `nonce + {"i": k, "ok": bool, "ms": int, "falha": null|"excecao"|"tempo"}` no stdout real, com flush. No fim, escreve `nonce + {"fim": true}`.

*Alternativas:* (a) pós-processar o texto do `main.py` com regex, o que é frágil com expressões de várias linhas e mais difícil de validar; (b) um processo por teste, que custaria 20× o tempo de inicialização e de import; (c) compilar cada teste num programa separado, que custaria 20 compilações. O AST é preciso e roda num só processo.

### D2. Shim: resultado indexado pelo teste atual
`plugin_testes` passa a ter `ATUAL = None` e `RESULTADOS = {}`. `_registrar(ok)` grava `RESULTADOS[ATUAL] = ok` só se `ATUAL is not None` e `ATUAL >= 0`. Chamadas no `inicio` ou fora de teste são ignoradas, e dentro de um teste vale a última chamada. Como os argumentos são avaliados antes, a última chamada é sempre a da linha de teste. Cada `esperar_*` envolve a comparação em `try/except Exception`, que vira `False`. `esperar_verdadeiro`/`falso` continuam usando `bool(...)`/`not ...`, como o plugin do Lab. O executor lê `RESULTADOS[k]` depois de cada teste. Se a chave não existir, o resultado é `False`.

### D3. Relatório incremental e limite de tempo total
O juiz usa `TEMPO_EXECUCAO = min(15, 2 + N)` e `RLIMIT_CPU = TEMPO_EXECUCAO + 1`. O resultado vem das linhas do stdout com o nonce: do `CompletedProcess` ou, em `TimeoutExpired`, de `exc.stdout`, decodificado de bytes com `errors="replace"`. Testes sem linha contam como reprovados. Sem nenhuma linha e sem compilação com erro, o status é `erro_execucao`. O nonce é lido do stdin antes do `exec` e fica numa variável local do executor, como hoje.

### D4. Interface do juiz
`juiz.julgar(fonte, exemplos, extras, detalhes=False)` monta `exemplos + "\n" + extras`. O teste `k` pertence a `exemplos` se `k < N_exemplos`. O retorno:
```
{"status": "aceito"|"reprovado_exemplos"|"erro_compilacao"|"erro_execucao",
 "exemplos": {"aprovados": a, "total": t}, "extras": {"aprovados": a, "total": t},
 "completo": bool, "caracteres": int, "mensagem"?: str, "linha"?: int,
 "falhaExemplo"?: "tempo"|"excecao"}
```
Com `detalhes=True` (só nos scripts e nos testes), o retorno inclui `testes: [{ok, ms, falha}]`. A API **nunca** usa esse modo. `falhaExemplo` só olha os exemplos, que são públicos.

### D5. Caracteres significativos
É uma função pura, `juiz.caracteres_significativos(fonte)`, que percorre o código linha a linha com as mesmas regras do lexer (ver Context): fora de texto, `//` termina a linha e `isspace()` é ignorado. Um texto vai de `"` até a `"` não escapada, e um texto sem fechamento conta até o fim da linha. A contagem usa o código original do aluno, antes de `montar()`.

*Alternativa:* contar os tokens do lexer do core. Foi descartada porque exigiria compilar antes, falharia em código inválido e não mede o "tamanho" que o aluno vê.

### D6. Fonte de verdade: lista de aceitas por equipe
Novas chaves em `store.py`:
- `k_aceitas(eid)`: lista de JSON compactos, a mais recente primeiro, com `{"t", "codigo", "pontos", "completo", "caracteres"}` (a equipe está na chave). A gravação é um `LPUSH` atômico, sem leitura e escrita;
- `k_tentativas(eid)` e `k_ultima(eid)` não mudam;
- `k_log()` ganha `exemplos`, `extras`, `pontos`, `completo` e `caracteres` (e continua com `fonte` e `participantes`, só para o admin);
- `k_resolvidos(eid)` deixa de ser usada.

O painel, a missão e a submissão de uma equipe leem só a lista dela, com um `LRANGE`. O placar lê as listas de todas as equipes, com um `LRANGE` por equipe (cerca de 8). O volume estimado é de 8 equipes × 9 módulos × cerca de 10 aceitas, o que dá menos de 1.000 registros e menos de 100 KB no total.

*Alternativas:* (a) um hash `melhor` atualizado a cada submissão, que exige ler, modificar e gravar (com risco de corrida entre duas abas) e não serve para o freeze; (b) uma lista global única, em que o painel de cada equipe leria os dados de todas. A lista por equipe resolve o freeze, não tem corrida e mantém leituras pequenas.

### D7. Regras puras em `arena.py`
- `pontos_submissao(desafio, extras_aprovados, extras_total, cfg)`: usa o modo `proporcional` (`floor` com aritmética inteira, `pontos * a // t`) ou `completo`. Se `t == 0`, a submissão é completa e vale todos os pontos;
- `melhor(a, b)`: o critério é `(-pontos, caracteres, t)`;
- `melhores(aceitas, ate=None)`: devolve `{codigo: registro}`, ignorando `t > ate`;
- `tempo_ultima_melhoria(aceitas, ate=None)`: percorre as aceitas em ordem crescente de `t`, mantendo as melhores por módulo, e guarda o `t` da última vez em que a soma de pontos **aumentou**;
- `contagem_desbloqueio(melhores, todos, cfg)`: conta por nível os módulos com registro (`aceito`) ou só os completos (`completo`). `nivel_liberado`/`falta_para_liberar` passam a receber essa contagem;
- `placar(equipes, aceitas_por_equipe, todos, cfg, ate=None)`: devolve linhas com `pontos`, `completos`, `caracteres` (soma só dos completos), `ultimaMelhoria`, `modulos: {Bronze: ["completo"|"parcial"|null, …]}` na ordem dos códigos, e `posicao`. A ordem usa a chave `(-pontos, -completos, caracteres, ultimaMelhoria or inf, nome)`.

`config()` valida `pontuacao.modo ∈ {proporcional, completo}` e `desbloqueioConta ∈ {aceito, completo}`. Os padrões são `proporcional` e `aceito`. Um valor desconhecido levanta erro e falha cedo (e nos testes).

### D8. Fluxo de `servico.submeter`
1. Janela, código vazio, participantes, nível liberado (com as aceitas da equipe) e cooldown, como hoje. O ramo `ja_resolvido` sai.
2. `HINCRBY` tentativas e `HSET` última, antes de julgar (como hoje).
3. `juiz.julgar(fonte, d["testesPublicos"], d["testesExtras"])`.
4. Se `aceito`: calcula os pontos e faz `LPUSH` em `k_aceitas(eid)`.
5. `LPUSH` no log do admin.
6. A resposta traz o veredito, `pontos` e `caracteres` desta submissão, `melhor` (`{pontos, completo, caracteres}`, calculado com as aceitas lidas no passo 1 mais a nova), `pontosModulo`, `tentativa` e `espera`.

### D9. Geração da bateria extra
`scripts/gerar_testes_extras.py` tem um registro `{COD: (referencia, gerador)}`:
- `referencia` é a solução em Python (por exemplo, `mascarar_token`, `reduzir_rota`), escrita a partir do enunciado;
- `gerador(rng)` devolve cerca de 15 entradas, mistura de tamanho máximo, casos degenerados e aleatórios, com `random.Random(semente_por_desafio)`.

O script lê `arena/extras_base/<COD>.txt` (as linhas dos antigos `testesOcultos`). Antes de gerar, ele **confere que a referência reproduz** os valores esperados das linhas base e dos `testesPublicos`, interpretando os literais Portugol de volta para Python. Isso valida a referência contra os testes que já foram revisados. Um serializador Python → Portugol (texto, inteiro, booleano, lista aninhada) escreve as linhas `esperar_igual(f(args), esperado, "extra k")`, e as funções booleanas (B03) usam `esperar_verdadeiro`/`esperar_falso`. O serializador **recusa** textos com `"` ou `\`. O JSON é regravado com `indent=2` e `ensure_ascii=False`, mudando só `testesExtras`, para manter diffs pequenos.

### D10. Validação
`scripts/validar_desafios.py` usa `julgar(..., detalhes=True)` e confere:
- gabarito `aceito`, `completo` e `max(ms) ≤ 500` (metade do limite de 1 s);
- código inicial não completo;
- `15 ≤ total de extras ≤ 25`;
- ausência de `testesOcultos`.

Ele imprime uma linha por desafio: `OK B01 gabarito=aceito 3/3 20/20 max=12ms · inicial=reprovado_exemplos 0/3 …`.

### D11. Interface
- `submissao.js`: novo mapa de mensagens (ver spec `arena-interface`). O status da missão mostra `Melhor: p/P pts` com o selo ✅ quando completo. O botão não trava mais em "Recuperado". `desafio.melhor` é atualizado com a resposta.
- `painel.js`: o card mostra `p/P pts` com ✅ e o estado `resolvido` vira `completo`/`parcial` (com classes CSS novas em `arena.css`).
- `placar.js` e `placar.html`: os símbolos ●/◐/○ vêm de `l.modulos[nivel]`, e entram as colunas Completos e Caracteres. O log do admin ganha as colunas Exemplos, Extras, Pts e Car.
- `ide.html`: o texto do aviso do modal muda.
- `missoes`/`missao` passam a devolver `melhor` (ou `null`) por módulo e `pontos` da equipe. O campo `resolvido` é substituído por `completo`.

### D12. Tempo da função na Vercel
`vercel.json`: `maxDuration` 20 → 30 (compilação ≤ 10 s + execução ≤ 15 s + Redis). O plano atual permite.

## Risks / Trade-offs

- [Um laço em código C (por exemplo, `10**10**8`) não é interrompido pelo `SIGALRM` até a operação terminar] → O limite total do processo e o `RLIMIT_CPU` matam o processo, e os testes já concluídos valem (D3). Só os testes restantes são perdidos.
- [Python injetado pode desarmar o timer ou capturar `_TempoDoTeste`] → O limite total continua valendo, e o caso fica no mesmo nível de risco das fraudes elaboradas de hoje: sorteio de explicação e log com o código-fonte.
- [Com `desbloqueioConta = "aceito"`, decorar os 3 exemplos (devolver valores fixos) libera o próximo nível com 0 pts] → É uma escolha da organização para ninguém travar. O log do admin mostra extras 0/N, e é possível trocar para `completo` em `config.json` sem deploy de código. Se preferirem um meio-termo (exigir pelo menos 1 extra), é uma mudança de uma linha em `contagem_desbloqueio`.
- [O desempate por caracteres incentiva código "golfado" (nomes de uma letra)] → É só o 3º critério e vale apenas entre equipes empatadas em pontos e completos. A regra está explicada nos enunciados.
- [Mais leituras no Upstash: o placar faz cerca de 8 `LRANGE` a cada 15 s] → Cerca de 5 mil comandos no evento, bem abaixo do limite do plano gratuito. Se precisar, dá para usar o endpoint de pipeline do Upstash depois.
- [Uma bateria maior aumenta o tempo do pior caso para cerca de 15 s por submissão travada] → O cooldown limita a frequência, e o `maxDuration` sobe para 30 s.
- [Uma referência em Python pode divergir do enunciado] → O script confere a referência contra os testes públicos e os casos de borda revisados antes de gerar, e o `validar` confere o gabarito Portugol contra a bateria final. São duas implementações independentes concordando.

## Migration Plan

1. Implementar atrás dos testes (`npm test`, `npm run validar`) em um branch.
2. No ensaio, usar um `ARENA_PREFIXO` novo (por exemplo, `ensaio2`), porque as chaves `resolvidos` antigas são ignoradas.
3. Fazer o piloto go/no-go (11/10) já com o modelo novo. Em caso de no-go, a decisão pode ser `pontuacao.modo = "completo"` + `desbloqueioConta = "completo"`, que se aproxima do comportamento antigo (tudo ou nada) sem rollback de código.
4. Rollback total: reverter o merge e trocar o `ARENA_PREFIXO`. Os dados do formato novo não são lidos pelo código antigo.
