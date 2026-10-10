# arena-pontuacao Specification

## Purpose
Definir como as submissões das equipes viram pontos na Code Arena: o que é aceito, quanto cada módulo vale, qual submissão conta, como os níveis se desbloqueiam e como o placar é ordenado e congelado.

## Requirements

### Requirement: Tentativa e cooldown
Toda submissão que passa pelas checagens de janela, nível liberado e cooldown SHALL contar como tentativa daquele módulo, qualquer que seja o veredito: `aceito`, `reprovado_exemplos`, `erro_compilacao` ou `erro_execucao`. A tentativa MUST ser registrada antes do julgamento. As 3 primeiras tentativas de um módulo são livres. A partir daí, cada nova submissão MUST esperar 180 s desde a anterior. Os dois valores vêm de `cooldown` em `arena/config.json`.

#### Scenario: Reprovação nos exemplos conta como tentativa
- **WHEN** uma equipe faz 3 submissões `reprovado_exemplos` em B01 e tenta a 4ª logo em seguida
- **THEN** a resposta tem status `cooldown` e o tempo de espera restante

### Requirement: Aceitação
Uma submissão SHALL ser aceita somente quando o veredito do juiz for `aceito`, ou seja, quando passar em 100% dos testes de exemplo. A equipe MAY enviar sem passar em todos os extras. Submissões não aceitas MUST NOT pontuar nem alterar a melhor submissão do módulo.

#### Scenario: Aceita com extras parciais
- **WHEN** um código passa em todos os exemplos e em 14 de 20 extras
- **THEN** a submissão é aceita e pontua

#### Scenario: Não aceita
- **WHEN** um código passa em 2 de 3 exemplos
- **THEN** a submissão não pontua e a melhor submissão do módulo continua a mesma

### Requirement: Pontuação do módulo
O modo de pontuação SHALL vir de `pontuacao.modo` em `arena/config.json`, e o padrão é `proporcional`.
- `proporcional`: `pontos = piso(pontosDoModulo × extrasAprovados / totalExtras)`.
- `completo`: `pontos = pontosDoModulo` se a submissão estiver completa, senão `0`.

Uma submissão aceita SHALL ser **completa** quando passa em 100% dos extras.

#### Scenario: Parcial proporcional
- **WHEN** no modo `proporcional` uma submissão aceita num módulo de 10 pts passa em 14 de 20 extras
- **THEN** ela vale 7 pts e não é completa

#### Scenario: Arredondamento para baixo
- **WHEN** no modo `proporcional` uma submissão aceita num módulo de 35 pts passa em 19 de 20 extras
- **THEN** ela vale 33 pts

#### Scenario: Completa
- **WHEN** uma submissão aceita passa em 20 de 20 extras
- **THEN** ela vale todos os pontos do módulo e é completa

### Requirement: Melhor submissão por módulo
Para cada equipe e módulo, a pontuação que vale SHALL ser a da melhor submissão aceita. A melhor é a de mais pontos. No empate, vence a de menos caracteres significativos. Se ainda empatar, vence a mais antiga. Uma submissão pior MUST NOT reduzir a pontuação de um módulo. Novas submissões SHALL continuar permitidas depois que o módulo estiver completo, sujeitas ao cooldown.

#### Scenario: Submissão pior não reduz
- **WHEN** uma equipe tem 7 pts em B01 e envia uma submissão aceita que vale 5 pts
- **THEN** B01 continua valendo 7 pts para a equipe

#### Scenario: Reduzir o código depois de completar
- **WHEN** uma equipe com B01 completo em 142 caracteres envia uma nova submissão completa com 118 caracteres
- **THEN** a submissão é aceita e B01 passa a registrar 118 caracteres, com os mesmos pontos

#### Scenario: Submissão completa maior não substitui
- **WHEN** uma equipe com B01 completo em 118 caracteres envia outra submissão completa com 130 caracteres
- **THEN** B01 continua registrando 118 caracteres

### Requirement: Desbloqueio de níveis
O desbloqueio SHALL seguir as quantidades de `desbloqueio` em `arena/config.json`, contando módulos por nível conforme `desbloqueioConta`:
- `aceito` (padrão): conta os módulos com pelo menos uma submissão aceita, inclusive parcial;
- `completo`: conta só os módulos completos.

#### Scenario: Parcial libera o nível seguinte
- **WHEN** com `desbloqueioConta = "aceito"` uma equipe tem B01 aceito parcial e B02 aceito completo
- **THEN** o nível Silver está liberado

#### Scenario: Modo completo
- **WHEN** com `desbloqueioConta = "completo"` uma equipe tem B01 parcial e B02 completo
- **THEN** o nível Silver continua bloqueado, com a dica "Recupere mais 1 Bronze para desbloquear."

### Requirement: Ordem do placar
O placar SHALL ordenar as equipes por estes critérios, nesta ordem:
1. total de pontos (soma das melhores submissões), decrescente;
2. número de módulos completos, decrescente;
3. soma dos caracteres significativos das melhores submissões dos módulos **completos**, crescente;
4. horário da última melhoria de pontuação, crescente. É o momento da última submissão aceita que aumentou o total de pontos da equipe. Reduzir caracteres não conta como melhoria, e equipes sem pontos ficam por último neste critério;
5. nome da equipe, crescente.

#### Scenario: Desempate por módulos completos
- **WHEN** as equipes A e B têm 40 pts, A com 3 módulos completos e B com 2
- **THEN** A fica à frente de B

#### Scenario: Desempate por caracteres
- **WHEN** as equipes A e B têm os mesmos pontos e módulos completos, A com 610 caracteres nos completos e B com 540
- **THEN** B fica à frente de A

#### Scenario: Desempate por horário
- **WHEN** as equipes A e B empatam em pontos, completos e caracteres, e A chegou à pontuação atual às 20h10 e B às 20h05
- **THEN** B fica à frente de A

#### Scenario: Redução de código não muda o horário
- **WHEN** uma equipe reduz os caracteres de um módulo completo às 21h00 sem mudar os pontos
- **THEN** o horário da última melhoria de pontuação dela continua o mesmo

### Requirement: Placar a partir das submissões aceitas
O placar, vivo ou congelado, SHALL ser calculado a partir do registro das submissões aceitas. Cada registro tem horário, equipe, módulo, pontos, completo e caracteres, e MUST NOT conter código-fonte. O log completo de submissões, com código-fonte e participantes, SHALL ficar separado e só para o admin.

#### Scenario: Placar sem código
- **WHEN** o placar público é pedido
- **THEN** a resposta não contém código-fonte nem participantes

### Requirement: Freeze
A partir de `freezeMinutos` antes do fim, o placar público SHALL mostrar o estado calculado só com as submissões aceitas até o horário do freeze, inclusive a melhor submissão de cada módulo até esse momento. Isso vale mesmo que a equipe melhore depois. O placar do admin, o modo ensaio e `ARENA_REVELAR=1` MUST mostrar o placar vivo.

#### Scenario: Melhoria depois do freeze
- **WHEN** uma equipe tem 7 pts em B01 antes do freeze e chega a 10 pts depois do freeze
- **THEN** o placar público congelado mostra 7 pts em B01 e o placar do admin mostra 10 pts

#### Scenario: Revelação
- **WHEN** `ARENA_REVELAR=1` está definido depois do fim
- **THEN** o placar público mostra 10 pts em B01

### Requirement: Estado da equipe no painel e na missão
O painel e a missão SHALL informar, para cada módulo, os pontos da melhor submissão, se está completo, os caracteres da melhor submissão, o número de tentativas e a espera do cooldown. O painel SHALL informar também o total de pontos da equipe (placar vivo).

#### Scenario: Painel com parcial
- **WHEN** a equipe tem B01 com 7 pts, não completo, em 3 tentativas
- **THEN** o painel devolve para B01 `pontos` 7, `completo` falso, a quantidade de caracteres e `tentativas` 3

### Requirement: Resposta da submissão
A resposta de uma submissão julgada SHALL trazer o veredito do juiz (status, exemplos, extras e, quando aceita, `completo`), os pontos e os caracteres desta submissão, os pontos, o `completo` e os caracteres da melhor submissão da equipe no módulo, o número da tentativa e a espera para a próxima.

#### Scenario: Submissão pior que a melhor
- **WHEN** uma equipe com 10/10 pts em B01 envia uma submissão aceita que vale 7 pts
- **THEN** a resposta mostra 7 pts para esta submissão e 10 pts como melhor da equipe em B01
