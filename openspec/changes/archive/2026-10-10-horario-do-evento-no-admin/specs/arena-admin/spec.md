## ADDED Requirements

### Requirement: Horário do evento pelo painel
O admin SHALL poder definir, numa seção Evento do painel, a data e a hora de início do evento, no fuso do evento
(o do `inicio` de `arena/config.json`). O fim SHALL ser o início mais a duração configurada no arquivo (`fim -
inicio` de `arena/config.json`), e o freeze continua sendo os `freezeMinutos` finais. O horário salvo SHALL valer
para abertura das missões, submissões, freeze, placar e relógios de todas as páginas, em no máximo 30 segundos.
Sem horário salvo, vale o do arquivo. O admin SHALL poder voltar ao horário do arquivo. Juízes SHALL ver o horário
efetivo e de onde ele vem, mas MUST NOT alterá-lo. Data inválida MUST ser recusada. Toda alteração SHALL entrar na
auditoria com o horário antigo e o novo. O horário salvo pertence à rodada (`ARENA_PREFIXO`): um ensaio não muda o
horário do evento.

#### Scenario: Adiar o início
- **WHEN** o arquivo diz início 19h10 e fim 21h50 e o admin salva início 19h30 do mesmo dia
- **THEN** as missões abrem às 19h30, o fim passa a 22h10 e o placar congela às 21h50

#### Scenario: Voltar ao arquivo
- **WHEN** o admin escolhe voltar ao horário do arquivo
- **THEN** o início e o fim voltam a ser os de `arena/config.json`

#### Scenario: Juiz não altera
- **WHEN** um juiz tenta salvar o horário do evento
- **THEN** a ação é recusada com "Seu perfil não pode fazer isso."

#### Scenario: Data inválida
- **WHEN** o admin envia uma data vazia ou mal formada para salvar
- **THEN** a ação é recusada e o horário efetivo não muda

#### Scenario: Auditoria
- **WHEN** o admin muda o início de 19h10 para 19h30
- **THEN** a auditoria registra "horário do evento" com o início antigo e o novo
