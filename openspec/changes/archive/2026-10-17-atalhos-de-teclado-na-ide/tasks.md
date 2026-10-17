## 1. Reconhecimento do atalho (sem DOM)

- [x] 1.1 Criar `src/arena/atalhos.js` com `atalhoDoEvento(ev)` e `podeAgir(...)` (D2), `ehMac(navegador)` e `textoAtalho(acao, mac)` (D3). Cobrir em `src/arena/atalhos.test.js`:
  - `Ctrl+Enter` e `⌘+Enter` → `"rodar"`;
  - `Ctrl+Shift+Enter` e `⌘+Shift+Enter` → `"submeter"`;
  - Enter sozinho, `Shift+Enter`, `Ctrl+Alt+Enter`, `Ctrl+A` → `null`;
  - `podeAgir` falso com botão ausente ou `disabled`, com modal aberto e com `repeat`;
  - `ehMac` com `userAgentData.platform` "macOS", com `platform` "MacIntel", e falso com "Win32" e "Linux x86_64";
  - `textoAtalho` nas duas plataformas.

  Verificar com `npm run test:js` passando.

## 2. Ligar os atalhos na IDE

- [x] 2.1 Implementar `setupAtalhos({ doc, janela, navegador })` em `src/arena/atalhos.js` (D1, D3): listener de `keydown` na fase de captura, que sempre consome as duas combinações e só chama `click()` quando `podeAgir`. Ele também define o `title` e o `aria-keyshortcuts` dos dois botões. Cobrir em `atalhos.test.js` com documento e janela falsos (como `ide-mobile.test.js`):
  - o evento reconhecido chama `preventDefault` e `stopPropagation`, mesmo com o botão desabilitado;
  - `click()` só com o botão habilitado e sem modal aberto;
  - os `title` ficam com `Ctrl` e, com `navegador` de Mac, com `⌘`.

  Verificar com `npm run test:js`.
- [x] 2.2 Em `ide.html`, pôr em `#run-btn` `title="Rodar os testes de exemplo (Ctrl+Enter)"` e `aria-keyshortcuts="Control+Enter Meta+Enter"`, e em `#submit-btn` o `title` com ` (Ctrl+Shift+Enter)` no fim e `aria-keyshortcuts="Control+Shift+Enter Meta+Shift+Enter"`. Em `src/main.js`, chamar `setupAtalhos` antes de `setupSubmissao` (D3). Conferir com `git diff` que `src/editor/*`, `src/engine/*` e `src/ui/*` não mudaram, e com `npm run build` sem erro.

## 3. Modal de Submeter pelo teclado

- [x] 3.1 Em `src/arena/submissao.js` (D4): ao abrir `#submit-modal`, dar foco ao primeiro `input` de `#participantes-lista`; criar `fecharModal()`, que põe `hidden` e chama `view.focus()`, usada pelo `x` e por um `keydown` de `Esc` no `document` (só com o modal aberto). Verificar com `npm run build` e na tarefa 4.1.

## 4. Verificação na IDE

- [x] 4.1 Com o servidor local (`npm run local` ou a configuração `arena-e2e`), entrar com `TROQUE-ESTE-CODIGO-1`, abrir B91 e conferir no navegador (preview):
  - `Ctrl+Enter` com o foco no editor roda os exemplos, e o código e o Desfazer continuam iguais (nenhuma linha inserida);
  - `Ctrl+Enter` com o foco no terminal roda;
  - `Ctrl+Enter` antes de o motor carregar não faz nada e não insere linha;
  - `Ctrl+Shift+Enter` abre o modal de Submeter com o foco no primeiro participante; Espaço marca, Tab até "Enviar para o juiz" e Enter envia, e o veredito aparece;
  - `Esc` fecha o modal de Submeter sem enviar, com o cursor de volta ao editor;
  - durante o cooldown, `Ctrl+Shift+Enter` não abre o modal;
  - com a Ajuda aberta, `Ctrl+Enter` não roda nada;
  - os `title` dos dois botões mostram os atalhos;
  - no celular (`resize_window` mobile), um `Ctrl+Enter` vindo de teclado físico leva à aba Terminal, como o toque em Rodar.

  Registrar com captura de tela da dica do botão Rodar e do modal aberto pelo atalho.
- [x] 4.2 Rodar `npm test` completo e confirmar que passa.

## 5. Documentação

- [x] 5.1 No `docs/cartao-dialeto.md`, seção "Na Arena", acrescentar a frase dos atalhos (D5). No `CLAUDE.md`, na linha de `ide.html` da Arquitetura, citar `src/arena/atalhos.js` (Ctrl+Enter / Ctrl+Shift+Enter, captura antes do CodeMirror). Rodar `npm test` (inclui `ajuda.test.js` e `test_cartao_dialeto.py`) e conferir que a busca por "atalho" na Ajuda acha a frase nova.
- [x] 5.2 Acrescentar ao roadmap do `CLAUDE.md`, no item do ensaio de 16/10 (ou no próximo ensaio), conferir `Ctrl+Shift+Enter` nos navegadores dos computadores do laboratório.
