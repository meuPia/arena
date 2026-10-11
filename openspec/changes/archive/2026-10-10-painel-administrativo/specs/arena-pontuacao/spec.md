## ADDED Requirements

### Requirement: Pontos efetivos com ajuste da banca
Quando uma submissão aceita tem ajuste de pontos, os **pontos efetivos** dela SHALL ser os ajustados. Sem ajuste, são os pontos calculados. A submissão SHALL contar como **completa efetiva** só se for completa pelo juiz **e** os pontos efetivos forem iguais aos pontos do módulo. Pontos e completo efetivos MUST valer em todos os cálculos: melhor submissão do módulo, total da equipe, módulos completos, soma de caracteres dos completos, horário da última melhoria, desbloqueio, painel, missão e placar vivo e congelado. O ajuste vale pelo horário da submissão: uma submissão anterior ao freeze, ajustada depois dele, aparece ajustada no placar congelado. O motivo do ajuste MUST NOT ser mostrado à equipe nem no placar público.

#### Scenario: Ajuste muda a melhor submissão
- **WHEN** a Equipe 2 tem em B01 uma submissão completa (10 pts) e uma parcial (7 pts), e a completa é ajustada para 0
- **THEN** a melhor submissão de B01 passa a ser a parcial, B01 vale 7 pts e não conta como completo

#### Scenario: Ajuste aparece no placar congelado
- **WHEN** uma submissão feita antes do freeze é ajustada de 10 para 0 durante o freeze
- **THEN** o placar público congelado já mostra os pontos sem aqueles 10

#### Scenario: Desfazer volta ao cálculo do juiz
- **WHEN** o ajuste de uma submissão é desfeito
- **THEN** a melhor submissão, o total e o placar voltam a usar os pontos calculados

## MODIFIED Requirements

### Requirement: Placar a partir das submissões aceitas
O placar, vivo ou congelado, SHALL ser calculado a partir do registro das submissões aceitas, aplicando os ajustes de pontos da banca. Cada registro tem um identificador, horário, equipe, módulo, pontos, completo e caracteres, e MUST NOT conter código-fonte. O log completo de submissões, com código-fonte e participantes, SHALL ficar separado e só pode ser lido por admin e juiz (sessão do painel) ou pelo acesso de emergência.

#### Scenario: Placar sem código
- **WHEN** o placar público é pedido
- **THEN** a resposta não contém código-fonte nem participantes

### Requirement: Freeze
A partir de `freezeMinutos` antes do fim, o placar público SHALL mostrar o estado calculado só com as submissões aceitas até o horário do freeze, inclusive a melhor submissão de cada módulo até esse momento. Isso vale mesmo que a equipe melhore depois. O placar vivo MUST aparecer no modo ensaio, com `ARENA_REVELAR=1` ou no **placar real**. O placar real é pedido explicitamente pela seção "Placar real" do painel, por admin ou juiz (sessão do painel) ou pelo acesso de emergência. O placar público (`/placar.html`) MUST seguir o freeze mesmo num navegador com sessão da banca.

#### Scenario: Melhoria depois do freeze
- **WHEN** uma equipe tem 7 pts em B01 antes do freeze e chega a 10 pts depois do freeze
- **THEN** o placar público congelado mostra 7 pts em B01, e o placar real mostra 10 pts

#### Scenario: Revelação
- **WHEN** `ARENA_REVELAR=1` está definido depois do fim
- **THEN** o placar público mostra 10 pts em B01

#### Scenario: Juiz vê o placar real
- **WHEN** um juiz logado abre o placar real pelo painel durante o freeze
- **THEN** ele vê o placar vivo

#### Scenario: Telão logado continua congelado
- **WHEN** o computador do telão tem uma sessão de admin e abre `/placar.html` durante o freeze
- **THEN** o telão mostra o placar congelado
