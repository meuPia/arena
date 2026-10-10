"""Gera arena/equipes.json com códigos aleatórios e imprime o valor para a env ARENA_EQUIPES.

Uso:
  python scripts/gerar_equipes.py 8
  python scripts/gerar_equipes.py arena/equipes_entrada.json   # [{"nome":..., "integrantes":[...]}, ...]
"""
import json
import os
import secrets
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PALAVRAS = ["ORION", "VEGA", "LYRA", "NOVA", "ATLAS", "TITAN", "PULSAR", "QUASAR", "COMET", "NEBULA",
            "DRACO", "RIGEL", "SIRIUS", "ALTAIR", "CYGNUS", "HYDRA"]
ALFABETO = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # sem 0/O/1/I


def codigo(i):
    return f"{PALAVRAS[i % len(PALAVRAS)]}-" + "".join(secrets.choice(ALFABETO) for _ in range(4))


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "8"
    if arg.isdigit():
        entrada = [{"nome": f"Equipe {i + 1}", "integrantes": []} for i in range(int(arg))]
    else:
        entrada = json.load(open(arg, encoding="utf-8"))
    equipes = [{
        "id": f"equipe{i + 1}", "nome": e["nome"], "codigo": codigo(i), "integrantes": e.get("integrantes", []),
    } for i, e in enumerate(entrada)]
    destino = os.path.join(RAIZ, "arena", "equipes.json")
    json.dump(equipes, open(destino, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"{len(equipes)} equipes -> {destino}\n")
    for e in equipes:
        print(f"  {e['nome']:<20} {e['codigo']}")
    print("\nValor para a variável ARENA_EQUIPES na Vercel:\n")
    print(json.dumps(equipes, ensure_ascii=False))


if __name__ == "__main__":
    main()
