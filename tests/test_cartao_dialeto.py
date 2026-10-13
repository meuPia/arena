"""Confere com o juiz real o que docs/cartao-dialeto.md afirma sobre o dialeto.

Se um teste daqui quebrar depois de trocar a versão do meupia-core, atualize o cartão junto.
"""
import os
import sys

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "api"))

from _lib import juiz  # noqa: E402


def programa(corpo):
    return f'algoritmo "cartao"\n{corpo}\ninicio\nfim_algoritmo'


ACEITOS = {
    "var local com valor e para": ("""
funcao f(n)
    var total : inteiro <- 0
    var i : inteiro
    para i de 1 ate n faca
        total <- total + i
    fim_para
    retorne total
fim_funcao""", 'esperar_igual(f(4), 10, "a")'),
    "variavel global": ("""
var
    contador : inteiro
funcao f()
    contador <- contador + 1
    retorne contador
fim_funcao""", 'esperar_igual(f(), 1, "a")'),
    "tipos e valores iniciais": ("""
funcao f()
    var i : inteiro
    var m : real
    var c : cadeia
    var s : string
    var ok : logico
    var v : lista
    var d : dicionario
    retorne "" + i + m + c + s + ok + tamanho(v) + tamanho(d)
fim_funcao""", 'esperar_igual(f(), "00.0falso00", "a")'),
    "operadores": ("""
funcao f(a)
    retorne (a mod 3) + (a % 4) * 10
fim_funcao""", 'esperar_igual(f(7), 31, "a")'),
    "comparacoes": ("""
funcao f(a)
    retorne (a = 3) e (a == 3) e (a <> 4) e (a != 4) e (a <= 3) e (a >= 3) e nao (a < 3) ou falso
fim_funcao""", 'esperar_verdadeiro(f(3), "a")\nesperar_falso(f(4), "b")'),
    "divisao": ("""
funcao f(a, b)
    retorne a / b
fim_funcao
funcao g(a, b)
    retorne piso(a / b)
fim_funcao""", 'esperar_igual(f(7, 2), 3.5, "a")\nesperar_igual(g(7, 2), 3, "b")\nesperar_igual(g(-7, 2), -4, "c")'),
    "texto em ordem alfabetica e expressao na comparacao": ("""
funcao f(c, i)
    retorne c >= "a" e c <= "z" e i % 2 = 0
fim_funcao""", 'esperar_verdadeiro(f("m", 2), "a")\nesperar_falso(f("M", 2), "b")'),
    "se aninhado": ("""
funcao f(n)
    se n < 0 entao
        retorne "negativo"
    senao
        se n = 0 entao
            retorne "zero"
        senao
            retorne "positivo"
        fim_se
    fim_se
fim_funcao""", 'esperar_igual(f(-1), "negativo", "a")\nesperar_igual(f(0), "zero", "b")\nesperar_igual(f(5), "positivo", "c")'),
    "acentos": ("""
funcao f(n)
    var i, s : inteiro
    s <- 0
    para i de 1 até n faça
        se não (i = 2) então
            s <- s + i
        senão
            s <- s + 0
        fim_se
    fim_para
    retorne s
fim_funcao""", 'esperar_igual(f(3), 4, "a")'),
    "para regressivo e texto": ("""
funcao f(t)
    var r : cadeia
    var i : inteiro
    r <- ""
    para i de tamanho(t) - 1 ate 0 passo -1 faca
        r <- r + t[i]
    fim_para
    retorne r + t[0] + t[tamanho(t) - 1]
fim_funcao""", 'esperar_igual(f("abc"), "cbaac", "a")'),
    "enquanto, interrompa e continue": ("""
funcao f(n)
    var i : inteiro
    i <- 0
    enquanto verdadeiro faca
        i <- i + 1
        se i % 2 = 0 entao
            continue
        fim_se
        se i > n entao
            interrompa
        fim_se
    fim_enquanto
    retorne i
fim_funcao""", 'esperar_igual(f(4), 5, "a")'),
    "juntar numero e logico em texto": ("""
funcao f(n)
    retorne "" + n + " " + verdadeiro
fim_funcao""", 'esperar_igual(f(42), "42 verdadeiro", "a")'),
    "escreva nao conta": ("""
funcao f()
    escreva("valor: ", 1)
    retorne 2
fim_funcao""", 'esperar_igual(f(), 2, "a")'),
    "lista": ("""
funcao f()
    var v, w : lista
    var x : inteiro
    v <- [5, 6, 7]
    v[0] <- 9
    v.adicionar(8)
    x <- v.removerFim()
    w <- []
    w.expandir(v)
    w.adicionar(x + tamanho(v))
    retorne w
fim_funcao
funcao g()
    var v : lista
    v <- [1]
    v.limpar()
    retorne tamanho(v)
fim_funcao
funcao h(m)
    retorne m[1][0]
fim_funcao""", 'esperar_igual(f(), [9, 6, 7, 11], "a")\nesperar_igual(g(), 0, "b")\n'
               'esperar_igual(h([[1, 2], [3, 4]]), 3, "c")'),
    "dicionario": ("""
funcao f(t)
    var conta : dicionario
    var i : inteiro
    para i de 0 ate tamanho(t) - 1 faca
        conta[t[i]] <- conta.pegar(t[i], 0) + 1
    fim_para
    retorne conta.pegar("a", 0) * 10 + conta.pegar("z", 0)
fim_funcao""", 'esperar_igual(f("banana"), 30, "a")'),
    "matematica": ("""
funcao f()
    retorne raiz(16) + potencia(2, 3) + absoluto(-2) + teto(1.2) + piso(1.8)
fim_funcao
funcao g()
    retorne "" + potencia(2, 3)
fim_funcao
funcao trig()
    retorne seno(0) + cosseno(0) + tangente(0) + piso(pi)
fim_funcao""", 'esperar_igual(f(), 17, "a")\nesperar_igual(g(), "8.0", "b")\nesperar_igual(trig(), 4, "c")'),
}

ERROS = {
    "contador sem var": ("""
funcao f(n)
    var s : inteiro
    para k de 1 ate n faca
        s <- s + k
    fim_para
    retorne s
fim_funcao""", 'esperar_igual(f(3), 6, "a")', 'a variável "k" não foi declarada no bloco var'),
    "fatia nao existe": ("""
funcao f(t)
    retorne t[1:3]
fim_funcao""", 'esperar_igual(f("abcde"), "bc", "a")', 'esperado "]", encontrado ":"'),
    "declarada duas vezes": ("""
funcao f()
    var x : inteiro
    var x : inteiro
    retorne x
fim_funcao""", 'esperar_igual(f(), 0, "a")', 'a variável "x" já foi declarada neste bloco'),
}

# "um exemplo deu erro durante a execução" (falhaExemplo = excecao, texto em src/arena/submissao.js)
EXCECOES = {
    "funcao com outro nome": ("""
funcao dobro(n)
    retorne n * 2
fim_funcao""", 'esperar_igual(f(2), 4, "a")'),
    "parametros a menos": ("""
funcao f(a)
    retorne a
fim_funcao""", 'esperar_igual(f(1, 2), 1, "a")'),
    "indice fora da lista": ("""
funcao f(v)
    retorne v[tamanho(v)]
fim_funcao""", 'esperar_igual(f([1, 2]), 2, "a")'),
    "divisao por zero": ("""
funcao f(a)
    retorne a / 0
fim_funcao""", 'esperar_igual(f(1), 0, "a")'),
}


@pytest.mark.parametrize("nome", ACEITOS)
def test_cartao_aceito(nome):
    corpo, testes = ACEITOS[nome]
    r = juiz.julgar(programa(corpo), testes, "")
    assert r["status"] == "aceito", r.get("mensagem")
    assert r["exemplos"]["aprovados"] == r["exemplos"]["total"]


@pytest.mark.parametrize("nome", ERROS)
def test_cartao_mensagens(nome):
    corpo, testes, mensagem = ERROS[nome]
    r = juiz.julgar(programa(corpo), testes, "")
    assert r["status"] != "aceito"
    assert mensagem in (r.get("mensagem") or "")


@pytest.mark.parametrize("nome", EXCECOES)
def test_cartao_erro_na_execucao(nome):
    corpo, testes = EXCECOES[nome]
    r = juiz.julgar(programa(corpo), testes, "")
    assert (r["status"], r.get("falhaExemplo")) == ("reprovado_exemplos", "excecao")


def test_leia_reprova_o_teste():
    r = juiz.julgar(programa("""
funcao f()
    var x : inteiro
    leia(x)
    retorne x
fim_funcao"""), 'esperar_igual(f(), 0, "a")', "")
    assert r["status"] != "aceito"
