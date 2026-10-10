## Context

- As funções da Vercel são Python puro (`BaseHTTPRequestHandler` em `api/_lib/web.py`), sem dependências além da biblioteca padrão (`requirements.txt` só tem o `meupia-core`). O `Base` só responde JSON: ainda não há redirecionamento nem cookies.
- `arena.equipes()` lê `ARENA_EQUIPES` ou `arena/equipes.json`. Hoje o token da equipe é o HMAC do id da equipe e não expira, então trocar o código não derruba ninguém.
- O banco é o Upstash Redis via REST (`store.RedisRest`) ou o arquivo local (`store.Local`), com `hgetall`, `hset`, `hsetnx`, `hincrby`, `lpush`, `lrange` e `apagar`.
- Desde a pontuação Codewars, a fonte de verdade dos pontos é a lista `aceitas:<equipe>`. O log com o código-fonte fica em `submissoes`. Nenhum desses registros tem id hoje.
- `scripts/servidor_local.py` roteia `/api/<nome>` para `api/<nome>.py` (só no primeiro nível). `vercel.json` publica `api/*.py`.
- O placar do admin hoje é `/placar.html?admin=ADMIN_TOKEN`, que também mostra o log.
- Prazos: o piloto é em 11/10 e o evento em 21/10. Os apps OAuth dependem de registro nos três provedores.

## Goals / Non-Goals

**Goals:**
- Login OAuth dos três provedores sem dependência nova, com `state` assinado, cookie de sessão seguro e papel resolvido a cada requisição.
- Equipes, participantes, perfis, ajustes e auditoria no mesmo banco da arena, editáveis sem redeploy.
- Ajuste de pontos aplicado num único ponto do código, para que melhor submissão, placar, freeze e desbloqueio fiquem coerentes.
- Um caminho de emergência (`ADMIN_TOKEN`) que não depende do OAuth.

**Non-Goals:**
- Login dos alunos por OAuth: a equipe continua entrando com o código.
- Anular, rejulgar ou editar o código de submissões. Só há ajuste de pontos.
- Editar desafios, horários ou a config pelo painel.
- Validar a assinatura dos `id_token` com JWKS (ver D3).

## Decisions

### D1. Rotas: arquivos de primeiro nível e uma API de ações
Arquivos novos em `api/`:
- `oauth_inicio.py`: `GET ?provedor=google|github|microsoft` → 302 para o provedor;
- `oauth_retorno.py`: `GET ?code&state` → 302 para `/admin.html` ou `/admin.html?erro=<motivo>`;
- `sessao.py`: `GET` → `{usuario|null, provedores[], emergencia: bool}`; `POST {acao: "sair"}` → apaga o cookie;
- `admin.py`: `GET ?acao=equipes|participantes|perfis|submissoes|submissao&id=|auditoria|placar` e `POST {acao, ...}` (criar, editar ou excluir equipe, participante ou perfil, regenerar código, importar, ajustar, desfazer ajuste).

Ficar no primeiro nível evita mexer no glob `api/*.py` do `vercel.json` e no roteador local. A URL de retorno (`<ARENA_URL>/api/oauth_retorno`) é a mesma para os três provedores e não tem query, o que facilita o registro exato que o Google e a Microsoft exigem.

*Alternativa:* `api/auth/[provedor].py` com rotas dinâmicas. Foi descartada porque exige mudar o `vercel.json` e o `servidor_local.py`.

### D2. Fluxo OAuth em `api/_lib/auth.py` (só biblioteca padrão)
Uma tabela de provedores define as URLs de autorização e de token, os escopos e a função de identidade:

| Provedor | Autorização / token | Escopos | Identidade |
|---|---|---|---|
| Google | `accounts.google.com/o/oauth2/v2/auth` / `oauth2.googleapis.com/token` | `openid email profile` | `id_token`: `email` com `email_verified` verdadeiro, `name` |
| Microsoft | `login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize` e `.../token` | `openid email profile` | `id_token`: `preferred_username`, `name`, `tid` |
| GitHub | `github.com/login/oauth/authorize` / `github.com/login/oauth/access_token` | `read:user user:email` | `GET api.github.com/user` (`login`, `name`) e `GET /user/emails` (só `verified`) |

O tenant da Microsoft vem de `OAUTH_MICROSOFT_TENANT` (padrão `common`). As credenciais vêm de `OAUTH_<PROVEDOR>_ID` e `OAUTH_<PROVEDOR>_SECRET`, e um provedor só aparece no login se as duas existirem. As chamadas HTTP usam `urllib.request`, com timeout de 8 s, por uma função `_http(metodo, url, dados, cabecalhos)` que os testes substituem.

**State:** `oauth_inicio` gera um `nonce` aleatório e faz um `state` = `base64(json{provedor, nonce, exp: +10min}).hmac`. O `nonce` também vai para o cookie `arena_oauth` (`HttpOnly`, `SameSite=Lax`, `Max-Age=600`). `oauth_retorno` confere a assinatura, a validade e se o `nonce` bate com o cookie, e apaga o cookie (uso único).

### D3. `id_token` sem verificação de assinatura
Os `id_token` do Google e da Microsoft chegam **direto do endpoint de token, via TLS e com o client secret**. O OIDC Core (§3.1.3.7) permite, nesse caso, usar a validação TLS no lugar da assinatura. O código confere `aud == client_id`, `iss` esperado (o da Microsoft depende do `tid`) e `exp`.

*Alternativa:* validar com JWKS (RS256). Foi descartada porque exige implementar RSA na mão ou adicionar uma dependência (`PyJWT` + `cryptography`) às funções, o que aumenta o pacote e o tempo de cold start.

### D4. Identidades, root e perfis
O login produz uma lista de identidades normalizadas em minúsculas:
- Google: `["google:<email>", "email:<email>"]`;
- Microsoft: `["microsoft:<upn>", "email:<upn>"]`;
- GitHub: `["github:<login>"] + ["email:<e>" para cada e-mail verificado]`.

O **root** vem da variável secreta `ARENA_ROOT`, por exemplo `{"google": "root@exemplo.com", "microsoft": "root@exemplo.edu", "github": "root-exemplo"}` (o repositório é público: identidades reais só na Vercel e no `.env.local`). JSON inválido em `ARENA_ROOT` falha cedo; variável ausente significa nenhum root via OAuth. Só a identidade **específica do provedor** (`google:`, `microsoft:`, `github:`) torna alguém root, e um `email:` igual vindo de outro provedor não basta (como pede a spec). O root não fica no banco, por isso não pode ser removido nem editado.

Os perfis ficam em `k_usuarios()`, um hash `email → {email, nome, github, papel}`. Um perfil bate com o login quando `email:<email>` está nas identidades ou quando `github:<login>` bate com o campo `github`. `auth.papel(identidades, db)` devolve `("admin", root=True)`, `(papel do perfil, root=False)` ou `None`.

### D5. Cookie de sessão sem papel
`arena_sessao` = `base64(json{ids, nome, provedor, exp: +12h}).hmac(ARENA_SECRET)`, com `HttpOnly; SameSite=Lax; Path=/; Max-Age=43200` e `Secure` quando a origem não é `localhost`. O papel **não** vai no cookie: `Base.banca()` lê o cookie e chama `auth.papel` a cada requisição, o que torna o rebaixamento imediato. A leitura extra é um `HGETALL usuarios`, que é pequeno.

Para requisições que alteram dados, `Base` exige `Content-Type: application/json` e, se houver `Origin`, que o host dele seja igual ao `Host`/`X-Forwarded-Host`. Com o `SameSite=Lax`, isso cobre CSRF sem precisar de token extra.

O **acesso de emergência** usa o cabeçalho `X-Arena-Token`. Se bater com `ADMIN_TOKEN` (comparação em tempo constante), `banca()` devolve um autor sintético `{nome: "token de emergência", papel: "admin", root: true}`. O painel tem um campo "token de emergência" que guarda o token só no `sessionStorage`.

### D6. Equipes no banco com versão do código
Chaves novas em `store.py`:
- `k_equipes()`: hash `id → {id, nome, codigo, versao, criadaEm}`;
- `k_participantes()`: hash `id → {id, equipe, nome, semestre, email}`;
- `k_usuarios()`;
- `k_ajustes()`: hash `idSubmissao → {pontos, motivo, autor, t}`;
- `k_auditoria()`: lista de JSON.

`store` ganha `hget` e `hdel` nas três implementações (`SupabaseRest`, `RedisRest` e `Local`).

`arena.equipes(db)` devolve as equipes do banco, com `integrantes` montados a partir dos participantes como `Nome (semestre)`. Se o hash estiver vazio, cai no comportamento atual (`ARENA_EQUIPES` ou arquivo, com `versao: 0`). Todos os chamadores em `servico` passam `db`.

**Token da equipe:** `emitir_token(eid, versao)` assina `eid:versao`. `ler_token` aceita também o formato antigo, só com o `eid`, como versão 0, então tokens emitidos antes da mudança continuam válidos até a primeira regeneração. `Base.equipe_id()` confere se a equipe existe e se a versão bate; senão, devolve 401. Regenerar o código faz `versao += 1`. A importação mantém id, código e `versao: 0`, e as equipes não precisam entrar de novo.

**Código:** a geração de `scripts/gerar_equipes.py` vai para `arena.gerar_codigo(palavra_indice, existentes)` (com `secrets` e alfabeto sem ambíguos), com até 20 tentativas para garantir unicidade. O script passa a importar essa função.

**Estatísticas da listagem:** o número de submissões é a soma de `k_tentativas(eid)` e a última submissão é o máximo de `k_ultima(eid)`. Os pontos e os completos vêm do placar vivo. Assim a listagem não precisa varrer o log.

### D7. Id das submissões e ajuste num ponto só
`servico.submeter` gera `id = secrets.token_hex(6)` e grava esse id no registro de `aceitas` e na entrada do log.

`arena.aplicar_ajustes(aceitas, ajustes, todos)` é uma função pura. Para cada registro com ajuste, ela devolve uma cópia com `pontos = ajuste.pontos`, `pontosJuiz = original` e `completo = original.completo and pontos == todos[cod]["pontos"]`.

`servico._aceitas(db, eid)` passa a carregar os ajustes (um `HGETALL ajustes` por requisição) e aplicá-los. Como missões, missão, submissão e placar já leem as aceitas por essa função, a regra vale em todos os pontos de uma vez (spec "Pontos efetivos"). O freeze continua filtrando por `t` da submissão, então um ajuste pós-freeze de uma submissão antiga aparece no congelado, como pede a spec.

O ajuste só é aceito se o id existir em `aceitas` da equipe (submissão aceita), `0 ≤ pontos ≤ pontos do módulo` e `len(motivo.strip()) ≥ 5`.

*Alternativa:* reescrever o registro em `aceitas` com `LSET`. Foi descartada porque perde o valor original, complica o "desfazer" e corre o risco de corrida com novas submissões (`LPUSH` muda os índices).

### D8. Casos de uso em `api/_lib/admin.py`
Este módulo tem funções sem HTTP, testáveis como `servico`. Cada uma recebe `(autor, dados, db)`, confere a permissão por uma tabela `PERMISSOES = {acao: "juiz"|"admin"}`, valida os dados, grava e chama `auditar(db, autor, acao, alvo, resumo)`. `api/admin.py` só faz a ponte: `autor = self.banca()` (401 sem sessão), `admin.executar(acao, autor, dados)`.

A auditoria guarda o `resumo` sem código-fonte e sem códigos de acesso (só "código regenerado").

### D9. Placar real só sob pedido explícito
`/api/placar` passa a ser **sempre** público: segue o freeze e ignora cookie e `?admin=`, que é removido. O placar vivo do painel vem de `GET /api/admin?acao=placar`, que chama `servico.placar(admin=True)`. Assim um telão com sessão de admin nunca descongela (spec "Freeze"). O log sai do `placar.js` e do `placar.html`. A tabela de placar vira `src/arena/placar-tabela.js`, usado pelo telão e pela seção Placar real do painel.

### D10. Frontend do painel
`admin.html` + `src/arena/admin.js`, a quarta página do Vite, sem framework (como o resto da arena). O conteúdo:
- tela de login com os botões dos provedores de `/api/sessao` e o campo de token de emergência;
- abas por papel, com tabelas e formulários simples num `<dialog>`;
- listagem de equipes com a versão para impressão (`@media print` só com nome, código e integrantes);
- log com filtros no cliente (sobre as últimas 500 entradas) e um modal com o código-fonte (em `<pre>`, com `textContent`);
- ajuste com campos de pontos e motivo.

Tudo que vem do banco é inserido com `escapar()` ou `textContent`.

### D11. Login na tela do painel e mensagens de erro
`oauth_retorno` redireciona com `?erro=` em `estado_invalido`, `provedor_falhou`, `identidade_nao_verificada` ou `nao_autorizado`. O painel traduz esses códigos para mensagens em pt-BR. Logins recusados vão para a auditoria com as identidades tentadas, para o admin cadastrar a pessoa certa.

## Risks / Trade-offs

- [Registrar os apps OAuth leva tempo. Na Microsoft, um app no tenant da Univille pode precisar de aprovação da TI] → Registrar o app Microsoft numa conta própria com `common` (contas de qualquer tenant), o que não exige consentimento de administrador para `openid email profile`. O `ADMIN_TOKEN` cobre o piloto e emergências.
- [Com o tenant `common`, o `preferred_username` é o UPN, que depende de domínio verificado no tenant. Um tenant malicioso não consegue ter um UPN `@univille.br` sem verificar o domínio, mas o `email` da Microsoft é editável e não é usado] → Usar só o `preferred_username`. Se quiser fechar mais, definir `OAUTH_MICROSOFT_TENANT` com o id do tenant da Univille.
- [O login do GitHub pode mudar de dono se for renomeado] → É baixo risco para um evento de um dia. Os perfis podem preferir e-mail. A auditoria mostra os logins.
- [Sem validação de assinatura do `id_token`] → Aceitável pelo D3 (o token vem direto do provedor por TLS, com o secret). `aud`, `iss` e `exp` são conferidos.
- [Mais leituras no Redis a cada requisição: equipes, participantes, usuários e ajustes] → Hashes pequenos (cerca de 8 equipes, 40 participantes, alguns perfis e poucos ajustes). Ficam milhares de comandos no evento, dentro do plano gratuito.
- [Um código de acesso regenerado no meio da prova derruba a equipe] → É o comportamento desejado quando há vazamento. O painel pede confirmação antes de regenerar.
- [Um ajuste errado muda o placar] → O desfazer está sempre disponível, e a auditoria mostra quem ajustou e por quê.

## Migration Plan

1. Fazer o deploy com as variáveis OAuth vazias: o painel funciona com o token de emergência, e as equipes continuam vindo de `ARENA_EQUIPES`.
2. Registrar os apps OAuth com a URL de retorno `https://<domínio>/api/oauth_retorno` (e `http://localhost:8787/api/oauth_retorno` para testes). Configurar `OAUTH_*` e `ARENA_URL`.
3. Entrar como root, importar as equipes (ou criá-las do zero), cadastrar os participantes e os juízes, e imprimir os códigos.
4. Depois de importar, remover `ARENA_EQUIPES` (opcional, porque o banco tem prioridade).
5. **Rollback:** reverter o deploy. As equipes voltam a vir de `ARENA_EQUIPES`. Tokens no formato novo (`eid:versao`) deixam de ser aceitos pelo código antigo, então as equipes precisam digitar o código de novo. Os ajustes ficam no banco, mas o código antigo os ignora.
