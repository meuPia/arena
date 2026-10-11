# arena-admin Specification

## Purpose
Dar à banca da Code Arena um painel web para organizar o evento sem redeploy: equipes e códigos de acesso, participantes, perfis de admin e juiz, desafios, acompanhamento das submissões, ajuste de pontos e auditoria de tudo o que foi feito.

## Requirements

### Requirement: Cadastro de desafios
O painel SHALL ter uma seção **Desafios**, só para admin, que lista os desafios (código, nível, pontos, título, número de testes extras e resultado da última validação) e permite criar e editar todos os campos: código, módulo, problema técnico, nível, pontos, formato, tempo esperado, inspiração, título, descrição (markdown), código inicial, testes de exemplo, testes extras e gabarito. O código do desafio é obrigatório, único e não pode ser alterado depois de criado. O nível MUST ser um dos níveis da config, e os pontos um inteiro positivo. Ao salvar, os testes MUST ser conferidos: só linhas `esperar_*`, sem aspas duplas nem barra invertida dentro de textos. Editar um desafio que já recebeu submissões SHALL pedir confirmação, avisando que a mudança não rejulga as submissões antigas. A auditoria SHALL registrar a criação e a edição com o código do desafio e a lista dos campos alterados, sem o conteúdo.

#### Scenario: Criar desafio
- **WHEN** o admin cria o desafio B04 no nível Bronze, com 10 pts e todos os campos preenchidos
- **THEN** B04 aparece para as equipes no nível Bronze em até 30 segundos

#### Scenario: Juiz não vê a seção
- **WHEN** um juiz entra no painel
- **THEN** a seção Desafios não aparece, e as ações de desafio respondem 403

#### Scenario: Edição auditada sem conteúdo
- **WHEN** o admin altera os testes extras de S03
- **THEN** a auditoria registra "desafio editado: S03 (testesExtras)" sem o texto dos testes

### Requirement: Validação de desafios pelo painel
O admin SHALL poder validar um desafio, ou todos, com o juiz real, pelo painel, com os mesmos critérios do `npm run validar`. O resultado mostra, por desafio, o veredito do gabarito (exemplos e extras), o veredito do código inicial, o maior tempo por teste e os erros encontrados. O painel SHALL também permitir validar o formulário antes de salvar.

#### Scenario: Gabarito quebrado
- **WHEN** o admin valida um desafio cujo gabarito falha em 2 extras
- **THEN** o painel mostra "gabarito não é aceito e completo" com extras 18/20

### Requirement: Exportação e importação de desafios
O admin SHALL poder exportar todos os desafios (partes pública e secreta) num arquivo JSON e importar um arquivo nesse formato. A importação mostra o que será criado e o que será substituído, pede confirmação, valida cada desafio com o juiz e grava só os válidos. Exportação e importação SHALL ir para a auditoria.

#### Scenario: Backup antes do evento
- **WHEN** o admin exporta os desafios
- **THEN** ele baixa um JSON com os 9 desafios, inclusive testes extras e gabaritos, que pode ser reimportado em outro banco

### Requirement: Painel por papel
O painel administrativo SHALL ficar em `/admin.html`. Sem sessão, ele mostra a tela de login com os provedores configurados. Com sessão, ele mostra o nome, o papel e o botão de sair, além das seções permitidas ao papel:
- `admin`: Equipes, Participantes, Perfis, Submissões, Placar real e Auditoria;
- `juiz`: Submissões e Placar real.

Seções fora do papel MUST NOT aparecer, e as ações correspondentes MUST ser recusadas pelo servidor.

#### Scenario: Juiz no painel
- **WHEN** um juiz entra no painel
- **THEN** ele vê só as seções Submissões e Placar real

### Requirement: Cadastro de equipes
O admin SHALL poder criar uma equipe informando o nome, editar o nome e excluir a equipe. O nome é obrigatório, tem até 40 caracteres e MUST ser único (sem diferenciar maiúsculas). A exclusão MUST ser recusada se a equipe tiver alguma submissão. Equipes e participantes SHALL ficar no banco da arena, e criar ou editar uma equipe MUST NOT exigir redeploy.

#### Scenario: Nova equipe
- **WHEN** o admin cria a equipe "Orion"
- **THEN** a equipe aparece na listagem com um código de acesso gerado e consegue entrar na Arena com esse código na hora

#### Scenario: Nome repetido
- **WHEN** o admin tenta criar a equipe "orion" com "Orion" já cadastrada
- **THEN** o cadastro é recusado com a mensagem de nome já usado

#### Scenario: Excluir equipe com submissões
- **WHEN** o admin tenta excluir uma equipe que já submeteu
- **THEN** a exclusão é recusada

### Requirement: Listagem de equipes
A listagem de equipes SHALL mostrar, para cada equipe, nome, código de acesso, integrantes, pontos atuais (placar vivo), módulos completos, número de submissões e horário da última submissão, em ordem de nome. O admin SHALL ter uma versão para impressão com nome, código e integrantes de cada equipe, para distribuir os códigos.

#### Scenario: Listagem com pontos
- **WHEN** a Equipe 1 tem 15 pts e 4 submissões
- **THEN** a linha da Equipe 1 mostra 15 pts, 4 submissões e o horário da última

### Requirement: Códigos de acesso das equipes
Toda equipe nova SHALL receber um código no formato `PALAVRA-XXXXXX`, em que `XXXXXX` são 6 caracteres aleatórios de um alfabeto sem caracteres ambíguos (sem `0`, `O`, `1` e `I`). O código é gerado com um gerador criptograficamente seguro e MUST ser único entre as equipes. O admin SHALL poder regenerar o código de uma equipe, o que invalida o anterior e as sessões abertas com ele. O código MUST aparecer só para admins.

#### Scenario: Regenerar código
- **WHEN** o admin regenera o código da Equipe 1
- **THEN** o código antigo deixa de entrar, o novo entra, e a listagem mostra o novo

### Requirement: Importação das equipes do arquivo
Enquanto o banco não tiver nenhuma equipe, a arena SHALL continuar usando as equipes de `ARENA_EQUIPES` ou de `arena/equipes.json` (o comportamento atual). O admin SHALL ter uma ação para importar essas equipes para o banco, mantendo id, nome, código e integrantes. A importação MUST ser recusada se o banco já tiver equipes. Depois que o banco tem equipes, só ele vale.

#### Scenario: Importar equipes do arquivo
- **WHEN** o banco não tem equipes e o admin importa as equipes de `ARENA_EQUIPES`
- **THEN** as equipes passam a ser editáveis no painel e continuam entrando com os mesmos códigos

### Requirement: Participantes
O admin SHALL poder cadastrar, editar e remover participantes. Cada participante tem nome (obrigatório), semestre (texto curto, por exemplo `2º`) e e-mail (opcional), e pertence a exatamente uma equipe. Mover um participante para outra equipe SHALL ser permitido. Na hora de submeter, a lista "quem trabalhou" de cada equipe SHALL mostrar os participantes dela como `Nome (semestre)`. Mudanças nos participantes MUST NOT alterar submissões já feitas.

#### Scenario: Participante aparece na submissão
- **WHEN** o admin cadastra "Ana", do `2º`, na Equipe 1
- **THEN** o modal de submissão da Equipe 1 lista "Ana (2º)"

### Requirement: Perfis da banca
O admin SHALL poder cadastrar, editar e remover perfis da banca. Cada perfil tem nome, e-mail (obrigatório e único), login do GitHub (opcional e único) e papel (`admin` ou `juiz`). O root SHALL aparecer na lista como somente leitura.

#### Scenario: Cadastrar juiz
- **WHEN** o admin cadastra um juiz com o e-mail `prof@exemplo.edu`
- **THEN** essa pessoa consegue entrar no painel com a conta Microsoft ou Google desse e-mail e tem papel `juiz`

#### Scenario: Root protegido
- **WHEN** alguém tenta remover, editar ou rebaixar o root pelo painel ou pela API
- **THEN** a ação é recusada

### Requirement: Log de submissões
Admin e juiz SHALL ver o log de submissões, da mais recente para a mais antiga, com filtros por equipe, módulo e status. Cada linha mostra horário, equipe, módulo, tentativa, status, exemplos, extras, pontos calculados, pontos efetivos (com o ajuste, se houver), caracteres e participantes. Ao abrir uma submissão, aparece o código-fonte enviado. O log MUST ser servido só a sessões de admin ou juiz, ou ao acesso de emergência.

#### Scenario: Ver código de uma submissão
- **WHEN** um juiz abre uma submissão no log
- **THEN** ele vê o código-fonte enviado e os participantes marcados

### Requirement: Ajuste de pontos
Admin e juiz SHALL poder ajustar os pontos de uma submissão **aceita**, informando um inteiro de `0` aos pontos do módulo e um motivo com pelo menos 5 caracteres. Um novo ajuste substitui o anterior, e desfazer o ajuste volta aos pontos calculados pelo juiz. Ajustes em submissões não aceitas, valores fora da faixa ou motivo vazio MUST ser recusados. O log SHALL mostrar os pontos calculados, os pontos ajustados, o motivo, o autor e o horário do ajuste.

#### Scenario: Zerar submissão após sorteio de explicação
- **WHEN** um juiz ajusta para 0 os pontos da submissão completa da Equipe 2 em B01, com o motivo "integrante sorteado não explicou a solução"
- **THEN** a Equipe 2 perde os 10 pts de B01 no placar, e o log mostra 10 → 0 com o motivo e o nome do juiz

#### Scenario: Ajuste fora da faixa
- **WHEN** alguém tenta ajustar uma submissão de B01 (10 pts) para 12
- **THEN** o ajuste é recusado

#### Scenario: Desfazer ajuste
- **WHEN** um admin desfaz o ajuste da submissão da Equipe 2
- **THEN** a submissão volta a valer os pontos calculados pelo juiz

### Requirement: Auditoria
Toda ação do painel SHALL ser registrada com horário, autor (nome, papel e provedor, ou `token de emergência`), ação, alvo e um resumo dos dados. Isso inclui login, login recusado, logout, criação, edição e exclusão de equipe, participante ou perfil, código gerado ou regenerado, importação e ajuste ou desfazer de pontos. O código-fonte e segredos MUST NOT entrar no resumo. O admin SHALL ver a auditoria, da mais recente para a mais antiga.

#### Scenario: Código regenerado auditado
- **WHEN** o root regenera o código da Equipe 1
- **THEN** a auditoria mostra o horário, o root, "código regenerado" e "Equipe 1"

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
