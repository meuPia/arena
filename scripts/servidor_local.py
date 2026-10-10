"""Servidor local que imita a Vercel: serve dist/ e roteia /api/<nome> para api/<nome>.py.

Uso:
  npm run build
  ARENA_MODO=ensaio python scripts/servidor_local.py        # http://localhost:8787
Sem KV_REST_API_URL, os dados ficam em /tmp/meupia-arena.json.
"""
import importlib.util
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = os.path.join(RAIZ, "api")
DIST = os.path.join(RAIZ, "dist")
sys.path.insert(0, API)

_handlers = {}


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
    porta = int(os.environ.get("PORTA", "8787"))
    print(f"Code Arena local em http://localhost:{porta}  (modo: {os.environ.get('ARENA_MODO') or 'horário real'})")
    ThreadingHTTPServer(("127.0.0.1", porta), Roteador).serve_forever()
