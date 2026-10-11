"""Juiz da Code Arena: monta o código, compila com meupia-core e roda os testes isolados.

A montagem é a mesma do meuPiá Lab (src/engine/wasm.js): remove
`fim_algoritmo`, insere `usar "testes"` depois da linha `algoritmo`,
anexa os testes e fecha com `fim_algoritmo`.
"""
import json
import os
import re
import secrets
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
EXECUTOR = os.path.join(AQUI, "executor.py")

TEMPO_COMPILACAO = 5  # segundos (compilar leva ~0,1 s; sobra margem no maxDuration de 30 s)
TEMPO_EXECUCAO_MAX = 15  # segundos (total: min(15, 2 + 1 s por teste))
MEMORIA_MAX = 512 * 1024 * 1024
TAMANHO_MAX_CODIGO = 20_000  # caracteres

_RE_ALGORITMO = re.compile(r'(algoritmo\s+"[^"]*")', re.IGNORECASE)
_RE_FIM = re.compile(r"fim_algoritmo", re.IGNORECASE)
_RE_LINHA = re.compile(r"linha (\d+)")
MSG_NAO_CONVERSA = "O código não conversa com os testes. Confira o nome e os parâmetros da função pedida."


def montar(codigo_aluno, testes):
    """Devolve (fonte_final, info) — info serve para mapear linhas de erro."""
    fonte = _RE_FIM.sub("", codigo_aluno)
    linha_usar = None
    if 'usar "testes"' not in fonte.lower():
        m = _RE_ALGORITMO.search(fonte)
        if m:
            linha_usar = fonte[: m.end()].count("\n") + 2
        fonte = _RE_ALGORITMO.sub(r'\1\nusar "testes"', fonte, count=1)
    inicio_testes = fonte.count("\n") + 2
    fonte += "\n\n// --- TESTES AUTOMATIZADOS ---\n" + testes + "\nfim_algoritmo"
    return fonte, {"linha_usar": linha_usar, "inicio_testes": inicio_testes}


def mapear_linha(linha, info):
    """Converte a linha do arquivo montado para a linha do editor do aluno."""
    if linha >= info["inicio_testes"]:
        return None  # erro dentro dos testes (ex.: função com nome errado)
    if info["linha_usar"] and linha > info["linha_usar"]:
        return linha - 1
    return linha


def _extrair_erro(saida):
    m = re.search(r"\[COMPILATION ERROR\]:\s*\n\s*(.+)", saida)
    if m:
        return m.group(1).strip()
    for linha in reversed(saida.strip().splitlines()):
        if "rror" in linha:
            return linha.strip()
    return "Erro de compilação."


def _proteger_processo():
    """Linux: marca o processo da função como não "dumpable". Assim /proc/<pid>/environ e
    /proc/<pid>/mem (onde estão SUPABASE_SERVICE_ROLE_KEY, ARENA_SECRET e ADMIN_TOKEN)
    deixam de ser legíveis pelos filhos que rodam o código do aluno com o mesmo usuário."""
    if not sys.platform.startswith("linux"):
        return
    try:
        import ctypes
        ctypes.CDLL(None, use_errno=True).prctl(4, 0, 0, 0, 0)  # PR_SET_DUMPABLE = 4
    except Exception:  # noqa: BLE001
        pass


_proteger_processo()


def _limitar_recursos(segundos):
    def aplicar():  # roda no filho, só em Linux/macOS
        import resource
        limites = [
            (resource.RLIMIT_AS, MEMORIA_MAX),
            (resource.RLIMIT_CPU, segundos + 1),
            (resource.RLIMIT_NPROC, 0),  # sem fork: o código do aluno não cria processos
            (resource.RLIMIT_FSIZE, 0),  # sem gravar arquivos
        ]
        for recurso, valor in limites:
            try:
                resource.setrlimit(recurso, (valor, valor))
            except Exception:  # noqa: BLE001
                pass
    return aplicar


def _ambiente_limpo():
    # Nada de tokens/segredos do servidor no processo do aluno.
    return {"PATH": "/usr/bin:/bin", "PYTHONHASHSEED": "0", "PYTHONIOENCODING": "utf-8"}


def caracteres_significativos(fonte):
    """Tamanho do código para o desempate, com as regras do lexer do meupia-core:
    fora de texto, `//` comenta até o fim da linha e espaços/tabs/quebras não contam;
    um texto vai de `"` até a próxima `"` não escapada da linha (escapada = precedida
    por nº ímpar de `\\`) e conta inteiro; texto sem fechamento conta até o fim da linha."""
    total = 0
    for linha in fonte.splitlines():
        i, n = 0, len(linha)
        while i < n:
            c = linha[i]
            if c == '"':
                j = i + 1
                while j < n:
                    if linha[j] == '"':
                        barras, b = 0, j - 1
                        while b > i and linha[b] == "\\":
                            barras += 1
                            b -= 1
                        if barras % 2 == 0:
                            break
                    j += 1
                fim = min(j + 1, n)
                total += fim - i
                i = fim
            elif linha.startswith("//", i):
                break
            elif c.isspace():
                i += 1
            else:
                total += 1
                i += 1
    return total


def _linhas_de_teste(testes):
    return [l for l in (testes or "").splitlines() if l.strip().startswith("esperar_")]


def _ler_relatorio(saida, nonce):
    """Linhas assinadas do executor: {i: resultado}, fim?, montagem inválida?"""
    if isinstance(saida, bytes):
        saida = saida.decode("utf-8", errors="replace")
    testes, fim, invalida = {}, False, False
    for linha in (saida or "").splitlines():
        if not linha.startswith(nonce):
            continue
        try:
            dados = json.loads(linha[len(nonce):])
        except ValueError:
            continue
        if "i" in dados:
            testes[int(dados["i"])] = dados
        elif dados.get("fim"):
            fim = True
        elif dados.get("montagem") == "invalida":
            invalida = True
    return testes, fim, invalida


def julgar(codigo_aluno, exemplos, extras, detalhes=False):
    """Julga o código com as duas baterias (exemplos antes dos extras) numa única execução.

    status: aceito (100% dos exemplos) | reprovado_exemplos | erro_compilacao | erro_execucao.
    Sempre devolve exemplos/extras {aprovados, total}, completo e caracteres. Nunca diz qual
    extra falhou; `testes` (por teste, com ms) só vem com detalhes=True — uso interno/scripts."""
    l_ex, l_xt = _linhas_de_teste(exemplos), _linhas_de_teste(extras)
    n_ex, n_xt = len(l_ex), len(l_xt)
    total = n_ex + n_xt
    base = {"exemplos": {"aprovados": 0, "total": n_ex}, "extras": {"aprovados": 0, "total": n_xt},
            "completo": False, "caracteres": caracteres_significativos(codigo_aluno or "")}

    def erro(status, mensagem, **extra):
        return {"status": status, "mensagem": mensagem, **base, **extra}

    if len(codigo_aluno) > TAMANHO_MAX_CODIGO:
        return erro("erro_compilacao", "Código grande demais.")

    fonte, info = montar(codigo_aluno, "\n".join(l_ex + l_xt))
    tempo_total = min(TEMPO_EXECUCAO_MAX, 2 + total)

    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "main.por"), "w", encoding="utf-8") as f:
            f.write(fonte)

        try:
            comp = subprocess.run(
                [sys.executable, "-I", "-c",
                 "from meuPia.compiler import main; main('main.por', 'output')"],
                cwd=tmp, capture_output=True, text=True, timeout=TEMPO_COMPILACAO, env=_ambiente_limpo(),
            )
            saida_comp = comp.stdout + comp.stderr
        except subprocess.TimeoutExpired:
            return erro("erro_compilacao", "Compilação demorou demais.")

        main_py = os.path.join(tmp, "output", "main.py")
        if not os.path.exists(main_py):
            msg = _extrair_erro(saida_comp)
            m = _RE_LINHA.search(msg)
            linha = None
            if m:
                linha = mapear_linha(int(m.group(1)), info)
                if linha is None:
                    msg = MSG_NAO_CONVERSA
                else:
                    msg = _RE_LINHA.sub(f"linha {linha}", msg, count=1)
            return erro("erro_compilacao", msg, linha=linha)

        nonce = secrets.token_hex(16)
        estourou = False
        try:
            exe = subprocess.run(
                [sys.executable, "-I", EXECUTOR, main_py],
                cwd=tmp, input=f"{nonce}\n{total}\n", capture_output=True, text=True,
                timeout=tempo_total, env=_ambiente_limpo(), preexec_fn=_limitar_recursos(tempo_total),
            )
            saida = exe.stdout
        except subprocess.TimeoutExpired as e:
            estourou = True
            saida = e.stdout

    testes, fim, invalida = _ler_relatorio(saida, nonce)
    if invalida:
        return erro("erro_compilacao", MSG_NAO_CONVERSA, linha=None)
    if not testes and not fim and total:
        msg = (f"A execução passou de {tempo_total} s (laço infinito?)." if estourou
               else "O programa terminou de forma inesperada.")
        return erro("erro_execucao", msg)

    resultados = []
    for k in range(total):
        r = testes.get(k) or {"ok": False, "ms": None, "falha": "tempo" if estourou else "excecao"}
        resultados.append({"ok": bool(r.get("ok")), "ms": r.get("ms"), "falha": r.get("falha")})

    ok_ex = sum(1 for r in resultados[:n_ex] if r["ok"])
    ok_xt = sum(1 for r in resultados[n_ex:] if r["ok"])
    out = {"status": "aceito" if ok_ex == n_ex else "reprovado_exemplos",
           "exemplos": {"aprovados": ok_ex, "total": n_ex}, "extras": {"aprovados": ok_xt, "total": n_xt},
           "completo": ok_ex == n_ex and ok_xt == n_xt, "caracteres": base["caracteres"]}
    falha_ex = next((r["falha"] for r in resultados[:n_ex] if not r["ok"] and r["falha"]), None)
    if falha_ex:
        out["falhaExemplo"] = falha_ex  # exemplos são públicos: pode dizer o motivo
    if detalhes:
        out["testes"] = resultados
    return out
