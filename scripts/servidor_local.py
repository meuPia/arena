"""Servidor local que imita a Vercel: serve dist/ e roteia /api/<nome> para api/<nome>.py.

Uso:
  npm run build
  ARENA_MODO=ensaio python scripts/servidor_local.py        # http://localhost:8787
Sem banco remoto, os dados ficam no SQLite em ARENA_SQLITE (padrão: /tmp/meupia-arena.sqlite3);
scripts/copiar_supabase.py copia o banco do evento para ele.
ARENA_DIST troca a pasta servida (o pacote offline usa offline/dist).

Do .env.local, só as variáveis do login da banca (OAUTH_*, ARENA_ROOT, ARENA_URL) e do modo offline
(ARENA_MODO, ARENA_SQLITE; caminho relativo = a partir da raiz do repositório) são lidas.
As do banco (SUPABASE_*, KV_*) ficam de fora de propósito: o servidor local nunca grava no
banco do evento. Para isso, exporte-as no shell de forma explícita.
"""
import importlib.util
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = os.path.join(RAIZ, "api")
DIST = os.path.abspath(os.environ.get("ARENA_DIST") or os.path.join(RAIZ, "dist"))
sys.path.insert(0, API)

_handlers = {}


def carregar_env_local():
    caminho = os.path.join(RAIZ, ".env.local")
    if not os.path.exists(caminho):
        return
    with open(caminho, encoding="utf-8") as f:
        for linha in f:
            nome, sep, valor = linha.strip().partition("=")
            nome = nome.removeprefix("export ").strip()
            if not sep or nome.startswith("#"):
                continue
            valor = valor.strip().strip("'\"")
            if nome == "ARENA_SQLITE":
                valor = os.path.join(RAIZ, os.path.expanduser(valor))  # absoluto continua absoluto
            if nome.startswith("OAUTH_") or nome in ("ARENA_ROOT", "ARENA_URL", "ARENA_MODO", "ARENA_SQLITE"):
                os.environ.setdefault(nome, valor)


def _handler(nome):
    if nome not in _handlers:
        caminho = os.path.join(API, nome + ".py")
        if not os.path.exists(caminho) or nome.startswith("_"):
            return None
        spec = importlib.util.spec_from_file_location(f"api_{nome}", caminho)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _handlers[nome] = mod.handler
    return _handlers[nome]


class Roteador(SimpleHTTPRequestHandler):
    # Tipos fixos: no Windows o mimetypes lê o registro, que às vezes diz text/plain para .js (o navegador
    # recusa módulos assim e a página fica em branco) e não conhece .wasm (o Pyodide carrega mais devagar).
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
        ".mjs": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8",
        ".json": "application/json", ".wasm": "application/wasm", ".svg": "image/svg+xml",
        ".woff": "font/woff", ".woff2": "font/woff2", ".zip": "application/zip", ".whl": "application/zip",
        ".por": "text/plain; charset=utf-8", ".md": "text/markdown; charset=utf-8",
    }

    def guess_type(self, path):
        ext = os.path.splitext(str(path))[1].lower()
        return self.extensions_map.get(ext) or super().guess_type(path)

    def __init__(self, *a, **kw):
        super().__init__(*a, directory=DIST, **kw)

    def _api(self):
        caminho = urlparse(self.path).path
        if not caminho.startswith("/api/"):
            return False
        h = _handler(caminho[len("/api/"):].strip("/"))
        if h is None:
            self.send_error(404)
            return True
        # Reaproveita a conexão atual com a classe da função
        self.__class__ = type("Api", (h,), {})
        getattr(self, "do_" + self.command)()
        return True

    def do_GET(self):
        if not self._api():
            super().do_GET()

    def do_POST(self):
        if not self._api():
            self.send_error(405)


if __name__ == "__main__":
    carregar_env_local()
    porta = int(os.environ.get("PORTA", "8787"))
    print(f"Code Arena local em http://localhost:{porta}  (modo: {os.environ.get('ARENA_MODO') or 'horário real'})")
    ThreadingHTTPServer(("127.0.0.1", porta), Roteador).serve_forever()
