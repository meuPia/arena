"""Pontua as entregas de uma equipe no modo offline: julga cada .por com o juiz real (testes de exemplo + testes
extras) e grava no SQLite da banca como submissões. Vale a melhor de cada desafio, como no evento online.

Roda na máquina da banca (macOS/Linux/WSL: o juiz precisa de POSIX), com o banco COMPLETO (copiar_supabase.py
sem --publico):
  ARENA_SQLITE=~/arena.sqlite3 python3 scripts/pontuar_equipe.py "Nome da equipe" pasta/ [arquivo.por ...]
  ARENA_SQLITE=~/arena.sqlite3 python3 scripts/pontuar_equipe.py --placar
  ARENA_SQLITE=~/arena.sqlite3 python3 scripts/pontuar_equipe.py --equipes

Qual desafio é cada arquivo: a 1ª linha que a IDE grava (`// arena: B01`) ou, sem ela, o nome (B01.por,
"B01 (2).por"). Vários arquivos do mesmo desafio: vale o modificado por último. O horário do arquivo é o
horário da submissão (desempate do placar), então copie as entregas preservando a data (pendrive/Explorer
preservam). --limpar apaga antes as submissões dessa equipe (para refazer uma pontuação errada).
"""
import argparse
import os
import re
import sys
import unicodedata

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "api"))

from _lib import arena, servico, store  # noqa: E402
from _lib.web import Erro  # noqa: E402

CABECALHO = re.compile(r"^\s*//\s*arena:\s*([A-Za-z]\d{2})\b")
NOME = re.compile(r"^([A-Za-z]\d{2})(?![0-9])")


def _sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").casefold().strip()


def ler_fonte(caminho):
    with open(caminho, "rb") as f:
        bruto = f.read()
    for cod in ("utf-8-sig", "cp1252"):  # Bloco de Notas antigo grava em ANSI
        try:
            return bruto.decode(cod)
        except UnicodeDecodeError:
            pass
    return bruto.decode("utf-8", "replace")


def codigo_do_arquivo(caminho, fonte):
    m = CABECALHO.match(fonte.splitlines()[0] if fonte.strip() else "") or NOME.match(os.path.basename(caminho))
    return m.group(1).upper() if m else None


def coletar(caminhos):
    """{codigo: caminho mais recente}, [avisos]."""
    arquivos = []
    for c in caminhos:
        if os.path.isdir(c):
            for raiz, _, nomes in os.walk(c):
                arquivos += [os.path.join(raiz, n) for n in sorted(nomes) if n.lower().endswith(".por")]
        elif os.path.isfile(c):
            arquivos.append(c)
        else:
            sys.exit(f"{c}: não encontrado")
    escolhidos, avisos = {}, []
    for a in arquivos:
        cod = codigo_do_arquivo(a, ler_fonte(a))
        if not cod:
            avisos.append(f"ignorado (sem código do desafio na 1ª linha nem no nome): {a}")
            continue
        if cod in escolhidos:
            velho, novo = sorted([escolhidos[cod], a], key=os.path.getmtime)
            avisos.append(f"{cod}: vale {os.path.basename(novo)} (mais recente); ignorado {os.path.basename(velho)}")
            escolhidos[cod] = novo
        else:
            escolhidos[cod] = a
    return escolhidos, avisos


def achar_equipe(nome, db):
    alvo = _sem_acento(nome)
    for eid, e in arena.equipes(db).items():
        if _sem_acento(e["nome"]) == alvo or eid == nome:
            return eid, e
    return None, None


def imprimir_equipes(db):
    for eid, e in sorted(arena.equipes(db).items(), key=lambda x: x[1]["nome"]):
        print(f"  {e['nome']}  ({eid})")


def imprimir_placar(db):
    p = servico.placar(admin=True, db=db)
    print(f"\n{'#':>2}  {'Equipe':<28} {'Pontos':>6} {'Compl.':>6} {'Caract.':>7}")
    for l in p["linhas"]:
        print(f"{l['posicao']:>2}  {l['nome'][:28]:<28} {l['pontos']:>6} {l['completos']:>6} {l['caracteres']:>7}")


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("equipe", nargs="?")
    ap.add_argument("caminhos", nargs="*")
    ap.add_argument("--placar", action="store_true", help="só mostra o placar")
    ap.add_argument("--equipes", action="store_true", help="lista as equipes do banco")
    ap.add_argument("--limpar", action="store_true", help="apaga as submissões da equipe antes de pontuar")
    a = ap.parse_args(argv)
    os.environ.setdefault("ARENA_MODO", "offline")  # placar sem freeze nem horário

    db = store.abrir()
    if not isinstance(db, store.Sqlite):
        sys.exit("pontue no SQLite da banca (ARENA_SQLITE), nunca direto no Supabase do evento: tire SUPABASE_*/KV_* do shell")
    print(f"banco: {db.caminho}")
    if a.equipes:
        return imprimir_equipes(db)
    if a.placar:
        return imprimir_placar(db)
    if not a.equipe or not a.caminhos:
        ap.error("informe a equipe e a pasta (ou os arquivos .por) da entrega")
    if not db.hgetall(store.k_segredos()):
        sys.exit("este banco não tem os testes extras (cópia --publico?): use o banco completo da banca")

    eid, e = achar_equipe(a.equipe, db)
    if not e:
        print(f'equipe "{a.equipe}" não encontrada. Equipes do banco:')
        imprimir_equipes(db)
        sys.exit(1)

    escolhidos, avisos = coletar(a.caminhos)
    for av in avisos:
        print("aviso:", av)
    if not escolhidos:
        sys.exit("nenhum arquivo .por com desafio reconhecido")

    if a.limpar:
        db.apagar(store.k_aceitas(eid), store.k_tentativas(eid), store.k_ultima(eid))
        print(f"submissões anteriores de {e['nome']} apagadas")

    print(f"\n{e['nome']}: {len(escolhidos)} entrega(s)")
    todos = arena.desafios(db)
    for cod in sorted(escolhidos):
        caminho = escolhidos[cod]
        if cod not in todos:
            print(f"  {cod}  desafio inexistente ({os.path.basename(caminho)})")
            continue
        try:
            r = servico.pontuar(eid, cod, ler_fonte(caminho), db=db, agora=os.path.getmtime(caminho))
        except Erro as erro:
            print(f"  {cod}  ERRO: {erro}")
            continue
        detalhe = {
            "aceito": lambda: f"extras {r['extras']['aprovados']}/{r['extras']['total']} · "
                              f"{r['pontos']}/{r['pontosModulo']} pts{' ✅' if r['completo'] else ''} · {r['caracteres']} caract.",
            "reprovado_exemplos": lambda: f"exemplos {r['exemplos']['aprovados']}/{r['exemplos']['total']} · 0 pts",
        }.get(r["status"], lambda: (r.get("mensagem") or "")[:90])()
        print(f"  {cod}  {r['status']:<20} {detalhe}")

    total = next(l["pontos"] for l in servico.placar(admin=True, db=db)["linhas"] if l["id"] == eid)
    print(f"  total da equipe (melhor de cada desafio): {total} pts")
    imprimir_placar(db)


if __name__ == "__main__":
    main(sys.argv[1:])
