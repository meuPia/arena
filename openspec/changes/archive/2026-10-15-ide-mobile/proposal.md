## Why

O editor (CodeMirror) já funciona no celular, mas a IDE (`ide.html`) quebra em telas estreitas: o cabeçalho
herdado do Lab empilha marca, missão, oito botões, Rodar e Submeter e ocupa metade da tela; a faixa da missão é
espremida numa coluna ao lado (título e relógio cortados); e o Split.js deixa editor, enunciado e terminal
lado a lado ou com divisores de arrastar que não servem para o dedo. A spec `arena-visual` já exige páginas
utilizáveis a partir de 360 px, mas hoje só o painel de missões cumpre isso. Como as equipes e a banca abrem a
Arena no celular (conferir enunciado, fazer pequenos ajustes, ensaiar) antes do evento de 21/10, a IDE precisa de
uma versão móvel funcional.

## What Changes

- Novo layout da IDE para telas estreitas (≤ 768 px de largura): uma coluna, altura da tela visível (`dvh`),
  sem rolagem horizontal.
- Cabeçalho compacto: marca reduzida ao ícone, botão Missões só com ícone (nome acessível mantido), faixa da
  missão numa linha (selo, módulo truncado, melhor pontuação, relógio).
- Ferramentas secundárias (abrir, salvar, desfazer, refazer, limpar, tema, ajuda, configurações) agrupadas num
  menu "Mais" (⋯) no cabeçalho; desfazer/refazer continuam a um toque.
- Painéis em abas (**Código**, **Missão**, **Terminal**) no lugar dos divisores arrastáveis; só o painel ativo
  aparece e ocupa a área toda. Ao Rodar, a IDE mostra o resultado (aba Terminal); os testes de exemplo seguem
  no fim da aba Missão.
- Barra de ação fixa no rodapé com **Rodar** e **Submeter** (alvos ≥ 44 px), sempre visíveis.
- Editor no celular com fonte de pelo menos 16 px (evita o zoom automático do navegador ao focar) e o
  terminal reajustado ao trocar de aba ou girar o aparelho.
- Modais (submeter, veredito, ajuda, configurações) em tela cheia no celular; a opção "Layout do painel
  auxiliar" fica oculta (não se aplica às abas).
- O layout de desktop (≥ 769 px) não muda. Nenhuma regra, API ou texto de veredito muda.

## Capabilities

### New Capabilities
<!-- Nenhuma. -->

### Modified Capabilities
- `arena-visual`: novo requisito "IDE no celular" (layout em abas, cabeçalho compacto, barra de ação fixa,
  modais em tela cheia, fonte mínima do editor) complementando "Acessibilidade e responsividade", que hoje só
  tem cenário para o painel de missões.

## Impact

- `ide.html`: barra de abas, barra de ação do rodapé, botão/menu "Mais"; `viewport` com
  `interactive-widget=resizes-content`.
- `src/arena/arena.css`: bloco `@media (max-width: 768px)` da IDE, só com tokens `--a-*`.
- Novo `src/arena/ide-mobile.js` (+ teste `ide-mobile.test.js`): troca de abas, menu "Mais", troca automática
  para o Terminal ao Rodar, `resize` para o `fitAddon`.
- Arquivos herdados do Lab (`src/ui/layout.js`, `src/style.css`, `src/main.js`): sem mudança ou mudança mínima
  (no máximo um guarda para não montar o Split.js no celular), para continuar mesclando o `upstream`.
- Sem mudança em API, juiz, banco ou pontuação.
