"""Sobe a Arena no modo offline numa máquina do laboratório (Windows, macOS ou Linux; Python 3.10+).

  python scripts/iniciar_offline.py              # http://localhost:8787
  python scripts/iniciar_offline.py --banca      # máquina da banca: placar e painel com as entregas pontuadas
  python scripts/iniciar_offline.py --abrir      # abre o navegador quando o servidor responder (versão portátil)

Sem login e sem submissão: as equipes resolvem na IDE (Rodar = testes de exemplo) e salvam cada missão com
"Salvar .por". O banco é o SQLite em ARENA_SQLITE (shell ou .env.local; padrão offline/arena.sqlite3):
  máquinas das equipes: cópia com --publico (scripts/copiar_supabase.py), sem testes extras nem gabaritos;
  máquina da banca: cópia completa; as entregas são pontuadas com scripts/pontuar_equipe.py.
Serve o build mais novo entre offline/dist (sem internet, scripts/preparar_offline.py) e dist/ (npm run build).
"""
import os
import socket
import subprocess
import sys
import time
import webbrowser

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(args):
    # avisos aparecem antes do log do servidor; console do Windows sem UTF-8 troca o caractere em vez de quebrar
    sys.stdout.reconfigure(line_buffering=True, errors="replace")
    sys.path.insert(0, os.path.join(RAIZ, "scripts"))
    from servidor_local import carregar_env_local
    carregar_env_local()  # ARENA_SQLITE do .env.local (o shell tem prioridade)
    os.environ["ARENA_MODO"] = "offline"
    os.environ.setdefault("ARENA_SQLITE", os.path.join(RAIZ, "offline", "arena.sqlite3"))
    for nome in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_SECRET_KEY", "KV_REST_API_URL",
                 "KV_REST_API_TOKEN", "UPSTASH_REDIS_REST_URL", "UPSTASH_REDIS_REST_TOKEN"):
        os.environ.pop(nome, None)  # nunca o banco do evento
    if "--banca" in args:
        os.environ.setdefault("ADMIN_TOKEN", "admin")
    # o build mais novo: offline/dist (sem internet) só vale se for refeito depois de mudar o código
    builds = [d for d in (os.path.join(RAIZ, "offline", "dist"), os.path.join(RAIZ, "dist"))
              if os.path.exists(os.path.join(d, "index.html"))]
    if not builds:
        sys.exit("sem build: rode `npm run build` (ou scripts/preparar_offline.py) antes")
    dist = max(builds, key=lambda d: os.path.getmtime(os.path.join(d, "index.html")))
    os.environ["ARENA_DIST"] = dist
    if os.path.exists(os.path.join(dist, "vendor", "pyodide", "pyodide.js")):
        print(f"build: {os.path.relpath(dist, RAIZ)} (sem internet)")
    else:
        print(f"build: {os.path.relpath(dist, RAIZ)} (a IDE baixa o Pyodide da internet; sem internet, rode "
              "scripts/preparar_offline.py)")

    sys.path.insert(0, os.path.join(RAIZ, "api"))
    from _lib import arena, store
    db = store.abrir()
    n = len(db.hgetall(store.k_desafios()))
    segredos = bool(db.hgetall(store.k_segredos()))
    print(f"banco: {db.caminho} · {n} desafio(s)" + (" · COM testes extras (máquina da banca)" if segredos else ""))
    if not n:
        print("ATENÇÃO: banco sem desafios — a IDE vai mostrar os desafios de EXEMPLO "
              f"({len(arena._exemplos())}). Copie o banco com scripts/copiar_supabase.py --publico.")
    if segredos and "--banca" not in args:
        print("ATENÇÃO: este banco tem testes extras e gabaritos. Nas máquinas das equipes use a cópia --publico.")
    servidor = subprocess.Popen([sys.executable, os.path.join(RAIZ, "scripts", "servidor_local.py")])
    if "--abrir" in args:
        abrir_quando_pronto(servidor, int(os.environ.get("PORTA", "8787")))
    servidor.wait()


def abrir_quando_pronto(servidor, porta):
    for _ in range(100):
        if servidor.poll() is not None:
            print("o servidor não subiu (porta ocupada? feche a outra janela da Arena e tente de novo)")
            return
        try:
            socket.create_connection(("127.0.0.1", porta), timeout=0.2).close()
        except OSError:
            time.sleep(0.1)
            continue
        url = f"http://localhost:{porta}/"
        print(f"\nArena aberta no navegador: {url}  (mantenha esta janela aberta; para sair, feche-a)\n")
        webbrowser.open(url)
        return


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        pass
