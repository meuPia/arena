## 1. Renderização, índice e busca (sem DOM)

- [x] 1.1 Criar `src/arena/ajuda.js` com `htmlAjuda(markdown)` (D2), que usa o `marked` já instalado, e deixar o `import ... from "../../docs/cartao-dialeto.md?raw"` fora do caminho que o teste importa (`import()` dinâmico em `setupAjuda` ou um módulo `src/arena/cartao.js`). Verificar com `npm run test:js`, sem erro de import.
- [x] 1.2 Criar `src/arena/ajuda.test.js`, que lê `docs/cartao-dialeto.md` com `fs` e confere que o HTML de `htmlAjuda` tem:
  - um `<h2>` para cada seção (Estrutura, Variáveis, Operadores, Decisão, Repetição, Texto, Lista, Dicionário, Matemática, Na Arena);
  - pelo menos uma `<table>`, incluindo a tabela "Mensagens comuns";
  - um `<pre><code>` com `fim_algoritmo` e a indentação do exemplo da seção Estrutura.

  Verificar com `npm run test:js` passando.
- [x] 1.3 Implementar em `src/arena/ajuda.js` as funções puras `normalizar`, `indiceAjuda(markdown)` (D7) e `buscar(indice, consulta)` (D8), que devolve os trechos na ordem do cartão com as posições a destacar no texto original. Cobrir em `ajuda.test.js`, com o cartão real:
  - `dic` acha os trechos com "dicionario", "índice(s)" e "adicionar";
  - `funcao` acha "função";
  - `dcnr` acha "dicionario" e "adicionar", mas não "índice";
  - `divisao inteira` acha só o item do `piso(7 / 2)`;
  - `xyzw` devolve lista vazia;
  - consulta vazia ou só com espaços indica "cartão inteiro";
  - uma linha de tabela vem com o cabeçalho;
  - casar com o título "Dicionário" traz a seção inteira;
  - um termo não casa juntando letras de duas palavras.

  Verificar com `npm run test:js` passando.

## 2. Botão, modal e busca na IDE

- [x] 2.1 Em `ide.html`, adicionar o botão `#ajuda-btn` (D6) no `.action-group` do tema, antes de Configurações, com ícone `circle-help` e `title` e `aria-label` "Ajuda: cartão do dialeto". Adicionar também o modal `#ajuda-modal` com:
  - `role="dialog"`, `aria-modal="true"` e `aria-labelledby="ajuda-titulo"`;
  - o título "Cartão do dialeto" e o botão `#close-ajuda-btn`;
  - o campo `<input type="search" id="ajuda-busca">`, com `aria-label` e `aria-controls`;
  - o corpo `.modal-body.desafio-instrucoes` e um status curto com `aria-live="polite"` (D9).

  Verificar com `npm run build` sem erros e o botão visível no cabeçalho.
- [x] 2.2 Implementar `setupAjuda(view)` em `src/arena/ajuda.js` (D3, D5):
  - no primeiro clique, renderiza o cartão e monta o índice;
  - abre o modal com a busca limpa e o foco no campo de busca;
  - fecha pelo `x`, por clique no overlay e por `Esc` (só com o modal aberto e o campo vazio), sempre com `view.focus()` ao fechar.

  Ligar em `src/main.js` logo depois de `setupToolbar`. Verificar no navegador: abrir, fechar das três formas e conferir que o cursor volta ao editor.
- [x] 2.3 Ligar a busca ao modal (D9). A cada `input`:
  - campo vazio: mostra o cartão inteiro, do cache;
  - com texto: mostra os trechos sob o título da seção, com destaque em `<mark>` aplicado só aos nós de texto;
  - sem resultado: mostra `Nada encontrado para "…"` via `textContent`.

  O `Esc` com texto limpa o campo sem fechar o modal. Verificar no navegador:
  - `dic`, `dcnr` e `xyzw` dão o resultado do spec, e o destaque aparece dentro dos blocos de código;
  - o primeiro `Esc` limpa a busca e o segundo fecha o modal.
- [x] 2.4 Em `src/arena/arena.css`, adicionar `.arena-modal-ajuda` (D4), usando os tokens de `tema.css`:
  - conteúdo com `min(880px, 92vw)` de largura e altura fixa de `88vh`;
  - cabeçalho e campo de busca fixos no topo, com rolagem só no corpo;
  - tabelas com rolagem horizontal;
  - estilo do `<mark>` e da mensagem de nada encontrado.

  Verificar no navegador, nos temas claro e escuro, que as tabelas, os blocos de código e o destaque ficam legíveis e que a página não ganha rolagem horizontal.

## 3. Verificação e documentação

- [x] 3.1 Atualizar o aviso no topo de `tests/test_cartao_dialeto.py` para dizer que o cartão também aparece na Ajuda da IDE, inclusive na busca. Verificar com `npm run test:py` passando.
- [x] 3.2 Verificação de ponta a ponta com `npm run local`, numa missão:
  - escrever código, abrir a ajuda, buscar `dic`, apertar `Esc` duas vezes e depois Desfazer, conferindo que o código e o histórico continuam iguais;
  - conferir na aba de rede que abrir a ajuda e buscar não fazem chamadas a `/api/*`;
  - conferir que Rodar e Submeter continuam funcionando;
  - rodar `npm test` completo e registrar o resultado.
