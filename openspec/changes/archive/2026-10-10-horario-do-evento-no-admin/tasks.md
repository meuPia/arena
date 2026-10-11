## 1. Servidor

- [x] 1.1 Chave `k_evento()` em `store.py` e `arena.config(db)` aplicando o início salvo (fim = início + duração do arquivo); verificar com teste em `tests/test_arena.py` (sem início salvo = arquivo; com início = fim e freeze deslocados; prefixo diferente não vê)
- [x] 1.2 `servico` usa `arena.config(db)` em missoes, missao, submeter e placar, e `missao` devolve `janela`; verificar com teste que a missão traz a janela e que as missões abrem no novo início
- [x] 1.3 Ações `evento` (juiz) e `salvar_evento` (admin) em `admin.py`, com validação de data, volta ao arquivo e auditoria; verificar com testes de permissão, data inválida, auditoria e volta ao arquivo

## 2. Painel e IDE

- [x] 2.1 Seção Evento em `admin.html`/`admin.js`: horário efetivo, origem, campo `datetime-local`, salvar e voltar ao arquivo (só admin altera); verificar no servidor local que salvar muda o relógio do painel das equipes
- [x] 2.2 `textoRelogio` em `api.js`, usado pelo painel e pelo cabeçalho da IDE (`submissao.js`), com teste JS; verificar na IDE local o cronômetro no modo ensaio e com `ARENA_MODO` desligado

## 3. Fechamento

- [x] 3.1 Rodar `npm test` e atualizar CLAUDE.md (seção Evento, chave `<prefixo>:evento`) e a tarefa 4.5 de `aplicar-novo-visual`
