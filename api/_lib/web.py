"""Utilidades HTTP para as Vercel Functions (Python) + autenticação da equipe e da banca."""
import base64
import hashlib
import hmac
import json
import os
import sys
import time
from http.cookies import SimpleCookie
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


def _b64(dados):
    return base64.urlsafe_b64encode(dados).decode().rstrip("=")


def _assinatura(proposito, corpo):
    # O propósito entra no HMAC: um state de OAuth nunca vale como sessão, e vice-versa.
    return hmac.new(_segredo(), f"{proposito}|{corpo}".encode(), hashlib.sha256).hexdigest()[:40]


def assinar(dados, proposito, validade):
    """Blob `base64(json).hmac` com expiração (`validade` em segundos)."""
    corpo = _b64(json.dumps({**dados, "exp": int(time.time() + validade)}).encode())
    return f"{corpo}.{_assinatura(proposito, corpo)}"


def ler_assinado(valor, proposito, agora=None):
    """Dados do blob, ou None se a assinatura não confere ou expirou."""
    try:
        corpo, assinatura = (valor or "").split(".", 1)
        if not hmac.compare_digest(assinatura, _assinatura(proposito, corpo)):
            return None
        dados = json.loads(base64.urlsafe_b64decode(corpo + "=" * (-len(corpo) % 4)))
        if dados.get("exp", 0) < (agora if agora is not None else time.time()):
            return None
        return dados
    except Exception:  # noqa: BLE001
        return None


def cookie(nome, valor, max_age, seguro):
    """Cabeçalho Set-Cookie HttpOnly/SameSite=Lax (max_age=0 apaga)."""
    partes = [f"{nome}={valor}", "Path=/", "HttpOnly", "SameSite=Lax", f"Max-Age={int(max_age)}"]
    if seguro:
        partes.append("Secure")
    return "; ".join(partes)


def eh_local(host):
    return (host or "").split(":")[0] in ("localhost", "127.0.0.1", "[::1]")


def origem_ok(origem, host):
    """POST só da própria origem (com o cookie SameSite=Lax, isso cobre CSRF). Sem Origin: ok."""
    if not origem:
        return True
    return urlparse(origem).netloc.lower() == (host or "").lower()


def admin_ok(valor):
    tok = os.environ.get("ADMIN_TOKEN")
    return bool(tok) and hmac.compare_digest(valor or "", tok)


class Erro(Exception):
    def __init__(self, status, mensagem):
        super().__init__(mensagem)
        self.status = status
        self.mensagem = mensagem


class Resposta:
    """Resposta com cookies e/ou redirecionamento (`local`); o padrão continua sendo devolver um dict."""

    def __init__(self, corpo=None, status=200, cookies=(), local=None):
        self.corpo, self.status, self.cookies, self.local = corpo, status, list(cookies), local


class Base(BaseHTTPRequestHandler):
    """Subclasses implementam get() e/ou post() devolvendo um dict ou uma Resposta."""

    def _responder(self, status, corpo, cookies=(), local=None):
        dados = b"" if local else json.dumps(corpo, ensure_ascii=False).encode()
        self.send_response(status)
        if local:
            self.send_header("Location", local)
        else:
            self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        for c in cookies:
            self.send_header("Set-Cookie", c)
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
                if not origem_ok(self.headers.get("Origin"), self.host()):
                    raise Erro(403, "Origem não permitida.")
                if not (self.headers.get("Content-Type") or "").startswith("application/json"):
                    raise Erro(415, "Envie JSON.")
                n = int(self.headers.get("Content-Length") or 0)
                if n > 100_000:
                    raise Erro(413, "Requisição grande demais.")
                self.corpo = json.loads(self.rfile.read(n) or b"{}")
            r = fn()
            if isinstance(r, Resposta):
                self._responder(r.status if not r.local else 302, r.corpo, r.cookies, r.local)
            else:
                self._responder(200, r)
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

    def host(self):
        return self.headers.get("X-Forwarded-Host") or self.headers.get("Host") or ""

    def base_url(self):
        """Origem pública do app: ARENA_URL ou o host da requisição (vale para a URL de retorno do OAuth)."""
        fixa = os.environ.get("ARENA_URL", "").rstrip("/")
        if fixa:
            return fixa
        proto = self.headers.get("X-Forwarded-Proto") or ("http" if eh_local(self.host()) else "https")
        return f"{proto}://{self.host()}"

    def seguro(self):
        return not eh_local(self.host())

    def cookies(self):
        c = SimpleCookie()
        try:
            c.load(self.headers.get("Cookie") or "")
        except Exception:  # noqa: BLE001
            return {}
        return {k: m.value for k, m in c.items()}

    def banca(self):
        """Quem da banca está chamando: token de emergência (X-Admin-Token) ou sessão OAuth. 401 sem nenhum."""
        from . import auth  # evita import circular
        if admin_ok(self.headers.get("X-Admin-Token")):
            return auth.AUTOR_EMERGENCIA
        autor = auth.autor_da_sessao(self.cookies().get(auth.COOKIE_SESSAO))
        if not autor:
            raise Erro(401, "Entre com sua conta para acessar o painel.")
        return autor

    def ip(self):
        """IP do cliente. Na Vercel, x-real-ip/x-forwarded-for são definidos pela plataforma."""
        ip = self.headers.get("x-real-ip") or (self.headers.get("x-forwarded-for") or "").split(",")[0]
        return ip.strip() or (self.client_address[0] if self.client_address else "")

    def log_message(self, *args):  # silencia o log padrão
        pass
