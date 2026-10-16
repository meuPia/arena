## Context

Equipes e participantes vivem no banco (`conteudo:equipes`, `conteudo:participantes`, hashes JSON acessados por
`store` com a interface mínima `hgetall/hset/hdel`, sem transação). Os casos de uso do painel ficam em
`api/_lib/admin.py`, com `PERMISSOES` por ação, POST só JSON e da mesma origem, e auditoria em toda gravação.
Hoje `_salvar_participante` exige uma equipe existente, e `_excluir_equipe` apaga os participantes da equipe.
`arena.equipes()` monta `integrantes` filtrando `p["equipe"] == eid`, então um participante com `equipe: ""` já
fica fora de todas as equipes. Já existe um fluxo de duas etapas (prévia → `confirmar`) em
`_importar_desafios`, e os códigos de acesso usam a lista `arena.PALAVRAS` (ORION, VEGA, LYRA…).

## Goals / Non-Goals

**Goals:**
- Lógica de leitura e de distribuição em funções puras, testadas sem banco nem HTTP.
- Prévia determinística: o que o admin vê é exatamente o que é gravado.
- Nenhuma mudança fora do painel da banca (IDE, juiz, placar, rotas das equipes).

**Non-Goals:**
- Ler `.xlsx` (o admin exporta a planilha como CSV ou copia e cola as colunas).
- Rebalancear equipes que já existem ou mexer em quem já tem equipe.
- Restrições por pessoa ("estes dois juntos/separados"); o ajuste fino é manual, movendo alunos de equipe.

## Decisions

### 1. Módulo puro `api/_lib/turmas.py`
- `normalizar_semestre(texto) -> "2º" | None`: pega o primeiro número de 1 a 12 em formas como `2`, `2º`, `2°`,
  `2o`, `2º semestre`, `fase 2`, `2ª fase`; qualquer outra coisa → `None`.
- `chave_nome(nome)`: `casefold`, sem acentos (`unicodedata` NFKD), espaços colapsados — usada para repetidos.
- `ler_listagem(texto) -> (alunos, ignoradas)`: remove BOM; detecta o separador pela primeira linha não vazia
  (tabulação > ponto e vírgula > vírgula); se a primeira linha tem `nome` e `semestre`/`fase`, é cabeçalho e
  define as colunas (com `email`/`e-mail` opcional); sem cabeçalho, a ordem é nome, semestre, e-mail. Linha sem
  separador no formato `Nome (2º)` também vale. Cada linha ignorada leva número e motivo. Máximo de 500 linhas.
- `distribuir(alunos, tamanho, semente) -> [[aluno, …], …]` (decisão 2).

**Por quê no servidor:** a mesma regra vale para a prévia e para a confirmação, com pytest; o navegador só lê o
arquivo como texto. **Alternativa descartada:** parser no `admin.js` — duplicaria a validação.

### 2. Distribuição: rodízio contínuo por semestre
`T = teto(n ÷ tamanho)` equipes. Os alunos são agrupados por semestre, do maior número para o menor (semestre não
reconhecido, possível em cadastro manual antigo, vai por último); dentro de cada grupo, a ordem é embaralhada com
`random.Random(semente)`. A lista concatenada é distribuída em rodízio contínuo: o aluno `i` vai para a equipe
`i mod T`, **sem reiniciar** o rodízio ao trocar de semestre.

Propriedades (cobertas por teste, inclusive por propriedade com várias sementes e tamanhos):
- tamanhos diferem em no máximo 1 e `≤ tamanho` (pois `n ≤ T × tamanho`);
- cada semestre é um bloco contíguo do rodízio, então sua contagem por equipe difere em no máximo 1;
- como o rodízio continua de onde o semestre anterior parou, as equipes que ficaram sem aluno do 6º são as
  primeiras a receber os do 4º — é o que evita um time só de 2º quando há poucos avançados.

**Alternativa descartada:** "snake draft" ou otimização por pontuação de nível — mais complexa e sem ganho para
três níveis; o rodízio contínuo já garante as regras da spec.

### 3. Prévia e confirmação reproduzíveis (semente + assinatura)
`montar_equipes` sem `confirmar`: lê os participantes sem equipe, gera `semente = secrets.randbits(32)` (ou usa a
recebida, para "Sortear de novo" o painel pede uma nova sem enviar semente), calcula a distribuição e devolve
`{semente, assinatura, equipes: [{nome, integrantes, porSemestre}]}`. `assinatura` = SHA-256 dos ids dos
participantes sem equipe, ordenados. Com `confirmar`, o painel reenvia `tamanho`, `semente` e `assinatura`; o
servidor recalcula — se a assinatura mudou, `409` "Os alunos sem equipe mudaram; gere uma nova prévia". Assim o
navegador não manda a lista de equipes (nada para validar ou adulterar) e o resultado gravado é o da prévia.

`importar_participantes` segue o padrão de `_importar_desafios`: o painel envia o texto; sem `confirmar` volta a
prévia; com `confirmar`, o servidor relê o mesmo texto contra o banco atual e grava (um repetido que surgiu no
meio do caminho vira "já cadastrado").

### 4. Nomes e códigos das equipes novas
Candidatos: `PALAVRAS` em ordem, com só a inicial maiúscula (`Orion`), pulando nomes já usados (sem diferenciar
maiúsculas). Esgotadas as 16, volta ao início com sufixo numérico (`Orion 2`, `Vega 2`…), sempre único. O código
é `arena.gerar_codigo(indice_da_palavra, existentes)`, então `Orion` recebe `ORION-XXXXXX`.

### 5. Gravação sem transação
A confirmação grava primeiro todas as equipes (`_gravar_equipe`) e depois atualiza `equipe` de cada participante.
Uma falha no meio deixa equipes vazias ou parcialmente preenchidas — recuperável: excluir equipe agora devolve os
alunos para "sem equipe" (decisão 6) e a montagem pode ser refeita. Auditoria: uma linha
`montar_equipes` com "N equipe(s), M aluno(s), tamanho K"; uma linha `importar_participantes` com "N aluno(s)".

### 6. Participante sem equipe e exclusão de equipe
`_salvar_participante` aceita `equipe` vazia (grava `""`); com valor, continua exigindo equipe existente.
`_excluir_equipe` passa a gravar `equipe: ""` nos participantes em vez de `hdel`; o resumo da auditoria diz
"N participante(s) sem equipe". `_participantes` ordena "sem equipe" primeiro e devolve `semEquipe` (quantidade).
Montagem e importação seguem a mesma regra do `_criar_equipe`: com equipes ainda vindas de
`ARENA_EQUIPES`/arquivo e banco vazio, a montagem é recusada (409) pedindo a importação das equipes antes.

### 7. Painel (`admin.html` + `admin.js`)
Na aba Participantes, acima da tabela:
- **Importar alunos**: `<input type="file" accept=".csv,.txt">` e uma `<textarea>`; o arquivo é lido com
  `TextDecoder("utf-8", {fatal: true})` e, se falhar, `windows-1252` (o Excel no Brasil costuma salvar assim).
  "Pré-visualizar" mostra a tabela de alunos a criar e a lista de linhas ignoradas; "Confirmar importação"
  grava e recarrega.
- **Montar equipes**: campo "Alunos por equipe" (número, 2–10, padrão 5) com o texto "N alunos sem equipe →
  X equipes"; "Pré-visualizar" mostra um cartão por equipe (nome, integrantes `Nome (semestre)` e contagem por
  semestre); "Sortear de novo" e "Confirmar equipes".
- Seletor de equipe do formulário ganha "Sem equipe"; a tabela mostra "sem equipe" com destaque.
Tudo com os componentes e tokens `--a-*` existentes.

## Risks / Trade-offs

- [Planilha com nomes contendo vírgula num CSV separado por vírgula] → Com cabeçalho e aspas, o `csv` do
  Python trata; sem aspas, a linha vira "semestre não reconhecido" e aparece na prévia para correção.
- [Codificação da planilha] → Tentativa UTF-8 estrita com volta para Windows-1252; a prévia mostra os nomes para
  o admin conferir acentos antes de confirmar.
- [Nomes de alunos são dados pessoais] → Ficam só no banco do evento e na API autenticada do painel; nada é
  versionado; a auditoria guarda só quantidades nas ações em lote.
- [Escrita parcial sem transação] → Ver decisão 5: recuperável pelo próprio painel.
- [Rodízio coloca as "sobras" sempre nas primeiras equipes] → Irrelevante para o nivelamento; a ordem das
  equipes na prévia é a da lista de nomes.

## Migration Plan

Sem migração de dados: participantes existentes continuam com equipe. Deploy normal na Vercel; rollback =
reverter o commit (participantes sem equipe gravados nesse meio-tempo continuam válidos, só não aparecem em
nenhuma equipe até serem atribuídos).
