"""Importação e exportação de desafios (painel admin; os scripts de carga ficam no repositório privado).

Formato de exportação (um arquivo):
  {"formato": "meupia-challenge/desafios", "versao": 1, "exportadoEm": "<ISO>", "desafios": [<completo>, ...]}
<completo> = campos públicos do registro + testesExtras + gabarito.
Também lê uma pasta no formato antigo: <COD>.json com o gabarito no próprio JSON, em <COD>.por ao lado
ou em ../gabaritos/<COD>.por.
"""
import json
import os
from datetime import datetime, timezone

from . import arena, validacao

FORMATO = "meupia-challenge/desafios"
CAMPOS = arena.CAMPOS_REGISTRO + arena.CAMPOS_SEGREDO


def _normalizar(d):
    return {k: d[k] for k in CAMPOS if k in d}


def ler_pasta(pasta):
    out = []
    for nome in sorted(os.listdir(pasta)):
        if not nome.endswith(".json"):
            continue
        with open(os.path.join(pasta, nome), encoding="utf-8") as f:
            d = json.load(f)
        if not d.get("gabarito"):
            for alt in (os.path.join(pasta, d["codigo"] + ".por"),
                        os.path.join(pasta, "..", "gabaritos", d["codigo"] + ".por")):
                if os.path.exists(alt):
                    with open(alt, encoding="utf-8") as f:
                        d["gabarito"] = f.read()
                    break
        out.append(_normalizar(d))
    return out


def ler_export(dados):
    if dados.get("formato") != FORMATO:
        raise ValueError("arquivo não é uma exportação de desafios do meuPiá Challenge")
    return [_normalizar(d) for d in dados.get("desafios", [])]


def ler(caminho):
    if os.path.isdir(caminho):
        return ler_pasta(caminho)
    with open(caminho, encoding="utf-8") as f:
        return ler_export(json.load(f))


def exportar(db):
    todos = arena.desafios(db)
    return {"formato": FORMATO, "versao": 1,
            "exportadoEm": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "desafios": [_normalizar(arena.desafio_completo(db, cod)) for cod in todos]}


def planejar(db, desafios):
    """Para cada desafio: acao (criar | substituir | igual) + resultado da validação com o juiz."""
    existentes = db.hgetall(arena.store.k_desafios())  # só o banco: exemplos não contam como existentes
    plano = []
    for d in desafios:
        cod = d.get("codigo", "?")
        if cod not in existentes:
            acao = "criar"
        else:
            atual = _normalizar(arena.desafio_completo(db, cod) or {})
            acao = "igual" if atual == d else "substituir"
        plano.append({"codigo": cod, "acao": acao, "validacao": validacao.validar(d), "desafio": d})
    return plano


def aplicar(db, plano):
    """Grava só os desafios válidos que mudaram. Devolve os códigos gravados."""
    gravados = []
    for item in plano:
        if item["validacao"]["ok"] and item["acao"] != "igual":
            arena.gravar_desafio(db, item["desafio"])
            gravados.append(item["codigo"])
    return gravados
