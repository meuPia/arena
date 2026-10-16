## Why

Durante a prova, as equipes esbarram em detalhes do dialeto (contador do `para` fora do `var`, `/` que sempre dá real, fatia `t[1:3]` que não existe, `leia` proibido) e só descobrem pela mensagem de erro. O `docs/cartao-dialeto.md` já responde a essas dúvidas e é conferido com o compilador real (`tests/test_cartao_dialeto.py`), mas hoje fica só no repositório: quem está na IDE da missão não o vê.

## What Changes

- Novo botão **Ajuda** no cabeçalho da IDE da missão (`ide.html`), ao lado de Configurações, com ícone e rótulo acessível.
- O botão abre um modal **"Cartão do dialeto"** com o conteúdo de `docs/cartao-dialeto.md` renderizado (títulos, tabelas e blocos de código), no tema atual da Arena (claro ou escuro).
- O conteúdo vem do próprio `docs/cartao-dialeto.md`, embutido no build: a IDE e o cartão impresso usam a mesma fonte, e não há cópia para manter em sincronia.
- **Busca** no topo do modal: a pessoa digita e o cartão mostra só os trechos que casam (linha de tabela, item de lista, parágrafo ou bloco de código), sob o título da seção, com o que casou destacado. A busca ignora acentos e maiúsculas e aceita letras na ordem dentro de uma palavra: `dic` acha "dicionário" e "índice", e `dcnr` acha "dicionário".
- O modal fecha pelo botão de fechar, pelo `Esc` (com o campo de busca vazio; com texto, o `Esc` limpa a busca) e por clique fora dele. Ao fechar, o foco volta ao editor, e o código e o histórico de desfazer continuam iguais.
- Abrir a ajuda não faz chamadas à API, não grava nada e não interfere em Rodar, Submeter nem no cronômetro.

Fora do escopo: tolerância a erro de digitação na busca (`dicionaro`), ajuda contextual por erro (ligar a mensagem do compilador à linha da tabela) e ajuda no painel de missões ou no placar.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `arena-interface`: novo requisito "Ajuda do dialeto na IDE", que define o botão, o conteúdo (vindo de `docs/cartao-dialeto.md`), a busca, como o modal abre e fecha e que ele não altera o código nem a submissão.

## Impact

- **Frontend**:
  - `ide.html`: botão Ajuda no cabeçalho e o modal;
  - novo `src/arena/ajuda.js`: importa o Markdown no build (`?raw`, do Vite), renderiza com `marked` (já é dependência), monta o índice de trechos, faz a busca e trata abrir e fechar;
  - `src/main.js`: liga a ajuda;
  - `src/arena/arena.css`: estilo do conteúdo do cartão no modal (largura maior, tabelas, código, campo de busca e destaque), usando os tokens de `tema.css`.
- **Testes**: novo `src/arena/ajuda.test.js` (`node --test`) cobrindo a renderização do cartão, o índice e a busca (acentos, ordem dos resultados, nada encontrado).
- **Docs**: `docs/cartao-dialeto.md` passa a ser usado pela IDE; quem editar o cartão muda também o que as equipes veem. O aviso no topo de `tests/test_cartao_dialeto.py` passa a dizer isso.
- Sem mudanças no backend, na API, no juiz ou nas dependências: a busca é escrita no projeto, sem biblioteca de fuzzy.
