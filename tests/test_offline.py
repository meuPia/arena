"""Modo offline (ARENA_MODO=offline): sem login nem submissão; a banca pontua os .por (scripts/pontuar_equipe.py)."""
import os
import sys

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "api"))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))

from _lib import arena, servico, store  # noqa: E402
from _lib.web import Erro  # noqa: E402
import pontuar_equipe  # noqa: E402

EXEMPLOS = arena._exemplos()


@pytest.fixture
def db(tmp_path, monkeypatch):
    monkeypatch.setenv("ARENA_MODO", "offline")
    for nome in ("KV_REST_API_URL", "UPSTASH_REDIS_REST_URL", "SUPABASE_URL"):
        monkeypatch.delenv(nome, raising=False)
    monkeypatch.setenv("ARENA_SQLITE", str(tmp_path / "db.sqlite3"))
    arena.limpar_cache()
    yield store.abrir()
    arena.limpar_cache()


def test_missoes_sem_login_e_todos_os_niveis_abertos(db):
    p = servico.missoes(None, db)
    assert p["offline"] and p["janela"]["offline"] and p["janela"]["situacao"] == "aberta"
    assert all(n["liberado"] for n in p["niveis"])
    m = servico.missao(None, "G91", db)  # Gold aberto sem ter resolvido nada
    assert m["offline"] and "gabarito" not in m and "testesExtras" not in m


def test_sem_modo_offline_continua_exigindo_equipe(db, monkeypatch):
    monkeypatch.setenv("ARENA_MODO", "ensaio")
    with pytest.raises(Erro) as e:
        servico.missoes(None, db)
    assert e.value.status == 401
    assert not servico.missoes("equipe1", db)["niveis"][-1]["liberado"]


def test_submeter_fechado_no_offline(db):
    with pytest.raises(Erro) as e:
        servico.submeter("equipe1", "B91", EXEMPLOS["B91"]["gabarito"], ["Ana"], db)
    assert e.value.status == 403


def test_pontuar_registra_a_melhor_com_o_horario_do_arquivo(db):
    fonte = "// arena: B91\n" + EXEMPLOS["B91"]["gabarito"]  # cabeçalho que a IDE grava
    r = servico.pontuar("equipe1", "B91", fonte, db=db, agora=1000.0)
    assert r["status"] == "aceito" and r["completo"] and r["pontos"] == r["pontosModulo"]
    r2 = servico.pontuar("equipe1", "B91", "algoritmo \"x\"\ninicio\nfimalgoritmo\n", db=db, agora=2000.0)
    assert r2["status"] != "aceito" and r2["melhor"]["completo"]  # a pior entrega não derruba a melhor
    linha = next(l for l in servico.placar(admin=True, db=db)["linhas"] if l["id"] == "equipe1")
    assert linha["pontos"] == r["pontosModulo"] and linha["ultimaMelhoria"] == 1000.0
    assert db.lrange(store.k_log(), 0, 0)[0].count("entrega offline") == 1


def test_pontuar_sem_testes_extras_recusa(db):
    db.hset(store.k_desafios(), "B91", '{"codigo": "B91"}')  # banco --publico: só a parte pública
    arena.limpar_cache()
    with pytest.raises(Erro):
        servico.pontuar("equipe1", "B91", "x", db=db)


def test_coletar_entregas(tmp_path):
    def escrever(nome, texto, mtime):
        p = tmp_path / nome
        p.write_text(texto, encoding="utf-8")
        os.utime(p, (mtime, mtime))
        return str(p)

    escrever("B91.por", "velho", 100)
    novo = escrever("B91 (1).por", "novo", 200)
    renomeado = escrever("minha solucao.por", "// arena: s91\ncodigo", 100)
    escrever("leiame.por", "sem cabeçalho", 100)
    escrever("notas.txt", "x", 100)
    escolhidos, avisos = pontuar_equipe.coletar([str(tmp_path)])
    assert escolhidos == {"B91": novo, "S91": renomeado}
    assert any("leiame.por" in a for a in avisos) and any("B91" in a for a in avisos)


def test_ler_fonte_em_ansi(tmp_path):
    p = tmp_path / "B91.por"
    p.write_bytes("escreva(\"ação\")".encode("cp1252"))
    assert pontuar_equipe.ler_fonte(str(p)) == "escreva(\"ação\")"


def test_achar_equipe_sem_acento_nem_caixa(db):
    eid, e = pontuar_equipe.achar_equipe(arena.equipes(db)["equipe1"]["nome"].upper(), db)
    assert eid == "equipe1"
    assert pontuar_equipe.achar_equipe("nao existe", db) == (None, None)
