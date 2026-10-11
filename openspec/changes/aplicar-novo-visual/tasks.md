## 1. Base: fontes, tokens e tema

- [x] 1.1 Adicionar `@fontsource/chakra-petch`, `@fontsource/ibm-plex-sans` e `@fontsource/jetbrains-mono` ao `package.json` e verificar que `npm install` e `npm run build` terminam sem erro, com os `woff2` em `dist/assets`
- [x] 1.2 Criar `src/arena/tema.css` com os tokens dos temas escuro e claro (tabela do design.md), fontes, `--a-chanfro` e o mapeamento das variáveis do Lab (`--bg-color`, `--text-color`, `--header-bg`, `--border-color`, `--primary-color`); verificar no navegador que trocar `data-theme` no `<html>` muda fundo e texto das quatro páginas
- [x] 1.3 Criar `src/arena/tema.js` (`temaAtual`, `definirTema`, `alternarTema`, chave `arena_tema` em `try/catch`, evento `arena:tema`, sincronização via `storage`) com teste em `src/arena/tema.test.js` (padrão escuro, persistência, armazenamento que lança erro) e verificar que `npm run test:js` passa
- [x] 1.4 Adicionar a cada página (`index.html`, `ide.html`, `placar.html`, `admin.html`) o script inline anti-flash no `<head>` e o `<link>` de `tema.css` antes de `arena.css`; verificar recarregando com `arena_tema=light` salvo que a página não pisca no escuro
- [x] 1.5 Fixar a versão do Lucide em `ide.html` igual à das outras páginas e verificar que os ícones da IDE continuam aparecendo

## 2. Componentes comuns

- [x] 2.1 Reescrever `src/arena/arena.css` sobre os tokens: fundo com grade, marca "meuPiá ARENA", `.a-chanfro`, `.a-hud`, `.a-selo` por nível, `.a-botao` (primário, secundário, perigo), `.a-kpi`, `.a-card` e estados, `.a-tabela`, foco visível e `prefers-reduced-motion`; verificar `npm run build` e inspeção visual nos dois temas
- [x] 2.2 Adicionar o botão de tema (ícone sol/lua, `aria-label` "Alternar tema") ao cabeçalho do painel e do admin, ligado a `tema.js`; verificar que alternar no painel muda a página e que outra aba aberta do admin acompanha

## 3. Login e painel de missões

- [x] 3.1 Atualizar a marcação do login em `index.html` (narrativa System Recovery, selos dos níveis, cartão com cantoneiras, botão primário) conforme o canvas; verificar login com `TROQUE-ESTE-CODIGO-1` em `npm run local` nos dois temas
- [x] 3.2 Atualizar `src/arena/painel.js` para os novos cartões: código na cor do nível, rótulo de estado em texto (COMPLETO, PARCIAL, ABERTA), barra de extras, `<p>/<P> pts`, tentativas; bloqueado com ícone `lock` + `aria-label`, "Bloqueada" e requisito, sem foco; verificar que o card de B01 parcial mostra `7/10 pts` (spec `arena-interface`) e que Tab pula os bloqueados
- [x] 3.3 Atualizar o cabeçalho do painel (equipe, pontos, cronômetro em selo, sair, tema) e a barra "Módulos restaurados"; verificar a 360 px de largura que não há rolagem horizontal e os cartões ficam em uma coluna

## 4. IDE

- [x] 4.1 Criar `src/arena/editor-tema.js` com os temas CodeMirror (tema + `HighlightStyle`) e Xterm, escuro e claro, com as cores do design.md; verificar com uma checagem de contraste (script ou teste) que palavra-chave, tipo, string, número e operador ficam ≥ 4,5:1 sobre o fundo do editor nos dois temas
- [x] 4.2 Em `src/main.js`, iniciar o `Compartment` e o Xterm com o tema de `temaAtual()` e reagir a `arena:tema`; em `src/ui/toolbar.js`, remover só o handler do `theme-btn` (comentário apontando para `tema.js`); verificar que alternar o tema com código digitado preserva código, desfazer (Ctrl+Z) e saída do terminal
- [x] 4.3 Aplicar a moldura da IDE em `ide.html`/`arena.css` (cabeçalho com voltar acessível, código e nível da missão, melhor pontuação; enunciado; barra com Rodar secundário e Submeter primário; modais de configurações e de submissão) sem alterar textos do spec `arena-interface`; verificar em `npm run local` uma rodada completa Rodar → Submeter nos dois temas
- [x] 4.4 Verificar que o tamanho de fonte das configurações continua valendo no editor com os novos temas
- [ ] 4.5 Cronômetro no cabeçalho da IDE (do protótipo): a resposta de `/api/missoes?codigo=` não traz a janela do evento; exige incluir `janela` em `servico.missao` (mudança de API, a decidir)

## 5. Placar e admin

- [x] 5.1 Atualizar `placar.html`, `src/arena/placar.js` e `src/arena/placar-tabela.js`: título System Recovery, tempo restante, aviso "Placar congelado", linhas grandes, 1º lugar destacado, `●◐○` coloridos por estado mantendo uma coluna por nível, legenda; verificar a 1920×1080 e com `ARENA_REVELAR` desligado/ligado que o aviso aparece só quando congelado
- [x] 5.2 Aplicar o sistema visual a `admin.html`/`src/arena/admin.js`: selo BANCA, usuário e papel, abas, indicadores, filtros, tabela de submissões com selos de status, painel de detalhe; verificar login por token de emergência em `npm run local` e navegação pelas quatro abas nos dois temas
- [x] 5.3 Verificar que o placar segue o tema salvo e não tem botão de tema

## 6. Verificação final

- [x] 6.1 Rodar `npm test` e confirmar que todos os testes JS e Python passam
- [x] 6.2 Conferir contraste e foco das quatro páginas nos dois temas (varredura de contraste por script no navegador + teste `editor-cores.test.js`; sem falhas, exceto comentários do editor ≥ 3:1 como o spec permite) e corrigir o que aparecer
- [x] 6.3 Testar com a rede bloqueando `fonts.googleapis.com` e confirmar que as fontes carregam do próprio build
- [x] 6.4 Atualizar o README/CLAUDE.md (tema, `tema.css`/`tema.js`/`editor-tema.js`, chave `arena_tema`) e registrar no roadmap a validação no projetor e no laboratório durante o ensaio de 16/10
