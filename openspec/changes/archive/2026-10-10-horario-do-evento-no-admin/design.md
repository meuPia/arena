## Context

- `arena.config()` lê `arena/config.json` (com `inicio` e `fim` ISO com fuso, ex.: `-03:00`). `arena.janela(cfg)`
  calcula a situação. `servico` chama `arena.config()` em `missoes`, `missao`, `submeter` e `placar`.
- O banco tem chaves por rodada (`ARENA_PREFIXO`, ex.: submissões) e de conteúdo (`ARENA_CONTEUDO`).
- O painel da banca já tem ações com `PERMISSOES` e auditoria (`admin.executar`).

## Goals / Non-Goals

**Goals:** início configurável pelo admin sem deploy; IDE com cronômetro.
**Non-Goals:** configurar fim, freeze, cooldown ou regras pelo painel (continuam no arquivo); multi-tenant.

## Decisions

1. **Guardar só o início, por rodada.** Hash `<prefixo>:evento`, campo `inicio` (ISO com fuso). Por rodada porque
   cada ensaio tem seu horário; não pode vazar para a rodada do evento. *Alternativa:* namespace de conteúdo —
   descartada: ensaios mudariam o evento.
2. **Horário efetivo em `arena.config(db)`.** Com `db`, aplica o início salvo e recalcula `fim = início + (fim -
   início do arquivo)`; sem `db`, só o arquivo (chamadas que só leem níveis seguem iguais). `servico` passa o `db`.
   Cache de 30 s como o dos desafios? Não: é uma leitura `hget` por requisição, barata; sem cache não há atraso.
3. **Fuso.** O formulário usa `datetime-local` (sem fuso); o servidor interpreta no fuso do `inicio` do arquivo e
   grava ISO com esse fuso. A resposta devolve início/fim como timestamp e ISO, e o painel mostra no fuso do evento.
4. **Ações.** `evento` (juiz+: horário efetivo, origem `banco|arquivo`, duração, freeze) e `salvar_evento` (admin:
   `{inicio}` ou `{inicio: null}` para voltar ao arquivo), auditadas como `horário do evento`.
5. **IDE.** `servico.missao` inclui `janela`. O cálculo do texto do relógio vira função compartilhada em `api.js`
   (`textoRelogio`), usada pelo painel e pela IDE.

## Risks / Trade-offs

- [Mudar o início com o evento em andamento] → o painel avisa quando já há submissões na rodada e a auditoria
  registra; não bloqueamos (pode ser necessário corrigir um erro de digitação).
- [Relógio da máquina] → todos os relógios usam o `agora` do servidor como já fazem.
