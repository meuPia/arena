import base64
import json
import os
import sys
import time
import urllib.parse

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "api"))

from _lib import admin, auth, servico, store  # noqa: E402
from _lib.web import Erro, assinar, cookie, ler_assinado, origem_ok  # noqa: E402

BASE = "https://arena.exemplo.dev"
# Identidades fictícias: nenhuma identidade real fica no repositório.
ROOT = {"google": "root@exemplo.com", "github": "root-exemplo"}


@pytest.fixture
def db(tmp_path, monkeypatch):
    for v in ("SUPABASE_URL", "KV_REST_API_URL", "UPSTASH_REDIS_REST_URL"):
        monkeypatch.delenv(v, raising=False)  # testes nunca gravam no banco real
    monkeypatch.setenv("ARENA_ARQUIVO_LOCAL", str(tmp_path / "db.json"))
    monkeypatch.setenv("ARENA_MODO", "ensaio")
    monkeypatch.setenv("OAUTH_GOOGLE_ID", "cid-google")
    monkeypatch.setenv("OAUTH_GOOGLE_SECRET", "seg-google")
    monkeypatch.setenv("OAUTH_GITHUB_ID", "cid-github")
    monkeypatch.setenv("OAUTH_GITHUB_SECRET", "seg-github")
    monkeypatch.setenv("ARENA_ROOT", json.dumps(ROOT))
    return store.abrir()


def jwt(payload):
    meio = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    return f"cabecalho.{meio}.assinatura"


def google_token(**kw):
    t = {"aud": "cid-google", "iss": "https://accounts.google.com", "exp": time.time() + 300,
         "email": "Juiza@Exemplo.com", "email_verified": True, "name": "Juíza"}
    t.update(kw)
    return t


def simular(monkeypatch, respostas):
    """Substitui auth._http: respostas = {url: dict | callable(dados, cabecalhos)}."""
    chamadas = []

    def falso(metodo, url, dados=None, cabecalhos=None):
        chamadas.append((metodo, url, dados, cabecalhos))
        r = respostas[url]
        return r(dados, cabecalhos) if callable(r) else r
    monkeypatch.setattr(auth, "_http", falso)
    return chamadas


def iniciar(provedor):
    url, nonce = auth.iniciar(provedor, BASE)
    state = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)["state"][0]
    return url, state, nonce


# ---------------- blobs assinados, cookies e origem ----------------

def test_blob_assinado_confere_proposito_e_validade():
    b = assinar({"x": 1}, "sessao", 60)
    assert ler_assinado(b, "sessao")["x"] == 1
    assert ler_assinado(b, "oauth") is None                 # outro propósito
    assert ler_assinado(b, "sessao", agora=time.time() + 120) is None  # expirado
    corpo, sig = b.split(".")
    assert ler_assinado(corpo + "." + "0" * len(sig), "sessao") is None
    assert ler_assinado("lixo", "sessao") is None


def test_cookie_secure_fora_de_localhost_e_origem():
    assert "Secure" in cookie("a", "1", 60, True) and "Secure" not in cookie("a", "1", 60, False)
    assert "HttpOnly" in cookie("a", "1", 60, False) and "SameSite=Lax" in cookie("a", "1", 60, False)
    assert origem_ok(None, "arena.dev") and origem_ok("https://arena.dev", "arena.dev")
    assert not origem_ok("https://malicioso.dev", "arena.dev")


# ---------------- início e state ----------------

def test_so_provedores_configurados(db, monkeypatch):
    assert [p["id"] for p in auth.provedores_configurados()] == ["google", "github"]
    monkeypatch.delenv("OAUTH_GITHUB_SECRET")
    assert [p["id"] for p in auth.provedores_configurados()] == ["google"]
    with pytest.raises(auth.ErroAuth):
        auth.iniciar("github", BASE)
    with pytest.raises(auth.ErroAuth):
        auth.iniciar("microsoft", BASE)


def test_inicio_monta_url_com_retorno_unico(db):
    url, state, nonce = iniciar("google")
    q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    assert url.startswith("https://accounts.google.com/")
    assert q["redirect_uri"] == [BASE + "/api/oauth_retorno"] and q["client_id"] == ["cid-google"]
    assert q["scope"] == ["openid email profile"] and nonce


@pytest.mark.parametrize("caso", ["nonce_diferente", "sem_cookie", "forjado", "expirado"])
def test_state_invalido_recusado(db, monkeypatch, caso):
    simular(monkeypatch, {auth.PROVEDORES["google"]["token"]: {"id_token": jwt(google_token())}})
    _, state, nonce = iniciar("google")
    agora = None
    if caso == "nonce_diferente":
        nonce = "outro"
    elif caso == "sem_cookie":
        nonce = None
    elif caso == "forjado":
        state = assinar({"p": "google", "n": nonce}, "sessao", 600)  # assinado para outro propósito
    else:
        agora = time.time() + auth.VALIDADE_STATE + 5
    with pytest.raises(auth.ErroAuth) as e:
        auth.concluir("code", state, nonce, BASE, agora=agora)
    assert e.value.motivo == "estado_invalido"


# ---------------- Google ----------------

def test_google_ok_normaliza_email(db, monkeypatch):
    chamadas = simular(monkeypatch, {auth.PROVEDORES["google"]["token"]: {"id_token": jwt(google_token())}})
    _, state, nonce = iniciar("google")
    ident = auth.concluir("code-1", state, nonce, BASE)
    assert ident == {"ids": ["google:juiza@exemplo.com", "email:juiza@exemplo.com"], "nome": "Juíza",
                     "provedor": "google"}
    assert chamadas[0][2]["redirect_uri"] == BASE + "/api/oauth_retorno" and chamadas[0][2]["code"] == "code-1"


@pytest.mark.parametrize("campo,valor,motivo", [
    ("email_verified", False, "identidade_nao_verificada"),
    ("aud", "outro-app", "provedor_falhou"),
    ("iss", "https://malicioso.dev", "provedor_falhou"),
    ("exp", 0, "provedor_falhou"),
])
def test_google_recusa_token_invalido(db, monkeypatch, campo, valor, motivo):
    simular(monkeypatch, {auth.PROVEDORES["google"]["token"]: {"id_token": jwt(google_token(**{campo: valor}))}})
    _, state, nonce = iniciar("google")
    with pytest.raises(auth.ErroAuth) as e:
        auth.concluir("code", state, nonce, BASE)
    assert e.value.motivo == motivo


# ---------------- GitHub ----------------

def test_github_usa_so_emails_verificados(db, monkeypatch):
    simular(monkeypatch, {
        auth.PROVEDORES["github"]["token"]: {"access_token": "tok"},
        "https://api.github.com/user": {"login": "Ana-Dev", "name": "Ana"},
        "https://api.github.com/user/emails": [
            {"email": "ana@exemplo.com", "verified": True}, {"email": "falso@exemplo.com", "verified": False}],
    })
    _, state, nonce = iniciar("github")
    ident = auth.concluir("code", state, nonce, BASE)
    assert ident["ids"] == ["github:ana-dev", "email:ana@exemplo.com"] and ident["provedor"] == "github"


# ---------------- root, perfis e sessão ----------------

def test_root_so_pela_identidade_do_provedor(db):
    assert auth.papel(["google:root@exemplo.com", "email:root@exemplo.com"], db)["root"]
    assert auth.papel(["github:root-exemplo"], db)["root"]
    # mesmo e-mail do root vindo do GitHub, com outro login: não é root nem tem perfil
    assert auth.papel(["github:outra-pessoa", "email:root@exemplo.com"], db) is None


def test_arena_root_ausente_ou_invalido(db, monkeypatch):
    monkeypatch.delenv("ARENA_ROOT")
    assert auth.root() == set() and auth.papel(["google:root@exemplo.com"], db) is None
    monkeypatch.setenv("ARENA_ROOT", "{nao é json")
    with pytest.raises(ValueError):
        auth.root()


def test_perfil_por_email_ou_github_e_rebaixamento_imediato(db):
    root = auth.AUTOR_EMERGENCIA
    admin.executar("salvar_perfil", root, {"email": "Juiza@Exemplo.com", "nome": "Juíza", "github": "@juiza-gh",
                                           "papel": "juiz"}, db)
    assert auth.papel(["google:juiza@exemplo.com", "email:juiza@exemplo.com"], db)["papel"] == "juiz"
    assert auth.papel(["github:juiza-gh"], db)["papel"] == "juiz"
    sessao = auth.emitir_sessao({"ids": ["github:juiza-gh"], "nome": "Juíza", "provedor": "github"})
    assert auth.autor_da_sessao(sessao, db)["papel"] == "juiz"
    admin.executar("salvar_perfil", root, {"email": "juiza@exemplo.com", "nome": "Juíza", "github": "juiza-gh",
                                           "papel": "admin"}, db)
    assert auth.autor_da_sessao(sessao, db)["papel"] == "admin"
    admin.executar("remover_perfil", root, {"email": "juiza@exemplo.com"}, db)
    assert auth.autor_da_sessao(sessao, db) is None  # removida: a sessão deixa de valer na hora


def test_sessao_expira(db):
    s = auth.emitir_sessao({"ids": ["google:root@exemplo.com"], "nome": "Root", "provedor": "google"})
    assert auth.autor_da_sessao(s, db)["root"]
    assert auth.autor_da_sessao(s, db, agora=time.time() + auth.VALIDADE_SESSAO + 5) is None


# ---------------- painel ----------------

JUIZ = {"nome": "Juiz", "papel": "juiz", "root": False}


def test_juiz_nao_faz_acao_de_admin_e_nada_e_gravado(db):
    for acao in ("perfis", "auditoria", "salvar_perfil", "remover_perfil"):
        with pytest.raises(Erro) as e:
            admin.executar(acao, JUIZ, {"email": "x@exemplo.com", "nome": "X", "papel": "admin"}, db)
        assert e.value.status == 403
    assert auth.perfis(db) == {} and db.lrange(store.k_auditoria(), 0, -1) == []
    with pytest.raises(Erro):
        admin.executar("placar", {"nome": "?", "papel": None}, {}, db)


def test_validacao_e_auditoria_de_perfis(db):
    root = auth.AUTOR_EMERGENCIA
    for ruim in ({"email": "sem-arroba", "nome": "A", "papel": "juiz"},
                 {"email": "a@exemplo.com", "nome": "", "papel": "juiz"},
                 {"email": "a@exemplo.com", "nome": "A", "papel": "root"},
                 {"email": "a@exemplo.com", "nome": "A", "papel": "juiz", "github": "nome inválido"}):
        with pytest.raises(Erro):
            admin.executar("salvar_perfil", root, ruim, db)
    admin.executar("salvar_perfil", root, {"email": "a@exemplo.com", "nome": "A", "papel": "juiz", "github": "gh-a"}, db)
    with pytest.raises(Erro) as e:  # mesmo GitHub em outro perfil
        admin.executar("salvar_perfil", root, {"email": "b@exemplo.com", "nome": "B", "papel": "juiz",
                                               "github": "gh-a"}, db)
    assert e.value.status == 409
    log = admin.executar("auditoria", root, {}, db)["auditoria"]
    assert [l["acao"] for l in log] == ["criar_perfil"] and log[0]["autor"] == "token de emergência"
    lista = admin.executar("perfis", root, {}, db)
    assert lista["root"] == ["github:root-exemplo", "google:root@exemplo.com"] and len(lista["perfis"]) == 1


def test_juiz_ve_placar_real_e_submissao_com_codigo(db):
    fonte = arena_gabarito("B92")
    r = servico.submeter("equipe1", "B92", fonte, ["Ana"], db=db)
    subs = admin.executar("submissoes", JUIZ, {}, db)["submissoes"]
    assert subs[0]["id"] and "fonte" not in subs[0]
    detalhe = admin.executar("submissao", JUIZ, {"id": subs[0]["id"]}, db)
    assert detalhe["fonte"] == fonte and detalhe["pontos"] == r["pontos"]
    assert not admin.executar("placar", JUIZ, {}, db)["congelado"]
    with pytest.raises(Erro) as e:
        admin.executar("submissao", JUIZ, {"id": "nao-existe"}, db)
    assert e.value.status == 404


def arena_gabarito(cod):
    from _lib import arena
    return arena._exemplos()[cod]["gabarito"]
