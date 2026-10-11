"""Casos de uso do painel da banca (sem HTTP): placar real, submissões, perfis e auditoria.

Toda ação passa por `executar`, que confere a permissão (tabela PERMISSOES) antes de qualquer
leitura ou gravação. Ações que alteram dados vão para a auditoria, sem código-fonte.
"""
import json
import re
import time

from . import auth, servico, store
from .web import Erro

PERMISSOES = {
    # leitura
    "placar": "juiz", "submissoes": "juiz", "submissao": "juiz",
    "perfis": "admin", "auditoria": "admin",
    # escrita
    "salvar_perfil": "admin", "remover_perfil": "admin",
}
_NIVEL = {"juiz": 1, "admin": 2}
_RE_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_RE_GITHUB = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,37}[a-z0-9])?$")


def auditar(db, autor, acao, alvo="", resumo=""):
    db.lpush(store.k_auditoria(), json.dumps({
        "t": time.time(), "autor": autor.get("nome", ""), "papel": autor.get("papel"),
        "acao": acao, "alvo": alvo, "resumo": resumo}, ensure_ascii=False))


def executar(acao, autor, dados=None, db=None):
    db = db or store.abrir()
    dados = dados or {}
    exigido = PERMISSOES.get(acao)
    if exigido is None:
        raise Erro(400, "Ação desconhecida.")
    if _NIVEL.get(autor.get("papel"), 0) < _NIVEL[exigido]:
        raise Erro(403, "Seu perfil não pode fazer isso.")
    return _ACOES[acao](autor, dados, db)


def _placar(_autor, _dados, db):
    return servico.placar(admin=True, db=db)


def _submissoes(_autor, dados, db):
    return {"submissoes": servico.submissoes(limite=min(int(dados.get("limite") or 500), 1000), db=db)}


def _submissao(_autor, dados, db):
    s = servico.submissao(str(dados.get("id", "")), db=db)
    if not s:
        raise Erro(404, "Submissão não encontrada.")
    return s


def _perfis(_autor, _dados, db):
    return {
        "root": sorted(auth.root()),
        "perfis": sorted(auth.perfis(db).values(), key=lambda p: (p.get("papel") != "admin", p.get("nome", ""))),
    }


def _salvar_perfil(autor, dados, db):
    email = str(dados.get("email", "")).strip().lower()
    nome = str(dados.get("nome", "")).strip()
    github = str(dados.get("github", "") or "").strip().lower().lstrip("@")
    papel = dados.get("papel")
    if not _RE_EMAIL.match(email) or len(email) > 120:
        raise Erro(400, "E-mail inválido.")
    if not nome or len(nome) > 80:
        raise Erro(400, "Informe o nome (até 80 caracteres).")
    if github and not _RE_GITHUB.match(github):
        raise Erro(400, "Login do GitHub inválido.")
    if papel not in auth.PAPEIS:
        raise Erro(400, "Papel deve ser admin ou juiz.")
    existentes = auth.perfis(db)
    if github and any(p.get("github") == github and e != email for e, p in existentes.items()):
        raise Erro(409, "Esse login do GitHub já está em outro perfil.")
    novo = email not in existentes
    db.hset(store.k_usuarios(), email, json.dumps(
        {"email": email, "nome": nome, "github": github, "papel": papel}, ensure_ascii=False))
    auditar(db, autor, "criar_perfil" if novo else "editar_perfil", email, f"papel={papel}")
    return {"ok": True}


def _remover_perfil(autor, dados, db):
    email = str(dados.get("email", "")).strip().lower()
    if email not in auth.perfis(db):
        raise Erro(404, "Perfil não encontrado.")
    db.hdel(store.k_usuarios(), email)
    auditar(db, autor, "remover_perfil", email)
    return {"ok": True}


def _auditoria(_autor, dados, db):
    limite = min(int(dados.get("limite") or 300), 1000)
    return {"auditoria": [json.loads(x) for x in db.lrange(store.k_auditoria(), 0, limite - 1)]}


_ACOES = {
    "placar": _placar, "submissoes": _submissoes, "submissao": _submissao,
    "perfis": _perfis, "auditoria": _auditoria,
    "salvar_perfil": _salvar_perfil, "remover_perfil": _remover_perfil,
}
