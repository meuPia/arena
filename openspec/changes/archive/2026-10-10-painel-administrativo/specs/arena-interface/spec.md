## MODIFIED Requirements

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
