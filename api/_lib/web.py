"""Utilidades HTTP para as Vercel Functions (Python) + autenticação da equipe."""
import base64
import hashlib
import hmac
import json
import os
import sys
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

_SEGREDO_DEV = "dev-inseguro-troque-ARENA_SECRET"


def _segredo():
    s = os.environ.get("ARENA_SECRET")
    if not s and os.environ.get("VERCEL_ENV") == "production":
        raise RuntimeError("ARENA_SECRET não configurado")
    return (s or _SEGREDO_DEV).encode()


def emitir_token(equipe_id):
    corpo = base64.urlsafe_b64encode(equipe_id.encode()).decode().rstrip("=")
    assinatura = hmac.new(_segredo(), corpo.encode(), hashlib.sha256).hexdigest()[:32]
    return f"{corpo}.{assinatura}"


def ler_token(token):
    try:
        corpo, assinatura = token.split(".", 1)
        esperado = hmac.new(_segredo(), corpo.encode(), hashlib.sha256).hexdigest()[:32]
        if not hmac.compare_digest(assinatura, esperado):
            return None
        return base64.urlsafe_b64decode(corpo + "=" * (-len(corpo) % 4)).decode()
    except Exception:  # noqa: BLE001
        return None


def admin_ok(valor):
    tok = os.environ.get("ADMIN_TOKEN")
    return bool(tok) and hmac.compare_digest(valor or "", tok)


class Erro(Exception):
    def __init__(self, status, mensagem):
        super().__init__(mensagem)
        self.status = status
        self.mensagem = mensagem


class Base(BaseHTTPRequestHandler):
    """Subclasses implementam get(req) e/ou post(req) devolvendo um dict."""

    def _responder(self, status, corpo):
        dados = json.dumps(corpo, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(dados)))
        self.end_headers()
        self.wfile.write(dados)

    def _rodar(self, metodo):
        fn = getattr(self, metodo, None)
        if fn is None:
            return self._responder(405, {"erro": "Método não permitido."})
        try:
            self.query = {k: v[0] for k, v in parse_qs(urlparse(self.path).query).items()}
            self.corpo = {}
            if metodo == "post":
                n = int(self.headers.get("Content-Length") or 0)
                if n > 100_000:
                    raise Erro(413, "Requisição grande demais.")
                self.corpo = json.loads(self.rfile.read(n) or b"{}")
            self._responder(200, fn())
        except Erro as e:
            self._responder(e.status, {"erro": e.mensagem})
        except Exception as e:  # noqa: BLE001
            print(f"[arena] erro interno: {e!r}", file=sys.stderr)
            self._responder(500, {"erro": "Erro interno. Avise a organização."})

    def do_GET(self):
        self._rodar("get")

    def do_POST(self):
        self._rodar("post")

    def equipe_id(self):
        auth = self.headers.get("Authorization", "")
        eid = ler_token(auth[7:]) if auth.startswith("Bearer ") else None
        if not eid:
            raise Erro(401, "Sessão inválida. Entre novamente com o código da equipe.")
        return eid

    def log_message(self, *args):  # silencia o log padrão
        pass
