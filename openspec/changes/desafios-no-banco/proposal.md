## Why

O repositório `meuPia/challenge` precisa ser privado porque guarda os gabaritos, a bateria de testes extras e o gerador (com as soluções de referência em Python). Por isso, a Vercel Hobby não consegue importá-lo: o plano gratuito não aceita repositório privado de organização. Com os desafios guardados **só no banco** e editados pelo painel administrativo, o código pode ser aberto num repositório público, publicado de graça na Vercel e reaproveitado por outras instituições, o que já prepara o roadmap multi-tenant.

## What Changes

- **BREAKING** — Os desafios saem de `arena/desafios/*.json` e passam a ficar no banco da arena (Supabase), em dois registros por desafio:
  - parte **pública**: metadados, enunciado, código inicial e testes de exemplo;
  - parte **secreta**: testes extras e gabarito.

  O conteúdo usa um namespace próprio (`ARENA_CONTEUDO`, padrão `conteudo`), separado do `ARENA_PREFIXO`, então ensaio e evento usam os mesmos desafios.
- **BREAKING** — O gabarito passa a ser um campo do desafio no banco (antes era `arena/gabaritos/<COD>.por`).
- Nova seção **Desafios** no painel administrativo (só admin):
  - listar, criar e editar todos os campos, inclusive testes extras e gabarito;
  - **validar com o juiz real** (gabarito aceito e completo, código inicial não completo, folga de tempo);
  - **exportar** tudo em JSON (backup) e **importar** de volta.

  As edições vão para a auditoria, sem o conteúdo.
- A regra de ouro muda de "testes extras nunca chegam ao navegador" para "testes extras e gabaritos nunca chegam ao navegador **das equipes**". Só um admin logado os vê no painel.
- O `supabase/arena.sql` deste repositório só cria as tabelas, sem migration nem seed de desafios. Os 9 desafios atuais são carregados uma vez por `scripts/popular_desafios.py`, que fica **só no repositório privado** `challenge` (junto dos JSON e gabaritos).
- **REMOVIDO** do repositório público: `arena/desafios/`, `arena/gabaritos/`, `arena/extras_base/` e `scripts/gerar_testes_extras.py`. O gerador e o histórico ficam no repositório privado atual, que vira arquivo.
- Novos **desafios de exemplo**, públicos e triviais, em `arena/exemplos/`. Eles alimentam o desenvolvimento local (store `Local`), os testes automatizados e o `npm run validar` sem banco. Os testes deixam de depender dos desafios reais.
- `npm run validar` passa a validar os desafios do banco configurado. Sem banco, valida os exemplos.
- **Publicação do código aberto**: um repositório público **novo**, com histórico limpo, porque o histórico atual e as refs do PR #1 contêm os desafios. Antes de publicar, uma varredura confere se nenhum trecho de teste extra ou gabarito ficou na árvore.

## Capabilities

### New Capabilities
<!-- Nenhuma: as mudanças entram em arena-desafios e arena-admin. -->

### Modified Capabilities
- `arena-desafios`:
  - armazenamento no banco (partes pública e secreta) e regra de sigilo restrita ao navegador das equipes;
  - validação contra o banco e desafios de exemplo;
  - a bateria extra deixa de citar `arena/extras_base`;
  - remove o requisito "Geração determinística".
- `arena-admin` (criado pela mudança `painel-administrativo`): cadastro, validação, exportação e importação de desafios pelo painel.

## Impact

- **Dependência**: a edição pelo painel precisa da mudança `painel-administrativo` (login, papéis, `admin.html`, auditoria). A importação por script e o carregamento a partir do banco não precisam e podem ir antes.
- **Backend**:
  - `api/_lib/arena.py`: `desafios(db)` com cache curto, e `segredos(db, codigo)`;
  - `api/_lib/servico.py`: carrega os segredos só ao submeter;
  - `api/_lib/store.py`: chaves de conteúdo e `hget`;
  - `api/_lib/admin.py` e `api/admin.py`: ações de desafio.
- **Scripts**: `scripts/validar_desafios.py` reescrito para validar o store; `scripts/gerar_testes_extras.py` removido. Os scripts de carga, importação e varredura (`popular_desafios.py`, `importar_desafios.py`, `varrer_vazamento.py`) ficam só no repositório privado.
- **Dados**: os 9 desafios reais vão para o Supabase. Novo `arena/exemplos/` (desafios fictícios com gabarito).
- **Testes**: `tests/test_arena.py` e `tests/test_juiz.py` passam a usar os exemplos, mais testes novos de carregamento, sigilo e ações de desafio.
- **Docs e repositório**: README e CLAUDE.md (regra de ouro, de onde vêm os desafios, backup), e o passo a passo para criar o repositório público e arquivar o privado.
- **Riscos**: o banco vira a única cópia dos desafios. Por isso exportar é obrigatório antes do evento, e o Supabase Free não oferece backups para baixar. Faltam 11 dias para 21/10, e as duas mudanças juntas são grandes.
