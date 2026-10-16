## Context

A IDE é montada pelo `ide.html` sobre o CSS herdado do Lab (`src/style.css`: `body` em `100vh`, cabeçalho em
flex) e pela camada da Arena em `src/arena/arena.css` (bloco "IDE"). Os painéis são posicionados pelo
`src/ui/layout.js` (Lab), que monta duas instâncias do Split.js: `#editor-pane | #side-pane` e, dentro do lado,
`#test-pane / #terminal-pane`. O Split.js grava tamanhos inline (`width/height: calc(55% - 3px)`) e insere
elementos `.gutter`. O terminal (xterm) só se ajusta quando `fitAddon.fit()` roda, e o `main.js` já chama isso
em todo `resize` da janela. A faixa da missão (`#missao-topo`) é preenchida por `src/arena/submissao.js`.
Hoje não há nenhum `@media` para a IDE; o resultado no celular é o da captura do usuário (ver proposal.md).

Restrição do projeto: mexer o mínimo possível nos arquivos do Lab (`src/ui/*`, `src/style.css`, `src/main.js`) e
usar só tokens `--a-*` no `arena.css`.

## Goals / Non-Goals

**Goals:**
- Layout móvel da IDE só com CSS + um módulo pequeno da Arena, sem tocar nos arquivos herdados do Lab.
- Desktop pixel a pixel igual ao atual.
- Funcionar em Chrome/Brave Android e Safari iOS recentes, retrato e paisagem.

**Non-Goals:**
- Placar e admin no celular (o placar é para o telão; o admin já tem regras responsivas próprias).
- Teclado auxiliar de símbolos (`←`, `[`, `]`) ou atalhos de toque para o Portugol.
- Mudar o editor (extensões do CodeMirror), o terminal ou o motor.

## Decisions

### 1. Abas por atributo no `<body>` e CSS, sem desmontar o Split.js
Um módulo novo `src/arena/ide-mobile.js` mantém `document.body.dataset.aba = "codigo" | "missao" | "terminal"`.
No `@media (max-width: 768px), (max-height: 500px) and (pointer: coarse)` (a mesma consulta fica em
`CONSULTA_CELULAR` no JS), o CSS:
- esconde `.gutter`;
- força `#editor-pane`, `#side-pane`, `#test-pane`, `#terminal-pane` a `width/height: 100% !important`
  (sobrepõe os tamanhos inline do Split.js) e mostra só o painel da aba ativa (`[data-aba=missao] #terminal-pane
  { display: none }` etc.).

**Por quê:** zero mudança no `layout.js`; ao passar de 768 px (girar um tablet, redimensionar) o media query deixa
de valer e os tamanhos inline do Split.js voltam a mandar, sem reconstruir nada. O editor e o terminal nunca são
destruídos, então código, histórico e saída ficam intactos.
**Alternativa descartada:** guarda no `applySettings()` do `layout.js` para não criar o Split no celular — exige
reagir à troca de breakpoint e reconstruir o Split, e altera arquivo do Lab.

### 2. Terminal reajustado com um `resize` sintético
Ao mostrar a aba Terminal (e no `orientationchange`/`resize` do `visualViewport`), o `ide-mobile.js` espera um
quadro (`requestAnimationFrame`) e dispara `window.dispatchEvent(new Event("resize"))`; o listener que já existe
no `main.js` chama `fitAddon.fit()`. `fit()` num elemento oculto mede 0 — por isso só depois de exibido.

### 3. Rodar → aba Terminal
O `ide-mobile.js` adiciona um listener próprio de `click` em `#run-btn` que, se `matchMedia("(max-width: 768px)")`
casar, ativa a aba Terminal antes da execução. Os resultados de teste continuam onde o Lab os escreve
(`#test-results`, no fim da aba Missão); a aba Missão ganha um marcador (ponto) quando chegam resultados novos
sem estar visível — feito observando `#test-results` com `MutationObserver`, sem mexer em `instructions.js`.

### 4. Barra de ação no rodapé com um invólucro `display: contents`
No `ide.html`, `#run-btn` e `#submit-btn` passam a ficar dentro de `<div class="arena-acoes-principais">`. No
desktop o invólucro é `display: contents` (layout idêntico ao atual); no celular vira barra `position: fixed;
bottom: 0` em grade de duas colunas, com `padding-bottom: env(safe-area-inset-bottom)`. Os ids não mudam, então
`submissao.js` e `main.js` continuam funcionando.

### 5. Menu "Mais" reaproveitando os grupos de ação existentes
Um botão `#mais-btn` (ícone `ellipsis`, `aria-haspopup="menu"`, `aria-expanded`) é adicionado ao `.actions`,
oculto no desktop. No celular os dois `.action-group` viram um painel suspenso (`.arena-mais.aberto`) em lista,
com rótulos visíveis: cada botão ganha um `<span class="arena-rotulo-menu">` (oculto no desktop) com o mesmo texto
do `aria-label`. Desfazer/refazer ficam a um toque por dois botões próprios do cabeçalho móvel
(`#undo-btn-m`, `#redo-btn-m`) que chamam `.click()` nos originais — assim o `toolbar.js` do Lab não muda.
O menu fecha com Esc, toque fora e depois de qualquer escolha.
**Alternativa descartada:** mover os botões no DOM via JS por breakpoint — frágil com os listeners e com o
`lucide.createIcons()`.

### 6. Cabeçalho compacto só com CSS
No celular: some o texto da marca (fica o ícone), o link Missões mostra só o ícone (o `title` vira `aria-label`
no HTML para manter o nome acessível), `.arena-missao-sub` some, `#missao-topo` vai para uma segunda linha em
`nowrap` com o módulo em `text-overflow: ellipsis` e o relógio com `margin-left: auto`.

### 7. Altura da tela e teclado
`body.arena-ide { height: 100dvh }` no celular (o `100vh` do Lab inclui a barra do navegador). O `viewport` ganha
`interactive-widget=resizes-content` para o Chrome Android encolher o layout quando o teclado abre (a barra de
ação fica acima do teclado). No Safari iOS, que ignora essa opção, o `ide-mobile.js` grava a altura do
`visualViewport` em `--a-vh` e o CSS usa `height: var(--a-vh, 100dvh)`.

### 8. Fonte mínima do editor
`body.arena-ide .cm-editor { font-size: max(16px, var(--editor-font-size, 14px)) }` no celular. O iOS amplia a
página ao focar campos com menos de 16 px; com o mínimo, isso não acontece e o tamanho escolhido nas
configurações continua valendo acima de 16 px.

### 9. Modais em tela cheia
No celular `.modal-content` (inclusive `.arena-modal-ajuda`) vira `width: 100%; height: 100dvh; max-width: none`,
com o corpo rolando e o cabeçalho fixo. A linha de layout das configurações recebe a classe
`arena-so-desktop` (oculta no celular).

### 10. Testes
`src/arena/ide-mobile.test.js` (node --test, como `tema.test.js`) cobre a lógica pura: troca de aba (valor
inválido cai em "codigo"), `aria-selected`/`hidden` coerentes, Rodar só troca de aba no celular, fechar o menu
com Esc/toque fora. A verificação visual é feita no navegador do app com `resize_window` (360×800, 390×844,
paisagem 844×390 e 1280×800), nos dois temas.

## Risks / Trade-offs

- [`!important` contra os tamanhos inline do Split.js] → Restrito ao media query móvel e a quatro seletores
  por id; desktop não é afetado.
- [Safari iOS e o teclado virtual cobrindo a barra de ação] → `--a-vh` pelo `visualViewport`; se ainda assim
  cobrir, a barra é escondida enquanto o editor tem foco e o teclado está aberto (decidido no ensaio).
- [Breakpoint de 768 px pega tablets em retrato] → Aceitável: tablet em retrato também fica melhor em abas;
  em paisagem (≥ 1024 px) volta o layout de desktop.
- [Celular deitado tem 740–932 px de largura e cairia no desktop com ~390 px de altura] → A consulta também
  casa com altura ≤ 500 px e `pointer: coarse`; uma janela baixa de computador (mouse) continua no desktop.
- [Merge do `upstream` no `ide.html`] → Mudanças no HTML são aditivas (invólucro, botões novos, spans de
  rótulo); conflitos, se houver, são pequenos.
- [Canvas do Visualizador 2D com 400 px fixos] → `max-width: 100%; height: auto` no celular.

## Migration Plan

Só front-end estático: entra com o deploy normal na Vercel. Rollback = reverter o commit. Conferir no ensaio de
16/10 num celular Android e num iPhone.
