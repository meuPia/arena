"""Casos de uso do painel da banca (sem HTTP): placar real, submissões, perfis e auditoria.

Toda ação passa por `executar`, que confere a permissão (tabela PERMISSOES) antes de qualquer
leitura ou gravação. Ações que alteram dados vão para a auditoria, sem código-fonte.
"""
import json
import re
import secrets
import time

from . import arena, auth, servico, store
from .web import Erro

PERMISSOES = {
    # leitura
    "placar": "juiz", "submissoes": "juiz", "submissao": "juiz",
    "perfis": "admin", "auditoria": "admin", "equipes": "admin",
    # escrita
    "salvar_perfil": "admin", "remover_perfil": "admin",
    "criar_equipe": "admin", "editar_equipe": "admin", "excluir_equipe": "admin",
    "regenerar_codigo": "admin", "importar_equipes": "admin",
    "participantes": "admin", "salvar_participante": "admin", "remover_participante": "admin",
    "ajustar": "juiz", "desfazer_ajuste": "juiz",
}
_NIVEL = {"juiz": 1, "admin": 2}
_RE_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_RE_GITHUB = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,37}[a-z0-9])?$")


def auditar(db, autor, acao, alvo="", resumo=""):
    db.lpush(store.k_auditoria(), json.dumps({
        "t": time.time(), "autor": autor.get("nome", ""), "papel": autor.get("papel"),
        "provedor": autor.get("provedor"), "acao": acao, "alvo": alvo, "resumo": resumo}, ensure_ascii=False))


def _eh_root(email="", github=""):
    """O perfil usaria uma identidade do root? (o root não pode ser criado, editado nem removido)"""
    r = auth.root()
    return any(f"{p}:{email}" in r for p in ("google", "microsoft") if email) or bool(github and f"github:{github}" in r)


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
    if _eh_root(email, github):
        raise Erro(403, "O root não pode ser editado pelo painel.")
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
    if _eh_root(email):
        raise Erro(403, "O root não pode ser removido.")
    if email not in auth.perfis(db):
        raise Erro(404, "Perfil não encontrado.")
    db.hdel(store.k_usuarios(), email)
    auditar(db, autor, "remover_perfil", email)
    return {"ok": True}


# ---------------- equipes ----------------

def _nome_equipe(dados, db, ignorar=None):
    nome = " ".join(str(dados.get("nome", "")).split())
    if not nome or len(nome) > 40:
        raise Erro(400, "Informe o nome da equipe (até 40 caracteres).")
    if any(e["nome"].lower() == nome.lower() and eid != ignorar for eid, e in arena.equipes_do_banco(db).items()):
        raise Erro(409, "Já existe uma equipe com esse nome.")
    return nome


def _equipe_do_banco(db, eid):
    e = arena.equipes_do_banco(db).get(str(eid or ""))
    if not e:
        raise Erro(404, "Equipe não encontrada no banco. Importe as equipes antes de editar.")
    return e


def _gravar_equipe(db, e):
    db.hset(store.k_equipes(), e["id"], json.dumps(
        {k: e[k] for k in ("id", "nome", "codigo", "versao", "criadaEm") if k in e}, ensure_ascii=False))


def _submissoes_da_equipe(db, eid):
    return sum(int(n) for n in db.hgetall(store.k_tentativas(eid)).values())


def _equipes(_autor, _dados, db):
    banco = bool(arena.equipes_do_banco(db))
    origem = "banco" if banco else arena.equipes_arquivo()[1]
    eqs = arena.equipes(db)
    vivo = {l["id"]: l for l in servico.placar(admin=True, db=db)["linhas"]}
    linhas = []
    for eid, e in eqs.items():
        ultima = [float(t) for t in db.hgetall(store.k_ultima(eid)).values()]
        linhas.append({
            "id": eid, "nome": e["nome"], "codigo": e["codigo"], "integrantes": e.get("integrantes", []),
            "pontos": vivo.get(eid, {}).get("pontos", 0), "completos": vivo.get(eid, {}).get("completos", 0),
            "submissoes": _submissoes_da_equipe(db, eid), "ultimaSubmissao": max(ultima) if ultima else None,
        })
    linhas.sort(key=lambda l: l["nome"].lower())
    return {"origem": origem, "equipes": linhas}


def _criar_equipe(autor, dados, db):
    banco = arena.equipes_do_banco(db)
    if not banco and arena.equipes_arquivo()[1] in ("env", "arquivo"):
        raise Erro(409, "As equipes ainda vêm de ARENA_EQUIPES/arquivo. Importe-as antes de criar outras.")
    nome = _nome_equipe(dados, db)
    e = {"id": "eq-" + secrets.token_hex(4), "nome": nome, "versao": 0, "criadaEm": time.time(),
         "codigo": arena.gerar_codigo(len(banco), [x["codigo"] for x in banco.values()])}
    _gravar_equipe(db, e)
    auditar(db, autor, "criar_equipe", nome)
    return {"ok": True, "id": e["id"]}


def _editar_equipe(autor, dados, db):
    e = _equipe_do_banco(db, dados.get("id"))
    antigo, e["nome"] = e["nome"], _nome_equipe(dados, db, ignorar=e["id"])
    _gravar_equipe(db, e)
    auditar(db, autor, "editar_equipe", e["nome"], f"nome: {antigo} → {e['nome']}")
    return {"ok": True}


def _excluir_equipe(autor, dados, db):
    e = _equipe_do_banco(db, dados.get("id"))
    if _submissoes_da_equipe(db, e["id"]) or db.lrange(store.k_aceitas(e["id"]), 0, 0):
        raise Erro(409, "A equipe já submeteu e não pode ser excluída.")
    removidos = [pid for pid, p in arena.participantes(db).items() if p.get("equipe") == e["id"]]
    for pid in removidos:
        db.hdel(store.k_participantes(), pid)
    db.hdel(store.k_equipes(), e["id"])
    auditar(db, autor, "excluir_equipe", e["nome"], f"{len(removidos)} participante(s) removido(s)")
    return {"ok": True}


def _regenerar_codigo(autor, dados, db):
    e = _equipe_do_banco(db, dados.get("id"))
    outros = [x["codigo"] for x in arena.equipes_do_banco(db).values()]
    indice = arena.PALAVRAS.index(e["codigo"].split("-")[0]) if e["codigo"].split("-")[0] in arena.PALAVRAS else 0
    e["codigo"] = arena.gerar_codigo(indice, outros)
    e["versao"] = int(e.get("versao", 0)) + 1  # derruba os tokens emitidos com o código antigo
    _gravar_equipe(db, e)
    auditar(db, autor, "codigo_regenerado", e["nome"])  # nunca o código em si
    return {"ok": True, "codigo": e["codigo"]}


def _participante_de_rotulo(rotulo, eid):
    """"Ana (2º)" -> {nome: Ana, semestre: 2º} (formato de integrantes do ARENA_EQUIPES)."""
    m = re.fullmatch(r"\s*(.+?)\s*\(([^()]{1,10})\)\s*", rotulo)
    nome, semestre = (m.group(1), m.group(2).strip()) if m else (rotulo.strip(), "")
    return {"id": "pt-" + secrets.token_hex(4), "equipe": eid, "nome": nome, "semestre": semestre, "email": ""}


def _importar_equipes(autor, _dados, db):
    if arena.equipes_do_banco(db):
        raise Erro(409, "O banco já tem equipes: a importação só vale para o banco vazio.")
    lista, origem = arena.equipes_arquivo()
    agora = time.time()
    for e in lista:
        _gravar_equipe(db, {"id": e["id"], "nome": e["nome"], "codigo": e["codigo"], "versao": 0, "criadaEm": agora})
        for rotulo in e.get("integrantes", []):
            p = _participante_de_rotulo(rotulo, e["id"])
            db.hset(store.k_participantes(), p["id"], json.dumps(p, ensure_ascii=False))
    auditar(db, autor, "importar_equipes", origem, f"{len(lista)} equipe(s)")
    return {"ok": True, "importadas": len(lista)}


# ---------------- participantes ----------------

def _participantes(_autor, _dados, db):
    eqs = arena.equipes_do_banco(db)
    lista = [{**p, "nomeEquipe": eqs.get(p["equipe"], {}).get("nome", "?")} for p in arena.participantes(db).values()]
    lista.sort(key=lambda p: (p["nomeEquipe"].lower(), p["nome"].lower()))
    return {"participantes": lista}


def _salvar_participante(autor, dados, db):
    """Cria (sem id) ou edita (com id), inclusive trocando de equipe. Submissões já feitas não mudam."""
    nome = " ".join(str(dados.get("nome", "")).split())
    semestre = str(dados.get("semestre", "")).strip()
    email = str(dados.get("email", "") or "").strip().lower()
    equipe = _equipe_do_banco(db, dados.get("equipe"))
    if not nome or len(nome) > 60:
        raise Erro(400, "Informe o nome do participante (até 60 caracteres).")
    if not semestre or len(semestre) > 10:
        raise Erro(400, "Informe o semestre (ex.: 2º).")
    if email and (not _RE_EMAIL.match(email) or len(email) > 120):
        raise Erro(400, "E-mail inválido.")
    pid = str(dados.get("id") or "")
    existentes = arena.participantes(db)
    if pid and pid not in existentes:
        raise Erro(404, "Participante não encontrado.")
    novo = not pid
    pid = pid or "pt-" + secrets.token_hex(4)
    db.hset(store.k_participantes(), pid, json.dumps(
        {"id": pid, "equipe": equipe["id"], "nome": nome, "semestre": semestre, "email": email}, ensure_ascii=False))
    auditar(db, autor, "criar_participante" if novo else "editar_participante", nome, f"equipe={equipe['nome']}")
    return {"ok": True, "id": pid}


def _remover_participante(autor, dados, db):
    pid = str(dados.get("id", ""))
    p = arena.participantes(db).get(pid)
    if not p:
        raise Erro(404, "Participante não encontrado.")
    db.hdel(store.k_participantes(), pid)
    auditar(db, autor, "remover_participante", p["nome"])
    return {"ok": True}


# ---------------- ajuste de pontos ----------------

def _aceita(db, sid):
    """(entrada do log, registro bruto em aceitas) de uma submissão ACEITA, ou Erro."""
    s = servico.submissao(sid, db=db)
    if not s:
        raise Erro(404, "Submissão não encontrada.")
    reg = next((json.loads(x) for x in db.lrange(store.k_aceitas(s["equipe"]), 0, -1)
                if json.loads(x).get("id") == sid), None)
    if s.get("status") != "aceito" or reg is None:
        raise Erro(409, "Só submissões aceitas podem ter os pontos ajustados.")
    return s, reg


def _ajustar(autor, dados, db):
    sid = str(dados.get("id", ""))
    s, reg = _aceita(db, sid)
    maximo = arena.desafios(db).get(reg["codigo"], {}).get("pontos", reg["pontos"])
    bruto = dados.get("pontos")
    if isinstance(bruto, bool) or not re.fullmatch(r"\d+", str(bruto).strip()):
        raise Erro(400, f"Pontos devem ser um inteiro de 0 a {maximo}.")
    pontos = int(str(bruto).strip())
    if pontos > maximo:
        raise Erro(400, f"Pontos devem ser um inteiro de 0 a {maximo}.")
    motivo = " ".join(str(dados.get("motivo", "")).split())
    if len(motivo) < 5 or len(motivo) > 300:
        raise Erro(400, "Informe o motivo do ajuste (de 5 a 300 caracteres).")
    db.hset(store.k_ajustes(), sid, json.dumps({
        "pontos": pontos, "pontosJuiz": reg["pontos"], "motivo": motivo, "t": time.time(),
        "autor": autor.get("nome", ""), "papel": autor.get("papel"), "provedor": autor.get("provedor"),
        "equipe": s["equipe"], "codigo": reg["codigo"]}, ensure_ascii=False))
    auditar(db, autor, "ajustar", f"{s.get('nome', s['equipe'])} · {reg['codigo']}",
            f"{reg['pontos']} → {pontos}: {motivo}")
    return {"ok": True}


def _desfazer_ajuste(autor, dados, db):
    sid = str(dados.get("id", ""))
    a = servico.ajustes(db).get(sid)
    if not a:
        raise Erro(404, "Essa submissão não tem ajuste.")
    db.hdel(store.k_ajustes(), sid)
    auditar(db, autor, "desfazer_ajuste", f"{a.get('equipe')} · {a.get('codigo')}",
            f"{a['pontos']} → {a['pontosJuiz']}")
    return {"ok": True}


def _auditoria(_autor, dados, db):
    limite = min(int(dados.get("limite") or 300), 1000)
    return {"auditoria": [json.loads(x) for x in db.lrange(store.k_auditoria(), 0, limite - 1)]}


_ACOES = {
    "placar": _placar, "submissoes": _submissoes, "submissao": _submissao,
    "perfis": _perfis, "auditoria": _auditoria,
    "salvar_perfil": _salvar_perfil, "remover_perfil": _remover_perfil,
    "equipes": _equipes, "criar_equipe": _criar_equipe, "editar_equipe": _editar_equipe,
    "excluir_equipe": _excluir_equipe, "regenerar_codigo": _regenerar_codigo, "importar_equipes": _importar_equipes,
    "participantes": _participantes, "salvar_participante": _salvar_participante,
    "remover_participante": _remover_participante,
    "ajustar": _ajustar, "desfazer_ajuste": _desfazer_ajuste,
}
