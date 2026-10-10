## Purpose

Definir o que a IDE da missão, o painel da equipe, o placar do telão e a visão admin mostram sobre o veredito da submissão e a pontuação no modelo de exemplos + extras.

## ADDED Requirements

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
Na visão admin, o log de submissões SHALL mostrar, para cada submissão, horário, equipe, módulo, tentativa, status, exemplos aprovados/total, extras aprovados/total, pontos, caracteres e participantes.

#### Scenario: Submissão parcial no log
- **WHEN** o admin abre `/placar.html?admin=...` depois de uma submissão aceita com 14/20 extras
- **THEN** a linha mostra exemplos 3/3, extras 14/20, os pontos e os caracteres dessa submissão

### Requirement: Textos da IDE sobre o juiz
Os textos da IDE que hoje falam em "testes ocultos" SHALL falar em "testes extras" e explicar a regra: enviar exige passar em todos os exemplos, os pontos dependem dos extras e o menor código desempata.

#### Scenario: Aviso no modal de submissão
- **WHEN** a equipe abre o modal de submissão
- **THEN** o aviso fala em testes de exemplo e testes extras, não em testes ocultos
