"""Gera arena/equipes.json com códigos aleatórios e imprime o valor para a env ARENA_EQUIPES.

Alternativa offline ao painel da banca (/admin.html), que cria e regenera códigos no banco.

Uso:
  python scripts/gerar_equipes.py 8
  python scripts/gerar_equipes.py arena/equipes_entrada.json   # [{"nome":..., "integrantes":[...]}, ...]
  python scripts/gerar_equipes.py 8 /caminho/saida.json        # destino diferente de arena/equipes.json
"""
import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "api"))
from _lib.arena import gerar_codigo  # noqa: E402


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "8"
    destino = sys.argv[2] if len(sys.argv) > 2 else os.path.join(RAIZ, "arena", "equipes.json")
    if arg.isdigit():
        entrada = [{"nome": f"Equipe {i + 1}", "integrantes": []} for i in range(int(arg))]
    else:
        entrada = json.load(open(arg, encoding="utf-8"))
    equipes, codigos = [], []
    for i, e in enumerate(entrada):
        codigos.append(gerar_codigo(i, codigos))
        equipes.append({"id": f"equipe{i + 1}", "nome": e["nome"], "codigo": codigos[-1],
                        "integrantes": e.get("integrantes", [])})
    json.dump(equipes, open(destino, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"{len(equipes)} equipes -> {destino}\n")
    for e in equipes:
        print(f"  {e['nome']:<20} {e['codigo']}")
    print("\nValor para a variável ARENA_EQUIPES na Vercel:\n")
    print(json.dumps(equipes, ensure_ascii=False))


if __name__ == "__main__":
    main()
