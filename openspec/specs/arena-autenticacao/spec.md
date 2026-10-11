# arena-autenticacao Specification

## Purpose
Identificar quem acessa a Code Arena: a banca (admin e juízes) entra por OAuth com Google, GitHub ou Microsoft, e as equipes entram pelo código. O papel de cada um define o que pode fazer.

## Requirements

### Requirement: Provedores OAuth
A banca SHALL entrar pelo fluxo OAuth 2.0 *authorization code* com Google, GitHub ou Microsoft. A tela de login MUST mostrar só os provedores configurados (com client id e secret definidos). A URL de retorno SHALL ser a mesma para os três provedores, e o provedor de cada login viaja no `state`.

#### Scenario: Só provedores configurados
- **WHEN** só os provedores Google e GitHub estão configurados
- **THEN** a tela de login do painel mostra os botões Google e GitHub e não mostra Microsoft

#### Scenario: Login concluído
- **WHEN** uma pessoa cadastrada como juiz conclui o login com o Google
- **THEN** ela volta para o painel com uma sessão ativa e o papel `juiz`

### Requirement: Proteção do fluxo OAuth
Cada início de login SHALL gerar um `state` aleatório, assinado e de uso único, guardado também num cookie de curta duração (10 minutos). Um retorno com `state` ausente, inválido, expirado ou diferente do cookie MUST ser recusado sem criar sessão.

#### Scenario: State forjado
- **WHEN** o retorno do OAuth chega com um `state` que não confere com o cookie
- **THEN** o login é recusado e nenhuma sessão é criada

### Requirement: Identidade verificada
O sistema SHALL extrair do provedor só identidades verificadas:
- Google: o e-mail, somente com `email_verified` verdadeiro;
- Microsoft: o `preferred_username` (UPN da conta);
- GitHub: o login do usuário e os e-mails marcados como verificados.

E-mails e logins MUST ser comparados em minúsculas. Um login sem nenhuma identidade verificada MUST ser recusado.

#### Scenario: E-mail não verificado no Google
- **WHEN** o Google devolve `email_verified` falso
- **THEN** o login é recusado

### Requirement: Usuário root
As identidades do usuário root SHALL vir da variável de ambiente `ARENA_ROOT` (JSON com `google`, `microsoft` e `github`, cada um opcional), e MUST NOT ficar em nenhum arquivo do repositório. Sem `ARENA_ROOT`, não há root via OAuth (só o acesso de emergência). Quem entra com uma dessas identidades, pelo provedor correspondente, SHALL ser admin. O root MUST NOT poder ser removido, rebaixado nem editado pelo painel.

#### Scenario: Root pela Microsoft
- **WHEN** `ARENA_ROOT` define `microsoft: root@exemplo.edu` e alguém entra pela Microsoft com `preferred_username` `root@exemplo.edu`
- **THEN** a sessão tem papel `admin` e aparece como root

#### Scenario: Root pelo GitHub
- **WHEN** `ARENA_ROOT` define `github: root-exemplo` e alguém entra pelo GitHub com o login `root-exemplo`
- **THEN** a sessão tem papel `admin`

#### Scenario: Sem ARENA_ROOT
- **WHEN** `ARENA_ROOT` não está definida
- **THEN** ninguém vira root pelo OAuth, e o painel só aceita perfis cadastrados e o acesso de emergência

#### Scenario: Identidade root em outro provedor
- **WHEN** alguém entra pelo GitHub com um e-mail verificado igual ao `microsoft` do `ARENA_ROOT`, mas com outro login
- **THEN** essa pessoa não é root, e só entra se estiver cadastrada

### Requirement: Só pessoas cadastradas entram no painel
Além do root, só SHALL entrar no painel quem tiver um perfil `admin` ou `juiz` cadastrado com um e-mail ou login do GitHub que bata com uma identidade verificada do login. Qualquer outra pessoa MUST receber "Acesso não autorizado" e não ganhar sessão. A tentativa SHALL ficar na auditoria.

#### Scenario: Pessoa não cadastrada
- **WHEN** alguém sem perfil cadastrado conclui o login com o Google
- **THEN** o painel mostra "Acesso não autorizado" e não há sessão

### Requirement: Sessão da banca
A sessão SHALL ser um cookie `HttpOnly`, `SameSite=Lax` e `Secure` (exceto em `localhost`), assinado com `ARENA_SECRET`, que expira em 12 horas. O papel MUST ser lido do cadastro a cada requisição: remover ou rebaixar uma pessoa vale na hora. SHALL existir um logout que apaga o cookie. Requisições que alteram dados MUST exigir corpo JSON e rejeitar uma origem (`Origin`) diferente da do site.

#### Scenario: Rebaixamento imediato
- **WHEN** um admin muda o perfil de uma pessoa de `admin` para `juiz` enquanto ela está logada
- **THEN** a próxima requisição dela ao painel já tem só as permissões de juiz

#### Scenario: Pedido de outra origem
- **WHEN** um formulário de outro site envia um POST para uma ação do painel
- **THEN** a ação é recusada

### Requirement: Permissões por papel
- `juiz` SHALL poder: ver o log de submissões com código-fonte e participantes, ajustar e desfazer o ajuste dos pontos de submissões, e ver o placar real (sem freeze).
- `admin` SHALL poder tudo o que o juiz pode e mais: gerenciar equipes, códigos, participantes e perfis, importar equipes e ver a auditoria.

Uma ação fora do papel MUST responder 403 sem alterar nada.

#### Scenario: Juiz tenta gerar código
- **WHEN** um juiz chama a ação de regenerar o código de uma equipe
- **THEN** a resposta é 403 e o código não muda

### Requirement: Acesso de emergência
Quando `ADMIN_TOKEN` está configurado, um pedido que apresente esse token SHALL ter as permissões do root, mesmo sem OAuth. As ações feitas assim SHALL aparecer na auditoria como `token de emergência`. Sem `ADMIN_TOKEN` configurado, esse acesso MUST NOT existir.

#### Scenario: OAuth fora do ar
- **WHEN** nenhum provedor OAuth está configurado e o admin abre o painel com o token de emergência
- **THEN** ele consegue usar todas as funções de admin

### Requirement: Sessão da equipe ligada ao código
O login da equipe SHALL continuar pelo código de acesso. O token da equipe MUST deixar de valer quando o código da equipe for regenerado ou a equipe for excluída. Nesse caso, as páginas da equipe pedem o código de novo.

#### Scenario: Código regenerado
- **WHEN** o admin regenera o código da Equipe 1 enquanto ela está logada
- **THEN** a próxima requisição da Equipe 1 com o token antigo recebe 401, e o login com o código novo funciona
