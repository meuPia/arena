## Why

O horário do Code Challenge (início e fim) só existe em `arena/config.json`: mudar a data exige um commit e um
novo deploy, e a banca não consegue reagendar o início no dia (atraso na abertura do laboratório, ensaio em outro
horário). Além disso, a IDE não mostra o tempo restante, o que o novo visual previa (tarefa 4.5 de
`aplicar-novo-visual`), porque a resposta da missão não traz o horário do evento.

## What Changes

- Nova seção **Evento** no painel da banca: o admin escolhe a data e a hora de **início** do evento. O fim passa a
  ser `início + duração`, onde a duração é a do `arena/config.json` (hoje 160 min); o freeze continua sendo os
  `freezeMinutos` finais.
- O início salvo no banco vale para tudo que usa o horário (abertura das missões, submissões, cooldown, freeze,
  placar, relógios). Sem início salvo, vale o do `arena/config.json`, como hoje. O admin pode voltar ao horário do
  arquivo.
- A alteração entra na auditoria. Juízes veem o horário, mas não alteram.
- A missão (`GET /api/missoes?codigo=`) passa a devolver a `janela` do evento, e a IDE mostra o cronômetro no
  cabeçalho (tempo para abrir, tempo restante ou encerrado), igual ao painel.

## Capabilities

### New Capabilities
<!-- nenhuma -->

### Modified Capabilities
- `arena-admin`: novo requisito de horário do evento configurável pelo painel.
- `arena-interface`: novo requisito de cronômetro na IDE.

## Impact

- Python: `api/_lib/arena.py` (horário efetivo a partir do banco), `api/_lib/servico.py` (usa o horário efetivo e
  devolve `janela` na missão), `api/_lib/admin.py` (ações `evento` e `salvar_evento`), `api/_lib/store.py`
  (chave `<prefixo>:evento`, separada por rodada como as submissões).
- Front-end: `admin.html`/`src/arena/admin.js` (seção Evento), `ide.html`/`src/arena/submissao.js` (cronômetro).
- Testes: `tests/test_admin.py`, `tests/test_arena.py`.
- Sem mudança em `arena/config.json` (continua sendo o padrão e a fonte da duração).
