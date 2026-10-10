## Why

Hoje uma submissão da Code Arena só pontua quando passa em 100% dos testes (públicos e ocultos). Uma equipe que resolve quase tudo recebe zero, e uma equipe que já resolveu não tem motivo para melhorar o código. Com equipes multisseriadas (2º, 4º e 6º semestres), isso desanima quem está começando e não recompensa quem escreve melhor. O modelo do Codewars resolve as duas coisas: testes de exemplo como requisito para enviar, uma bateria extra maior que dá pontos proporcionais e desempate pelo código mais curto. A mudança precisa estar pronta antes do piloto go/no-go (11/10) e do evento de 21/10/2026.

## What Changes

- **BREAKING** — Duas baterias por desafio: **testes de exemplo** (os atuais `testesPublicos`, que o botão Rodar do Lab continua executando) e **testes extras** (só no servidor). Em `arena/desafios/*.json`, o campo `testesOcultos` passa a se chamar `testesExtras` e a bateria cresce para cerca de 20 testes: os casos de borda atuais mais casos grandes e aleatórios.
- **BREAKING** — Novo veredito do juiz. Uma submissão é **aceita** quando passa em 100% dos exemplos. Senão, o status é `reprovado_exemplos`: não pontua, mas conta como tentativa. Os status `validado`, `nao_validado`, `ja_resolvido` e `tempo_esgotado` deixam de existir.
- Pontuação proporcional por módulo: `pontos = piso(pontosDoModulo × extrasAprovados / totalExtras)`. O módulo fica **completo** quando passa em 100% dos extras. Vale a **melhor** submissão da equipe: mais pontos e, no empate, menos caracteres. Novas submissões continuam liberadas depois de completar (sujeitas ao cooldown, que não muda). O modo fica em `arena/config.json` (`"pontuacao": {"modo": "proporcional"}`).
- Tamanho do código em **caracteres significativos**: não contam comentários `//` nem espaços, tabs e quebras de linha fora de textos entre aspas. O valor é guardado em cada submissão e na melhor de cada módulo.
- Nova ordem do placar: pontos ↓, módulos completos ↓, soma dos caracteres das melhores soluções completas ↑, horário da última melhoria de pontuação ↑, nome ↑.
- Desbloqueio de níveis configurável (`"desbloqueioConta": "aceito" | "completo"`). O padrão é `aceito`, que conta os módulos com pelo menos uma submissão aceita (inclusive parcial), para nenhuma equipe travar.
- O placar passa a ser calculado a partir de uma lista compacta de submissões aceitas, sem código-fonte. Assim o placar congelado mostra a melhor submissão até o freeze, mesmo que a equipe melhore depois. O log completo com o código-fonte continua separado e só para o admin.
- Juiz com **testes isolados**. Cada teste roda com alarme próprio, e uma exceção, um laço infinito ou uma comparação que falha num teste não derruba os seguintes. Os resultados saem por teste, assinados com o nonce, e sobrevivem ao estouro do tempo total do processo.
- Novo `scripts/gerar_testes_extras.py`: gera as baterias de forma determinística, com uma implementação de referência em Python para cada desafio e os casos de borda em `arena/extras_base/<COD>.txt`. O `validar_desafios.py` passa a conferir "gabarito aceito e completo dentro do tempo por teste" e "código inicial não completo".
- Interface: veredito no estilo do Codewars na IDE, melhor pontuação e selo de completo no painel, placar do telão com ●/◐/○ e colunas Pontos, Completos e Caracteres, log do admin com exemplos, extras, pontos e caracteres. Os enunciados explicam a regra.

## Capabilities

### New Capabilities
- `arena-juiz`: julgamento de uma submissão no servidor. Cobre as duas baterias, o isolamento de cada teste, os limites de tempo, o relatório assinado, a contagem de caracteres significativos e o veredito ("N de M", sem dizer qual extra falhou).
- `arena-pontuacao`: aceitação, pontuação proporcional, melhor submissão por módulo, cooldown, desbloqueio de níveis, ordem do placar e freeze.
- `arena-desafios`: formato dos desafios (`testesPublicos` e `testesExtras`), geração determinística da bateria extra e validação dos gabaritos e dos códigos iniciais.
- `arena-interface`: o que a IDE, o painel, o placar do telão e a visão admin mostram sobre o veredito e a pontuação.

### Modified Capabilities
<!-- Nenhuma. As capabilities existentes (editor-portugol, motor-de-execucao) descrevem o Lab no navegador, e o botão Rodar não muda. -->

## Impact

- **Backend**: `api/_lib/juiz.py`, `api/_lib/executor.py`, `api/_lib/shim/meupia_testes/plugin_testes.py`, `api/_lib/arena.py`, `api/_lib/servico.py` e `api/_lib/store.py` (novas chaves; `resolvidos` sai). O contrato de `POST /api/submeter`, `GET /api/missoes` e `GET /api/placar` muda.
- **Dados**: os 9 `arena/desafios/*.json` (campo renomeado e bateria nova), novo `arena/extras_base/`, `arena/config.json` (`pontuacao` e `desbloqueioConta`) e os enunciados (`descricao`).
- **Scripts**: novo `scripts/gerar_testes_extras.py` e `scripts/validar_desafios.py` reescrito.
- **Frontend**: `src/arena/submissao.js`, `src/arena/painel.js`, `src/arena/placar.js`, `placar.html`, `ide.html` (texto de aviso) e `src/arena/arena.css`. Os arquivos herdados do Lab (`src/engine`, `src/editor`, `src/ui`) não mudam.
- **Infra**: `vercel.json` aumenta `maxDuration` (compilação + execução isolada podem passar dos 20 s atuais). Dados de ensaio gravados no formato antigo ficam incompatíveis: use um `ARENA_PREFIXO` novo.
- **Testes e docs**: `tests/test_arena.py` (reescrito e ampliado), `README.md` e `CLAUDE.md` (seção de pontuação e a regra de ouro com `testesExtras`).
- Sem mudança no `meupia-core` nem nas dependências.
