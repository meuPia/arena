"""Plugin `testes` da Arena para o Rodar (src/arena/plugin_testes_arena.py), contra o meupia-core real.

O trecho roda no Pyodide; aqui ele roda no CPython com módulos falsos no lugar do plugin do PyPI e do
módulo JavaScript `arena_testes`, sobre o main.py que o meupia-core gera para o desafio de exemplo B91,
montado como no navegador (juiz.montar = wasm.js).
"""
import contextlib
import io
import json
import os
import sys
import types

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "api"))

from _lib import juiz  # noqa: E402

PLUGIN = os.path.join(RAIZ, "src", "arena", "plugin_testes_arena.py")
B91 = json.load(open(os.path.join(RAIZ, "arena", "exemplos", "B91.json"), encoding="utf-8"))
FUNCOES = ("igual", "diferente", "maior", "menor", "contem", "verdadeiro", "falso")


@pytest.fixture
def arena(monkeypatch, tmp_path):
    """Instala o plugin da Arena sobre um plugin "original" falso e devolve um objeto para rodar código."""
    monkeypatch.chdir(tmp_path)
    originais = []
    falso = types.ModuleType("meupia_testes.plugin_testes")
    for f in FUNCOES:
        def original(*args, _f=f, **kwargs):
            originais.append((_f, args))
            return True
        setattr(falso, "esperar_" + f, original)
    pacote = types.ModuleType("meupia_testes")
    pacote.plugin_testes = falso
    registrados = []
    js = types.ModuleType("arena_testes")
    js.registrar = lambda texto: registrados.append(json.loads(texto))
    monkeypatch.setitem(sys.modules, "meupia_testes", pacote)
    monkeypatch.setitem(sys.modules, "meupia_testes.plugin_testes", falso)
    monkeypatch.setitem(sys.modules, "arena_testes", js)

    ns = {"__name__": "arena_plugin_testes"}
    with open(PLUGIN, encoding="utf-8") as f:
        exec(compile(f.read(), PLUGIN, "exec"), ns)

    class Arena:
        def __init__(self):
            self.ns, self.registrados, self.originais = ns, registrados, originais
            self.saida = ""

        def rodar(self, codigo_aluno, testes=B91["testesPublicos"]):
            from meuPia.compiler import main
            fonte, _ = juiz.montar(codigo_aluno, testes)
            with open("main.por", "w", encoding="utf-8") as f:
                f.write(fonte)
            with contextlib.redirect_stdout(io.StringIO()):
                main("main.por", "output")
            assert os.path.exists("output/main.py"), "não compilou"
            ns["iniciar_rodada"](len(juiz._linhas_de_teste(testes)))
            with open("output/main.py", encoding="utf-8") as f:
                gerado = f.read()
            saida = io.StringIO()
            with contextlib.redirect_stdout(saida):
                exec(gerado, {"__name__": "__main__"})
            self.saida = saida.getvalue()
            return self.registrados

    return Arena()


def com_dobro(corpo, inicio="    escreva(dobro(21))"):
    return ('algoritmo "B91_Calibracao"\n\nvar\n    x : inteiro\n\nfuncao dobro(n)\n'
            f"{corpo}\nfim_funcao\n\ninicio\n{inicio}\nfim_algoritmo\n")


def test_gabarito_tres_resultados_aprovados(arena):
    r = arena.rodar(B91["gabarito"])
    assert [x["k"] for x in r] == [0, 1, 2]
    assert all(x["ok"] for x in r)
    assert [x["mensagem"] for x in r] == ["Exemplo 1", "Exemplo 2", "Exemplo 3"]
    assert "[TESTE_OK] Exemplo 1" in arena.saida


def test_cadeia_contra_inteiro(arena):
    r = arena.rodar(com_dobro('    retorne "" + n * 2'))
    assert r[0]["ok"] is False and r[0]["funcao"] == "igual" and r[0]["erro"] is None
    assert r[0]["esperado"] == {"tipo": "inteiro", "texto": "4"}
    assert r[0]["obtido"] == {"tipo": "cadeia", "texto": '"4"', "bruto": "4"}
    assert '[TESTE_FALHA] Exemplo 1: esperado 4 (inteiro), obtido "4" (cadeia)' in arena.saida


def test_funcao_sem_retorne(arena):
    r = arena.rodar(com_dobro("    x <- n * 2"))
    assert r[0]["obtido"] == {"tipo": "sem valor", "texto": "sem valor"}


def test_esperar_do_aluno_vai_para_o_original(arena):
    r = arena.rodar(com_dobro("    retorne n * 2", inicio="    esperar_igual(1, 1)"))
    assert [x["k"] for x in r] == [0, 1, 2]
    assert [(f, a[:2]) for f, a in arena.originais] == [("igual", (1, 1))]


def test_esperar_dentro_da_funcao_nao_conta(arena):
    # Chamada de dentro de dobro(): o frame não é o main(), então vai para o original, e o teste da linha vale.
    r = arena.rodar(com_dobro("    esperar_igual(1, 1)\n    retorne 0"))
    assert len(arena.originais) == 4  # 1 do inicio (dobro(21)) + 3 testes
    assert [x["ok"] for x in r] == [False, True, False]


def test_comparacao_invalida_reprova_so_o_teste(arena):
    testes = ('esperar_maior(dobro(1), 10, "Exemplo 1")\n'
              'esperar_maior(texto(1), 10, "Exemplo 2")\n'
              'esperar_igual(dobro(2), 4, "Exemplo 3")')
    codigo = ('algoritmo "T"\n\nfuncao dobro(n)\n    retorne n * 2\nfim_funcao\n\n'
              'funcao texto(n)\n    retorne "abc"\nfim_funcao\n\ninicio\nfim_algoritmo\n')
    r = arena.rodar(codigo, testes)
    assert [(x["k"], x["ok"], x["erro"]) for x in r] == [(0, False, None), (1, False, "comparar"), (2, True, None)]
    assert "[TESTE_FALHA] Exemplo 2: não dá para comparar cadeia com inteiro" in arena.saida
    assert "[TESTE_FALHA] Exemplo 1: esperado maior que 10 (inteiro), obtido 2 (inteiro)" in arena.saida


def test_escreva_com_marcador_nao_gera_resultado(arena):
    r = arena.rodar(com_dobro("    retorne 0", inicio='    escreva("[TESTE_OK] Sucesso: tudo certo")'))
    assert [x["ok"] for x in r] == [False, True, False]  # dobro(0) = 0 passa: só a função decide


def test_verdadeiro_e_contem(arena):
    testes = ('esperar_verdadeiro(par(2), "par")\n'
              'esperar_contem(lst(), 9, "lista")')
    codigo = ('algoritmo "T"\n\nfuncao par(n)\n    retorne n % 2 == 1\nfim_funcao\n\n'
              'funcao lst()\n    var v : lista\n    v <- [1, 2]\n    retorne v\nfim_funcao\n\ninicio\nfim_algoritmo\n')
    r = arena.rodar(codigo, testes)
    assert r[0]["esperado"] == {"tipo": "logico", "texto": "verdadeiro"}
    assert r[0]["obtido"] == {"tipo": "logico", "texto": "falso"}
    assert r[1]["obtido"]["texto"] == "[1, 2]" and r[1]["esperado"]["texto"] == "9"
    assert "esperado conter 9 (inteiro), obtido [1, 2] (lista)" in arena.saida


def test_montagem_inesperada_nao_gera_resultado(arena):
    # N maior que o número de instruções esperar_* no fim de main(): mapa vazio, chamadas vão ao original.
    arena.ns["iniciar_rodada"](99)
    assert arena.ns["mapa_de_testes"]("def main():\n    x = 1\n    esperar_igual(1, 1)\n", 2) == {}
    assert arena.ns["mapa_de_testes"]("def main():\n    esperar_igual(\n        1,\n        1)\n", 1) == {2: 0, 3: 0, 4: 0}


def test_formatar(arena):
    from collections import deque
    fmt, valor = arena.ns["formatar"], arena.ns["valor"]
    assert fmt(None) == "sem valor"
    assert fmt(True) == "verdadeiro" and fmt(False) == "falso"
    assert fmt(4) == "4" and fmt(4.0) == "4.0" and fmt(0.1 + 0.2) == "0.30000000000000004"
    assert fmt("a b\n\tc") == '"a·b↵→c"'
    assert fmt([1, "a b", [True, None]]) == '[1, "a·b", [verdadeiro, sem valor]]'
    assert fmt(deque([1])) == "[1]"
    assert fmt({"a": 1}) == '{"a": 1}'
    assert fmt([[[[[1]]]]]) == "[[[[[…]]]]]"
    assert valor(True) == {"tipo": "logico", "texto": "verdadeiro"}
    assert valor(2.5) == {"tipo": "real", "texto": "2.5", "bruto": 2.5}
    assert "bruto" not in valor(float("nan"))
    grande = valor("x" * 5000)
    assert len(grande["texto"]) == 2001 and grande["texto"].endswith("…") and len(grande["bruto"]) == 2000
    assert len(valor(list(range(10000)))["texto"]) <= 2001
