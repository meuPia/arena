"""Versão do plugin `testes` usada SOMENTE pelo juiz no servidor.

Mesma API do meupia-testes, mas não imprime [TESTE_OK]/[TESTE_FALHA]:
o resultado vai para RESULTADOS[ATUAL], e o executor define ATUAL antes de
cada linha de teste do desafio. Chamadas fora de um teste (ATUAL None ou
negativo) são ignoradas; dentro de um teste vale a última chamada, que é a
da própria linha de teste (os argumentos são avaliados antes dela).
Uma comparação que lança exceção conta como falha daquele teste.
"""

ATUAL = None
RESULTADOS = {}


def _registrar(comparar):
    try:
        ok = bool(comparar())
    except Exception:  # noqa: BLE001 — comparação inválida = teste reprovado
        ok = False
    if ATUAL is not None and ATUAL >= 0:
        RESULTADOS[ATUAL] = ok
    return ok


def esperar_igual(recebido, esperado, mensagem=""):
    return _registrar(lambda: recebido == esperado)


def esperar_diferente(recebido, esperado, mensagem=""):
    return _registrar(lambda: recebido != esperado)


def esperar_verdadeiro(condicao, mensagem=""):
    return _registrar(lambda: condicao)


def esperar_falso(condicao, mensagem=""):
    return _registrar(lambda: not condicao)


def esperar_maior(recebido, limite, mensagem=""):
    return _registrar(lambda: recebido > limite)


def esperar_menor(recebido, limite, mensagem=""):
    return _registrar(lambda: recebido < limite)


def esperar_contem(colecao, item, mensagem=""):
    return _registrar(lambda: item in colecao)
