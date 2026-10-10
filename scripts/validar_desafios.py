"""Confere com o juiz real os desafios do banco configurado (store.abrir()).

Com SUPABASE_* (ou Upstash) valida os desafios do evento; sem banco (store Local vazio), valida os
exemplos de arena/exemplos. Critérios em api/_lib/validacao.py.
Uso: python scripts/validar_desafios.py
"""
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "api"))
from _lib import arena, store, validacao  # noqa: E402


def principal():
    db = store.abrir()
    todos = arena.desafios(db)
    print(f"Banco: {type(db).__name__} · conteúdo: {store.k_desafios()} · {len(todos)} desafio(s)")
    if not todos:
        print("Nenhum desafio encontrado.")
        return 1
    ok = True
    for cod in todos:
        r = validacao.validar(arena.desafio_completo(db, cod))
        ok &= r["ok"]
        print(f"{'OK  ' if r['ok'] else 'ERRO'} {cod}  gabarito={r['gabarito']} max={r['maxMs']}ms"
              f"  ·  inicial={r['inicial']}" + "".join(f"\n       ✗ {e}" for e in r["erros"]))
    print("TUDO OK" if ok else "HÁ ERROS")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(principal())
