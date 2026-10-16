## ADDED Requirements

### Requirement: Desafios no banco
Os desafios SHALL ficar no banco da arena, num namespace de conteúdo definido por `ARENA_CONTEUDO` (padrão `conteudo`), independente do `ARENA_PREFIXO`. Assim, ensaio e evento usam os mesmos desafios. Cada desafio SHALL ter dois registros:
- **público**: código, id, módulo, problema técnico, nível, pontos, formato, tempo esperado, inspiração, título, descrição, código inicial e `testesPublicos`;
- **secreto**: `testesExtras` e `gabarito`.

Telas e respostas que não julgam MUST carregar só os registros públicos. A parte secreta é lida só para julgar uma submissão ou pelo painel de admin. Uma edição feita no banco SHALL valer para as equipes em até 30 segundos, sem redeploy.

#### Scenario: Desafio editado sem deploy
- **WHEN** um admin muda o enunciado de B01 no painel
- **THEN** as equipes passam a ver o enunciado novo em até 30 segundos, sem novo deploy

#### Scenario: Painel não carrega segredos
- **WHEN** uma equipe abre o painel de missões
- **THEN** o servidor não lê os testes extras nem os gabaritos para montar essa resposta

### Requirement: Repositório sem conteúdo secreto
O repositório de código MUST NOT conter testes extras, gabaritos, casos de borda nem implementações de referência dos desafios reais, nem na árvore atual nem no histórico do repositório público. O único conteúdo de desafio versionado SHALL ser o de `arena/exemplos/`.

#### Scenario: Varredura antes de publicar
- **WHEN** a varredura de vazamento roda na árvore que vai para o repositório público
- **THEN** nenhuma linha de teste extra nem trecho de gabarito dos desafios reais é encontrado

### Requirement: Desafios de exemplo
`arena/exemplos/` SHALL ter desafios fictícios e públicos, no mesmo formato (com gabarito e entre 15 e 25 testes extras), cobrindo os quatro níveis em quantidade suficiente para as regras de desbloqueio da config. Com o store `Local` (desenvolvimento e testes) e nenhum desafio no banco, a arena SHALL usar os exemplos. Com Supabase ou Upstash, a arena MUST NOT cair nos exemplos: um banco sem desafios mostra a arena sem missões.

#### Scenario: Desenvolvimento local
- **WHEN** alguém roda `npm run local` sem banco configurado
- **THEN** o painel mostra os desafios de exemplo

#### Scenario: Produção sem desafios
- **WHEN** o Supabase está configurado e ainda não tem desafios
- **THEN** a arena não mostra missões de exemplo

### Requirement: Importação inicial dos desafios
A carga inicial SHALL ser feita por um script do repositório **privado** (`scripts/popular_desafios.py`, sobre `api/_lib/conteudo.py`), que nunca é publicado. Ele SHALL ler desafios no formato antigo (`<COD>.json` mais o gabarito em `<COD>.por` ou no próprio JSON) ou um arquivo exportado pelo painel, validar cada um com o juiz e gravá-los no banco configurado (parte pública e parte secreta). Desafios inválidos MUST NOT ser gravados. Rodar a importação de novo com os mesmos dados MUST deixar o banco igual.

#### Scenario: Repositório público sem scripts de carga
- **WHEN** os scripts do repositório público são listados
- **THEN** não há script de carga, importação ou varredura de desafios reais

#### Scenario: Importar os 9 desafios
- **WHEN** o script roda sobre `arena/desafios` e `arena/gabaritos` do repositório privado, com o Supabase configurado
- **THEN** os 9 desafios ficam no banco, e o `npm run validar` contra o banco termina com sucesso

## MODIFIED Requirements

### Requirement: Campos de teste do desafio
Cada desafio SHALL ter `testesPublicos` (os testes de exemplo, que o botão Rodar do Lab executa no navegador) no registro público, e `testesExtras` (a bateria de submissão) e `gabarito` no registro secreto. O campo `testesOcultos` MUST NOT existir. Cada linha de teste é uma chamada `esperar_*`.

#### Scenario: Campo renomeado
- **WHEN** os desafios do banco são carregados
- **THEN** todos têm `testesPublicos`, `testesExtras` e `gabarito`, e nenhum tem `testesOcultos`

### Requirement: Testes extras nunca saem do servidor
`testesExtras` e `gabarito` MUST NOT aparecer em nenhuma resposta da API às equipes nem no placar. O desafio que a equipe recebe SHALL conter só os campos públicos. A única exceção é o painel administrativo: um **admin** logado (ou o acesso de emergência) SHALL poder ler e editar esses campos. Juízes MUST NOT recebê-los.

#### Scenario: Missão sem extras
- **WHEN** uma equipe abre a missão S01
- **THEN** a resposta não contém `testesExtras`, `gabarito` nem nenhum texto de teste extra

#### Scenario: Juiz não lê segredos
- **WHEN** um juiz pede os dados completos de um desafio pela API do painel
- **THEN** a resposta é 403

### Requirement: Tamanho e dificuldade da bateria extra
A bateria extra de cada desafio SHALL ter entre 15 e 25 testes, com a meta de cerca de 20. Ela inclui casos de borda e casos grandes ou aleatórios, nos limites do desafio, por exemplo: listas de até 300 itens, matrizes de até 12×12, números com até 80 dígitos e rotas de até 120 passos. Os literais de texto dos testes MUST NOT conter aspas duplas nem barra invertida.

#### Scenario: Bateria ampliada
- **WHEN** a bateria extra de qualquer desafio é contada
- **THEN** ela tem entre 15 e 25 linhas `esperar_*`

### Requirement: Validação dos desafios
`npm run validar` SHALL julgar com o juiz real os desafios do store configurado: o banco, quando Supabase ou Upstash estão configurados, ou os exemplos, com o store `Local`. A mesma validação SHALL estar disponível no painel para um desafio ou para todos. Ela falha se alguma destas condições não valer:
- o gabarito tem veredito `aceito` e completo (100% dos exemplos e dos extras);
- o código inicial **não** é completo;
- nenhum teste do gabarito chega perto do limite por teste (margem: no máximo metade do limite);
- a bateria extra respeita o tamanho do requisito anterior.

#### Scenario: Gabarito lento
- **WHEN** um teste extra faz o gabarito levar mais da metade do limite por teste
- **THEN** a validação aponta o desafio e o teste e termina com erro

#### Scenario: Tudo certo
- **WHEN** todos os desafios estão corretos
- **THEN** a validação imprime uma linha `OK` por desafio, com exemplos e extras do gabarito e do código inicial, e termina com sucesso

## REMOVED Requirements

### Requirement: Geração determinística
**Reason**: O gerador (`scripts/gerar_testes_extras.py`) tem as soluções de referência e a semente fixa, e com ele qualquer pessoa recria a bateria extra. Ele não pode ficar no repositório público. A bateria passa a ser guardada pronta no banco e editada pelo painel.
**Migration**: As baterias atuais vão para o banco com `scripts/popular_desafios.py`, no repositório privado. Para gerar uma bateria nova, use o gerador que fica no repositório privado arquivado e importe o resultado (pelo script ou pelo painel).
