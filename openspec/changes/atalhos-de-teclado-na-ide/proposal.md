## Why

Na IDE da missão, rodar os testes de exemplo e submeter exigem levar o mouse até os botões do cabeçalho. Durante a prova, a equipe roda o código dezenas de vezes, e cada ida ao mouse tira o foco do editor. A IDE não tem nenhum atalho de teclado próprio hoje: os únicos `keydown` do código são o `Esc` dos modais de ajuda e veredito e as setas das abas do celular. Pior: `Ctrl+Enter`, o atalho que muita gente tenta por hábito, hoje insere uma linha em branco no editor (é o `Mod-Enter` do teclado padrão do CodeMirror).

## What Changes

- **`Ctrl+Enter`** roda os testes de exemplo, como um clique em Rodar, de qualquer lugar da IDE (editor, terminal, painel da missão).
- **`Ctrl+Shift+Enter`** abre o modal de Submeter, como um clique em Submeter. Ele não envia nada sozinho: a equipe ainda marca os participantes e confirma.
- No Mac, `⌘` vale no lugar de `Ctrl` (`⌘+Enter` e `⌘+Shift+Enter`).
- Os atalhos respeitam o estado dos botões. Não fazem nada com o botão desabilitado (motor ainda carregando, cooldown, julgamento em andamento, submissões fechadas), com algum modal aberto ou quando a tecla fica pressionada (repetição automática).
- No editor, `Ctrl+Enter` deixa de inserir linha em branco e passa a rodar.
- O `title` dos botões mostra a dica: "Rodar os testes de exemplo (Ctrl+Enter)" e "Envia para o juiz (testes de exemplo + testes extras) (Ctrl+Shift+Enter)", com `⌘` no Mac. Os botões ganham também `aria-keyshortcuts`.
- Modal de Submeter usável pelo teclado: ao abrir, o foco vai para o primeiro participante (ou o campo de nomes), e o `Esc` fecha o modal e devolve o foco ao editor. Isso vale para qualquer forma de abrir o modal. Sem essa parte, o foco ficaria no editor por trás do modal, e a equipe digitaria no código sem ver.
- O cartão do dialeto (seção "Na Arena") cita os dois atalhos.

Fora do escopo: atalho para confirmar o envio dentro do modal, atalhos configuráveis, atalhos no painel de missões, no placar ou no painel da banca, e uma lista de atalhos na interface além do `title` e do cartão.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `arena-interface`: novo requisito "Atalhos de teclado na IDE", com os atalhos de Rodar e Submeter, as condições em que não agem, a dica nos botões e o foco e o `Esc` do modal de Submeter.

## Impact

- **Frontend**:
  - novo `src/arena/atalhos.js`: função pura que reconhece o atalho de um evento de teclado (plataforma, modificadores, repetição) e `setupAtalhos`, que ouve o `keydown` na fase de captura e aciona o `click()` do botão;
  - `src/main.js`: liga os atalhos;
  - `src/arena/submissao.js`: foco no primeiro campo ao abrir o modal de Submeter e `Esc` para fechar;
  - `ide.html`: `title` e `aria-keyshortcuts` em `#run-btn` e `#submit-btn` (o texto é ajustado para o Mac em tempo de execução).
- **Testes**: novo `src/arena/atalhos.test.js` (`node --test`).
- **Docs**: `docs/cartao-dialeto.md` (seção "Na Arena"); o teste da busca da ajuda roda contra o cartão real.
- **Arquivos herdados do Lab** (`src/ui/toolbar.js`, `src/engine/*`, `src/editor/*`): sem mudança. O `Mod-Enter` do CodeMirror é sobreposto pelo atalho da Arena, sem editar a configuração do editor.
- Sem mudanças no backend, na API, no juiz ou nas dependências.
