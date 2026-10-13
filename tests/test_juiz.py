import os
import sys

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "api"))
sys.path.insert(0, os.path.join(RAIZ, "api", "_lib", "shim"))

from _lib import juiz  # noqa: E402
from meupia_testes import plugin_testes  # noqa: E402


# ---------------- shim ----------------

@pytest.fixture
def shim():
    plugin_testes.ATUAL = None
    plugin_testes.RESULTADOS.clear()
    yield plugin_testes
    plugin_testes.ATUAL = None
    plugin_testes.RESULTADOS.clear()


def test_shim_ignora_chamada_fora_de_teste(shim):
    shim.esperar_igual(1, 1)
    shim.ATUAL = -1
    shim.esperar_igual(1, 1)
    assert shim.RESULTADOS == {}


def test_shim_vale_a_ultima_chamada_do_teste(shim):
    shim.ATUAL = 0
    shim.esperar_igual(1, 1)
    shim.esperar_igual(1, 2)
    shim.ATUAL = 1
    shim.esperar_igual(1, 2)
    shim.esperar_igual(1, 1)
    assert shim.RESULTADOS == {0: False, 1: True}


def test_shim_comparacao_que_lanca_vira_falha(shim):
    shim.ATUAL = 0
    assert shim.esperar_maior("a", 1) is False
    shim.ATUAL = 1
    assert shim.esperar_contem(5, 1) is False
    assert shim.RESULTADOS == {0: False, 1: False}


def test_shim_verdadeiro_e_falso_por_truthiness(shim):
    shim.ATUAL = 0
    assert shim.esperar_verdadeiro("x")
    shim.ATUAL = 1
    assert shim.esperar_falso([])
    shim.ATUAL = 2
    assert not shim.esperar_verdadeiro(0)
    assert shim.RESULTADOS == {0: True, 1: True, 2: False}


# ---------------- caracteres significativos ----------------

def test_caracteres_ignoram_comentarios_indentacao_e_linhas_em_branco():
    a = 'funcao f(x)\n    retorne x + 1\nfim_funcao'
    b = '// cabeçalho\nfuncao   f(x)   // comentário\n\n\tretorne x+1\n\nfim_funcao\n'
    assert juiz.caracteres_significativos(a) == juiz.caracteres_significativos(b)
    assert juiz.caracteres_significativos("retorne x") == len("retornex")


def test_caracteres_espaco_dentro_de_texto_conta():
    assert juiz.caracteres_significativos('escreva("a b")') == juiz.caracteres_significativos('escreva("ab")') + 1


def test_caracteres_barra_dupla_dentro_de_texto_nao_e_comentario():
    assert juiz.caracteres_significativos('x <- "http://x" // fim') == len('x<-"http://x"')


def test_caracteres_aspas_escapadas_e_texto_sem_fechamento():
    assert juiz.caracteres_significativos('"a\\" b"') == len('"a\\" b"')
    assert juiz.caracteres_significativos('"a\\\\" b') == len('"a\\\\"b')
    assert juiz.caracteres_significativos('x <- "aberto  // x') == len('x<-"aberto  // x')


# ---------------- julgamento ----------------
# Função fictícia definida aqui mesmo: os testes do juiz não dependem de nenhum desafio real.

EXEMPLOS = '''esperar_igual(triplo(1), 3, "a")
esperar_igual(triplo(2), 6, "b")
esperar_igual(triplo(0), 0, "c")'''
EXTRAS = '''esperar_igual(triplo(5), 15, "x1")
esperar_igual(triplo(6), 18, "x2")
esperar_igual(triplo(7), 21, "x3")
esperar_igual(triplo(-1), -3, "x4")'''
TESTE = 'esperar_igual(triplo(4), 12, "x")'
CORRETO = "    retorne n * 3"


def aluno(corpo, inicio=""):
    return (f'algoritmo "T"\nvar\n    i, x : inteiro\n    v : inteiro\nfuncao triplo(n)\n{corpo}\nfim_funcao\n'
            f'inicio\n{inicio}\nfim_algoritmo')


def se_n(cond, bloco):
    return f"    se {cond} então\n{bloco}\n    fim_se\n{CORRETO}"


LACO = "        i <- 0\n        enquanto i < 1 faça\n            i <- 0\n        fim_enquanto"


def test_juiz_correto_aceito_e_completo():
    fonte = aluno(CORRETO)
    r = juiz.julgar(fonte, EXEMPLOS, EXTRAS)
    assert r["status"] == "aceito" and r["completo"]
    assert r["exemplos"] == {"aprovados": 3, "total": 3}
    assert r["extras"] == {"aprovados": 4, "total": 4}
    assert r["caracteres"] == juiz.caracteres_significativos(fonte)
    assert "testes" not in r


def test_juiz_reprovado_nos_exemplos():
    r = juiz.julgar(aluno(se_n("n = 2", "        retorne 0")), EXEMPLOS, EXTRAS)
    assert r["status"] == "reprovado_exemplos"
    assert r["exemplos"] == {"aprovados": 2, "total": 3}
    assert not r["completo"]


def test_juiz_aceito_parcial_nao_revela_qual_extra_falhou():
    r = juiz.julgar(aluno(se_n("n = 7", "        retorne 0")), EXEMPLOS, EXTRAS)
    assert r["status"] == "aceito" and not r["completo"]
    assert r["extras"] == {"aprovados": 3, "total": 4}
    assert set(r) == {"status", "exemplos", "extras", "completo", "caracteres"}


def test_juiz_excecao_em_um_teste_nao_afeta_os_demais():
    r = juiz.julgar(aluno(se_n("n = 5", "        v <- []\n        retorne v[99]")), EXEMPLOS, EXTRAS, detalhes=True)
    assert r["status"] == "aceito"
    assert [t["ok"] for t in r["testes"]] == [True, True, True, False, True, True, True]
    assert r["testes"][3]["falha"] == "excecao"


def test_juiz_laco_infinito_em_um_teste_reprova_so_ele():
    import time
    t = time.time()
    r = juiz.julgar(aluno(se_n("n = 7", LACO)), EXEMPLOS, EXTRAS, detalhes=True)
    assert time.time() - t < 4
    assert [t["ok"] for t in r["testes"]] == [True, True, True, True, True, False, True]
    assert r["testes"][5]["falha"] == "tempo"
    assert r["extras"] == {"aprovados": 3, "total": 4}


def test_juiz_esperar_chamado_pelo_aluno_nao_aprova():
    r = juiz.julgar(aluno('    esperar_igual(1, 1, "forjado")\n    retorne 0'), "", TESTE)
    assert r["extras"]["aprovados"] == 0


def test_juiz_inicio_com_erro_nao_impede_os_testes():
    r = juiz.julgar(aluno(CORRETO, inicio="    x <- 0\n    escreva(10 / x)"), EXEMPLOS, EXTRAS)
    assert r["status"] == "aceito" and r["completo"]


def test_juiz_estouro_do_tempo_total_mantem_testes_concluidos(monkeypatch):
    monkeypatch.setattr(juiz, "TEMPO_EXECUCAO_MAX", 3)
    extras = "\n".join([f'esperar_igual(triplo({k}), {3 * k}, "x")' for k in range(4)]
                       + ['esperar_igual(triplo(8), 24, "x")'] * 6)
    r = juiz.julgar(aluno(se_n("n > 4", LACO)), 'esperar_igual(triplo(1), 3, "c")', extras, detalhes=True)
    assert r["status"] == "aceito"
    assert r["extras"] == {"aprovados": 4, "total": 10}
    assert all(not t["ok"] for t in r["testes"][5:])


def test_juiz_nao_aceita_marcador_forjado():
    fonte = 'algoritmo "T"\nfuncao triplo(n)\n    escreva("[TESTE_OK] Sucesso: forjado")\n    retorne 0\nfim_funcao\ninicio\nfim_algoritmo'
    r = juiz.julgar(fonte, "", TESTE)
    assert r["status"] == "aceito" and r["extras"]["aprovados"] == 0 and not r["completo"]


def test_juiz_erro_de_compilacao_aponta_linha_do_editor():
    fonte = 'algoritmo "T"\nfuncao triplo(n)\n    retorne x\nfim_funcao\ninicio\nfim_algoritmo'
    r = juiz.julgar(fonte, TESTE, "")
    assert r["status"] == "erro_compilacao"
    assert r["linha"] == 3


def test_juiz_nome_de_funcao_errado_vira_mensagem_amigavel():
    fonte = 'algoritmo "T"\nfuncao triplicar(n)\n    retorne n\nfim_funcao\ninicio\nfim_algoritmo'
    r = juiz.julgar(fonte, TESTE, "")
    assert r["status"] in ("erro_compilacao", "reprovado_exemplos")
    assert r["exemplos"]["aprovados"] == 0


def test_juiz_nao_ve_segredos_do_servidor(monkeypatch):
    monkeypatch.setenv("ARENA_SECRET", "segredo-super")
    fonte = 'algoritmo "T"\nfuncao triplo(n)\n    retorne os.environ.get("ARENA_SECRET", "")\nfim_funcao\ninicio\nfim_algoritmo'
    r = juiz.julgar(fonte, "", 'esperar_igual(triplo(1), "segredo-super", "x")')
    assert not r["completo"]


# ---------------- isolamento do código do aluno ----------------
# `expr` é Python que o aluno consegue escrever (identificadores desconhecidos passam direto).
# A função soma 0 * len(expr) à resposta certa: se a operação for permitida, os testes passam.

def com_operacao(expr):
    return aluno(f"    retorne n * 3 + 0 * len(str({expr}))")


@pytest.mark.parametrize("expr", [
    'open("main.por").read()',                      # testes extras no diretório de trabalho
    'open("output/main.py").read()',
    'open("/etc/hosts").read()',                     # qualquer arquivo fora das bibliotecas
    'open("/proc/self/environ").read()',
    'open("x.txt", "w").write("a")',                 # gravar arquivo
    '__import__("os").listdir(".")',
    '__import__("os").system("true")',               # processos
    '__import__("subprocess").run(["true"])',
    '__import__("_posixsubprocess")',
    '__import__("socket")',                          # rede
    '__import__("urllib.request")',
    '__import__("ctypes")',                          # memória crua
], ids=lambda e: e[:40])
def test_juiz_bloqueia_operacao_perigosa(expr):
    r = juiz.julgar(com_operacao(expr), EXEMPLOS, EXTRAS)
    assert r["status"] == "reprovado_exemplos" and r["exemplos"]["aprovados"] == 0, r


def test_juiz_apaga_os_testes_antes_de_executar():
    # os.path.exists não é auditado: confirma que os arquivos com os testes já foram apagados.
    fonte = aluno('    se __import__("os").path.exists("main.por") ou __import__("os").path.exists("output") então\n'
                  '        retorne 0\n    fim_se\n' + CORRETO)
    r = juiz.julgar(fonte, EXEMPLOS, EXTRAS)
    assert r["status"] == "aceito" and r["completo"], r


def test_juiz_permite_bibliotecas_do_python():
    r = juiz.julgar(com_operacao('__import__("fractions").Fraction(1, 3)'), EXEMPLOS, EXTRAS)
    assert r["status"] == "aceito" and r["completo"], r


# ---------------- layout da Vercel ----------------

def test_compila_com_dependencias_fora_do_site_packages(tmp_path):
    """Na Vercel o meupia-core fica fora do site-packages do interpretador e o compilador roda com -I.
    Regressão: a submissão dava "ModuleNotFoundError: No module named 'meuPia'" só em produção."""
    import importlib.util
    import subprocess

    venv = tmp_path / "venv"
    subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(venv)], check=True)
    deps = os.path.dirname(os.path.dirname(importlib.util.find_spec("meuPia").origin))
    script = (
        "import json, sys; sys.path.insert(0, 'api'); from _lib import juiz; "
        "d = json.load(open('arena/exemplos/B91.json')); "
        "print(juiz.julgar(d['gabarito'], d['testesPublicos'], d['testesExtras'])['status'])"
    )
    r = subprocess.run([str(venv / "bin" / "python"), "-c", script], cwd=RAIZ, capture_output=True, text=True,
                       timeout=120, env={"PATH": "/usr/bin:/bin", "PYTHONPATH": deps})
    assert r.stdout.strip() == "aceito", r.stdout + r.stderr
