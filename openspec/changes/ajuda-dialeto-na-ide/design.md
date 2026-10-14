## Context

Para a motivação, veja `proposal.md`; para o comportamento esperado, `specs/arena-interface/spec.md`. O que existe hoje e define a abordagem:

- `ide.html` já tem três modais com o mesmo padrão: `.modal-overlay.hidden` > `.modal-content` > `.modal-header` + `.modal-body`. São eles Configurações, Submeter e Veredito. Os botões do cabeçalho ficam em `.action-group`, com ícones Lucide (`data-lucide`, `lucide.createIcons()`).
- O modal do veredito (`src/arena/submissao.js`) já trata fechar pelo `x`, por clique no overlay e por `Esc` (`keydown` no `document`) e devolve o foco com `view.focus()`. É o modelo a seguir.
- As instruções da missão já são Markdown renderizado com `marked` (`src/ui/instructions.js`), e `src/arena/arena.css` tem estilos prontos para esse conteúdo em `.desafio-instrucoes` (títulos, `code`, `pre`, tabelas, blockquote) nos dois temas.
- O build é Vite (`vite.config.js`, quatro páginas). O deploy na Vercel serve só o `dist/` e as funções Python, então o `docs/` não está publicado como arquivo estático.
- `.modal-content` tem largura fixa de `450px` (`src/style.css`), estreita demais para as tabelas do cartão.

## Goals / Non-Goals

**Goals:**
- Uma única fonte para o conteúdo: `docs/cartao-dialeto.md`.
- Seguir o padrão dos modais e dos estilos que a IDE já usa, sem dependências novas.
- Manter testável em `node --test` a parte que não depende do DOM, incluindo o índice e a busca.

**Non-Goals:**
- Não mexer no layout com Split.js nem na aba Instruções.
- Não criar um sistema genérico de modais nem refatorar os três modais que já existem.
- Não tolerar letras erradas na busca (distância de edição) nem ordenar por relevância: os resultados seguem a ordem do cartão.

## Decisions

### D1. Conteúdo embutido no build com `import ... from "../../docs/cartao-dialeto.md?raw"`
O Vite põe o texto do Markdown dentro do bundle da IDE. Assim a ajuda funciona sem nenhuma chamada de rede, mesmo com a API instável no dia do evento, e qualquer edição no cartão entra no próximo deploy.

- *Alternativa: `fetch("/docs/cartao-dialeto.md")`*. Exigiria publicar `docs/` (copiar para `public/` ou criar um plugin), seria mais um ponto de falha em produção e repetiria o arquivo.
- *Alternativa: copiar o conteúdo para HTML em `ide.html`*. Teria duas fontes para manter em sincronia, que é justamente o que se quer evitar.

O cartão tem 4,4 KB, então o aumento do bundle é desprezível.

### D2. Renderização numa função pura, separada do DOM
`src/arena/ajuda.js` exporta:
- `htmlAjuda(markdown)`, que devolve `marked.parse(markdown)`;
- `indiceAjuda(markdown)` e `buscar(indice, consulta)` (D7, D8), sem DOM;
- `setupAjuda(view)`, que liga o botão, o campo de busca e o modal.

O teste importa as funções puras e lê o `.md` com `fs`, porque o `node --test` não entende `?raw`. Por isso o `import ... ?raw` fica dentro de `setupAjuda`, como `import()` dinâmico, ou num módulo pequeno separado (`src/arena/cartao.js`) que só o `main.js` importa. A escolha final fica para a implementação, desde que o teste não precise do Vite.

O Markdown vem do repositório, não do usuário, então não há sanitização extra. É o mesmo nível de confiança das instruções dos desafios.

### D3. Renderizar uma vez, na primeira abertura
O HTML é gerado no primeiro clique e guardado no `.modal-body`. Isso evita trabalho no carregamento da IDE, que já inicia o Pyodide.

### D4. Reaproveitar `.desafio-instrucoes` e alargar só este modal
O corpo do modal recebe as classes `modal-body desafio-instrucoes`, e herda os estilos de tabela e código nos dois temas. Uma classe nova, `.arena-modal-ajuda`, define:
- `.modal-content` com `width: min(880px, 92vw)` e altura fixa de `88vh` (com `max-height`, o modal encolhia com poucos resultados e, centralizado, o campo de busca mudava de lugar enquanto a pessoa digitava);
- rolagem só no `.modal-body` (`overflow: auto`), com o cabeçalho fixo;
- tabelas com `overflow-x: auto` (num wrapper ou com `display: block`) para caber em telas estreitas.

### D5. Fechar e devolver o foco como o modal do veredito
O botão `x`, o clique no overlay e o `Esc` (só com o modal aberto e o campo de busca vazio; com texto, o `Esc` limpa a busca, D9) chamam `fechar()`, que esconde o modal e chama `view.focus()`. O CodeMirror guarda a seleção ao perder o foco, então o cursor volta para onde estava. A ajuda não mexe no `EditorState`, o que preserva o histórico de desfazer.

Ao abrir, o foco vai para o campo de busca, e o texto da busca anterior é limpo. O overlay recebe `role="dialog"`, `aria-modal="true"` e `aria-labelledby`, como no veredito.

### D6. Botão no grupo da direita, antes de Configurações
`<button id="ajuda-btn" title="Ajuda: cartão do dialeto" aria-label="Ajuda: cartão do dialeto"><i data-lucide="circle-help"></i></button>` vai no `.action-group` do tema e de Configurações, que são as ferramentas da IDE. Fica longe de Rodar e Submeter, para não ser clicado por engano.

### D7. Índice de trechos com `marked.lexer`
`indiceAjuda(markdown)` percorre os tokens de `marked.lexer` uma vez e devolve uma lista na ordem do cartão. Cada item tem:
- `secao` (o `##` atual, e o `###` quando houver, como em "Na Arena › Mensagens comuns");
- `tipo` (`titulo`, `linha`, `item`, `paragrafo` ou `codigo`);
- `texto`: o texto do trecho, sem marcação Markdown;
- `markdown`: o pedaço original para renderizar.

Cada linha de tabela vira um trecho próprio, cujo `markdown` é uma minitabela (cabeçalho + aquela linha), para que a coluna faça sentido isolada. Itens de lista e parágrafos são um trecho cada. Um bloco de código é um trecho inteiro: cortar por linha perderia o contexto e a indentação.

O índice é montado uma vez, junto com a primeira renderização (D3). O cartão gera uns 80 trechos.

- *Alternativa: buscar no DOM renderizado (`querySelectorAll("tr, li, p, pre")`)*. Dispensaria o índice, mas não daria para testar sem DOM e misturaria a busca com o HTML.

### D8. Casamento escrito no projeto, por palavra
`normalizar(s)` = `s.normalize("NFD")`, sem as marcas combinantes (`\p{M}`), em minúsculas. A consulta normalizada é separada por espaços em termos, e o texto do trecho é separado em palavras (`[\p{L}\p{N}_]+`). Um termo casa com uma palavra quando é uma subsequência dela: as letras na ordem, contíguas ou não. Prefixo e pedaço são casos particulares disso. O trecho entra quando todos os termos casam em alguma palavra. O título de seção que casa traz a seção inteira.

Conferido no cartão atual: `dic` casa com `adicionar`, `dicionario`, `indice` e `indices`; `dcnr` casa com `adicionar` e `dicionario`.

O destaque marca, em cada palavra que casou, as letras do primeiro casamento: o pedaço contíguo quando existe (`dic` em "ín**dic**e"), ou as letras soltas quando não. Para mapear de volta ao texto com acento, a normalização é feita caractere a caractere, guardando o índice original.

- *Alternativa: Fuse.js ou outra biblioteca*. Seria uma dependência nova para ~40 linhas. Além disso, o fuzzy padrão delas atravessa palavras e tolera erros, o que traz ruído num texto curto e foi descartado (ver Non-Goals).

### D9. Renderização dos resultados e `Esc` em dois passos
A cada `input`, sem debounce (são ~80 trechos):
- campo vazio: o corpo volta ao HTML completo, guardado em cache;
- com texto: cada trecho que casou é renderizado com `marked.parse(trecho.markdown)`, sob um `<h3>` com a `secao` sempre que ela muda, e com o destaque em `<mark>`;
- sem nenhum trecho: aparece `Nada encontrado para "<consulta>"`, com a consulta escapada e via `textContent`.

O destaque é aplicado depois da renderização, percorrendo só os nós de texto (`TreeWalker`) do HTML do trecho. Assim o `<mark>` nunca quebra uma tag e funciona dentro de `<code>` e `<pre>`.

O campo é um `<input type="search">` com `aria-label` e `aria-controls` apontando para o corpo. O `aria-live="polite"` fica num status curto ao lado do campo ("4 trechos encontrados" / "Nada encontrado…"), e não no corpo: um corpo vivo leria o cartão inteiro a cada tecla. O `keydown` de `Esc` com texto chama `preventDefault()` e limpa o campo. Com o campo vazio, o `Esc` cai em `fechar()`.

## Risks / Trade-offs

- [Subsequência dentro da palavra ainda traz alguns resultados inesperados (`dcnr` acha "adicionar")] → É limitado a uma palavra e destacado, então a pessoa vê por que apareceu. Os testes fixam o comportamento com os exemplos do spec.
- [Mudar a estrutura do cartão (por exemplo, tabela vira lista) muda o que a busca devolve] → O índice segue os tokens do Markdown, não posições fixas, e `ajuda.test.js` usa o arquivo real.

- [O cartão cita `tests/test_cartao_dialeto.py` na introdução, o que não diz nada para quem está na prova] → Mantido assim nesta mudança, porque o spec pede o conteúdo sem cortes. Se incomodar, a frase pode ser ajustada no próprio `.md`.
- [Editar o cartão muda a IDE sem nenhum teste de interface] → O aviso de `tests/test_cartao_dialeto.py` passa a lembrar disso, e `ajuda.test.js` falha se uma seção esperada sumir ou se o Markdown deixar de gerar tabelas e blocos de código.
- [`Esc` com o autocomplete do CodeMirror aberto] → O modal cobre o editor e o listener só age com o modal visível, então o `Esc` do editor não muda.
- [Tabelas largas no celular] → Rolagem horizontal da tabela (D4). A IDE não é pensada para celular, mas o conteúdo continua acessível.

## Migration Plan

Só frontend. Basta publicar o build. Para voltar atrás, reverta o commit: não há dados nem configuração envolvidos.
