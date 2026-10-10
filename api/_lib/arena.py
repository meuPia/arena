"""Dados e regras da Code Arena: desafios, equipes, horário, desbloqueio, cooldown e placar."""
import json
import os
import time
from datetime import datetime

from . import store

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIR_ARENA = os.path.join(RAIZ, "arena")
DIR_EXEMPLOS = os.path.join(DIR_ARENA, "exemplos")

# O que a equipe pode receber (arena.publico) ...
CAMPOS_PUBLICOS = ("codigo", "id", "modulo", "problemaTecnico", "nivel", "pontos", "formato",
                   "tempoEsperado", "titulo", "descricao", "codigoInicial", "testesPublicos")
# ... o que fica no registro público do banco (inclui metadados internos) ...
CAMPOS_REGISTRO = CAMPOS_PUBLICOS + ("inspiradoEm",)
# ... e o que fica no registro secreto: só para julgar e para o admin.
CAMPOS_SEGREDO = ("testesExtras", "gabarito")
TTL_DESAFIOS = 30  # segundos: edição no banco chega às equipes em até 30 s


def _ler_json(caminho):
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


MODOS_PONTUACAO = ("proporcional", "completo")
MODOS_DESBLOQUEIO = ("aceito", "completo")


def validar_config(cfg):
    """Completa os padrões de pontuação/desbloqueio e falha cedo com valor desconhecido."""
    cfg.setdefault("pontuacao", {}).setdefault("modo", "proporcional")
    cfg.setdefault("desbloqueioConta", "aceito")
    if cfg["pontuacao"]["modo"] not in MODOS_PONTUACAO:
        raise ValueError(f"pontuacao.modo inválido: {cfg['pontuacao']['modo']!r} (use {MODOS_PONTUACAO})")
    if cfg["desbloqueioConta"] not in MODOS_DESBLOQUEIO:
        raise ValueError(f"desbloqueioConta inválido: {cfg['desbloqueioConta']!r} (use {MODOS_DESBLOQUEIO})")
    return cfg


def config():
    return validar_config(_ler_json(os.path.join(DIR_ARENA, "config.json")))


_CACHE = {}


def _id_banco(db):
    return (type(db).__name__, getattr(db, "caminho", None) or getattr(db, "base", None) or getattr(db, "url", None),
            store.k_desafios())


def _exemplos():
    """Desafios fictícios de arena/exemplos (formato de exportação: público + segredos)."""
    out = {}
    if os.path.isdir(DIR_EXEMPLOS):
        for nome in sorted(os.listdir(DIR_EXEMPLOS)):
            if nome.endswith(".json"):
                d = _ler_json(os.path.join(DIR_EXEMPLOS, nome))
                out[d["codigo"]] = d
    return out


def _usa_exemplos(db):
    # Só no desenvolvimento/testes. Com Supabase ou Upstash, banco vazio = arena sem missões.
    return isinstance(db, store.Local)


def limpar_cache():
    _CACHE.clear()


def desafios(db=None):
    """{codigo: registro PÚBLICO do desafio}, do banco (cache de 30 s). Não inclui testesExtras nem gabarito."""
    db = db or store.abrir()
    chave = _id_banco(db)
    item = _CACHE.get(chave)
    if item and item["expira"] > time.time():
        return item["valor"]
    bruto = db.hgetall(store.k_desafios())
    if bruto:
        valor = {c: json.loads(v) for c, v in bruto.items()}
    elif _usa_exemplos(db):
        valor = {c: {k: d[k] for k in CAMPOS_REGISTRO if k in d} for c, d in _exemplos().items()}
    else:
        valor = {}
    valor = dict(sorted(valor.items()))
    _CACHE[chave] = {"valor": valor, "expira": time.time() + TTL_DESAFIOS}
    return valor


def segredos(db, codigo):
    """{"testesExtras", "gabarito"} de um desafio, ou None. Só para julgar e para o admin."""
    bruto = db.hget(store.k_segredos(), codigo)
    if bruto:
        return json.loads(bruto)
    if _usa_exemplos(db) and not db.hgetall(store.k_desafios()):
        d = _exemplos().get(codigo)
        return {k: d.get(k, "") for k in CAMPOS_SEGREDO} if d else None
    return None


def desafio_completo(db, codigo):
    """Registro público + segredos (validação, exportação, admin). None se o desafio não existir."""
    d = desafios(db).get(codigo)
    if d is None:
        return None
    return {**d, **(segredos(db, codigo) or {k: "" for k in CAMPOS_SEGREDO})}


def gravar_desafio(db, desafio):
    """Grava as duas partes do desafio (pública e secreta) e limpa o cache deste processo."""
    cod = desafio["codigo"]
    db.hset(store.k_desafios(), cod, json.dumps({k: desafio[k] for k in CAMPOS_REGISTRO if k in desafio},
                                                ensure_ascii=False))
    db.hset(store.k_segredos(), cod, json.dumps({k: desafio.get(k, "") for k in CAMPOS_SEGREDO},
                                                ensure_ascii=False))
    limpar_cache()


def publico(desafio):
    return {k: desafio[k] for k in CAMPOS_PUBLICOS if k in desafio}


def equipes():
    """Equipes vêm da variável ARENA_EQUIPES (JSON) ou de arena/equipes.json (fora do git)."""
    bruto = os.environ.get("ARENA_EQUIPES")
    if bruto:
        lista = json.loads(bruto)
    else:
        caminho = os.path.join(DIR_ARENA, "equipes.json")
        if not os.path.exists(caminho):
            caminho = os.path.join(DIR_ARENA, "equipes.exemplo.json")
        lista = _ler_json(caminho)
    return {e["id"]: e for e in lista}


def equipe_por_codigo(codigo):
    codigo = (codigo or "").strip().upper()
    for e in equipes().values():
        if e["codigo"].strip().upper() == codigo:
            return e
    return None


# ---------------- horário ----------------

def _ts(iso):
    return datetime.fromisoformat(iso).timestamp()


def modo_ensaio():
    return os.environ.get("ARENA_MODO", "").lower() == "ensaio"


def janela(cfg=None, agora=None):
    """Situação da competição: 'antes' | 'aberta' | 'encerrada' (+ tempos)."""
    cfg = cfg or config()
    agora = agora if agora is not None else time.time()
    inicio, fim = _ts(cfg["inicio"]), _ts(cfg["fim"])
    freeze = fim - cfg.get("freezeMinutos", 0) * 60
    if modo_ensaio():
        situacao = "aberta"
    elif agora < inicio:
        situacao = "antes"
    elif agora <= fim:
        situacao = "aberta"
    else:
        situacao = "encerrada"
    return {"situacao": situacao, "inicio": inicio, "fim": fim, "freeze": freeze,
            "agora": agora, "ensaio": modo_ensaio()}


# ---------------- regras ----------------
#
# Fonte de verdade: a lista de submissões ACEITAS de cada equipe, registros compactos
# {"t", "codigo", "pontos", "completo", "caracteres"} (sem código-fonte). Pontos, desbloqueio
# e placar (vivo e congelado) são calculados a partir dela.

def pontos_submissao(desafio, aprovados, total, cfg):
    """Pontos de uma submissão aceita, pelo modo de `pontuacao` da config."""
    if total <= 0 or aprovados >= total:
        return desafio["pontos"]
    if cfg["pontuacao"]["modo"] == "completo":
        return 0
    return desafio["pontos"] * aprovados // total  # piso(pontos × aprovados / total)


def _ordem_melhor(r):
    return (-r["pontos"], r["caracteres"], r["t"])  # mais pontos, menos caracteres, mais antiga


def melhores(aceitas, ate=None):
    """{codigo: melhor registro aceito} considerando só as submissões até `ate` (freeze)."""
    out = {}
    for r in aceitas:
        if ate is not None and r["t"] > ate:
            continue
        atual = out.get(r["codigo"])
        if atual is None or _ordem_melhor(r) < _ordem_melhor(atual):
            out[r["codigo"]] = r
    return out


def tempo_ultima_melhoria(aceitas, ate=None):
    """Momento da última submissão aceita que AUMENTOU o total de pontos (reduzir caracteres não conta)."""
    pontos, quando = {}, None
    for r in sorted(aceitas, key=lambda r: r["t"]):
        if ate is not None and r["t"] > ate:
            break
        if r["pontos"] > pontos.get(r["codigo"], 0):
            pontos[r["codigo"]] = r["pontos"]
            quando = r["t"]
    return quando


def contagem_desbloqueio(melhores_eq, todos, cfg):
    """Módulos que contam para desbloquear, por nível: aceitos (inclusive parciais) ou só completos."""
    so_completos = cfg["desbloqueioConta"] == "completo"
    cont = {}
    for cod, r in melhores_eq.items():
        if cod in todos and (r["completo"] or not so_completos):
            n = todos[cod]["nivel"]
            cont[n] = cont.get(n, 0) + 1
    return cont


def nivel_liberado(nivel, contagem, cfg):
    req = cfg["desbloqueio"].get(nivel, {})
    return all(contagem.get(n, 0) >= q for n, q in req.items())


def falta_para_liberar(nivel, contagem, cfg):
    req = cfg["desbloqueio"].get(nivel, {})
    partes = [f"{q - contagem.get(n, 0)} {n}" for n, q in req.items() if contagem.get(n, 0) < q]
    return "Recupere mais " + " + ".join(partes) + " para desbloquear." if partes else ""


def cooldown_restante(tentativas, ultima, cfg, agora=None):
    """Segundos de espera antes da próxima submissão (0 = pode enviar)."""
    agora = agora if agora is not None else time.time()
    cd = cfg["cooldown"]
    if tentativas < cd["tentativasLivres"] or not ultima:
        return 0
    return max(0, int(ultima + cd["segundos"] - agora))


def placar(equipes, aceitas_por_equipe, todos, cfg, ate=None):
    """equipes: {id: {"nome": ...}}; aceitas_por_equipe: {id: [registros aceitos]}.
    `ate` = timestamp do freeze: vale a melhor submissão de cada módulo até ele.
    Ordem: pontos ↓, completos ↓, caracteres dos completos ↑, última melhoria ↑, nome ↑."""
    linhas = []
    for eid, e in equipes.items():
        aceitas = aceitas_por_equipe.get(eid, [])
        m = {c: r for c, r in melhores(aceitas, ate).items() if c in todos}
        completos = [r for r in m.values() if r["completo"]]
        modulos = {n: [] for n in cfg["niveis"]}
        for cod in sorted(todos):
            r = m.get(cod)
            estado = None if r is None else "completo" if r["completo"] else "parcial"
            modulos.setdefault(todos[cod]["nivel"], []).append(estado)
        linhas.append({
            "id": eid, "nome": e["nome"],
            "pontos": sum(r["pontos"] for r in m.values()),
            "completos": len(completos),
            "caracteres": sum(r["caracteres"] for r in completos),
            "ultimaMelhoria": tempo_ultima_melhoria([r for r in aceitas if r["codigo"] in todos], ate),
            "modulos": modulos,
        })
    linhas.sort(key=lambda l: (-l["pontos"], -l["completos"], l["caracteres"],
                               l["ultimaMelhoria"] if l["ultimaMelhoria"] is not None else float("inf"), l["nome"]))
    for i, l in enumerate(linhas, 1):
        l["posicao"] = i
    return linhas
