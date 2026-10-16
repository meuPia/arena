## 1. Lógica das abas e do menu (sem DOM real)

- [x] 1.1 Criar `src/arena/ide-mobile.js` com funções puras/injetáveis: `normalizarAba(valor)` (inválido → `"codigo"`), `aplicarAba(doc, aba)` (grava `body.dataset.aba` e `aria-selected`/`tabIndex` nas abas; a visibilidade dos painéis fica só no CSS do celular, para não afetar o desktop), `deveIrParaTerminal(ehCelular)` e o controle do menu "Mais" (`abrir`/`fechar`, `aria-expanded`). O `matchMedia`, o `document` e o `requestAnimationFrame` entram por parâmetro. Verificar com `npm run test:js` sem erro de import.
- [x] 1.2 Criar `src/arena/ide-mobile.test.js` (no estilo de `tema.test.js`, com objetos falsos) cobrindo: aba inválida cai em Código; só uma aba com `aria-selected="true"`; Rodar troca para Terminal só quando é celular; menu fecha com Esc, com toque fora e depois de escolher uma opção; troca para Terminal dispara um `resize` depois do quadro. Verificar com `npm run test:js` passando.

## 2. Marcação da IDE (`ide.html`, só acréscimos)

- [x] 2.1 Envolver `#run-btn` e `#submit-btn` em `<div class="arena-acoes-principais">` (D4), adicionar `#mais-btn` (ícone `ellipsis`, `aria-label="Mais ações"`, `aria-haspopup="menu"`, `aria-expanded="false"`), os botões móveis `#undo-btn-m`/`#redo-btn-m` com `aria-label`, os rótulos do menu (feitos no CSS com `::after { content: attr(aria-label) }`, porque o `tema.js` reescreve o conteúdo do botão de tema; sem `<span>` extra) e `aria-label="Voltar às missões"` no `#voltar-painel`. Verificar no desktop (1280 px) que a página está igual à de antes (captura lado a lado) e que `npm run build` passa.
- [x] 2.2 Adicionar a barra de abas `<div class="arena-abas-mobile" role="tablist">` com Código, Missão e Terminal (`role="tab"`, `aria-controls` para `#editor-pane`, `#test-pane`, `#terminal-pane`), a classe `arena-so-desktop` no grupo "Layout do painel auxiliar" e `interactive-widget=resizes-content` na meta `viewport`. Importar `ide-mobile.js` no `ide.html`. Verificar com `read_page` que as abas aparecem na árvore de acessibilidade no celular e não no desktop.

## 3. Estilo móvel (`src/arena/arena.css`, só tokens `--a-*`)

- [x] 3.1 Estilos-base fora do media query: `.arena-acoes-principais { display: contents }`; `#mais-btn`, `.arena-abas-mobile`, `#undo-btn-m`, `#redo-btn-m` ocultos no desktop. Verificar a 1280 px que nada mudou (cenário "Desktop inalterado").
- [x] 3.2 Bloco `@media (max-width: 768px)` do cabeçalho compacto (D6): marca só com ícone, Missões só com ícone, `#missao-topo` em uma linha com módulo truncado, `.arena-missao-sub` oculto, relógio à direita. Verificar a 360 px que cabeçalho ocupa no máximo duas linhas e o cronômetro aparece.
- [x] 3.3 Layout em abas (D1): `body.arena-ide` com `height: var(--a-vh, 100dvh)` em grade (cabeçalho, abas, área, barra de ação); `.gutter` oculto; painéis em `100% !important`; só o painel da aba ativa visível; canvas do Visualizador 2D com `max-width: 100%`. Verificar a 360 px que não há rolagem horizontal (`document.documentElement.scrollWidth <= innerWidth` via `javascript_tool`).
- [x] 3.4 Barra de ação fixa (D4) com Rodar e Submeter em duas colunas, alvos ≥ 44 px e `env(safe-area-inset-bottom)`; menu "Mais" suspenso em lista com rótulos visíveis (D5); editor com `font-size: max(16px, var(--editor-font-size, 14px))` (D8). Verificar com `javascript_tool` a altura dos botões (≥ 44) e o `font-size` calculado do `.cm-content` (16px com a configuração em 14).
- [x] 3.5 Modais em tela cheia no celular (D9), incluindo `.arena-modal-ajuda`, e linha `arena-so-desktop` oculta. Verificar abrindo Configurações, Ajuda e Submeter a 360 px: ocupam a tela, fechar visível, opção de layout ausente.

## 4. Comportamento no navegador

- [x] 4.1 Ligar o `ide-mobile.js` ao DOM real: cliques nas abas, `#mais-btn`, proxies de desfazer/refazer, Rodar → Terminal, `resize` sintético depois de mostrar o Terminal, `visualViewport` → `--a-vh`, e o marcador na aba Missão quando `#test-results` muda fora da vista (`MutationObserver`). Verificar a 360 px: Rodar mostra o Terminal com a saída na largura da tela; a aba Missão traz os resultados no fim (cenário "Rodar mostra o terminal").
- [x] 4.2 Verificar a preservação do trabalho: editar, trocar para Missão e voltar mantém código, cursor e desfazer; girar para paisagem com o Terminal ativo reajusta sem perder a saída; passar de 360 para 1280 px volta os divisores e o layout salvo. Registrar capturas. (Verificado a 740×360; o 844×390 depende de `pointer: coarse`, que o navegador do app não emula nessa largura: fica para o aparelho real no ensaio de 16/10.)

## 5. Verificação geral e documentação

- [x] 5.1 Rodar `npm test` (JS + pytest) e `npm run build` sem falhas.
- [x] 5.2 Com `npm run local` e o navegador do app (`resize_window` 360×800, 390×844, 844×390 e 1280×800, temas escuro e claro): percorrer todos os cenários de "IDE no celular" da spec, conferir contraste dos rótulos novos (≥ 4,5:1) e anexar as capturas ao resumo.
- [x] 5.3 Atualizar o `CLAUDE.md` (seção Arquitetura → visual: layout móvel da IDE em `ide-mobile.js` + bloco `@media` do `arena.css`) e acrescentar às pendências do ensaio de 16/10 conferir a IDE num Android e num iPhone (teclado virtual sobre a barra de ação).
