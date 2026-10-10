-- Banco da Code Arena no Supabase (Postgres acessado pela API REST / PostgREST).
-- Rode uma vez no SQL Editor do projeto. É idempotente: pode rodar de novo sem perder dados.
--
-- O servidor (api/_lib/store.py) imita os comandos de Redis que a arena usa:
--   arena_hash  -> HGETALL / HSET / HSETNX / HINCRBY   (tentativas, última submissão, ...)
--   arena_lista -> LPUSH / LRANGE                      (submissões aceitas, log com código-fonte)
-- `chave` já vem com o prefixo ARENA_PREFIXO (ex.: "evento:aceitas:equipe1").
--
-- SEGURANÇA: o log guarda código-fonte das equipes. As tabelas ficam com RLS ligado e
-- SEM políticas, e sem permissão para anon/authenticated: só a chave secreta
-- (service_role), usada apenas nas funções da Vercel, lê e grava.

create table if not exists public.arena_hash (
  chave text not null,
  campo text not null,
  valor text not null,
  primary key (chave, campo)
);

create table if not exists public.arena_lista (
  id bigint generated always as identity primary key,
  chave text not null,
  valor text not null,
  criado timestamptz not null default now()
);

create index if not exists arena_lista_chave_id on public.arena_lista (chave, id desc);

alter table public.arena_hash enable row level security;
alter table public.arena_lista enable row level security;
revoke all on table public.arena_hash, public.arena_lista from anon, authenticated;

-- HINCRBY atômico (duas abas submetendo ao mesmo tempo contam duas tentativas).
create or replace function public.arena_hincrby(p_chave text, p_campo text, p_n bigint default 1)
returns bigint
language sql
set search_path = ''
as $$
  insert into public.arena_hash as h (chave, campo, valor)
  values (p_chave, p_campo, p_n::text)
  on conflict (chave, campo)
  do update set valor = (h.valor::bigint + excluded.valor::bigint)::text
  returning valor::bigint;
$$;

revoke execute on function public.arena_hincrby(text, text, bigint) from public, anon, authenticated;
grant execute on function public.arena_hincrby(text, text, bigint) to service_role;
