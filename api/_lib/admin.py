"""Casos de uso do painel da banca (sem HTTP): placar real, submissões, perfis e auditoria.

Toda ação passa por `executar`, que confere o método (só as ações de LEITURA aceitam GET) e a
permissão (tabela PERMISSOES) antes de qualquer leitura ou gravação. Ações que alteram dados vão para a auditoria, sem código-fonte.
"""
import json
import re
import secrets
import time
from datetime import datetime

import hashlib

from . import arena, auth, conteudo, servico, store, turmas, validacao
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
    "importar_participantes": "admin", "montar_equipes": "admin",
    "ajustar": "juiz", "desfazer_ajuste": "juiz",
    # desafios: só admin (juízes nunca recebem testes extras nem gabaritos)
    "desafios": "admin", "desafio": "admin", "salvar_desafio": "admin", "validar_desafio": "admin",
    "validar_todos": "admin", "exportar_desafios": "admin", "importar_desafios": "admin",
    # horário do evento: juiz vê, admin altera
    "evento": "juiz", "salvar_evento": "admin",
}
# Únicas ações aceitas por GET: não gravam nada (nem auditoria). O resto é só POST, que exige JSON e mesma
# origem (web.Base); assim um link malicioso aberto por alguém da banca logada não altera dados (CSRF).
LEITURA = frozenset({"placar", "submissoes", "submissao", "perfis", "auditoria", "equipes", "participantes",
                     "desafios", "desafio", "evento"})
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


def executar(acao, autor, dados=None, db=None, metodo="POST"):
    exigido = PERMISSOES.get(acao)
    if exigido is None:
        raise Erro(400, "Ação desconhecida.")
    if metodo.upper() != "POST" and acao not in LEITURA:
        raise Erro(405, "Esta ação altera dados: use POST.")
    if _NIVEL.get(autor.get("papel"), 0) < _NIVEL[exigido]:
        raise Erro(403, "Seu perfil não pode fazer isso.")
    db = db or store.abrir()
    dados = dados or {}
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
    soltos = [p for p in arena.participantes(db).values() if p.get("equipe") == e["id"]]
    for p in soltos:  # voltam para "sem equipe" (podem entrar numa nova montagem)
        _gravar_participante(db, {**p, "equipe": ""})
    db.hdel(store.k_equipes(), e["id"])
    auditar(db, autor, "excluir_equipe", e["nome"], f"{len(soltos)} participante(s) sem equipe")
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
    if not lista:
        raise Erro(409, "Não há equipes para importar: crie as equipes no painel.")
    agora = time.time()
    for e in lista:
        _gravar_equipe(db, {"id": e["id"], "nome": e["nome"], "codigo": e["codigo"], "versao": 0, "criadaEm": agora})
        for rotulo in e.get("integrantes", []):
            p = _participante_de_rotulo(rotulo, e["id"])
            db.hset(store.k_participantes(), p["id"], json.dumps(p, ensure_ascii=False))
    auditar(db, autor, "importar_equipes", origem, f"{len(lista)} equipe(s)")
    return {"ok": True, "importadas": len(lista)}


# ---------------- participantes ----------------

def _gravar_participante(db, p):
    db.hset(store.k_participantes(), p["id"], json.dumps(
        {k: p.get(k, "") for k in ("id", "equipe", "nome", "semestre", "email")}, ensure_ascii=False))


def _sem_equipe(db):
    """Participantes sem equipe (equipe vazia ou de uma equipe que não existe mais no banco)."""
    eqs = arena.equipes_do_banco(db)
    return [p for p in arena.participantes(db).values() if p.get("equipe", "") not in eqs]


def _participantes(_autor, _dados, db):
    eqs = arena.equipes_do_banco(db)
    lista = [{**p, "nomeEquipe": eqs[p["equipe"]]["nome"] if p.get("equipe") in eqs else ""}
             for p in arena.participantes(db).values()]
    lista.sort(key=lambda p: (bool(p["nomeEquipe"]), p["nomeEquipe"].lower(), p["nome"].lower()))
    return {"participantes": lista, "semEquipe": sum(1 for p in lista if not p["nomeEquipe"])}


def _salvar_participante(autor, dados, db):
    """Cria (sem id) ou edita (com id), inclusive trocando de equipe ou ficando sem equipe (`equipe` vazia).
    Submissões já feitas não mudam."""
    nome = " ".join(str(dados.get("nome", "")).split())
    semestre = str(dados.get("semestre", "")).strip()
    email = str(dados.get("email", "") or "").strip().lower()
    equipe = _equipe_do_banco(db, dados.get("equipe")) if dados.get("equipe") else None
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
    _gravar_participante(db, {"id": pid, "equipe": equipe["id"] if equipe else "", "nome": nome,
                              "semestre": semestre, "email": email})
    auditar(db, autor, "criar_participante" if novo else "editar_participante", nome,
            f"equipe={equipe['nome'] if equipe else 'sem equipe'}")
    return {"ok": True, "id": pid}


def _remover_participante(autor, dados, db):
    pid = str(dados.get("id", ""))
    p = arena.participantes(db).get(pid)
    if not p:
        raise Erro(404, "Participante não encontrado.")
    db.hdel(store.k_participantes(), pid)
    auditar(db, autor, "remover_participante", p["nome"])
    return {"ok": True}


def _importar_participantes(autor, dados, db):
    """Duas etapas: sem `confirmar`, devolve a prévia (alunos a criar + linhas ignoradas com o motivo); com
    `confirmar`, relê o mesmo texto contra o banco atual e grava os alunos sem equipe."""
    texto = dados.get("texto")
    if not isinstance(texto, str) or not texto.strip():
        raise Erro(400, "Envie um arquivo CSV ou cole a listagem de alunos.")
    if len(texto) > 200_000:
        raise Erro(400, "A listagem é grande demais.")
    try:
        alunos, ignoradas = turmas.ler_listagem(texto, [p["nome"] for p in arena.participantes(db).values()])
    except ValueError as e:
        raise Erro(400, str(e)) from None
    if not dados.get("confirmar"):
        return {"alunos": alunos, "ignoradas": ignoradas}
    for a in alunos:
        _gravar_participante(db, {"id": "pt-" + secrets.token_hex(4), "equipe": "", **a})
    auditar(db, autor, "importar_participantes", "", f"{len(alunos)} aluno(s), {len(ignoradas)} linha(s) ignorada(s)")
    return {"alunos": alunos, "ignoradas": ignoradas, "criados": len(alunos)}


def _assinatura(participantes):
    return hashlib.sha256(",".join(sorted(p["id"] for p in participantes)).encode()).hexdigest()


def _montar_equipes(autor, dados, db):
    """Duas etapas: sem `confirmar`, sorteia (semente nova, ou a recebida) e devolve a prévia com `semente` e
    `assinatura` (dos alunos sem equipe); com `confirmar`, recalcula com a mesma semente e grava exatamente a
    prévia, recusando se os alunos sem equipe mudaram. Equipes existentes não mudam."""
    try:
        tamanho = int(dados.get("tamanho"))
    except (TypeError, ValueError):
        tamanho = 0
    if not 2 <= tamanho <= 10:
        raise Erro(400, "Informe de 2 a 10 alunos por equipe.")
    banco = arena.equipes_do_banco(db)
    if not banco and arena.equipes_arquivo()[1] in ("env", "arquivo"):
        raise Erro(409, "As equipes ainda vêm de ARENA_EQUIPES/arquivo. Importe-as antes de montar outras.")
    soltos = _sem_equipe(db)
    if not soltos:
        raise Erro(409, "Não há alunos sem equipe para montar equipes.")
    assinatura = _assinatura(soltos)
    if dados.get("confirmar"):
        if dados.get("assinatura") != assinatura:
            raise Erro(409, "Os alunos sem equipe mudaram; gere uma nova prévia.")
        try:
            semente = int(dados.get("semente"))
        except (TypeError, ValueError):
            raise Erro(400, "Prévia inválida; gere uma nova prévia.") from None
    else:
        semente = secrets.randbits(32)
    grupos = turmas.distribuir(soltos, tamanho, semente)
    nomes = turmas.nomes_de_equipes(len(grupos), arena.PALAVRAS, [e["nome"] for e in banco.values()])
    previa = [{"nome": nome, "integrantes": [arena.rotulo_participante(p) for p in g],
               "porSemestre": turmas.por_semestre(g)} for (nome, _), g in zip(nomes, grupos)]
    if not dados.get("confirmar"):
        return {"semente": semente, "assinatura": assinatura, "tamanho": tamanho, "equipes": previa}
    codigos, agora = [e["codigo"] for e in banco.values()], time.time()
    for (nome, indice), g in zip(nomes, grupos):
        e = {"id": "eq-" + secrets.token_hex(4), "nome": nome, "versao": 0, "criadaEm": agora,
             "codigo": arena.gerar_codigo(indice, codigos)}
        codigos.append(e["codigo"])
        _gravar_equipe(db, e)
        for p in g:
            _gravar_participante(db, {**p, "equipe": e["id"]})
    auditar(db, autor, "montar_equipes", "", f"{len(grupos)} equipe(s), {len(soltos)} aluno(s), tamanho {tamanho}")
    return {"ok": True, "equipes": previa}


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


# ---------------- desafios ----------------

_RE_CODIGO_DESAFIO = re.compile(r"^[A-Z]\d{2}$")
OBRIGATORIOS = ("codigo", "modulo", "problemaTecnico", "nivel", "pontos", "titulo", "descricao", "codigoInicial",
                "testesPublicos", "testesExtras", "gabarito")
TEXTOS = tuple(c for c in arena.CAMPOS_REGISTRO + arena.CAMPOS_SEGREDO if c not in ("codigo", "pontos", "nivel"))


def _ultimas_validacoes(db):
    return {c: json.loads(v) for c, v in db.hgetall(store.k_validacao()).items()}


def _registrar_validacao(db, codigo, r):
    db.hset(store.k_validacao(), codigo, json.dumps(
        {"ok": r["ok"], "quando": time.time(), "erros": r["erros"], "gabarito": r["gabarito"],
         "inicial": r["inicial"], "maxMs": r["maxMs"]}, ensure_ascii=False))


def _desafios(_autor, _dados, db):
    vals = _ultimas_validacoes(db)
    lista = []
    for cod in arena.desafios(db):
        d = arena.desafio_completo(db, cod)
        lista.append({"codigo": cod, "nivel": d.get("nivel"), "pontos": d.get("pontos"), "titulo": d.get("titulo"),
                      "modulo": d.get("modulo"), "extras": len(validacao_linhas(d.get("testesExtras"))),
                      "validacao": vals.get(cod)})
    return {"niveis": arena.config()["niveis"], "desafios": lista}


def validacao_linhas(testes):
    return [l for l in (testes or "").splitlines() if l.strip()]


def _desafio(_autor, dados, db):
    d = arena.desafio_completo(db, str(dados.get("codigo", "")).upper())
    if d is None:
        raise Erro(404, "Desafio não encontrado.")
    return {"desafio": d, "validacao": _ultimas_validacoes(db).get(d["codigo"])}


def _normalizar_desafio(bruto):
    """Confere e normaliza os campos de um desafio vindo do formulário (Erro 400 com a lista de problemas)."""
    if not isinstance(bruto, dict):
        raise Erro(400, "Envie o desafio.")
    d, erros = {}, []
    d["codigo"] = str(bruto.get("codigo", "")).strip().upper()
    if not _RE_CODIGO_DESAFIO.match(d["codigo"]):
        erros.append("código no formato B01 (letra maiúscula e dois dígitos)")
    d["nivel"] = bruto.get("nivel")
    if d["nivel"] not in arena.config()["niveis"]:
        erros.append("nível inválido")
    try:
        d["pontos"] = int(str(bruto.get("pontos", "")).strip())
        if d["pontos"] <= 0 or str(bruto.get("pontos")).strip() != str(d["pontos"]):
            raise ValueError
    except ValueError:
        erros.append("pontos devem ser um inteiro positivo")
    for campo in TEXTOS:
        if campo in bruto and bruto[campo] is not None:
            d[campo] = str(bruto[campo])
    d.setdefault("id", f"arena_{d['codigo'].lower()}")
    faltando = [c for c in OBRIGATORIOS if c not in ("codigo", "nivel", "pontos") and not str(d.get(c, "")).strip()]
    if faltando:
        erros.append("campos obrigatórios vazios: " + ", ".join(faltando))
    for campo in ("testesPublicos", "testesExtras"):
        erros += [f"{campo}, {e}" for e in validacao.problemas_de_formato(d.get(campo, ""))]
        aspas = [n for n, l in enumerate(validacao_linhas(d.get(campo)), 1) if l.count('"') % 2]
        erros += [f"{campo}, linha {n}: aspas duplas dentro de texto" for n in aspas]
    if erros:
        raise Erro(400, "Desafio inválido: " + "; ".join(erros) + ".")
    return d


def _tem_tentativas(db, codigo):
    return any(int(db.hgetall(store.k_tentativas(eid)).get(codigo, 0) or 0) for eid in arena.equipes(db))


def _salvar_desafio(autor, dados, db):
    d = _normalizar_desafio(dados.get("desafio"))
    anterior = arena.desafio_completo(db, d["codigo"]) if d["codigo"] in db.hgetall(store.k_desafios()) else None
    if dados.get("novo") and anterior is not None:
        raise Erro(409, f"Já existe o desafio {d['codigo']} (o código não muda depois de criado).")
    if not dados.get("novo") and anterior is None:
        raise Erro(404, "Desafio não encontrado no banco. Para criar, use o botão Novo desafio.")
    if anterior is not None and not dados.get("confirmarSubmissoes") and _tem_tentativas(db, d["codigo"]):
        raise Erro(409, "Este desafio já recebeu submissões: a mudança não rejulga as antigas. Confirme para salvar.")
    alterados = sorted(c for c in set(d) | set(anterior or {})
                       if c in conteudo.CAMPOS and (d.get(c) or "") != ((anterior or {}).get(c) or ""))
    arena.gravar_desafio(db, d)  # duas partes + limpa o cache deste processo
    if anterior is None:
        auditar(db, autor, "criar_desafio", d["codigo"])
    else:
        auditar(db, autor, "editar_desafio", d["codigo"], f"({', '.join(alterados) or 'sem mudança'})")
    return {"ok": True, "alterados": alterados}


def _validar_desafio(_autor, dados, db):
    """Valida o formulário (`desafio`, sem salvar) ou um desafio salvo (`codigo`, registra o resultado)."""
    if dados.get("desafio") is not None:
        return {"validacao": validacao.validar(_normalizar_desafio(dados["desafio"]))}
    d = arena.desafio_completo(db, str(dados.get("codigo", "")).upper())
    if d is None:
        raise Erro(404, "Desafio não encontrado.")
    r = validacao.validar(d)
    _registrar_validacao(db, d["codigo"], r)
    return {"validacao": r}


def _validar_todos(_autor, _dados, db):
    out = {}
    for cod in arena.desafios(db):
        r = validacao.validar(arena.desafio_completo(db, cod))
        _registrar_validacao(db, cod, r)
        out[cod] = r
    return {"ok": all(r["ok"] for r in out.values()), "validacoes": out}


def _exportar_desafios(autor, _dados, db):
    dados = conteudo.exportar(db)
    auditar(db, autor, "exportar_desafios", "", f"{len(dados['desafios'])} desafio(s)")
    return dados


def _importar_desafios(autor, dados, db):
    """Duas etapas: sem `confirmar`, devolve a prévia (criar/substituir/igual + validação); com `confirmar`,
    valida de novo e grava só os válidos que mudaram."""
    try:
        desafios = conteudo.ler_export(dados.get("arquivo") or {})
    except (ValueError, AttributeError) as e:
        raise Erro(400, str(e) or "Arquivo inválido.") from None
    plano = conteudo.planejar(db, desafios)
    previa = [{"codigo": p["codigo"], "acao": p["acao"], "ok": p["validacao"]["ok"], "erros": p["validacao"]["erros"]}
              for p in plano]
    if not dados.get("confirmar"):
        return {"previa": previa}
    gravados = conteudo.aplicar(db, plano)
    for p in plano:
        if p["codigo"] in gravados:
            _registrar_validacao(db, p["codigo"], p["validacao"])
    auditar(db, autor, "importar_desafios", "", f"{len(gravados)} gravado(s): {', '.join(gravados) or '–'}")
    return {"previa": previa, "gravados": gravados}


def _auditoria(_autor, dados, db):
    limite = min(int(dados.get("limite") or 300), 1000)
    return {"auditoria": [json.loads(x) for x in db.lrange(store.k_auditoria(), 0, limite - 1)]}


# ---------------- horário do evento ----------------

def _evento(_autor, _dados, db):
    cfg = arena.config(db)
    arquivo = arena.config()
    jan = arena.janela(cfg)
    return {
        "inicio": cfg["inicio"], "fim": cfg["fim"], "origem": cfg["origemHorario"],
        "inicioArquivo": arquivo["inicio"], "fimArquivo": arquivo["fim"],
        "duracaoMinutos": round((jan["fim"] - jan["inicio"]) / 60), "freezeMinutos": cfg.get("freezeMinutos", 0),
        "janela": jan, "temSubmissoes": bool(db.lrange(store.k_log(), 0, 0)),
    }


def _salvar_evento(autor, dados, db):
    """{inicio: "AAAA-MM-DDTHH:MM"} no fuso do evento, ou {inicio: null} para voltar ao arquivo."""
    antes = arena.config(db)["inicio"]
    bruto = dados.get("inicio")
    if bruto in (None, ""):
        if dados.get("voltarAoArquivo"):
            db.hdel(store.k_evento(), "inicio")
            depois = arena.config()["inicio"]
            auditar(db, autor, "horário do evento", "início", f"{antes} → {depois} (arquivo)")
            return {"ok": True, "inicio": depois, "origem": "arquivo"}
        raise Erro(400, "Informe a data e a hora de início.")
    try:
        novo = datetime.fromisoformat(str(bruto).strip())
    except ValueError:
        raise Erro(400, "Data e hora inválidas. Use o formato AAAA-MM-DDTHH:MM.") from None
    if novo.tzinfo is None:  # datetime-local do navegador: fuso do evento (o do arquivo)
        novo = novo.replace(tzinfo=datetime.fromisoformat(arena.config()["inicio"]).tzinfo)
    if not 2000 <= novo.year <= 2100:
        raise Erro(400, "Data fora do intervalo aceito.")
    iso = novo.isoformat(timespec="minutes")
    db.hset(store.k_evento(), "inicio", iso)
    auditar(db, autor, "horário do evento", "início", f"{antes} → {iso}")
    return {"ok": True, "inicio": iso, "origem": "banco"}


_ACOES = {
    "placar": _placar, "submissoes": _submissoes, "submissao": _submissao,
    "perfis": _perfis, "auditoria": _auditoria,
    "salvar_perfil": _salvar_perfil, "remover_perfil": _remover_perfil,
    "equipes": _equipes, "criar_equipe": _criar_equipe, "editar_equipe": _editar_equipe,
    "excluir_equipe": _excluir_equipe, "regenerar_codigo": _regenerar_codigo, "importar_equipes": _importar_equipes,
    "participantes": _participantes, "salvar_participante": _salvar_participante,
    "remover_participante": _remover_participante,
    "importar_participantes": _importar_participantes, "montar_equipes": _montar_equipes,
    "ajustar": _ajustar, "desfazer_ajuste": _desfazer_ajuste,
    "desafios": _desafios, "desafio": _desafio, "salvar_desafio": _salvar_desafio,
    "validar_desafio": _validar_desafio, "validar_todos": _validar_todos,
    "exportar_desafios": _exportar_desafios, "importar_desafios": _importar_desafios,
    "evento": _evento, "salvar_evento": _salvar_evento,
}
