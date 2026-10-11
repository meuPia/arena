## ADDED Requirements

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
