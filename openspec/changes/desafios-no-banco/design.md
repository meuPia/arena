## Context

- `arena.desafios()` lê `arena/desafios/*.json` a cada requisição, e os gabaritos ficam em `arena/gabaritos/<COD>.por`. `servico` (missões, missão, submissão, placar), `scripts/validar_desafios.py` e os testes chamam essa função sem `db`.
- Tamanho atual: cerca de 114 KB para os 9 desafios, dos quais cerca de 83 KB são `testesExtras`. A parte pública tem cerca de 3 KB por desafio.
- `store` tem três implementações com a mesma interface (`SupabaseRest`, `RedisRest` e `Local`): `hgetall`, `hset`, `hsetnx`, `hincrby`, `lpush`, `lrange` e `apagar`. A mudança `painel-administrativo` (ainda não implementada) acrescenta `hget` e `hdel`, o login da banca, os papéis, `admin.html`, `api/admin.py` e a auditoria.
- O Supabase já tem `arena_hash` e `arena_lista` (`supabase/arena.sql`), com RLS ligado e sem acesso para anon.
- O repositório `meuPia/challenge` é privado e tem os desafios em vários commits e no PR #1.

## Goals / Non-Goals

**Goals:**
- Desafios carregados do banco sem mudar o schema SQL, com os segredos lidos só para julgar.
- Testes e desenvolvimento local sem nenhum conteúdo real (exemplos públicos).
- Uma única rotina de validação usada pelo script, pela importação e pelo painel.
- Publicação do código aberto sem vazar o histórico.

**Non-Goals:**
- Gerador de baterias no painel. As baterias são editadas como texto ou importadas.
- Rejulgar submissões depois de editar um desafio.
- Multi-tenant: o namespace `ARENA_CONTEUDO` é só o primeiro passo.

## Decisions

### D1. Dois hashes no store, sem SQL novo
- `k_desafios()` = `<ARENA_CONTEUDO>:desafios`: hash `codigo → JSON público`;
- `k_segredos()` = `<ARENA_CONTEUDO>:segredos`: hash `codigo → {"testesExtras", "gabarito"}`.

As duas chaves usam `ARENA_CONTEUDO` (padrão `conteudo`), e não `ARENA_PREFIXO`, então os ensaios e o evento compartilham os desafios. Gravar um desafio faz dois `hset`. Uma falha entre eles deixa o desafio com a parte pública nova e os segredos antigos, o que a validação aponta e o admin corrige salvando de novo. É aceitável para edições raras e manuais.

*Alternativa:* uma tabela `arena_desafios` com colunas próprias. Foi descartada porque exigiria SQL novo, uma quarta forma de acesso e não funcionaria no `Local` nem no Upstash.

### D2. Carregamento com cache curto
`arena.desafios(db)` lê `HGETALL k_desafios`, ordena por código e guarda em memória do processo por 30 s (`_CACHE = {"valor", "expira"}`). Instâncias quentes da Vercel reaproveitam o cache. Isso dá no máximo uma leitura de cerca de 30 KB a cada 30 s por instância, em vez de uma por requisição. As ações de admin que gravam desafios limpam o cache local, e as outras instâncias atualizam em até 30 s, como pede a spec.

`arena.segredos(db, codigo)` faz `HGET k_segredos codigo`, sem cache, e só é chamado por `servico.submeter` e pela validação. `servico` passa `db` a `arena.desafios`. `arena.publico()` não muda e continua sendo o único jeito de entregar um desafio à equipe.

### D3. Exemplos só com o store `Local`
Se o hash estiver vazio **e** o `db` for `store.Local`, `desafios`/`segredos` leem `arena/exemplos/*.json`, que estão no formato de exportação (D5, um desafio por arquivo, com `testesExtras` e `gabarito`). Com Supabase ou Upstash não há queda para os exemplos, como pede a spec. Os testes usam o `Local` com arquivo temporário, então passam a rodar sobre os exemplos.

**Os exemplos** são 7 desafios triviais com códigos `*9x`, que deixam claro que são fictícios:

| Código | Nível | Pontos | Função |
|---|---|---|---|
| B91 | Bronze | 10 | `dobro(n)` |
| B92 | Bronze | 10 | `maior(lista)` |
| B93 | Bronze | 10 | `contar_vogais(texto)` |
| S91 | Silver | 20 | `inverter(texto)` |
| S92 | Silver | 20 | `soma_digitos(n)` |
| G91 | Gold | 35 | `fatorial(n)` (inteiros grandes) |
| X91 | Extra | 50 | `fibonacci(n)` |

Eles cobrem as regras de desbloqueio da config (2 Bronze → Silver; 2 Bronze + 2 Silver → Gold; 1 Gold → Extra). Cada um tem gabarito, código inicial incompleto, 3 exemplos e 15 extras. São criados uma vez durante a implementação e validados pelo `npm run validar`. Os pontos de B91 e G91 repetem os de B01 e G01, então os testes de pontuação só trocam os códigos.

### D4. Validação compartilhada em `api/_lib/validacao.py`
A lógica de `scripts/validar_desafios.py` vira `validar(desafio_completo) → {ok, erros[], gabarito, inicial, maxMs}`, que usa `juiz.julgar(..., detalhes=True)`. Ela é usada pelo script (`npm run validar`, que valida o store de `store.abrir()`), por `importar_desafios.py` e pelas ações do painel. Validar os 9 desafios dá 18 julgamentos de cerca de 0,3 s, o que leva cerca de 6 s e cabe no `maxDuration` de 30 s.

### D5. Formato de exportação e importação
```json
{"formato": "meupia-challenge/desafios", "versao": 1, "exportadoEm": "<ISO>",
 "desafios": [{"codigo": "B01", "...campos públicos...": "...", "testesExtras": "...", "gabarito": "..."}]}
```
`api/_lib/conteudo.py` (público, usado pelo painel) lê esse arquivo ou uma pasta com `<COD>.json` (formato antigo) mais `<COD>.por` ao lado ou em `../gabaritos/`. Os scripts de linha de comando que o usam (`importar_desafios.py` e `popular_desafios.py`, que valida, mostra criar/substituir/inválido e só grava com confirmação) ficam **só no repositório privado**. A importação pelo painel usa a mesma função `admin.importar(dados, confirmar)`, em duas etapas: prévia e confirmação. Gravar o mesmo conteúdo de novo produz o mesmo estado, porque o `hset` é idempotente.

### D6. Ações de desafio no painel (sobre `painel-administrativo`)
`PERMISSOES` ganha estas ações, todas com papel mínimo `admin`: `desafios` (lista com metadados, contagem de extras e última validação), `desafio` (completo, com segredos), `salvar_desafio`, `validar_desafio`, `validar_todos`, `exportar_desafios` e `importar_desafios`.

`salvar_desafio` valida os campos (código imutável `^[A-Z]\d{2}$`, nível da config, pontos inteiros > 0, linhas `esperar_*` sem `"` interno nem `\`), grava as duas partes e limpa o cache. Se `confirmarSubmissoes` não vier e o desafio já tiver tentativas em alguma equipe (`k_tentativas`), devolve 409 pedindo confirmação. A auditoria registra os nomes dos campos alterados (comparando com o registro anterior) e nunca os valores. A última validação fica em `<ARENA_CONTEUDO>:validacao` (`codigo → {ok, quando, resumo}`).

No `admin.js`, a aba Desafios tem uma tabela e um editor num `<dialog>` grande, com `<textarea>` monoespaçado para o código e os testes, e uma prévia do enunciado com `marked` (já é dependência). Também tem os botões validar formulário, salvar, validar todos, exportar (download de `Blob`) e importar (`<input type=file>`, com prévia e confirmação).

### D7. Varredura de vazamento e repositório público novo
`scripts/varrer_vazamento.py --referencia <pasta ou export.json>` monta um conjunto com as linhas de `testesExtras` e as linhas não triviais (com 20 caracteres ou mais, sem contar espaços) de cada gabarito real. Depois percorre os arquivos que o git versiona (`git ls-files`) e falha se encontrar algum trecho. O script fica no repositório privado e varre o público com `--raiz ../arena`.

**Publicação:** o histórico atual não pode ir a público, e o GitHub mantém as refs do PR #1 mesmo depois de um force-push. Por isso:
1. renomear `meuPia/challenge` para `meuPia/challenge-privado` (continua privado e vira arquivo, com o gerador);
2. no clone limpo, `git checkout --orphan publico`, um único commit "meuPiá Challenge — código aberto", e push para um `meuPia/challenge` **novo e público**;
3. conectar a Vercel Hobby ao repositório público.

As operações no GitHub são feitas pelo dono, com confirmação, porque mudam um repositório público.

*Alternativa:* `git filter-repo` no repositório atual. Foi descartada porque as refs de PR e os forks continuam expondo os commits antigos.

### D8. Ordem de implementação
1. Carregamento do banco, exemplos, testes e validação (independem do painel).
2. Importação dos desafios reais para o Supabase e conferência com `npm run validar`.
3. Remoção dos arquivos secretos e varredura.
4. Aba Desafios (depois do `painel-administrativo`).
5. Publicação.

Os passos 1 a 3 já permitem publicar o repositório aberto e fazer o deploy, editando os desafios por exportação, script e importação até o painel ficar pronto.

## Risks / Trade-offs

- [O banco é a única cópia dos desafios, e o Supabase Free não oferece backup para baixar] → Exportação no painel e no script, com a regra operacional de exportar depois de cada edição e na véspera do evento. O repositório privado arquivado guarda a versão de hoje.
- [Projeto Free pausado depois de 7 dias sem uso] → Os ensaios até 16/10 mantêm o projeto ativo. Conferir na véspera.
- [Edição no meio da prova muda o desafio para quem ainda não resolveu] → Confirmação obrigatória quando já há tentativas, e auditoria com os campos alterados.
- [Cache de 30 s mostra o enunciado antigo por alguns segundos] → Aceitável. Não há edição de enunciado esperada durante a prova.
- [Admin vê testes extras no navegador] → Restrito ao papel admin, que já é a banca e tem acesso ao repositório privado hoje. Juízes não recebem os campos.
- [Prazo: esta mudança somada ao painel] → A ordem do D8 permite parar depois do passo 3 e ainda publicar no Hobby, deixando a aba Desafios para depois.

## Migration Plan

1. Implementar os passos 1 e 2 do D8 no branch atual (privado), com os desafios reais ainda presentes.
2. Criar as tabelas com `supabase/arena.sql` (só estrutura, sem dados). No repositório **privado** `challenge`, rodar `python3 scripts/popular_desafios.py` (lê o `.env.local`, valida, pede confirmação, grava e exporta o backup). O repositório público não tem nenhuma migration que popule desafios.
3. O `popular_desafios.py` exporta o backup fora do repositório.
4. Montar o repositório público sem `arena/desafios`, `arena/gabaritos`, `arena/extras_base`, `scripts/gerar_testes_extras.py`, `scripts/importar_desafios.py` e `scripts/varrer_vazamento.py`, e varrê-lo a partir do privado (`varrer_vazamento.py --referencia arena/desafios --raiz ../arena`).
5. Publicar (D7) e fazer o deploy na Vercel Hobby com `SUPABASE_*`.
6. **Rollback:** o repositório privado arquivado continua com os desafios em arquivo e o deploy antigo. É só voltar a apontar a Vercel para ele (o que exige plano Pro ou repositório pessoal).
