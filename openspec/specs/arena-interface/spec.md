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
