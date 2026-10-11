## Why

Hoje a organização da Code Arena depende de arquivos e variáveis de ambiente. As equipes saem do `scripts/gerar_equipes.py` para `ARENA_EQUIPES` (cada mudança exige redeploy). A visão de admin é uma URL com um token compartilhado (`/placar.html?admin=TOKEN`). E não há como corrigir a pontuação de uma submissão: por exemplo, zerar uma solução cujo integrante sorteado não soube explicar. Para o evento de 21/10/2026, a banca (admin e juízes) precisa de um painel com login individual, papéis e registro de quem fez o quê.

## What Changes

- Novo **painel administrativo** (`admin.html`) com login OAuth (Google, GitHub ou Microsoft). Só entram as pessoas cadastradas com perfil `admin` ou `juiz`, além do usuário **root**.
- **Root fixo**, que não pode ser removido nem rebaixado e sempre é admin. As identidades dele (uma por provedor: e-mail Google, conta Microsoft e login GitHub) vêm da variável secreta `ARENA_ROOT` na Vercel e **nunca** ficam no repositório, que é público.
- **Cadastro de perfis**:
  - `admin` e `juiz`: pessoas que entram via OAuth, identificadas pelo e-mail e, opcionalmente, pelo login do GitHub;
  - `participante`: aluno ligado a uma equipe (nome, semestre e e-mail opcional). Não tem login próprio: a equipe continua entrando com o código.
- **Equipes**: cadastro, edição, listagem (com integrantes, pontos e situação) e exclusão de equipes sem submissões. **Geração e regeneração do código** de acesso de cada equipe. Regenerar o código encerra as sessões abertas com o código antigo.
- **BREAKING (operação)** — As equipes passam a ficar no banco (Redis). `ARENA_EQUIPES` e `arena/equipes.json` viram só uma fonte de importação inicial: são lidos enquanto o banco não tiver equipes, e o painel tem um botão de importar.
- **Ajuste de pontos de submissões**: admin e juiz podem sobrescrever os pontos de uma submissão aceita (de 0 aos pontos do módulo), com motivo obrigatório, e desfazer o ajuste. O ajuste vale para a melhor submissão, o placar (vivo e congelado) e o desbloqueio.
- **Papéis**:
  - `juiz`: vê o log de submissões com código-fonte, ajusta pontos e vê o placar real;
  - `admin`: tudo isso mais equipes, códigos e perfis.
- **Auditoria**: toda ação do painel (login, cadastro, código gerado, ajuste) fica registrada com autor e horário.
- O placar real (sem freeze) passa a ser liberado pela sessão de admin ou juiz. `ADMIN_TOKEN` continua aceito como acesso de emergência (equivale ao root), para o caso de o OAuth falhar no dia do evento.

## Capabilities

### New Capabilities
- `arena-autenticacao`: login OAuth da banca (Google, GitHub, Microsoft), identificação por e-mail verificado ou login do GitHub, usuário root, sessão, papéis e permissões, acesso de emergência por `ADMIN_TOKEN` e sessão da equipe ligada à versão do código.
- `arena-admin`: painel administrativo, com equipes e códigos, participantes, perfis de admin e juiz, log de submissões, ajuste de pontos e auditoria.

### Modified Capabilities
- `arena-pontuacao`: novo requisito de ajuste manual de pontos. "Placar a partir das submissões aceitas" e "Freeze" passam a falar em admin **ou juiz** (sessão do painel) em vez de "admin".
- `arena-interface`: "Log do admin" sai do `/placar.html?admin=...` e vai para o painel administrativo, com a coluna de ajuste.

## Impact

- **Backend**:
  - novos `api/oauth_inicio.py`, `api/oauth_retorno.py`, `api/sessao.py` e `api/admin.py` (ações do painel);
  - `api/_lib/web.py`: redirecionamento, cookies e sessão da banca;
  - novo `api/_lib/auth.py` (provedores OAuth, papéis e root) e novo `api/_lib/admin.py` (casos de uso);
  - `api/_lib/arena.py`: equipes no banco e ajustes no placar;
  - `api/_lib/servico.py`: login da equipe com a versão do código e um id para cada submissão;
  - `api/_lib/store.py`: `hdel` e chaves novas;
  - `api/placar.py`: placar real pela sessão.
- **Frontend**: novos `admin.html` e `src/arena/admin.js`. Mudam `src/arena/placar.js` (o log sai daqui), `vite.config.js` (quarta página) e `src/arena/arena.css`.
- **Config/infra**: as novas variáveis são `ARENA_ROOT` (JSON com as identidades do root), `OAUTH_GOOGLE_*`, `OAUTH_GITHUB_*`, `OAUTH_MICROSOFT_*` e `ARENA_URL`. Os apps OAuth precisam ser registrados nos três provedores, com a URL de retorno da Vercel. `scripts/gerar_equipes.py` fica como alternativa offline.
- **Prazo**: o piloto é em 11/10 e o evento em 21/10. Registrar os apps OAuth, principalmente na Microsoft, pode depender de terceiros. Por isso o `ADMIN_TOKEN` continua funcionando.
- **Testes e docs**: novo `tests/test_admin.py`, mais `README.md` e `CLAUDE.md` (painel, variáveis e regras de acesso).
- Sem mudança no juiz, nos desafios, na IDE nem no meupia-core.
