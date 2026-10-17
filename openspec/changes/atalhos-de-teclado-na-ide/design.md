## Context

Motivação em `proposal.md`; comportamento em `specs/arena-interface/spec.md`. O que existe hoje e define a abordagem:

- **Botões** (`ide.html`): `#run-btn` (sem `title`) e `#submit-btn` (`title` "Envia para o juiz (testes de exemplo + testes extras)") ficam em `.arena-acoes-principais`. No celular, o mesmo par vira a barra do rodapé (CSS), então não há botões duplicados.
- **Estado dos botões**:
  - `#run-btn` nasce `disabled` e é habilitado no fim do `initWasmEngine` (`src/engine/wasm.js`, do Lab). Ele não é desabilitado durante uma execução.
  - `#submit-btn` é controlado por `src/arena/submissao.js`: fica desabilitado no cooldown (com o relógio), durante "Julgando..." e com as submissões fechadas, quando também recebe `title = "Submissões fechadas"`.
- **Cliques**: o handler do Rodar está em `src/main.js` (`iniciarRodada` → `runWasmCode` → `concluirRodada`). O `src/arena/ide-mobile.js` também escuta o clique para ir à aba Terminal no celular. O clique no Submeter só tira o `hidden` de `#submit-modal`.
- **Conflito no editor**: o `basicSetup` do CodeMirror inclui o `defaultKeymap`, em que `Mod-Enter` = `insertBlankLine`. O xterm também trata o `keydown` quando o terminal tem foco.
- **Modais**: os quatro (`#settings-modal`, `#submit-modal`, `#ajuda-modal`, `#veredito-modal`) são `.modal-overlay` e ficam fechados com a classe `hidden`. Ajuda e veredito já fecham com `Esc` (`keydown` no `document`) e devolvem o foco com `view.focus()`. O modal de Submeter não fecha com `Esc` nem move o foco.
- O `CLAUDE.md` pede mexer o mínimo nos arquivos do Lab (`src/editor/*`, `src/engine/*`, `src/ui/*`).

## Goals / Non-Goals

**Goals:**
- Atalhos que fazem exatamente o que o clique faz, incluindo o desvio para o terminal no celular e o fluxo do Rodar da change esperado-obtido-nos-exemplos.
- Nenhuma mudança nos arquivos do Lab nem na configuração do CodeMirror.
- Reconhecimento do atalho numa função pura, testável com `node --test`.

**Non-Goals:**
- Não impedir duas execuções simultâneas do Rodar (o clique duplo já permite hoje). O atalho só ignora a repetição automática da tecla.
- Não criar um sistema genérico de atalhos nem tratar foco preso (focus trap) nos modais.

## Decisions

### D1. `keydown` na fase de captura, na `window`, acionando `click()` do botão
`setupAtalhos({ doc, janela, view })` registra `janela.addEventListener("keydown", tratar, { capture: true })`. Na captura, o listener da `window` roda antes dos handlers do CodeMirror (no `contentDOM`) e do xterm (no `textarea` dele). Quando a combinação é de atalho, ele chama `preventDefault()` e `stopPropagation()` sempre, mesmo que o atalho não aja (requisito: a combinação nunca tem outro efeito). Assim o `insertBlankLine` não roda e o histórico de desfazer não muda. Se o atalho puder agir, ele chama `doc.getElementById("run-btn").click()` ou `("submit-btn").click()`.

O `click()` reaproveita todos os handlers que já existem (o do `main.js`, o do `ide-mobile.js` e o do `submissao.js`), sem duplicar lógica. Um `click()` num `<button disabled>` não dispara `click` no navegador, mas a checagem de `disabled` é feita antes, explicitamente, para ficar clara e testável.

- *Alternativa: um `keymap` do CodeMirror com `Prec.highest`*. Só valeria com o foco no editor, e o requisito pede o atalho também no terminal e no painel.
- *Alternativa: tirar `Mod-Enter` do `defaultKeymap`*. Mexeria na montagem do editor (`basicSetup`), e não resolveria o terminal.

### D2. Função pura `atalhoDoEvento(ev)`
Ela devolve `"rodar"`, `"submeter"` ou `null`:
- `ev.key === "Enter"` (o Enter do teclado numérico também tem `key` `"Enter"`);
- `ev.ctrlKey || ev.metaKey` e `!ev.altKey`;
- com `ev.shiftKey`, `"submeter"`; sem, `"rodar"`.

Ctrl e ⌘ são aceitos em qualquer plataforma. No Windows e no Linux, `metaKey` é a tecla Windows/Super, e Super+Enter não tem uso na IDE. Separar por plataforma só deixaria o código mais difícil de testar.

`podeAgir(acao, { botao, modalAberto, repeticao })` devolve `false` se o botão não existe ou está `disabled`, se algum `.modal-overlay` não tem `hidden`, ou se `ev.repeat`. Uma função separada facilita testar cada condição.

### D3. Dica no `title` e `aria-keyshortcuts`, ajustados à plataforma
`ehMac(navegador)` usa `navigator.userAgentData?.platform` e, sem ele, `navigator.platform`, com `/mac|iphone|ipad/i`. `textoAtalho(acao, mac)` monta `Ctrl+Enter` / `Ctrl+Shift+Enter` ou `⌘+Enter` / `⌘+Shift+Enter`.

Em tempo de execução, `setupAtalhos`:
- define o `title` do Rodar como `Rodar os testes de exemplo (<atalho>)`;
- acrescenta ` (<atalho>)` ao `title` do Submeter;
- define `aria-keyshortcuts` (`Control+Enter Meta+Enter`; `Control+Shift+Enter Meta+Shift+Enter`).

O `ide.html` já recebe os textos com `Ctrl`, para a dica existir mesmo antes do JavaScript.

O `setupAtalhos` roda **antes** do `setupSubmissao` no `main.js`. Assim, com as submissões fechadas, o `title = "Submissões fechadas"` do `submissao.js` continua valendo (requisito).

### D4. Foco e `Esc` no modal de Submeter, dentro do `submissao.js`
Ao abrir o modal (no handler de clique do `#submit-btn`), o `submissao.js` chama `focus()` no primeiro `input` de `#participantes-lista`, que é o primeiro checkbox ou o `#part-livre`. Um `keydown` no `document` fecha o modal com `Esc` quando ele está aberto: põe `hidden` e chama `view.focus()`, no mesmo padrão do veredito e da ajuda. O botão `x` passa a usar a mesma função `fecharModal()`, que também devolve o foco ao editor. Os checkboxes marcados não são tocados.

O fluxo só com teclado (Tab até "Enviar para o juiz" e Enter) já funciona, porque é um `<button>`. Nada muda no envio.

### D5. Cartão do dialeto
Uma frase em "Na Arena": "Atalhos: `Ctrl+Enter` roda e `Ctrl+Shift+Enter` abre o Submeter (no Mac, `⌘`)." O cartão é a fonte da Ajuda da IDE, então a busca por "atalho" passa a achá-la. O `ajuda.test.js` roda contra o cartão real e precisa continuar passando.

## Risks / Trade-offs

- [`Ctrl+Enter` deixa de inserir linha em branco no editor] → é o objetivo. Quem quiser a linha usa End + Enter. Fica registrado.
- [Navegador ou sistema com atalho global em `Ctrl+Shift+Enter`] → nos navegadores comuns (Chrome, Firefox, Edge) a combinação não tem uso na página. A conferência fica para o ensaio no laboratório (tarefa de verificação).
- [Teclado virtual do celular] → não tem Ctrl; os atalhos só valem com teclado físico (tablet com teclado). Nada muda no toque.
- [Foco no primeiro participante também ao abrir pelo mouse] → mudança pequena no comportamento atual, a favor do teclado e de leitores de tela.

## Migration Plan

Só frontend, sem dados. Rollback: não chamar `setupAtalhos` no `main.js`. O foco e o `Esc` do modal são independentes e podem ficar.
