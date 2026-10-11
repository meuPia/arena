## Why

Hoje as quatro páginas da Arena (painel, IDE, placar e admin) usam o visual herdado do Lab: tema escuro genérico
(`#11151a`, verde `#4caf50`, fonte do sistema) e um botão de tema na IDE que só troca o editor e o terminal, sem
guardar a escolha. Para o Code Challenge de 21/10 queremos uma identidade própria, "gamer" e arrojada, com a
narrativa System Recovery, sem perder o conforto do editor, onde as equipes passam a maior parte do tempo. O
visual foi desenhado e aprovado no canvas de design (tema escuro e tema claro das cinco telas).

## What Changes

- Novo sistema visual (tokens de cor, tipografia, cantos chanfrados, cantoneiras de HUD) aplicado a `index.html`,
  `ide.html`, `placar.html` e `admin.html`: fundo grafite com grade sutil, destaque verde-limão, ciano para
  tempo/parcial e uma cor por nível (Bronze, Silver, Gold, Extra).
- Dois temas, **escuro** (padrão) e **claro**, com os mesmos componentes. A escolha vale para todas as páginas
  do navegador e é lembrada entre visitas.
- Tipografia: Chakra Petch (títulos, botões, selos), IBM Plex Sans (texto) e JetBrains Mono (código, números,
  terminal), servidas pelo próprio build (sem depender do Google Fonts no laboratório).
- IDE: o estilo gamer fica na moldura (cabeçalho, enunciado, barra de ações); o editor e o terminal ganham temas
  próprios, sóbrios, para escuro e claro, com realce de sintaxe discreto e boa legibilidade.
- Painel de missões em cartões por nível, com status (completo, parcial, aberta, bloqueada), barra de testes
  extras e pontos; login com a narrativa do evento.
- Placar do telão com a nova hierarquia (posição, equipe, ●/◐/○ coloridos por módulo, completos, caracteres,
  pontos), destaque do 1º lugar e aviso de placar congelado.
- Admin com o mesmo sistema visual e um selo "BANCA" para não confundir com as telas das equipes.
- Não muda nenhuma regra de negócio, API, texto de veredito ou dado exibido: só apresentação.

## Capabilities

### New Capabilities
- `arena-visual`: identidade visual da Arena, temas escuro/claro, persistência da escolha de tema, temas do
  editor e do terminal, e requisitos de legibilidade/acessibilidade das páginas.

### Modified Capabilities
<!-- Nenhuma: os requisitos de conteúdo de arena-interface (veredito, cards, placar, log) continuam iguais. -->

## Impact

- CSS: novo `src/arena/tema.css` (tokens dos dois temas); `src/arena/arena.css` reescrito sobre os tokens;
  variáveis do Lab em `src/style.css` mapeadas para os tokens (sem reescrever o arquivo herdado).
- JS: novo `src/arena/tema.js` (aplicar/alternar/persistir tema) e `src/arena/editor-tema.js` (temas do
  CodeMirror e do Xterm); ajustes de marcação em `painel.js`, `placar.js`, `placar-tabela.js`, `admin.js`.
- Arquivos herdados do Lab: mudança mínima em `src/ui/toolbar.js` (o botão de tema passa a ser da Arena) e em
  `src/main.js` (tema inicial do editor/terminal).
- HTML: as quatro páginas (fontes, script anti-flash de tema, botão de tema, marcação dos componentes).
- Dependências: `@fontsource/chakra-petch`, `@fontsource/ibm-plex-sans`, `@fontsource/jetbrains-mono`.
- Sem impacto em `api/`, banco, juiz ou testes Python.
