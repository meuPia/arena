# 🏁 meuPiá-arena

Plataforma para resolução de desafios de programação em **eventos de code challenge**.

O **meuPiá-arena** foi criado para apoiar competições e maratonas de programação com uma experiência simples para participantes e organizadores. A plataforma permite distribuir desafios por equipes, receber submissões, validar soluções com testes e acompanhar a evolução da competição em tempo real.

É um fork do [meuPiá Lab](https://github.com/meuPia/lab) adaptado para o contexto de eventos competitivos.

## Principais funcionalidades

- **Painel de desafios por equipe**, com acesso por login/código;
- **Desbloqueio progressivo de níveis**, permitindo organizar a competição em etapas;
- **IDE no navegador**, para programar e executar testes de exemplo sem precisar configurar ambiente local;
- **Correção automática**, com testes públicos e testes privados;
- **Pontuação por desempenho**, com melhor submissão registrada;
- **Execução isolada no servidor**, evitando que falhas em um teste afetem os demais;
- **Registro de autoria**, indicando quem trabalhou em cada solução;
- **Cooldown de tentativas**, para ajudar no controle da dinâmica da competição;
- **Placar em tempo real**, com opção de exibição para telão;
- **Modo administrativo**, para acompanhamento de submissões e operação do evento.

## Como funciona

Durante o evento, cada equipe acessa a plataforma com suas credenciais e visualiza os desafios disponíveis. As soluções podem ser desenvolvidas diretamente na interface da arena e submetidas para correção.

A avaliação combina:

- **testes de exemplo**, visíveis para os participantes;
- **testes privados**, executados apenas no servidor.

Isso permite que a plataforma ofereça feedback imediato sem expor todos os critérios de correção.

## Rodando localmente

```bash
npm install
pip install -r requirements-dev.txt
npm run validar
npm test
npm run local
```

Por padrão, sem banco configurado, a arena pode usar desafios de exemplo para desenvolvimento e testes locais.

## Estrutura de operação

A plataforma foi pensada para dois contextos principais:

### Participantes
- acesso aos desafios;
- editor no navegador;
- execução de testes de exemplo;
- envio de submissões;
- acompanhamento de progresso e pontuação.

### Organização
- cadastro e controle de equipes;
- gerenciamento do conjunto de desafios;
- execução de correção com testes privados;
- monitoramento das submissões;
- exibição de placar ao vivo;
- operação em modo de ensaio ou evento oficial.

## Deploy

A plataforma pode ser publicada em ambientes como a **Vercel**, utilizando funções para execução da correção e integração com banco de dados, como **Supabase**.

De forma geral, o deploy envolve:

1. publicar o repositório;
2. configurar o banco de dados;
3. definir variáveis de ambiente da arena;
4. cadastrar equipes e credenciais;
5. carregar os desafios do evento.

### Painel da banca (`/admin.html`)

Admin e juízes entram com **Google** ou **GitHub** (OAuth). Só entram o root (identidades na variável
secreta `ARENA_ROOT`) e as pessoas cadastradas na aba Perfis. O painel mostra o placar real (sem freeze),
as submissões com o código-fonte e, para admins, os perfis e a auditoria. O `ADMIN_TOKEN` continua
valendo como acesso de emergência, se o OAuth falhar.

Para ligar um provedor, registre um app OAuth com a URL de retorno `https://<domínio>/api/oauth_retorno`
(e `http://localhost:8787/api/oauth_retorno` para testes; no GitHub, um app por URL) e defina
`OAUTH_<PROVEDOR>_ID` e `OAUTH_<PROVEDOR>_SECRET`. Um provedor só aparece no login com as duas variáveis.

| Variável | Para quê |
|---|---|
| `OAUTH_GOOGLE_ID` / `OAUTH_GOOGLE_SECRET` | login com Google (escopos `openid email profile`) |
| `OAUTH_GITHUB_ID` / `OAUTH_GITHUB_SECRET` | login com GitHub (escopos `read:user user:email`) |
| `ARENA_ROOT` | JSON com as identidades do root, ex.: `{"google": "voce@gmail.com", "github": "seu-login"}`. Só na Vercel/`.env.local` |
| `ARENA_URL` | opcional: origem fixa usada na URL de retorno (padrão: o host da requisição) |

O `npm run local` lê do `.env.local` só essas variáveis (nunca as do banco).

## Desenvolvimento e testes

O repositório pode incluir desafios fictícios para desenvolvimento local, enquanto os desafios oficiais do evento permanecem armazenados de forma privada.

Isso facilita a evolução da plataforma sem comprometer o conteúdo real das competições.

## 🙌 Créditos

> **meuPiá** é desenvolvido com ❤️ por **[@henryhamon](https://github.com/henryhamon)**.