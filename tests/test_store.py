"""Contrato do armazenamento: Local sempre; Supabase real só com ARENA_TESTE_SUPABASE=1.

Para rodar contra o Supabase (usa chaves com prefixo aleatório e apaga tudo no final):
  ARENA_TESTE_SUPABASE=1 SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY=... python3 -m pytest -q tests/test_store.py
"""
import os
import secrets
import sys
import threading

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "api"))

from _lib import store  # noqa: E402

SUPABASE_REAL = (os.environ.get("ARENA_TESTE_SUPABASE") == "1" and os.environ.get("SUPABASE_URL")
                 and (os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_SECRET_KEY")))


@pytest.fixture(params=["local", "supabase"])
def banco(request, tmp_path):
    if request.param == "local":
        yield store.Local(str(tmp_path / "db.json")), "t"
        return
    if not SUPABASE_REAL:
        pytest.skip("defina ARENA_TESTE_SUPABASE=1 e as variáveis do Supabase para testar o banco real")
    db = store.SupabaseRest(os.environ["SUPABASE_URL"],
                            os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ["SUPABASE_SECRET_KEY"])
    prefixo = "teste-" + secrets.token_hex(4)
    yield db, prefixo
    db.apagar(*(f"{prefixo}:{k}" for k in ("h", "l", "n", "x")))


def test_hash(banco):
    db, p = banco
    assert db.hgetall(f"{p}:h") == {}
    db.hset(f"{p}:h", "B01", 1000.5)
    db.hset(f"{p}:h", "B01", 2000)
    db.hset(f"{p}:h", "B02", "texto: com 'aspas' e \"duplas\"")
    assert db.hgetall(f"{p}:h") == {"B01": "2000", "B02": "texto: com 'aspas' e \"duplas\""}
    assert db.hsetnx(f"{p}:h", "B03", 1) is True
    assert db.hsetnx(f"{p}:h", "B03", 2) is False
    assert db.hgetall(f"{p}:h")["B03"] == "1"
    assert db.hget(f"{p}:h", "B01") == "2000"
    assert db.hget(f"{p}:h", "nada") is None
    assert db.hget(f"{p}:nada", "B01") is None


def test_hincrby(banco):
    db, p = banco
    assert db.hincrby(f"{p}:n", "B01") == 1
    assert db.hincrby(f"{p}:n", "B01") == 2
    assert db.hincrby(f"{p}:n", "B01", 5) == 7
    assert db.hgetall(f"{p}:n") == {"B01": "7"}


def test_hincrby_concorrente(banco):
    db, p = banco
    threads = [threading.Thread(target=db.hincrby, args=(f"{p}:n", "B01")) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert db.hgetall(f"{p}:n") == {"B01": "8"}


def test_lista(banco):
    db, p = banco
    assert db.lrange(f"{p}:l", 0, -1) == []
    for i in range(5):
        db.lpush(f"{p}:l", f'{{"i": {i}}}')
    assert db.lrange(f"{p}:l", 0, -1) == [f'{{"i": {i}}}' for i in (4, 3, 2, 1, 0)]
    assert db.lrange(f"{p}:l", 0, 1) == ['{"i": 4}', '{"i": 3}']
    assert db.lrange(f"{p}:l", 2, 3) == ['{"i": 2}', '{"i": 1}']


def test_apagar(banco):
    db, p = banco
    db.hset(f"{p}:h", "a", 1)
    db.lpush(f"{p}:l", "x")
    db.hset(f"{p}:x", "a", 1)
    db.apagar(f"{p}:h", f"{p}:l")
    assert db.hgetall(f"{p}:h") == {} and db.lrange(f"{p}:l", 0, -1) == []
    assert db.hgetall(f"{p}:x") == {"a": "1"}


# ---------------- SupabaseRest sem rede ----------------

def test_supabase_lrange_pagina_e_monta_pedidos(monkeypatch):
    db = store.SupabaseRest("https://exemplo.supabase.co/", "sb_secret_x")
    db.PAGINA = 2
    dados = [{"valor": str(i)} for i in range(5)]
    pedidos = []

    def falso(metodo, caminho, filtros=None, corpo=None, prefer=None):
        pedidos.append((metodo, caminho, dict(filtros or {}), corpo, prefer))
        o, n = filtros["offset"], filtros["limit"]
        return dados[o:o + n]

    monkeypatch.setattr(db, "_req", falso)
    assert db.lrange("arena:l", 0, -1) == ["0", "1", "2", "3", "4"]
    assert [(f["offset"], f["limit"]) for _, _, f, _, _ in pedidos] == [(0, 2), (2, 2), (4, 2)]
    assert pedidos[0][2]["order"] == "id.desc" and pedidos[0][2]["chave"] == "eq.arena:l"
    pedidos.clear()
    assert db.lrange("arena:l", 1, 3) == ["1", "2", "3"]
    assert [(f["offset"], f["limit"]) for _, _, f, _, _ in pedidos] == [(1, 2), (3, 1)]


def test_chaves_de_conteudo_nao_dependem_do_prefixo(monkeypatch):
    monkeypatch.delenv("ARENA_CONTEUDO", raising=False)
    monkeypatch.setenv("ARENA_PREFIXO", "ensaio1")
    a = (store.k_desafios(), store.k_segredos(), store.k_validacao())
    monkeypatch.setenv("ARENA_PREFIXO", "evento")
    assert (store.k_desafios(), store.k_segredos(), store.k_validacao()) == a
    assert a == ("conteudo:desafios", "conteudo:segredos", "conteudo:validacao")
    assert store.k_log().startswith("evento:")
    monkeypatch.setenv("ARENA_CONTEUDO", "univille")
    assert store.k_desafios() == "univille:desafios"


def test_supabase_escolhido_pelas_variaveis(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://exemplo.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "sb_secret_x")
    monkeypatch.setenv("KV_REST_API_URL", "https://redis")
    monkeypatch.setenv("KV_REST_API_TOKEN", "t")
    assert isinstance(store.abrir(), store.SupabaseRest)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY")
    assert isinstance(store.abrir(), store.RedisRest)


def test_supabase_cabecalhos(monkeypatch):
    capturado = {}

    class Resp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return b"[]"

    def urlopen(req, timeout):
        capturado["url"], capturado["cab"] = req.full_url, dict(req.header_items())
        return Resp()

    monkeypatch.setattr(store.urllib.request, "urlopen", urlopen)
    store.SupabaseRest("https://x.supabase.co", "sb_secret_abc").hgetall("arena:tentativas:e1")
    assert capturado["url"] == ("https://x.supabase.co/rest/v1/arena_hash"
                                "?select=campo,valor&chave=eq.arena:tentativas:e1")
    assert capturado["cab"]["Apikey"] == "sb_secret_abc" and "Authorization" not in capturado["cab"]
    store.SupabaseRest("https://x.supabase.co", "eyJlegado").hgetall("k")
    assert capturado["cab"]["Authorization"] == "Bearer eyJlegado"
