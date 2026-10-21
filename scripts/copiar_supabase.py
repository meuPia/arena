"""Copia o banco do Supabase (todas as linhas de arena_hash e arena_lista) para o SQLite do servidor local.

Uso (as variáveis do Supabase vão no shell, de forma explícita, como no servidor local):
  SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY=... python3 scripts/copiar_supabase.py [destino.sqlite3] [--substituir] [--publico]

--publico copia só a parte pública dos desafios (enunciado, código inicial, testes de exemplo): é o banco das
máquinas das equipes no modo offline. Sem segredos (testes extras e gabaritos), equipes, perfis nem submissões.
O banco completo fica só na máquina da banca, que pontua as entregas (scripts/pontuar_equipe.py).

Destino padrão: ARENA_SQLITE ou /tmp/meupia-arena.sqlite3. Com o destino já preenchido, só grava com
--substituir (apaga tudo no SQLite antes). Só lê do Supabase. O arquivo tem desafios reais, gabaritos e
código-fonte: fora do repositório, com permissão só do dono.
"""
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "api"))

from _lib import store  # noqa: E402


def main(args):
    substituir, publico = "--substituir" in args, "--publico" in args
    resto = [a for a in args if a not in ("--substituir", "--publico")]
    url = os.environ.get("SUPABASE_URL")
    chave = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_SECRET_KEY")
    if not (url and chave):
        sys.exit("defina SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY no shell")
    destino = os.path.abspath(resto[0] if resto else os.environ.get("ARENA_SQLITE", "/tmp/meupia-arena.sqlite3"))
    if destino.startswith(RAIZ + os.sep) and not destino.startswith(os.path.join(RAIZ, "offline") + os.sep):
        sys.exit(f"{destino}: dentro do repositório (público). Use um caminho fora dele ou em offline/")

    db = store.Sqlite(destino)
    if not db.vazio() and not substituir:
        sys.exit(f"{destino} já tem dados: use --substituir para apagar e copiar de novo")

    hashes, listas = store.SupabaseRest(url, chave).tudo()
    if publico:
        hashes, listas = [h for h in hashes if h[0] == store.k_desafios()], []
    db.carregar(hashes, listas, substituir=substituir)

    desafios = db.hgetall(store.k_desafios())
    segredos = db.hgetall(store.k_segredos())
    print(f"copiado para {destino}: {len(hashes)} campos de hash, {len(listas)} itens de lista")
    print(f"  {store.k_desafios()}: {len(desafios)} · {store.k_segredos()}: {len(segredos)} · "
          f"{store.k_equipes()}: {len(db.hgetall(store.k_equipes()))} · "
          f"{store.k_usuarios()}: {len(db.hgetall(store.k_usuarios()))}")
    if publico:
        print("  só a parte pública (sem testes extras, gabaritos, equipes nem perfis): banco das máquinas das equipes")
    elif set(desafios) != set(segredos):
        print("  ATENÇÃO: desafios sem segredos (ou o contrário): " + ", ".join(sorted(set(desafios) ^ set(segredos))))
    print(f"Para usar: ARENA_SQLITE={destino} npm run local")


if __name__ == "__main__":
    main(sys.argv[1:])
