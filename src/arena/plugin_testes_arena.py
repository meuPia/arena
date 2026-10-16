"""Plugin `testes` da Arena para o Rodar (Pyodide). Ver design.md da change esperado-obtido-nos-exemplos.

Troca as funções `esperar_*` de `meupia_testes.plugin_testes` (pacote do PyPI) por versões que mantêm a
comparação e entregam o resultado de cada linha de teste de exemplo ao JavaScript (`arena_testes.registrar`,
módulo registrado pelo testes-exemplo.js), com o tipo e o valor no formato do Portugol. Só conta como teste a
chamada feita direto de main() numa das N últimas instruções `esperar_*` (a mesma regra do executor do juiz);
as outras chamadas vão para a função original do plugin, como antes.

Roda num dicionário de globais próprio (não no __main__ do Pyodide, que o wasm.js do Lab usa).
"""
import ast
import json
import math
import sys
from collections import deque

import arena_testes
from meupia_testes import plugin_testes as _plugin

CAMINHO = "output/main.py"
LIMITE = 2000  # caracteres de um valor formatado
PROFUNDIDADE = 4
FUNCOES = ("igual", "diferente", "maior", "menor", "contem", "verdadeiro", "falso")

if not hasattr(_plugin, "_arena_originais"):
    _plugin._arena_originais = {f: getattr(_plugin, "esperar_" + f) for f in FUNCOES}
_ORIGINAIS = _plugin._arena_originais

_estado = {"n": 0, "mapa": None}


def iniciar_rodada(n):
    """Chamada pelo JavaScript antes de cada Rodar, com o número de linhas de teste de exemplo."""
    _estado["n"] = int(n)
    _estado["mapa"] = None


def _eh_teste(no):
    return (isinstance(no, ast.Expr) and isinstance(no.value, ast.Call)
            and isinstance(no.value.func, ast.Name) and no.value.func.id.startswith("esperar_"))


def mapa_de_testes(codigo, n):
    """{linha do main.py: k} das N últimas instruções de main(), se todas forem `esperar_*`; senão {}."""
    try:
        arvore = ast.parse(codigo)
    except SyntaxError:
        return {}
    main = next((no for no in arvore.body if isinstance(no, ast.FunctionDef) and no.name == "main"), None)
    if main is None or n <= 0:
        return {}
    corpo = [no for no in main.body if not isinstance(no, ast.Global)]
    testes = corpo[len(corpo) - n:]
    if len(corpo) < n or not all(_eh_teste(no) for no in testes):
        return {}
    mapa = {}
    for k, no in enumerate(testes):
        for linha in range(no.lineno, (no.end_lineno or no.lineno) + 1):
            mapa[linha] = k
    return mapa


def _indice(quadro):
    if quadro is None or quadro.f_code.co_name != "main":
        return None
    if _estado["mapa"] is None:
        try:
            with open(CAMINHO, encoding="utf-8") as f:
                _estado["mapa"] = mapa_de_testes(f.read(), _estado["n"])
        except OSError:
            _estado["mapa"] = {}
    return _estado["mapa"].get(quadro.f_lineno)


# --- valores no formato do Portugol ---

def tipo(v):
    if v is None:
        return "sem valor"
    if isinstance(v, bool):
        return "logico"
    if isinstance(v, int):
        return "inteiro"
    if isinstance(v, float):
        return "real"
    if isinstance(v, str):
        return "cadeia"
    if isinstance(v, (list, tuple, deque)):
        return "lista"
    if isinstance(v, dict):
        return "dicionario"
    return "valor"


def _juntar(abre, partes, fecha):
    texto, total = [], len(abre)
    for i, p in enumerate(partes):
        if total > LIMITE:
            texto.append(", …")
            break
        texto.append((", " if i else "") + p)
        total += len(texto[-1])
    return abre + "".join(texto) + fecha


def formatar(v, profundidade=0):
    t = tipo(v)
    if t == "sem valor":
        return "sem valor"
    if t == "logico":
        return "verdadeiro" if v else "falso"
    if t in ("inteiro", "real"):
        return repr(v) if t == "real" else str(int(v))
    if t == "cadeia":
        return '"' + str(v)[:LIMITE + 1].replace(" ", "·").replace("\t", "→").replace("\n", "↵") + '"'
    if t in ("lista", "dicionario") and profundidade >= PROFUNDIDADE:
        return "[…]" if t == "lista" else "{…}"
    if t == "lista":
        return _juntar("[", (formatar(x, profundidade + 1) for x in v), "]")
    if t == "dicionario":
        return _juntar("{", (formatar(c, profundidade + 1) + ": " + formatar(x, profundidade + 1)
                             for c, x in v.items()), "}")
    try:
        return str(v)
    except Exception:  # noqa: BLE001 — __str__ do aluno com erro
        return "<valor>"


def valor(v):
    texto = formatar(v)
    if len(texto) > LIMITE:
        texto = texto[:LIMITE] + "…"
    dados = {"tipo": tipo(v), "texto": texto}
    if dados["tipo"] == "cadeia":
        dados["bruto"] = str(v)[:LIMITE]
    elif dados["tipo"] == "real" and math.isfinite(v):
        dados["bruto"] = v
    return dados


# --- julgamento ---

def _descrever(funcao, dados):
    e, o = dados["esperado"], dados["obtido"]
    if dados["erro"] == "comparar":
        return f"não dá para comparar {o['tipo']} com {e['tipo']}"
    prefixo = {"diferente": "diferente de ", "maior": "maior que ", "menor": "menor que ", "contem": "conter "}
    return f"esperado {prefixo.get(funcao, '')}{e['texto']} ({e['tipo']}), obtido {o['texto']} ({o['tipo']})"


def _julgar(k, funcao, comparar, obtido, esperado, mensagem):
    erro = None
    try:
        ok = bool(comparar())
    except Exception:  # noqa: BLE001 — como no juiz: comparação inválida reprova só este teste
        ok, erro = False, "comparar"
    rotulo = str(mensagem) if mensagem else f"Exemplo {k + 1}"
    try:
        dados = {"k": k, "funcao": funcao, "ok": ok, "erro": erro, "mensagem": rotulo,
                 "esperado": valor(esperado), "obtido": valor(obtido)}
    except Exception:  # noqa: BLE001 — valor que não dá para formatar: o resultado vale sem detalhe
        dados = {"k": k, "funcao": funcao, "ok": ok, "erro": erro, "mensagem": rotulo,
                 "esperado": {"tipo": "valor", "texto": "?"}, "obtido": {"tipo": "valor", "texto": "?"}}
    print(f"[TESTE_OK] {rotulo}" if ok else f"[TESTE_FALHA] {rotulo}: {_descrever(funcao, dados)}")
    arena_testes.registrar(json.dumps(dados, ensure_ascii=False))
    return ok


def _versao_arena(funcao, aridade, comparar):
    original = _ORIGINAIS[funcao]

    def esperar(*args, **kwargs):
        k = _indice(sys._getframe(1))
        if k is None or kwargs or not aridade <= len(args) <= aridade + 1:
            return original(*args, **kwargs)
        mensagem = args[aridade] if len(args) > aridade else ""
        esperado = args[1] if aridade == 2 else funcao == "verdadeiro"
        return _julgar(k, funcao, lambda: comparar(args), args[0], esperado, mensagem)

    esperar.__name__ = "esperar_" + funcao
    return esperar


# Aridade e comparação, iguais às do shim do juiz. Em `contem`, o obtido é a coleção e o esperado, o item.
_REGRAS = {
    "igual": (2, lambda a: a[0] == a[1]),
    "diferente": (2, lambda a: a[0] != a[1]),
    "maior": (2, lambda a: a[0] > a[1]),
    "menor": (2, lambda a: a[0] < a[1]),
    "contem": (2, lambda a: a[1] in a[0]),
    "verdadeiro": (1, lambda a: a[0]),
    "falso": (1, lambda a: not a[0]),
}

for _f, (_aridade, _comparar) in _REGRAS.items():
    setattr(_plugin, "esperar_" + _f, _versao_arena(_f, _aridade, _comparar))
