"""Validação de um desafio com o juiz real (usada pelo `npm run validar`, pela importação e pelo painel).

Critérios: gabarito aceito e completo; código inicial NÃO completo; cada teste do gabarito com no
máximo metade do limite por teste; bateria extra com 15 a 25 testes; testes só com linhas esperar_*.
"""
from . import executor, juiz

LIMITE_MS = int(executor.TEMPO_POR_TESTE * 1000 / 2)
EXTRAS_MIN, EXTRAS_MAX = 15, 25


def problemas_de_formato(testes):
    """Linhas que não são esperar_* ou que têm barra invertida. Sem `\\`, um texto não consegue conter aspas
    duplas (o lexer só as aceita escapadas), então isso cobre as duas regras."""
    erros = []
    for n, linha in enumerate((testes or "").splitlines(), 1):
        s = linha.strip()
        if not s:
            continue
        if not s.startswith("esperar_"):
            erros.append(f"linha {n}: não é uma chamada esperar_*")
        elif "\\" in s:
            erros.append(f"linha {n}: barra invertida não é permitida em testes")
    return erros


def resumo(r):
    return f"{r['status']} {r['exemplos']['aprovados']}/{r['exemplos']['total']} {r['extras']['aprovados']}/{r['extras']['total']}"


def validar(d):
    """d = desafio completo (público + testesExtras + gabarito). Devolve {ok, erros[], gabarito, inicial, maxMs}."""
    erros = []
    if "testesOcultos" in d:
        erros.append("ainda tem testesOcultos")
    for campo in ("testesPublicos", "testesExtras"):
        erros += [f"{campo}, {e}" for e in problemas_de_formato(d.get(campo, ""))]
    if not (d.get("gabarito") or "").strip():
        erros.append("sem gabarito")
        return {"ok": False, "erros": erros, "gabarito": None, "inicial": None, "maxMs": 0}

    rg = juiz.julgar(d["gabarito"], d.get("testesPublicos", ""), d.get("testesExtras", ""), detalhes=True)
    ri = juiz.julgar(d.get("codigoInicial", ""), d.get("testesPublicos", ""), d.get("testesExtras", ""))
    tempos = [t["ms"] or 0 for t in rg.get("testes", [])]
    lentos = [i for i, ms in enumerate(tempos) if ms > LIMITE_MS]

    if not EXTRAS_MIN <= rg["extras"]["total"] <= EXTRAS_MAX:
        erros.append(f"bateria extra com {rg['extras']['total']} testes (use {EXTRAS_MIN}-{EXTRAS_MAX})")
    if rg["status"] != "aceito" or not rg["completo"]:
        erros.append("gabarito não é aceito e completo" + (f": {rg['mensagem']}" if rg.get("mensagem") else ""))
    if lentos:
        erros.append(f"gabarito lento (> {LIMITE_MS} ms) nos testes {lentos}")
    if ri["completo"]:
        erros.append("código inicial já é completo")
    return {"ok": not erros, "erros": erros, "gabarito": resumo(rg), "inicial": resumo(ri),
            "maxMs": max(tempos, default=0)}
