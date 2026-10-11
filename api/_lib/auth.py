"""Login da banca (admin e juízes) por OAuth 2.0 authorization code, só com a biblioteca padrão.

Fluxo: /api/oauth_inicio gera um `state` assinado (provedor + nonce, 10 min) e guarda o nonce no
cookie `arena_oauth`; o provedor volta em /api/oauth_retorno, que confere state e cookie, troca o
code por identidades verificadas e, se a pessoa tiver papel, grava o cookie de sessão (12 h).

Identidades (minúsculas): google:<email> + email:<email>; github:<login> + email:<cada verificado>.
Root: só pela identidade do provedor que está em ARENA_ROOT (um email: igual vindo de outro provedor
não basta). O papel NÃO vai no cookie: é resolvido a cada requisição (rebaixar vale na hora).

O id_token do Google chega direto do endpoint de token, por TLS e com o client secret: pelo OIDC
Core §3.1.3.7 a validação TLS substitui a assinatura; conferimos aud, iss e exp.
"""
import base64
import json
import os
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request

from . import store
from .web import assinar, ler_assinado

COOKIE_OAUTH = "arena_oauth"
COOKIE_SESSAO = "arena_sessao"
VALIDADE_STATE = 600  # segundos
VALIDADE_SESSAO = 12 * 3600
PAPEIS = ("admin", "juiz")
AUTOR_EMERGENCIA = {"nome": "token de emergência", "papel": "admin", "root": True, "ids": [], "provedor": None}

PROVEDORES = {
    "google": {
        "nome": "Google",
        "autorizacao": "https://accounts.google.com/o/oauth2/v2/auth",
        "token": "https://oauth2.googleapis.com/token",
        "escopo": "openid email profile",
        "extra": {"prompt": "select_account"},
    },
    "github": {
        "nome": "GitHub",
        "autorizacao": "https://github.com/login/oauth/authorize",
        "token": "https://github.com/login/oauth/access_token",
        "escopo": "read:user user:email",
        "extra": {"allow_signup": "false"},
    },
}
EMISSORES_GOOGLE = ("https://accounts.google.com", "accounts.google.com")


class ErroAuth(Exception):
    """Login recusado; `motivo` vira ?erro=<motivo> na tela do painel."""

    def __init__(self, motivo, ids=()):
        super().__init__(motivo)
        self.motivo = motivo
        self.ids = list(ids)


def _credenciais(provedor):
    p = provedor.upper()
    return os.environ.get(f"OAUTH_{p}_ID", ""), os.environ.get(f"OAUTH_{p}_SECRET", "")


def provedores_configurados():
    """[{id, nome}] dos provedores com client id e secret definidos."""
    return [{"id": p, "nome": d["nome"]} for p, d in PROVEDORES.items() if all(_credenciais(p))]


def _http(metodo, url, dados=None, cabecalhos=None):
    """Chamada HTTP que devolve JSON (os testes substituem esta função)."""
    corpo = urllib.parse.urlencode(dados).encode() if dados is not None else None
    cab = {"Accept": "application/json", "User-Agent": "meupia-arena", **(cabecalhos or {})}
    req = urllib.request.Request(url, data=corpo, headers=cab, method=metodo)
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            return json.loads(r.read())
    except (urllib.error.URLError, ValueError) as e:
        raise ErroAuth("provedor_falhou") from e


def url_retorno(base_url):
    return base_url.rstrip("/") + "/api/oauth_retorno"


def iniciar(provedor, base_url):
    """(url do provedor, nonce para o cookie arena_oauth)."""
    if provedor not in PROVEDORES or not all(_credenciais(provedor)):
        raise ErroAuth("provedor_invalido")
    cid, _ = _credenciais(provedor)
    nonce = secrets.token_urlsafe(16)
    d = PROVEDORES[provedor]
    params = {"client_id": cid, "redirect_uri": url_retorno(base_url), "response_type": "code",
              "scope": d["escopo"], "state": assinar({"p": provedor, "n": nonce}, "oauth", VALIDADE_STATE),
              **d["extra"]}
    return d["autorizacao"] + "?" + urllib.parse.urlencode(params), nonce


def _payload_jwt(token):
    try:
        meio = token.split(".")[1]
        return json.loads(base64.urlsafe_b64decode(meio + "=" * (-len(meio) % 4)))
    except Exception as e:  # noqa: BLE001
        raise ErroAuth("provedor_falhou") from e


def _google(code, base_url, agora):
    cid, segredo = _credenciais("google")
    r = _http("POST", PROVEDORES["google"]["token"], {
        "code": code, "client_id": cid, "client_secret": segredo,
        "redirect_uri": url_retorno(base_url), "grant_type": "authorization_code"})
    if "id_token" not in r:
        raise ErroAuth("provedor_falhou")
    t = _payload_jwt(r["id_token"])
    if t.get("aud") != cid or t.get("iss") not in EMISSORES_GOOGLE or t.get("exp", 0) < agora:
        raise ErroAuth("provedor_falhou")
    email = (t.get("email") or "").strip().lower()
    if not email or t.get("email_verified") not in (True, "true"):
        raise ErroAuth("identidade_nao_verificada")
    return {"ids": [f"google:{email}", f"email:{email}"], "nome": t.get("name") or email}


def _github(code, base_url, _agora):
    cid, segredo = _credenciais("github")
    r = _http("POST", PROVEDORES["github"]["token"], {
        "code": code, "client_id": cid, "client_secret": segredo, "redirect_uri": url_retorno(base_url)})
    tok = r.get("access_token")
    if not tok:
        raise ErroAuth("provedor_falhou")
    cab = {"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json"}
    usuario = _http("GET", "https://api.github.com/user", cabecalhos=cab)
    emails = _http("GET", "https://api.github.com/user/emails", cabecalhos=cab)
    login = (usuario.get("login") or "").strip().lower()
    if not login:
        raise ErroAuth("provedor_falhou")
    verificados = sorted({e["email"].strip().lower() for e in emails if e.get("verified") and e.get("email")})
    return {"ids": [f"github:{login}"] + [f"email:{e}" for e in verificados], "nome": usuario.get("name") or login}


_TROCAR = {"google": _google, "github": _github}


def concluir(code, state, nonce_cookie, base_url, agora=None):
    """Confere o state (assinatura, validade, nonce do cookie) e devolve {ids, nome, provedor}."""
    agora = agora if agora is not None else time.time()
    dados = ler_assinado(state, "oauth", agora)
    if not dados or not nonce_cookie or not secrets.compare_digest(str(dados.get("n", "")), nonce_cookie):
        raise ErroAuth("estado_invalido")
    provedor = dados.get("p")
    if provedor not in _TROCAR or not all(_credenciais(provedor)):
        raise ErroAuth("estado_invalido")
    if not code:
        raise ErroAuth("provedor_falhou")
    ident = _TROCAR[provedor](code, base_url, agora)
    return {**ident, "provedor": provedor}


# ---------------- root, perfis e papel ----------------

def root():
    """Identidades do root ({"google": email, "github": login}), da variável secreta ARENA_ROOT."""
    bruto = os.environ.get("ARENA_ROOT", "").strip()
    if not bruto:
        return set()
    try:
        dados = json.loads(bruto)
    except ValueError as e:
        raise ValueError("ARENA_ROOT não é um JSON válido") from e
    if not isinstance(dados, dict):
        raise ValueError("ARENA_ROOT deve ser um objeto JSON")
    return {f"{p}:{str(v).strip().lower()}" for p, v in dados.items() if p in PROVEDORES and v}


def perfis(db):
    """{email: {email, nome, github, papel}} da banca cadastrada."""
    return {e: json.loads(v) for e, v in db.hgetall(store.k_usuarios()).items()}


def papel(ids, db):
    """{"papel", "root", "email"} de quem tem essas identidades, ou None."""
    ids = set(ids)
    if ids & root():
        return {"papel": "admin", "root": True, "email": None}
    for email, p in perfis(db).items():
        gh = (p.get("github") or "").strip().lower()
        if f"email:{email}" in ids or (gh and f"github:{gh}" in ids):
            if p.get("papel") in PAPEIS:
                return {"papel": p["papel"], "root": False, "email": email}
    return None


def emitir_sessao(ident):
    return assinar({"ids": ident["ids"], "nome": ident["nome"], "provedor": ident["provedor"]},
                   "sessao", VALIDADE_SESSAO)


def autor_da_sessao(valor, db=None, agora=None):
    """Autor (nome, papel, root, ids, provedor) do cookie de sessão, com o papel lido agora. None se inválido."""
    dados = ler_assinado(valor, "sessao", agora)
    if not dados:
        return None
    p = papel(dados.get("ids", []), db or store.abrir())
    if not p:
        return None
    return {"nome": dados.get("nome", ""), "ids": dados.get("ids", []), "provedor": dados.get("provedor"),
            "papel": p["papel"], "root": p["root"]}
