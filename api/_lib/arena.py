"""Dados e regras da Code Arena: desafios, equipes, horário, desbloqueio, cooldown e placar."""
import json
import os
import secrets
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


def config(db=None):
    """Configuração do arquivo. Com `db`, aplica o início do evento salvo pelo painel (fim = início + duração)."""
    cfg = validar_config(_ler_json(os.path.join(DIR_ARENA, "config.json")))
    if db is not None:
        aplicar_inicio(cfg, inicio_salvo(db))
    return cfg


def inicio_salvo(db):
    """Início do evento definido no painel (ISO com fuso) ou None."""
    try:
        return db.hget(store.k_evento(), "inicio") or None
    except Exception:  # banco fora do ar: segue com o horário do arquivo
        return None


def aplicar_inicio(cfg, inicio):
    """Troca o início mantendo a duração do arquivo. Marca a origem em cfg['origemHorario']."""
    cfg["origemHorario"] = "arquivo"
    if not inicio:
        return cfg
    duracao = _ts(cfg["fim"]) - _ts(cfg["inicio"])
    novo = datetime.fromisoformat(inicio)
    cfg["inicio"] = novo.isoformat()
    cfg["fim"] = datetime.fromtimestamp(novo.timestamp() + duracao, tz=novo.tzinfo).isoformat()
    cfg["origemHorario"] = "banco"
    return cfg


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


PALAVRAS = ["ORION", "VEGA", "LYRA", "NOVA", "ATLAS", "TITAN", "PULSAR", "QUASAR", "COMET", "NEBULA",
            "DRACO", "RIGEL", "SIRIUS", "ALTAIR", "CYGNUS", "HYDRA"]
ALFABETO = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # sem 0/O/1/I
TAMANHO_CODIGO = 6  # 32^6 ≈ 1 bilhão de combinações por palavra (as palavras são públicas)


def gerar_codigo(indice, existentes=()):
    """Código PALAVRA-XXXXXX (gerador criptográfico), único entre `existentes` (sem diferenciar caixa)."""
    usados = {c.strip().upper() for c in existentes}
    for _ in range(20):
        c = f"{PALAVRAS[indice % len(PALAVRAS)]}-" + "".join(secrets.choice(ALFABETO) for _ in range(TAMANHO_CODIGO))
        if c not in usados:
            return c
    raise RuntimeError("não foi possível gerar um código único")


def equipes_arquivo():
    """(lista, origem) das equipes fora do banco: ARENA_EQUIPES ('env'), arena/equipes.json ('arquivo')
    ou arena/equipes.exemplo.json ('exemplo', nunca em produção: os códigos dele são públicos).
    Servem de importação inicial para o banco. Sem nenhuma fonte: ([], 'nenhuma')."""
    bruto = os.environ.get("ARENA_EQUIPES")
    if bruto:
        return json.loads(bruto), "env"
    caminho = os.path.join(DIR_ARENA, "equipes.json")
    if os.path.exists(caminho):
        return _ler_json(caminho), "arquivo"
    if store.em_producao():
        return [], "nenhuma"
    return _ler_json(os.path.join(DIR_ARENA, "equipes.exemplo.json")), "exemplo"


def participantes(db):
    """{id: {id, equipe, nome, semestre, email}} cadastrados no banco."""
    return {pid: json.loads(v) for pid, v in db.hgetall(store.k_participantes()).items()}


def rotulo_participante(p):
    return f"{p['nome']} ({p['semestre']})" if p.get("semestre") else p["nome"]


def equipes_do_banco(db):
    return {eid: json.loads(v) for eid, v in db.hgetall(store.k_equipes()).items()}


def equipes(db=None):
    """{id: equipe}. Com equipes no banco, só elas valem (integrantes = participantes como `Nome (semestre)`);
    com o banco vazio, vale a fonte antiga (ARENA_EQUIPES ou arquivo), com versao 0."""
    db = db or store.abrir()
    banco = equipes_do_banco(db)
    if banco:
        parts = sorted(participantes(db).values(), key=lambda p: p["nome"].lower())
        for eid, e in banco.items():
            e["integrantes"] = [rotulo_participante(p) for p in parts if p.get("equipe") == eid]
            e.setdefault("versao", 0)
        return banco
    lista, _ = equipes_arquivo()
    return {e["id"]: {**e, "versao": 0} for e in lista}


def equipe_por_codigo(codigo, db=None):
    codigo = (codigo or "").strip().upper()
    for e in equipes(db).values():
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

def aplicar_ajustes(aceitas, ajustes, todos):
    """Pontos efetivos: cópia das aceitas com o ajuste da banca aplicado (pura).
    Ajustada: pontos = ajuste, pontosJuiz = original e completo só se era completa E vale o máximo do módulo."""
    out = []
    for r in aceitas:
        a = ajustes.get(r.get("id")) if r.get("id") else None
        if a is None:
            out.append(r)
            continue
        maximo = todos[r["codigo"]]["pontos"] if r["codigo"] in todos else r["pontos"]
        out.append({**r, "pontos": a["pontos"], "pontosJuiz": r["pontos"], "ajustado": True,
                    "completo": bool(r["completo"]) and a["pontos"] == maximo})
    return out


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
