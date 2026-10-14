# arena-interface Specification

## Purpose
Definir o que a IDE da missão, o painel da equipe, o placar do telão e a visão admin mostram sobre o veredito da submissão e a pontuação no modelo de exemplos + extras.

## Requirements

### Requirement: Veredito na IDE
Depois de uma submissão, a IDE SHALL mostrar o veredito nestes formatos:
- aceito e completo: `✅ ACEITO — <a>/<t> testes extras · <p>/<P> pts · <c> caracteres`
- aceito parcial: `🟡 ACEITO PARCIAL — <a>/<t> extras · <p>/<P> pts`
- reprovado nos exemplos: `❌ Passe primeiro em todos os testes de exemplo (<a>/<t>)`
- erro de compilação, erro de execução e cooldown: mensagens como as de hoje.

Para submissões aceitas, a IDE SHALL mostrar também a melhor pontuação da equipe no módulo e os caracteres dessa melhor submissão. A IDE MUST NOT mostrar qual teste extra falhou.

#### Scenario: Completo
- **WHEN** a submissão é aceita com 20/20 extras num módulo de 10 pts e 142 caracteres
- **THEN** a IDE mostra `✅ ACEITO — 20/20 testes extras · 10/10 pts · 142 caracteres`

#### Scenario: Parcial
- **WHEN** a submissão é aceita com 14/20 extras num módulo de 10 pts
- **THEN** a IDE mostra `🟡 ACEITO PARCIAL — 14/20 extras · 7/10 pts` e a melhor pontuação da equipe no módulo

#### Scenario: Reprovado nos exemplos
- **WHEN** a submissão passa em 2 de 3 exemplos
- **THEN** a IDE mostra `❌ Passe primeiro em todos os testes de exemplo (2/3)`

### Requirement: Botão Submeter sempre disponível
O botão Submeter SHALL continuar disponível depois que o módulo estiver completo, enquanto a janela estiver aberta e fora do cooldown. O status da missão na IDE SHALL mostrar a melhor pontuação (por exemplo `Melhor: 7/10 pts`) e o selo de completo quando houver.

#### Scenario: Módulo completo
- **WHEN** a equipe abre a IDE de um módulo completo, fora do cooldown
- **THEN** o botão Submeter está habilitado e o status mostra a melhor pontuação com o selo de completo

### Requirement: Card do painel
Cada card de módulo liberado no painel SHALL mostrar a melhor pontuação da equipe no formato `<p>/<P> pts`, o selo de completo quando completo, e o número de tentativas. Módulo sem submissão aceita SHALL mostrar só os pontos do módulo e as tentativas, como hoje.

#### Scenario: Card parcial
- **WHEN** a equipe tem 7 pts em B01, não completo
- **THEN** o card de B01 mostra `7/10 pts`, sem selo de completo

### Requirement: Placar do telão
O placar SHALL ter as colunas posição, equipe, uma coluna por nível, Pontos, Completos e Caracteres. Em cada nível, cada módulo aparece como `●` (completo), `◐` (aceito parcial) ou `○` (sem submissão aceita). A coluna Caracteres mostra a soma dos caracteres das melhores submissões completas. O placar público MUST NOT mostrar código-fonte nem participantes.

#### Scenario: Linha do telão
- **WHEN** uma equipe tem B01 completo, B02 parcial e B03 sem submissão aceita
- **THEN** a coluna Bronze mostra `●◐○`

### Requirement: Log do admin
O log de submissões SHALL ficar na seção Submissões do painel administrativo (`/admin.html`), e não mais em `/placar.html`. Para cada submissão, ele mostra horário, equipe, módulo, tentativa, status, exemplos aprovados/total, extras aprovados/total, pontos calculados, pontos efetivos (destacando quando há ajuste), caracteres e participantes. O `/placar.html` MUST mostrar só o placar: ele não exibe log, código-fonte nem participantes, mesmo quando aberto por alguém da banca.

#### Scenario: Submissão parcial no log
- **WHEN** um admin ou juiz abre a seção Submissões do painel depois de uma submissão aceita com 14/20 extras
- **THEN** a linha mostra exemplos 3/3, extras 14/20, os pontos e os caracteres dessa submissão

#### Scenario: Submissão ajustada no log
- **WHEN** a submissão foi ajustada de 10 para 0 pts
- **THEN** a linha mostra os pontos calculados (10), os efetivos (0) destacados e o motivo ao abrir a submissão

#### Scenario: Placar do telão sem log
- **WHEN** alguém abre `/placar.html`
- **THEN** a página mostra só o placar, sem a tabela de submissões

### Requirement: Textos da IDE sobre o juiz
Os textos da IDE que hoje falam em "testes ocultos" SHALL falar em "testes extras" e explicar a regra: enviar exige passar em todos os exemplos, os pontos dependem dos extras e o menor código desempata.

#### Scenario: Aviso no modal de submissão
- **WHEN** a equipe abre o modal de submissão
- **THEN** o aviso fala em testes de exemplo e testes extras, não em testes ocultos

### Requirement: Cronômetro na IDE
O cabeçalho da IDE SHALL mostrar o cronômetro do evento, sincronizado com o horário do servidor: o tempo para
abrir antes do início, o tempo restante enquanto estiver aberto e "encerrado" depois do fim; no modo ensaio, o
rótulo do modo ensaio. Para isso, a resposta da missão SHALL incluir a janela do evento (início, fim, freeze,
agora, situação e ensaio), calculada com o horário efetivo (incluindo o definido pelo painel).

#### Scenario: Tempo restante
- **WHEN** a equipe abre uma missão às 20h00 e o evento termina às 21h50
- **THEN** o cabeçalho da IDE mostra `1:50:00` como tempo restante (mesmo formato do painel), diminuindo a cada segundo

#### Scenario: Evento encerrado
- **WHEN** a equipe está na IDE e passa do horário de fim
- **THEN** o cronômetro mostra que o evento foi encerrado

### Requirement: Ajuda do dialeto na IDE
O cabeçalho da IDE da missão SHALL ter um botão Ajuda, com rótulo acessível, que abre um modal "Cartão do dialeto" com o conteúdo de `docs/cartao-dialeto.md`, sem cortes, renderizado como Markdown: títulos, listas, tabelas e blocos de código com a indentação preservada. O conteúdo MUST vir desse arquivo, para que a IDE e o cartão impresso não divirjam. O modal SHALL seguir o tema atual da Arena (claro ou escuro) e rolar por dentro quando o conteúdo passar da altura da tela.

O modal SHALL fechar pelo botão de fechar, pela tecla `Esc` com o campo de busca vazio e por clique fora do conteúdo. Ao fechar, o foco SHALL voltar ao editor. Abrir ou fechar a ajuda, ou buscar nela, MUST NOT alterar o código do editor nem o histórico de desfazer, MUST NOT fazer chamadas à API e MUST NOT interferir em Rodar, Submeter ou no cronômetro.

#### Scenario: Abrir a ajuda
- **WHEN** a equipe clica no botão Ajuda na IDE de uma missão
- **THEN** abre o modal "Cartão do dialeto" com as seções do cartão (Estrutura, Variáveis, Operadores, Decisão, Repetição, Texto, Lista, Dicionário, Matemática e Na Arena), incluindo a tabela "Mensagens comuns"

#### Scenario: Código do cartão legível
- **WHEN** o modal mostra o exemplo da seção Estrutura
- **THEN** o exemplo aparece num bloco de código, com a indentação e os comentários `//` como estão no cartão

#### Scenario: Fechar com Esc
- **WHEN** o modal de ajuda está aberto com o campo de busca vazio e a equipe aperta `Esc`
- **THEN** o modal fecha e o cursor volta ao editor, na posição em que estava

#### Scenario: Fechar clicando fora
- **WHEN** a equipe clica fora do conteúdo do modal
- **THEN** o modal fecha

#### Scenario: Código preservado
- **WHEN** a equipe escreve código, abre a ajuda, busca algo, fecha e depois aperta Desfazer
- **THEN** o código continua igual e Desfazer desfaz a última edição feita antes de abrir a ajuda

#### Scenario: Cartão atualizado
- **WHEN** alguém altera `docs/cartao-dialeto.md` e a Arena é publicada de novo
- **THEN** o modal de ajuda mostra o texto novo, e a busca encontra esse texto, sem nenhuma outra edição

#### Scenario: Tema claro
- **WHEN** a equipe está no tema claro e abre a ajuda
- **THEN** o modal, as tabelas, os blocos de código, o campo de busca e o destaque usam as cores do tema claro

### Requirement: Busca na ajuda do dialeto
O modal de ajuda SHALL ter um campo de busca no topo, que recebe o foco quando o modal abre. Com o campo vazio, o modal SHALL mostrar o cartão inteiro. Com texto, o modal SHALL mostrar só os trechos do cartão que casam, na ordem do cartão e sob o título da seção de cada um. Um trecho é uma linha de tabela (mostrada com o cabeçalho da tabela), um item de lista, um parágrafo ou um bloco de código. Quando o título de uma seção casa, a seção inteira aparece.

A busca SHALL ignorar acentos e maiúsculas e SHALL separar a consulta em termos pelos espaços. Um trecho casa quando **todos** os termos casam nele. Um termo casa com uma palavra do trecho quando é um prefixo dela, um pedaço dela ou quando as letras do termo aparecem na mesma ordem dentro dessa palavra. Um termo MUST NOT casar juntando letras de palavras diferentes. O que casou SHALL aparecer destacado no trecho. A busca MUST NOT tolerar letras erradas (por exemplo, `dicionaro` não acha "dicionario"). Os resultados SHALL atualizar a cada tecla.

Sem nenhum trecho que case, o modal SHALL mostrar "Nada encontrado para "<consulta>"". Com texto no campo, `Esc` SHALL limpar a busca e voltar ao cartão inteiro, sem fechar o modal.

#### Scenario: Prefixo e pedaço de palavra
- **WHEN** a equipe digita `dic` na busca
- **THEN** aparecem a seção Dicionário, a linha `dicionario` da tabela de Variáveis, o bloco de código da Lista (por "índices" e "adicionar") e a linha "um exemplo deu erro durante a execução" de Mensagens comuns (por "índice"), com `dic` destacado em cada um

#### Scenario: Sem acento
- **WHEN** a equipe digita `funcao`
- **THEN** aparecem também os trechos que só têm "função" com acento, como "Os testes chamam a sua função"

#### Scenario: Letras na ordem dentro da palavra
- **WHEN** a equipe digita `dcnr`
- **THEN** aparecem os trechos com "dicionario" ou "Dicionário" e o bloco de código da Lista (por "adicionar"), e não aparece a linha de Mensagens comuns com "índice"

#### Scenario: Letras de palavras diferentes não casam
- **WHEN** a equipe digita `dcnr` e um trecho só tem essas letras espalhadas em palavras diferentes
- **THEN** esse trecho não aparece

#### Scenario: Vários termos
- **WHEN** a equipe digita `divisao inteira`
- **THEN** aparece o item de Operadores sobre `piso(7 / 2)` e não aparecem trechos que só falam de "divisão"

#### Scenario: Nada encontrado
- **WHEN** a equipe digita `xyzw`
- **THEN** o modal mostra `Nada encontrado para "xyzw"`

#### Scenario: Esc limpa a busca
- **WHEN** há texto na busca e a equipe aperta `Esc`
- **THEN** o campo fica vazio, o cartão inteiro volta e o modal continua aberto; um segundo `Esc` fecha o modal

#### Scenario: Foco na busca
- **WHEN** a equipe abre a ajuda
- **THEN** o cursor já está no campo de busca e o que ela digitar vai para a busca, não para o editor
