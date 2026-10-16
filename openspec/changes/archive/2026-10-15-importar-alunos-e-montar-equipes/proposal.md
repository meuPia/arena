## Why

Hoje a banca cadastra os participantes um a um no painel, e cada um precisa já estar numa equipe. Para o Code
Challenge de 21/10 são cerca de 40 alunos de três semestres (2º, 4º e 6º) e 8 equipes multisseriadas: digitar
tudo à mão é lento, e montar as equipes "de cabeça" arrisca deixar um time só com alunos avançados. A banca já
recebe a lista de inscritos em planilha; o painel deve aproveitá-la e propor equipes niveladas.

## What Changes

- **Importar alunos**: na aba Participantes, o admin envia um arquivo CSV ou cola uma listagem (uma linha por
  aluno, com nome e semestre/fase; e-mail opcional). O painel mostra uma prévia (quem entra, quem é ignorado e por
  quê: linha inválida, semestre não reconhecido, nome já cadastrado) e só grava ao confirmar. Os alunos
  importados ficam **sem equipe**.
- **Participante sem equipe**: um participante passa a poder existir sem equipe (antes era obrigatório). Quem
  está sem equipe não aparece no modal de submissão de nenhuma equipe e aparece no topo da lista do painel.
- **Montar equipes automaticamente**: o admin informa o **tamanho da equipe**; o painel distribui só os alunos
  **sem equipe** em equipes **novas** e niveladas: cada semestre é espalhado igualmente entre as equipes (os
  alunos do 6º em equipes diferentes e completados com 4º e 2º), os tamanhos diferem em no máximo 1 e nenhuma
  passa do tamanho informado. Equipes já existentes não mudam.
- As equipes novas recebem **nomes temáticos** (Orion, Vega, Lyra…, as mesmas palavras dos códigos de acesso,
  com o código combinando com o nome) e código de acesso; o nome pode ser trocado depois, como hoje.
- Prévia antes de gravar, com **"Sortear de novo"**; ao confirmar, as equipes e os vínculos são gravados de uma
  vez. Depois, o admin ajusta à mão (mover aluno de equipe) como já faz.
- **Excluir equipe** (sem submissões) passa a devolver os participantes para "sem equipe" em vez de apagá-los,
  para a banca poder desfazer uma montagem e sortear de novo sem reimportar ninguém.
- Importação e montagem vão para a auditoria (quantidades, sem códigos de acesso).

## Capabilities

### New Capabilities
<!-- Nenhuma: tudo cabe no painel da banca. -->

### Modified Capabilities
- `arena-admin`: "Participantes" (participante pode ficar sem equipe), "Cadastro de equipes" (excluir devolve os
  participantes para sem equipe) e novos requisitos "Importação de alunos" e "Montagem automática de equipes".
  (A "Auditoria" já cobre importação e cadastros; os novos requisitos dizem o que vai para o resumo.)

## Impact

- `api/_lib/admin.py`: ações novas `importar_participantes` e `montar_equipes` (só `admin`, POST, em duas
  etapas prévia/confirmação), `salvar_participante` aceita equipe vazia, `excluir_equipe` desvincula.
- Novo `api/_lib/turmas.py` (funções puras: ler a listagem/CSV, normalizar semestre, distribuir em equipes),
  com testes em `tests/test_turmas.py`; fluxo do painel em `tests/test_admin.py`.
- `api/_lib/arena.py`: `equipes()` ignora participantes sem equipe (já ignora, conferir com teste).
- `admin.html` + `src/arena/admin.js`: blocos "Importar alunos" e "Montar equipes" na aba Participantes, filtro
  "sem equipe", opção "Sem equipe" no seletor.
- Sem mudança no juiz, na pontuação, na IDE ou nas rotas públicas. Nenhum dado de aluno vai para o repositório
  (a planilha é lida no navegador e enviada só à API do painel).
