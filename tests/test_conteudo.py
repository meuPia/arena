import json
import os
import sys

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "api"))

from _lib import arena, conteudo, store  # noqa: E402

PASTA_EXEMPLOS = os.path.join(RAIZ, "arena", "exemplos")


@pytest.fixture
def db(tmp_path, monkeypatch):
    for v in ("SUPABASE_URL", "KV_REST_API_URL", "UPSTASH_REDIS_REST_URL"):
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setenv("ARENA_ARQUIVO_LOCAL", str(tmp_path / "db.json"))
    arena.limpar_cache()
    yield store.abrir()
    arena.limpar_cache()


def test_importar_exportar_e_reimportar_sem_mudanca(db, tmp_path):
    plano = conteudo.planejar(db, conteudo.ler(PASTA_EXEMPLOS))
    assert {i["acao"] for i in plano} == {"criar"} and all(i["validacao"]["ok"] for i in plano)
    assert db.hgetall(store.k_desafios()) == {}  # planejar não grava
    assert sorted(conteudo.aplicar(db, plano)) == sorted(arena._exemplos())

    dados = conteudo.exportar(db)
    assert dados["formato"] == conteudo.FORMATO and len(dados["desafios"]) == 7
    assert all(d["gabarito"] and d["testesExtras"] for d in dados["desafios"])
    backup = tmp_path / "backup.json"
    backup.write_text(json.dumps(dados), encoding="utf-8")

    plano = conteudo.planejar(db, conteudo.ler(str(backup)))
    assert {i["acao"] for i in plano} == {"igual"}
    assert conteudo.aplicar(db, plano) == []


def test_formato_antigo_com_gabarito_em_pasta_irma(db, tmp_path):
    (tmp_path / "desafios").mkdir()
    (tmp_path / "gabaritos").mkdir()
    d = dict(arena._exemplos()["B91"])
    gab = d.pop("gabarito")
    (tmp_path / "desafios" / "B91.json").write_text(json.dumps(d), encoding="utf-8")
    (tmp_path / "gabaritos" / "B91.por").write_text(gab, encoding="utf-8")
    lidos = conteudo.ler(str(tmp_path / "desafios"))
    assert lidos[0]["gabarito"] == gab


def test_desafio_invalido_nao_e_gravado(db, tmp_path):
    ruim = dict(arena._exemplos()["B91"], codigo="B01", gabarito='algoritmo "x"\nfuncao dobro(n)\n    retorne n\nfim_funcao\ninicio\nfim_algoritmo')
    bom = dict(arena._exemplos()["B92"])
    arq = tmp_path / "import.json"
    arq.write_text(json.dumps({"formato": conteudo.FORMATO, "versao": 1, "desafios": [ruim, bom]}), encoding="utf-8")
    plano = conteudo.planejar(db, conteudo.ler(str(arq)))
    assert [i["validacao"]["ok"] for i in plano] == [False, True]
    assert conteudo.aplicar(db, plano) == ["B92"]
    assert list(db.hgetall(store.k_desafios())) == ["B92"]


def test_arquivo_que_nao_e_exportacao_e_recusado(tmp_path):
    arq = tmp_path / "x.json"
    arq.write_text('{"qualquer": 1}', encoding="utf-8")
    with pytest.raises(ValueError):
        conteudo.ler(str(arq))
