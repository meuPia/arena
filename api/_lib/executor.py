"""Executa o main.py gerado pelo meupia-core num processo separado, com cada teste isolado.

Uso: python -I executor.py <main.py>
stdin: 1ª linha = nonce, 2ª linha = N (nº de linhas de teste anexadas pelo juiz).

As N últimas instruções de main() são as linhas de teste do desafio. Cada uma
roda dentro de _arena_teste(k, ...), com alarme próprio: exceção, laço infinito
ou comparação inválida reprovam só aquele teste. O `inicio` do aluno roda antes,
com o mesmo limite, e não conta como teste.

Antes de executar, o executor apaga os arquivos do diretório de trabalho (main.por e
output/, que contêm os testes extras) e liga um guarda de auditoria (sys.addaudithook):
o código do aluno só lê arquivos das bibliotecas do Python e não abre outros arquivos,
não grava, não usa rede, não cria processos nem carrega ctypes. Não é um sandbox
completo: é uma camada a mais sobre o ambiente vazio e os rlimits do juiz.

A saída do programa do aluno é descartada. No stdout real saem só linhas
<nonce>{json}: uma por teste ({"i", "ok", "ms", "falha"}), e {"fim": true} no final
(ou {"montagem": "invalida"}). Como cada linha sai na hora, os testes já concluídos
valem mesmo que o processo seja morto pelo limite de tempo total.
"""
import ast
import io
import json
import os
import shutil
import signal
import sys
import time

TEMPO_POR_TESTE = 1.0  # segundos

# Módulos que o código do aluno não pode importar (rede, processos, memória crua).
MODULOS_PROIBIDOS = frozenset({
    "_posixsubprocess", "subprocess", "_ctypes", "ctypes", "socket", "_socket", "ssl", "_ssl",
    "select", "selectors", "multiprocessing", "_multiprocessing", "_posixshmem", "pty", "mmap",
    "fcntl", "resource", "urllib.request", "http.client", "ftplib", "smtplib", "webbrowser",
})
# Prefixos de eventos de auditoria sempre recusados (os.listdir/os.scandir são tratados à parte).
EVENTOS_PROIBIDOS = ("os.", "socket.", "subprocess.", "ctypes.", "shutil.", "urllib.", "http.",
                     "ftplib.", "smtplib.", "webbrowser.", "mmap.", "pty.", "fcntl.", "resource.")
_FLAGS_ESCRITA = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND


class _TempoDoTeste(BaseException):
    pass


def _eh_teste(no):
    return (isinstance(no, ast.Expr) and isinstance(no.value, ast.Call)
            and isinstance(no.value.func, ast.Name) and no.value.func.id.startswith("esperar_"))


def transformar(codigo, n):
    """Reescreve main(): `inicio` do aluno -> _arena_inicio(); teste k -> _arena_teste(k, lambda: ...).
    Devolve None se as N últimas instruções de main() não forem chamadas esperar_*."""
    arvore = ast.parse(codigo)
    main = next((no for no in arvore.body if isinstance(no, ast.FunctionDef) and no.name == "main"), None)
    if main is None:
        return None
    globais = [no for no in main.body if isinstance(no, ast.Global)]
    corpo = [no for no in main.body if not isinstance(no, ast.Global)]
    if len(corpo) < n or not all(_eh_teste(no) for no in corpo[len(corpo) - n:]):
        return None
    inicio, testes = corpo[: len(corpo) - n], corpo[len(corpo) - n:]

    novo = list(globais)
    novo.append(ast.FunctionDef(
        name="_arena_inicio", args=ast.arguments(posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], defaults=[]),
        body=list(globais) + (inicio or [ast.Pass()]), decorator_list=[], type_params=[]))
    novo.append(ast.Expr(ast.Call(ast.Name("_arena_teste", ast.Load()),
                                  [ast.Constant(-1), ast.Name("_arena_inicio", ast.Load())], [])))
    for k, teste in enumerate(testes):
        fn = ast.Lambda(ast.arguments(posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], defaults=[]), teste.value)
        novo.append(ast.Expr(ast.Call(ast.Name("_arena_teste", ast.Load()), [ast.Constant(k), fn], [])))
    main.body = novo
    return compile(ast.fix_missing_locations(arvore), "main.py", "exec")


def _raizes_leitura():
    """Diretórios das bibliotecas do Python (stdlib, site-packages, shim): os únicos legíveis."""
    candidatos = list(sys.path) + [sys.prefix, sys.base_prefix, sys.exec_prefix, sys.base_exec_prefix]
    raizes = set()
    for c in candidatos:
        if c and os.path.isdir(c):
            r = os.path.realpath(c)
            if r != os.path.sep:
                raizes.add(r.rstrip(os.path.sep) + os.path.sep)
    return tuple(sorted(raizes))


def _guarda(raizes):
    """Hook de auditoria: recusa o que o código do aluno não precisa (ver docstring do módulo)."""
    def legivel(caminho):
        if isinstance(caminho, int):
            return False  # descritores (ex.: open(1, "w") no stdout real)
        try:
            real = os.path.realpath(os.fsdecode(caminho if caminho not in (None, "") else "."))
        except (TypeError, ValueError):
            return False
        return (real + os.path.sep).startswith(raizes)

    def gancho(evento, args):
        if evento == "open":
            caminho, modo, flags = args
            escrita = (isinstance(modo, str) and any(c in modo for c in "wax+")) or \
                (isinstance(flags, int) and flags & _FLAGS_ESCRITA)
            if escrita or not legivel(caminho):
                raise PermissionError("acesso a arquivo não permitido no juiz")
        elif evento in ("os.listdir", "os.scandir"):
            if not legivel(args[0]):
                raise PermissionError("acesso a arquivo não permitido no juiz")
        elif evento == "import":
            if args[0] in MODULOS_PROIBIDOS or args[0].split(".")[0] in MODULOS_PROIBIDOS:
                raise ImportError(f"módulo {args[0]} não permitido no juiz")
        elif evento.startswith(EVENTOS_PROIBIDOS):
            raise PermissionError(f"operação não permitida no juiz ({evento})")
    return gancho


def _apagar_diretorio_de_trabalho():
    """Remove main.por, output/ e o que mais o compilador deixou (os testes estão lá)."""
    for nome in os.listdir("."):
        caminho = os.path.join(".", nome)
        if os.path.isdir(caminho) and not os.path.islink(caminho):
            shutil.rmtree(caminho, ignore_errors=True)
        else:
            try:
                os.remove(caminho)
            except OSError:
                pass


def principal():
    nonce = sys.stdin.readline().strip()
    n = int(sys.stdin.readline().strip() or 0)
    caminho = sys.argv[1]
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "shim"))

    from meupia_testes import plugin_testes  # noqa: E402  (shim do juiz)

    saida_real = sys.stdout

    def emitir(dados):
        saida_real.write("\n" + nonce + json.dumps(dados) + "\n")
        saida_real.flush()

    with open(caminho, encoding="utf-8") as f:
        try:
            programa = transformar(f.read(), n)
        except SyntaxError:
            programa = None
    if programa is None:
        emitir({"montagem": "invalida"})
        return

    ativo = [False]

    def alarme(_sinal, _quadro):
        if ativo[0]:
            raise _TempoDoTeste()

    signal.signal(signal.SIGALRM, alarme)

    def _arena_teste(k, fn):
        plugin_testes.ATUAL = k
        plugin_testes.RESULTADOS.pop(k, None)
        falha = None
        inicio = time.perf_counter()
        ativo[0] = True
        signal.setitimer(signal.ITIMER_REAL, TEMPO_POR_TESTE)
        try:
            fn()
            ativo[0] = False
        except _TempoDoTeste:
            falha = "tempo"
        except BaseException:  # noqa: BLE001 — inclusive SystemExit: só este teste falha
            falha = "excecao"
        finally:
            ativo[0] = False
            signal.setitimer(signal.ITIMER_REAL, 0)
            plugin_testes.ATUAL = None
        if k < 0:
            return
        ok = falha is None and plugin_testes.RESULTADOS.get(k, False)
        emitir({"i": k, "ok": bool(ok), "ms": int((time.perf_counter() - inicio) * 1000), "falha": falha})

    _apagar_diretorio_de_trabalho()
    sys.addaudithook(_guarda(_raizes_leitura()))  # daqui em diante não dá para desligar

    sys.stdout = io.StringIO()
    sys.stdin = io.StringIO("")  # sem leia() interativo no juiz
    try:
        exec(programa, {"__name__": "__main__", "_arena_teste": _arena_teste})
    except BaseException:  # noqa: BLE001 — erro fora dos testes (ex.: no nível do módulo)
        pass
    finally:
        sys.stdout = saida_real
    emitir({"fim": True})


if __name__ == "__main__":
    principal()
