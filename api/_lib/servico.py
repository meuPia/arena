"""Casos de uso da arena (sem HTTP): login, missões, submissão, placar."""
import json
import secrets
import time

from . import arena, juiz, store
from .web import Erro, emitir_token


def ajustes(db):
    """{id da submissão: ajuste da banca} desta rodada."""
    return {sid: json.loads(v) for sid, v in db.hgetall(store.k_ajustes()).items()}


def _aceitas(db, eid, ajustes_=None, todos=None):
    """Submissões aceitas da equipe (registros compactos, sem código-fonte), com os pontos EFETIVOS:
    é aqui, num ponto só, que os ajustes da banca entram em melhor, placar, freeze e desbloqueio."""
    brutas = [json.loads(x) for x in db.lrange(store.k_aceitas(eid), 0, -1)]
    return arena.aplicar_ajustes(brutas, ajustes(db) if ajustes_ is None else ajustes_,
                                 arena.desafios(db) if todos is None else todos)


def _estado(db, eid):
    aceitas = _aceitas(db, eid)
    tentativas = {c: int(n) for c, n in db.hgetall(store.k_tentativas(eid)).items()}
    ultima = {c: float(t) for c, t in db.hgetall(store.k_ultima(eid)).items()}
    return aceitas, tentativas, ultima


def _resumo(r):
    """Melhor submissão de um módulo, como o painel/IDE mostram (ou None)."""
    return None if r is None else {"pontos": r["pontos"], "completo": r["completo"], "caracteres": r["caracteres"]}


def _equipe(eid, db=None):
    e = arena.equipes(db).get(eid)
    if not e:
        raise Erro(401, "Equipe não encontrada. Entre novamente.")
    return e


LOGIN_JANELA = 600  # segundos
LOGIN_MAX_ERROS = 30  # por IP e janela: o laboratório inteiro pode sair pelo mesmo IP


def login(codigo, ip="", db=None, agora=None):
    """Troca o código da equipe por um token. Erros contam por IP: passou do limite, nem o
    código certo entra até a janela virar (senão a força bruta continuaria)."""
    db = db or store.abrir()
    agora = agora if agora is not None else time.time()
    chave, campo = store.k_login(int(agora // LOGIN_JANELA)), ip or "?"
    if int(db.hget(chave, campo) or 0) >= LOGIN_MAX_ERROS:
        raise Erro(429, "Muitas tentativas de login. Aguarde alguns minutos.")
    e = arena.equipe_por_codigo(codigo, db)
    if not e:
        db.hincrby(chave, campo, 1)
        raise Erro(401, "Código de equipe inválido.")
    return {"token": emitir_token(e["id"], e.get("versao", 0)), "equipe": {"id": e["id"], "nome": e["nome"]}}


def missoes(eid, db=None):
    db = db or store.abrir()
    e = _equipe(eid, db)
    cfg, todos = arena.config(), arena.desafios(db)
    jan = arena.janela(cfg)
    aceitas, tentativas, ultima = _estado(db, eid)
    melhores = arena.melhores(aceitas)
    contagem = arena.contagem_desbloqueio(melhores, todos, cfg)
    niveis = []
    for nivel in cfg["niveis"]:
        liberado = jan["situacao"] != "antes" and arena.nivel_liberado(nivel, contagem, cfg)
        itens = [{
            "codigo": d["codigo"], "modulo": d["modulo"], "pontos": d["pontos"],
            "problemaTecnico": d["problemaTecnico"] if liberado else None,
            "melhor": _resumo(melhores.get(d["codigo"])),
            "completo": bool(melhores.get(d["codigo"], {}).get("completo")),
            "tentativas": tentativas.get(d["codigo"], 0),
            "espera": arena.cooldown_restante(tentativas.get(d["codigo"], 0), ultima.get(d["codigo"]), cfg),
        } for d in todos.values() if d["nivel"] == nivel]
        niveis.append({
            "nivel": nivel, "liberado": liberado, "itens": itens,
            "dica": "" if liberado else arena.falta_para_liberar(nivel, contagem, cfg),
        })
    pontos = sum(r["pontos"] for c, r in melhores.items() if c in todos)
    return {
        "evento": cfg["evento"], "janela": jan,
        "equipe": {"id": eid, "nome": e["nome"], "integrantes": e.get("integrantes", []), "pontos": pontos},
        "niveis": niveis,
    }


def missao(eid, codigo, db=None):
    db = db or store.abrir()
    e = _equipe(eid, db)
    cfg, todos = arena.config(), arena.desafios(db)
    d = todos.get(codigo)
    if not d:
        raise Erro(404, "Missão não encontrada.")
    aceitas, tentativas, ultima = _estado(db, eid)
    melhores = arena.melhores(aceitas)
    contagem = arena.contagem_desbloqueio(melhores, todos, cfg)
    jan = arena.janela(cfg)
    if jan["situacao"] == "antes":
        raise Erro(403, "A Code Arena ainda não abriu.")
    if not arena.nivel_liberado(d["nivel"], contagem, cfg):
        raise Erro(403, arena.falta_para_liberar(d["nivel"], contagem, cfg))
    out = arena.publico(d)
    out.update({
        "melhor": _resumo(melhores.get(codigo)),
        "completo": bool(melhores.get(codigo, {}).get("completo")),
        "tentativas": tentativas.get(codigo, 0),
        "espera": arena.cooldown_restante(tentativas.get(codigo, 0), ultima.get(codigo), cfg),
        "integrantes": e.get("integrantes", []),
        "situacao": jan["situacao"],
    })
    return out


def submeter(eid, codigo, fonte, participantes, db=None, agora=None):
    db = db or store.abrir()
    agora = agora if agora is not None else time.time()
    e = _equipe(eid, db)
    cfg, todos = arena.config(), arena.desafios(db)
    d = todos.get(codigo)
    if not d:
        raise Erro(404, "Missão não encontrada.")
    jan = arena.janela(cfg, agora)
    if jan["situacao"] != "aberta":
        raise Erro(403, "Submissões fechadas." if jan["situacao"] == "encerrada" else "A Code Arena ainda não abriu.")
    if not isinstance(fonte, str) or not fonte.strip():
        raise Erro(400, "Código vazio.")
    if not participantes:
        raise Erro(400, "Marque quem trabalhou nesta solução.")

    aceitas, tentativas, ultima = _estado(db, eid)
    contagem = arena.contagem_desbloqueio(arena.melhores(aceitas), todos, cfg)
    if not arena.nivel_liberado(d["nivel"], contagem, cfg):
        raise Erro(403, arena.falta_para_liberar(d["nivel"], contagem, cfg))
    espera = arena.cooldown_restante(tentativas.get(codigo, 0), ultima.get(codigo), cfg, agora)
    if espera > 0:
        return {"status": "cooldown", "espera": espera,
                "mensagem": f"Aguarde {espera} s para submeter este módulo novamente."}

    seg = arena.segredos(db, codigo)
    if not seg or not seg.get("testesExtras", "").strip():
        # Sem bateria extra o juiz daria "completo" com 0 de 0: nunca julgar assim.
        raise Erro(503, "Este módulo está sem bateria de testes. Avise a organização.")

    # Registra a tentativa ANTES de julgar (duas abas ao mesmo tempo também contam).
    n = db.hincrby(store.k_tentativas(eid), codigo, 1)
    db.hset(store.k_ultima(eid), codigo, agora)

    r = juiz.julgar(fonte, d["testesPublicos"], seg["testesExtras"])
    sid = secrets.token_hex(6)  # mesmo id no log e em aceitas (o painel abre a submissão por ele)
    pontos = 0
    if r["status"] == "aceito":
        pontos = arena.pontos_submissao(d, r["extras"]["aprovados"], r["extras"]["total"], cfg)
        registro = {"id": sid, "t": agora, "codigo": codigo, "pontos": pontos,
                    "completo": r["completo"], "caracteres": r["caracteres"]}
        db.lpush(store.k_aceitas(eid), json.dumps(registro))
        aceitas.append(registro)

    db.lpush(store.k_log(), json.dumps({
        "id": sid, "t": agora, "equipe": eid, "nome": e["nome"], "codigo": codigo, "tentativa": n,
        "status": r["status"], "exemplos": r["exemplos"], "extras": r["extras"],
        "pontos": pontos, "completo": r["completo"], "caracteres": r["caracteres"],
        "participantes": list(participantes)[:10], "fonte": fonte[:juiz.TAMANHO_MAX_CODIGO],
    }, ensure_ascii=False))

    r["tentativa"] = n
    r["pontos"] = pontos
    r["pontosModulo"] = d["pontos"]
    r["melhor"] = _resumo(arena.melhores(aceitas).get(codigo))
    r["espera"] = arena.cooldown_restante(n, agora, cfg, agora)
    return r


def placar(admin=False, db=None, agora=None):
    db = db or store.abrir()
    cfg, todos = arena.config(), arena.desafios(db)
    jan = arena.janela(cfg, agora)
    congelado = (not admin and not arena.modo_ensaio() and jan["agora"] >= jan["freeze"]
                 and not _revelado())
    equipes = {eid: {"nome": e["nome"]} for eid, e in arena.equipes(db).items()}
    ajs = ajustes(db)
    aceitas = {eid: _aceitas(db, eid, ajs, todos) for eid in equipes}
    linhas = arena.placar(equipes, aceitas, todos, cfg, ate=jan["freeze"] if congelado else None)
    totais = {n: sum(1 for d in todos.values() if d["nivel"] == n) for n in cfg["niveis"]}
    return {"evento": cfg["evento"], "janela": jan, "congelado": congelado, "totais": totais, "linhas": linhas}


def _com_ajuste(s, ajs):
    """Entrada do log com `pontosEfetivos` (calculados ou ajustados) e o `ajuste`, se houver."""
    a = ajs.get(s.get("id")) if s.get("id") else None
    s["ajuste"] = a
    s["pontosEfetivos"] = a["pontos"] if a else s.get("pontos", 0)
    return s


def submissao(sid, db=None):
    """Uma entrada do log COM o código-fonte e o ajuste (só para a banca), ou None."""
    db = db or store.abrir()
    for x in db.lrange(store.k_log(), 0, -1):
        s = json.loads(x)
        if s.get("id") == sid:
            return _com_ajuste(s, ajustes(db))
    return None


def submissoes(limite=200, db=None):
    """Log para a banca (mais recente primeiro), sem o código-fonte (fica só no banco), com os ajustes."""
    db = db or store.abrir()
    ajs = ajustes(db)
    out = []
    for x in db.lrange(store.k_log(), 0, limite - 1):
        s = json.loads(x)
        s.pop("fonte", None)
        out.append(_com_ajuste(s, ajs))
    return out


def _revelado():
    import os
    return os.environ.get("ARENA_REVELAR", "") == "1"
