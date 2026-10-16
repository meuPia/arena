## 1. Funções puras (`api/_lib/turmas.py`)

- [x] 1.1 Criar `normalizar_semestre` e `chave_nome` (D1). Cobrir em `tests/test_turmas.py`: `2`, `2º`, `2°`, `2o`, `2º semestre`, `fase 2`, `2ª fase` → `2º`; `9x`, `abc`, `0`, `13` → `None`; "  Ána   Souza " e "ana souza" têm a mesma chave. Verificar com `python3 -m pytest -q tests/test_turmas.py`.
- [x] 1.2 Criar `ler_listagem(texto)` (D1): BOM, separador por tabulação/ponto e vírgula/vírgula, cabeçalho opcional (`nome`, `semestre`/`fase`, `email`/`e-mail` em qualquer ordem), formato `Nome (2º)`, aspas de CSV, limite de 500 linhas, e motivos de linha ignorada (sem nome, nome > 60, semestre não reconhecido, e-mail inválido, repetido na listagem). Testes com os exemplos dos cenários "Prévia de uma planilha" e "Listagem colada". Verificar com pytest.
- [x] 1.3 Criar `distribuir(alunos, tamanho, semente)` (D2) e `nomes_de_equipes(qtd, usados)` (D4). Testes: os dois cenários numéricos da spec (40 → 8×5 com 1 do 6º cada; 13 → 4 equipes de 3–4 sem dupla do 6º e com um do 4º em cada); mesma semente → mesmo resultado, sementes diferentes → resultados diferentes; teste por propriedade (tamanhos 2–10, n de 1 a 60, 50 sementes) para tamanhos ≤ tamanho e diferença ≤ 1 no total e por semestre; nomes pulam os usados e viram `Orion 2` depois de 16. Verificar com pytest.

## 2. Casos de uso do painel (`api/_lib/admin.py`)

- [x] 2.1 `_salvar_participante` aceita equipe vazia; `_excluir_equipe` desvincula em vez de apagar; `_participantes` ordena "sem equipe" primeiro e devolve `semEquipe` (D6). Em `tests/test_admin.py`: participante sem equipe não aparece em `arena.equipes()` nem em `servico.missoes`; excluir equipe sem submissões deixa os integrantes sem equipe. Verificar com `npm run test:py`.
- [x] 2.2 Ação `importar_participantes` (só admin, POST) com prévia e `confirmar` (D3), contra os nomes já cadastrados, e auditoria com a quantidade. Testes: prévia não grava; confirmação grava sem equipe; "já cadastrado" ignorado; juiz → 403; GET → 405. Verificar com pytest.
- [x] 2.3 Ação `montar_equipes` (só admin, POST): valida `tamanho` 2–10, recusa sem alunos sem equipe e com equipes ainda no arquivo, prévia com `semente`/`assinatura`/equipes/`porSemestre`, confirmação que recalcula, recusa com assinatura diferente (409), grava equipes com nome e código (D4/D5) e audita sem códigos. Testes: cenários "Confirmar a montagem" (a equipe entra com `servico.login` pelo código), "Equipes existentes intactas" e "Prévia desatualizada"; auditoria sem nenhum código de acesso. Verificar com pytest.
- [x] 2.4 Registrar as duas ações em `PERMISSOES` (admin) e fora de `LEITURA`; atualizar a docstring/tabela de ações do `CLAUDE.md` (lista de ações do `/api/admin`). Verificar com `npm run test:py`.

## 3. Painel (`admin.html`, `src/arena/admin.js`)

- [x] 3.1 Opção "Sem equipe" no seletor do formulário, linha "sem equipe" destacada e contador na tabela de participantes. Verificar no navegador do app (`npm run local`, token de emergência `admin`) cadastrando um participante sem equipe.
- [x] 3.2 Bloco "Importar alunos": arquivo (UTF-8 estrito com volta para Windows-1252) ou texto colado, prévia (a criar + ignoradas com motivo) e confirmação (D7). Verificar no navegador com um CSV de teste em Windows-1252 com acentos e uma listagem colada: a prévia mostra os nomes corretos e as linhas ignoradas; confirmar recarrega a tabela com os alunos sem equipe.
- [x] 3.3 Bloco "Montar equipes": tamanho (2–10, padrão 5) com "N alunos sem equipe → X equipes", prévia em cartões com contagem por semestre, "Sortear de novo" e "Confirmar equipes" (D7). Verificar no navegador: sortear de novo muda a distribuição; confirmar cria as equipes na aba Equipes com códigos, e "Imprimir códigos" inclui as novas.
- [x] 3.4 Conferir os dois blocos a 360 px (sem rolagem horizontal da página) e nos temas escuro e claro, só com tokens `--a-*`. Verificar com `resize_window` e capturas.

## 4. Verificação geral e documentação

- [x] 4.1 Ensaio ponta a ponta no `npm run local`: importar 40 alunos fictícios (8 do 6º, 14 do 4º, 18 do 2º), montar equipes de 5, entrar com o código de uma equipe nova e ver os integrantes no modal de submissão; excluir uma equipe e conferir que os alunos voltam para "sem equipe". Rodar `npm test` sem falhas.
- [x] 4.2 Atualizar o `CLAUDE.md` (Arquitetura: `turmas.py`; ações do `/api/admin`; seção "Acesso da banca": importação e montagem só para admin) e conferir que nenhum dado de aluno real foi versionado (`git status` sem CSV).
