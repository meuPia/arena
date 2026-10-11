## Context

- Referência visual aprovada: canvas "meuPiá Arena — Visual" (https://claude.ai/artifact/4mdgdKHdptidfdGa43eURo),
  com as cinco telas nos temas escuro e claro. Os valores de cor e tipografia abaixo saem dele.
- Hoje há duas camadas de CSS: `src/style.css` (herdado do Lab, variáveis `--bg-color`, `--header-bg`… com
  `[data-theme="dark"]`) usado só pela IDE, e `src/arena/arena.css` (variáveis `--a-*`, só escuro) usado pelas
  quatro páginas. As páginas já declaram `data-theme="dark"` no `<html>`.
- A troca de tema existe apenas na IDE, em `src/ui/toolbar.js` (herdado): alterna `data-theme`, troca o
  CodeMirror entre `oneDark` e o tema padrão via `Compartment`, e troca o tema do Xterm. Não persiste.
- Os ícones vêm do Lucide via CDN (`ide.html` usa `lucide@latest`, as outras páginas versão fixa).
- Regra do projeto: mexer o mínimo possível nos arquivos herdados do Lab (`src/ui/*`, `src/editor`,
  `src/engine/wasm.js`) para continuar trazendo o `upstream`.
- O laboratório terá cerca de 20 máquinas abrindo a IDE ao mesmo tempo (ensaio de carga até 16/10).

## Goals / Non-Goals

**Goals:**
- Um único conjunto de tokens para os dois temas, consumido por todas as páginas e pelo CSS herdado.
- Tema aplicado antes da primeira pintura e compartilhado entre páginas.
- Editor/terminal com temas próprios, trocados sem recriar o editor.

**Non-Goals:**
- Mudar textos, dados, rotas ou regras (veredito, cards, placar, log continuam como em `arena-interface`).
- Desenhar as abas Placar real, Perfis e Auditoria do admin além de aplicar os tokens e componentes comuns.
- Seguir `prefers-color-scheme` automaticamente (o padrão é sempre o escuro, ver Decisões).
- Trocar o Lucide por outra biblioteca de ícones.

## Decisions

### 1. Tokens em CSS custom properties, por `data-theme`
Novo `src/arena/tema.css`, carregado antes de `arena.css` em todas as páginas, com `:root, [data-theme="dark"]`
e `[data-theme="light"]` definindo tokens semânticos:

| Token | Escuro | Claro |
|---|---|---|
| `--a-bg` | `#07090D` | `#F2F4F7` |
| `--a-surface` / `--a-surface-2` | `#0E121A` / `#0A0D13` | `#FFFFFF` / `#F7F8FA` |
| `--a-border` / `--a-border-forte` | `#1B2230` / `#2E384A` | `#DCE1E8` / `#C9D0DA` |
| `--a-text` / `--a-text-2` / `--a-muted` | `#E6EDF5` / `#C3CCD8` / `#8B98AB` | `#11161E` / `#3A4452` / `#5A6576` |
| `--a-accent` (fundo) / `--a-accent-ink` (texto sobre ele) | `#C6FF3D` / `#0A0D06` | igual |
| `--a-accent-text` (destaque como texto) | `#C6FF3D` | `#3F6A00` |
| `--a-info` (tempo, parcial, Rodar) | `#38E1FF` | `#0A6E8F` |
| `--a-fail` | `#FF7A8A` | `#C2213A` |
| `--a-forte` (selo escuro do cronômetro, logo) | `#C6FF3D` sobre surface | `#11161E` |
| níveis `--a-bronze/silver/gold/extra` + `-bg`/`-borda` | `#E9A36C` `#C9D2DB` `#F2C14E` `#FF6FB4` | `#8F4E17` `#4A5563` `#7A5A00` `#B0145F` |
| `--a-grade` (linhas do fundo) | `rgba(198,255,61,.04)` | `rgba(17,22,30,.05)` |

Também `--a-font-display`, `--a-font-text`, `--a-font-mono`, `--a-chanfro` (10 px). Os nomes `--a-*` já existem
em `arena.css`, então o resto do CSS migra sem renomear tudo.
*Alternativa:* duas folhas separadas (`escuro.css`/`claro.css`) trocadas por `<link>` — descartada: causa flash
na troca e duplica regras.

### 2. CSS herdado mapeado, não reescrito
Em `tema.css`, as variáveis do Lab (`--bg-color`, `--text-color`, `--header-bg`, `--border-color`,
`--primary-color`) recebem os tokens nos dois temas. Ajustes de layout/estilo da IDE ficam em `arena.css` com
seletores da Arena (ex.: `body.arena-ide header`), sobrescrevendo o `style.css` sem editá-lo.
*Alternativa:* editar `style.css` — descartada pela regra do upstream.

### 3. Aplicação do tema sem flash, persistência em `localStorage`
Um script inline mínimo no `<head>` de cada página lê `localStorage['arena_tema']` (em `try/catch`) e define
`document.documentElement.dataset.theme` antes do CSS pintar; padrão `dark`. `src/arena/tema.js` expõe
`temaAtual()`, `definirTema(t)` e `alternarTema()`, grava a chave, atualiza o ícone/rótulo do botão e dispara
`arena:tema` (CustomEvent) para quem precisar reagir (IDE). O evento `storage` sincroniza outras abas abertas
(por exemplo, o painel aberto atrás da IDE).
*Por que escuro fixo como padrão:* é o visual do evento e do telão; seguir o sistema faria máquinas do
laboratório abrirem em temas diferentes.

### 4. Botão de tema da IDE passa para a Arena
O `theme-btn` da IDE continua no HTML, mas quem trata o clique é `tema.js`. Em `src/ui/toolbar.js` a única
mudança é não registrar o handler de tema (guarda/remoção do bloco), mantendo o resto igual ao upstream. O painel
e o admin ganham o mesmo botão no cabeçalho; o placar não tem botão.
*Alternativa:* deixar o handler do Lab e "corrigir" depois — descartada: dois handlers no mesmo botão divergem
(o do Lab não sabe do estado salvo).

### 5. Temas do editor e do terminal em `src/arena/editor-tema.js`
Dois temas CodeMirror (`EditorView.theme` + `HighlightStyle` via `syntaxHighlighting`) e dois temas Xterm,
com as cores do protótipo (escuro: fundo `#0B0E14`, palavra-chave `#6CC6FF`, tipo `#B39DFF`, string `#E9C46A`,
número `#F49B6C`, operador `#8B98AB`, linha ativa `#111827`; claro: fundo `#FFFFFF`, `#0B62A8`, `#6347C9`,
`#8A5A00`, `#B0471A`, `#5A6576`, linha ativa `#F3FBE3`). O mapeamento usa as tags que `meupia-lang.js` já emite
(keyword, typeName, operator, number, string, atom, comment), sem mudar o tokenizer.
`main.js` passa a iniciar o `Compartment` com o tema correspondente a `temaAtual()` (em vez de `oneDark` fixo) e
escuta `arena:tema` para `reconfigure` do editor e `term.options.theme`. Isso preserva documento, histórico e
saída (requisito "Troca de tema preserva o trabalho"). `@codemirror/theme-one-dark` deixa de ser importado pela
Arena (pode continuar no `package.json` por causa do `toolbar.js`).
*Alternativa:* recriar o `EditorView` na troca — descartada: perde histórico de desfazer.

### 6. Fontes empacotadas com `@fontsource`
Importar `@fontsource/chakra-petch` (500, 600, 700), `@fontsource/ibm-plex-sans` (400, 500, 600) e
`@fontsource/jetbrains-mono` (400, 600) a partir de `tema.css`/entrada JS; o Vite copia os `woff2` para o build,
servidos pela Vercel com cache. Só subconjunto latin. `font-display: swap`.
*Alternativa:* Google Fonts — descartada: dependência externa no laboratório e mais uma origem no ensaio de carga.

### 7. Componentes visuais como classes utilitárias da Arena
Em `arena.css`: `.a-chanfro` (clip-path dos cantos), `.a-hud` (cantoneiras via `::before/::after`), `.a-selo` +
modificadores por nível, `.a-botao` (`--primario`, `--secundario`, `--perigo`), `.a-kpi`, `.a-card` com estados
`completo|parcial|aberta|bloqueada`, `.a-tabela`, fundo com grade em `.arena-pagina`. Os JS que montam HTML
(`painel.js`, `placar-tabela.js`, `admin.js`) trocam/adicionam classes e rótulos de estado; a lógica não muda.
Emojis decorativos de cadeado (`🔒`) viram ícone Lucide `lock` com `aria-label`. Os textos de veredito do spec
`arena-interface` (que têm emoji) **não** mudam.

### 8. Placar: mantém uma coluna por nível
O protótipo mostra uma coluna por módulo; o spec `arena-interface` exige uma coluna por nível com `●◐○`.
Mantemos o spec: cada célula de nível mostra os símbolos (texto, preserva leitura e testes), coloridos por
estado (`--a-accent`/`--a-info`/`--a-border-forte`) e em fonte grande. Cabeçalhos de nível na cor do nível.

## Risks / Trade-offs

- [Contraste do verde-limão no claro] → limão só como fundo com texto escuro; texto de destaque usa
  `--a-accent-text` (`#3F6A00`). Conferir com verificação de contraste na tarefa de revisão.
- [Merge com o upstream do Lab] → mudanças em `toolbar.js`/`main.js` pequenas e comentadas; o restante fica em
  arquivos da Arena.
- [`clip-path` corta bordas e foco] → chanfro só em elementos de fundo sólido (botões, selos); painéis usam borda
  reta + cantoneiras; foco visível com `outline` + `outline-offset` fora do clip.
- [Peso das fontes no ensaio de carga] → 8 arquivos `woff2` latin (~20–30 KB cada), em cache após a primeira carga;
  medir no ensaio de 16/10.
- [Leitura no projetor] → grade de fundo muito sutil pode virar ruído; o placar usa grade mais espaçada e
  pode ter a grade desligada se o ensaio mostrar problema.
- [Lucide `@latest` na IDE] → fixar a mesma versão das outras páginas junto com esta mudança, para o ícone de tema
  e o cadeado não mudarem de nome na véspera.

## Migration Plan

1. Implantar como qualquer mudança de front-end (build do Vite + deploy na Vercel); não há dados a migrar.
2. Quem tinha o tema da IDE trocado não tinha nada salvo: todos começam no escuro.
3. Rollback: reverter o commit; a chave `arena_tema` no navegador é ignorada pela versão antiga.
4. Validar no ensaio de 16/10 (projetor do telão, monitores do laboratório) antes do piloto final.
