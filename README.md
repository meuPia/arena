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

## Desenvolvimento e testes

O repositório pode incluir desafios fictícios para desenvolvimento local, enquanto os desafios oficiais do evento permanecem armazenados de forma privada.

Isso facilita a evolução da plataforma sem comprometer o conteúdo real das competições.

## 🙌 Créditos

> **meuPiá** é desenvolvido com ❤️ por **[@henryhamon](https://github.com/henryhamon)**.