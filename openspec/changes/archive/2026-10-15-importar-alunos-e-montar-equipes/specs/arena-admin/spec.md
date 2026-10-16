## ADDED Requirements

### Requirement: Importação de alunos
O admin SHALL poder importar alunos de uma vez, enviando um arquivo CSV ou colando uma listagem no painel. Cada
linha descreve um aluno com nome e semestre (ou fase) e, opcionalmente, e-mail. O painel SHALL aceitar:

- CSV separado por vírgula, ponto e vírgula ou tabulação, com ou sem linha de cabeçalho; com cabeçalho, as
  colunas são reconhecidas pelo nome (`nome`; `semestre` ou `fase`; `email` ou `e-mail`), em qualquer ordem;
- listagem colada com uma linha por aluno, no formato `Nome, 2`, `Nome; 2º`, `Nome (2º)` ou `Nome<TAB>2`.

O semestre SHALL ser reconhecido a partir de formas como `2`, `2º`, `2°`, `2o`, `2º semestre` ou `fase 2`, e
gravado no formato curto `2º`. A importação SHALL ter duas etapas: primeiro uma prévia, sem gravar nada, com os
alunos que serão criados e as linhas ignoradas com o motivo (sem nome, nome com mais de 60 caracteres, semestre
não reconhecido, e-mail inválido, nome repetido na listagem ou já cadastrado); depois, só com a confirmação do
admin, a gravação. Nomes repetidos MUST ser comparados sem diferenciar maiúsculas, acentos e espaços extras.
Os alunos importados SHALL ficar sem equipe. Uma importação MUST aceitar no máximo 500 linhas. A ação MUST ser
só do papel `admin` e a confirmação SHALL ir para a auditoria com a quantidade de alunos criados.

#### Scenario: Prévia de uma planilha
- **WHEN** o admin envia um CSV com cabeçalho `Nome;Fase;E-mail` e 40 alunos, um deles com fase `semestre 9x`
- **THEN** a prévia mostra 39 alunos a criar, com o semestre no formato `2º`/`4º`/`6º`, e 1 linha ignorada com
  o motivo "semestre não reconhecido", e nada é gravado

#### Scenario: Confirmar a importação
- **WHEN** o admin confirma a prévia
- **THEN** os 39 alunos aparecem na aba Participantes como "sem equipe" e a auditoria registra "importar
  participantes" com "39 aluno(s)"

#### Scenario: Listagem colada
- **WHEN** o admin cola as linhas `Ana Souza, 2`, `Bruno Lima (6º)` e `Carla Dias	4`
- **THEN** a prévia mostra Ana Souza (2º), Bruno Lima (6º) e Carla Dias (4º)

#### Scenario: Aluno já cadastrado
- **WHEN** a listagem tem `ana souza, 2` e "Ana Souza" já é participante
- **THEN** a linha é ignorada com o motivo "já cadastrado" e não cria um segundo participante

#### Scenario: Juiz não importa
- **WHEN** um juiz chama a importação de alunos
- **THEN** a API responde 403 sem gravar nada

### Requirement: Montagem automática de equipes
O admin SHALL poder montar equipes automaticamente a partir dos participantes **sem equipe**, informando o
tamanho desejado da equipe (de 2 a 10). O painel SHALL criar `teto(alunos ÷ tamanho)` equipes novas e distribuir
os alunos de forma nivelada:

- os tamanhos das equipes MUST diferir em no máximo 1 e nenhuma equipe MUST passar do tamanho informado;
- os alunos de cada semestre MUST ficar espalhados entre as equipes (a quantidade de um mesmo semestre em duas
  equipes difere em no máximo 1), começando pelo semestre mais avançado, de modo que os alunos do 6º fiquem em
  equipes diferentes e as equipes sem aluno do 6º recebam primeiro os do 4º;
- dentro de cada semestre, a ordem é sorteada.

As equipes novas SHALL receber nomes temáticos da lista de palavras dos códigos de acesso (Orion, Vega, Lyra…),
pulando nomes já usados, com o código de acesso começando pela mesma palavra; se as palavras acabarem, o nome
recebe um número (`Orion 2`). Equipes existentes e participantes que já têm equipe MUST NOT mudar.

A montagem SHALL ter duas etapas: uma prévia, sem gravar nada, com as equipes propostas e a contagem por
semestre de cada uma, e um botão "Sortear de novo"; e a confirmação, que grava exatamente a prévia mostrada.
Se os participantes sem equipe mudarem entre a prévia e a confirmação, a confirmação MUST ser recusada pedindo
uma nova prévia. Com menos alunos sem equipe do que o tamanho informado, a montagem cria uma única equipe. Sem
alunos sem equipe, a montagem MUST ser recusada com uma mensagem. A ação MUST ser só do papel `admin`, e a
confirmação SHALL ir para a auditoria com a quantidade de equipes e de alunos, sem códigos de acesso.

#### Scenario: Equipes niveladas
- **WHEN** há 40 alunos sem equipe (8 do 6º, 14 do 4º e 18 do 2º) e o admin monta equipes de 5
- **THEN** a prévia mostra 8 equipes de 5, cada uma com 1 aluno do 6º, 1 ou 2 do 4º e 2 ou 3 do 2º

#### Scenario: Poucos alunos avançados
- **WHEN** há 13 alunos sem equipe (2 do 6º, 4 do 4º e 7 do 2º) e o admin monta equipes de 4
- **THEN** a prévia mostra 4 equipes com 3 ou 4 alunos; nenhuma tem dois alunos do 6º, cada equipe tem um aluno
  do 4º, e nenhuma equipe tem só alunos do 2º

#### Scenario: Sortear de novo
- **WHEN** o admin clica em "Sortear de novo"
- **THEN** a prévia mostra outra distribuição que segue as mesmas regras, e nada foi gravado

#### Scenario: Confirmar a montagem
- **WHEN** o admin confirma a prévia
- **THEN** as equipes aparecem na aba Equipes com os nomes e os integrantes mostrados na prévia, cada uma com
  código de acesso, e a equipe consegue entrar na Arena com ele na hora

#### Scenario: Equipes existentes intactas
- **WHEN** já existem as equipes Orion e Vega e há 10 alunos sem equipe montados em equipes de 5
- **THEN** são criadas duas equipes novas, com nomes diferentes de Orion e Vega, e Orion e Vega continuam com os
  mesmos integrantes e códigos

#### Scenario: Prévia desatualizada
- **WHEN** outro admin importa mais alunos depois da prévia e o admin confirma a prévia antiga
- **THEN** a confirmação é recusada pedindo uma nova prévia, e nada é gravado

## MODIFIED Requirements

### Requirement: Participantes
O admin SHALL poder cadastrar, editar e remover participantes. Cada participante tem nome (obrigatório), semestre (texto curto, por exemplo `2º`) e e-mail (opcional), e pertence a no máximo uma equipe: um participante SHALL poder ficar sem equipe (por exemplo, logo depois de importado). Mover um participante para outra equipe, ou tirá-lo da equipe, SHALL ser permitido. Na hora de submeter, a lista "quem trabalhou" de cada equipe SHALL mostrar os participantes dela como `Nome (semestre)`; participantes sem equipe MUST NOT aparecer na lista de nenhuma equipe. Na aba Participantes, os sem equipe SHALL aparecer primeiro, identificados como "sem equipe", com a quantidade total. Mudanças nos participantes MUST NOT alterar submissões já feitas.

#### Scenario: Participante aparece na submissão
- **WHEN** o admin cadastra "Ana", do `2º`, na Equipe 1
- **THEN** o modal de submissão da Equipe 1 lista "Ana (2º)"

#### Scenario: Participante sem equipe
- **WHEN** o admin cadastra "Bruno", do `6º`, escolhendo "Sem equipe"
- **THEN** Bruno aparece na aba Participantes como "sem equipe" e não aparece no modal de submissão de nenhuma
  equipe

### Requirement: Cadastro de equipes
O admin SHALL poder criar uma equipe informando o nome, editar o nome e excluir a equipe. O nome é obrigatório, tem até 40 caracteres e MUST ser único (sem diferenciar maiúsculas). A exclusão MUST ser recusada se a equipe tiver alguma submissão; ao excluir, os participantes da equipe SHALL voltar a ficar sem equipe (não são apagados). Equipes e participantes SHALL ficar no banco da arena, e criar ou editar uma equipe MUST NOT exigir redeploy.

#### Scenario: Nova equipe
- **WHEN** o admin cria a equipe "Orion"
- **THEN** a equipe aparece na listagem com um código de acesso gerado e consegue entrar na Arena com esse código na hora

#### Scenario: Nome repetido
- **WHEN** o admin tenta criar a equipe "orion" com "Orion" já cadastrada
- **THEN** o cadastro é recusado com a mensagem de nome já usado

#### Scenario: Excluir equipe com submissões
- **WHEN** o admin tenta excluir uma equipe que já submeteu
- **THEN** a exclusão é recusada

#### Scenario: Excluir equipe devolve os participantes
- **WHEN** o admin exclui a equipe Lyra, sem submissões, com 5 integrantes
- **THEN** a equipe some da listagem e os 5 participantes aparecem como "sem equipe", prontos para uma nova
  montagem
