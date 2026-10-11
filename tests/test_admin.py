import json
import os
import sys

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "api"))

from _lib import admin, arena, auth, servico, store  # noqa: E402
from _lib.web import Erro  # noqa: E402

ROOT = auth.AUTOR_EMERGENCIA
JUIZ = {"nome": "Juiz", "papel": "juiz", "root": False, "provedor": "google"}


@pytest.fixture
def db(tmp_path, monkeypatch):
    for v in ("SUPABASE_URL", "KV_REST_API_URL", "UPSTASH_REDIS_REST_URL", "ARENA_EQUIPES", "ARENA_ROOT"):
        monkeypatch.delenv(v, raising=False)  # testes nunca gravam no banco real
    monkeypatch.setenv("ARENA_ARQUIVO_LOCAL", str(tmp_path / "db.json"))
    monkeypatch.setenv("ARENA_MODO", "ensaio")
    arena.limpar_cache()
    yield store.abrir()
    arena.limpar_cache()


def ex(acao, dados=None, db=None, autor=ROOT):
    return admin.executar(acao, autor, dados or {}, db)


def acoes(db):
    return [a["acao"] for a in ex("auditoria", db=db)["auditoria"]]


def gabarito(cod):
    return arena._exemplos()[cod]["gabarito"]


# ---------------- equipes ----------------

def test_listagem_com_banco_vazio_mostra_a_fonte_antiga(db):
    r = ex("equipes", db=db)
    assert r["origem"] == "exemplo" and [e["nome"] for e in r["equipes"]] == ["Equipe 1", "Equipe 2"]


def test_criar_equipe_entra_na_hora_e_nome_unico(db):
    ex("criar_equipe", {"nome": "  Orion  "}, db)
    e = next(e for e in ex("equipes", db=db)["equipes"] if e["nome"] == "Orion")
    assert e["codigo"].startswith("ORION-") and e["pontos"] == 0 and e["submissoes"] == 0
    assert servico.login(e["codigo"], db=db)["equipe"]["nome"] == "Orion"
    for nome in ("orion", "", "x" * 41):
        with pytest.raises(Erro):
            ex("criar_equipe", {"nome": nome}, db)
    assert acoes(db) == ["criar_equipe"]
    assert e["codigo"] not in json.dumps(ex("auditoria", db=db))  # o código nunca vai para a auditoria


def test_criar_exige_importar_quando_ha_equipes_no_arquivo(db, monkeypatch):
    monkeypatch.setenv("ARENA_EQUIPES", json.dumps([{"id": "a", "nome": "A", "codigo": "A-1"}]))
    with pytest.raises(Erro) as e:
        ex("criar_equipe", {"nome": "Nova"}, db)
    assert e.value.status == 409


def test_importar_mantem_codigos_e_vira_participantes(db, monkeypatch):
    tok = servico.login("TROQUE-ESTE-CODIGO-1", db=db)["token"]
    r = ex("importar_equipes", db=db)
    assert r["importadas"] == 2
    eqs = arena.equipes(db)
    assert eqs["equipe1"]["codigo"] == "TROQUE-ESTE-CODIGO-1" and eqs["equipe1"]["versao"] == 0
    assert "Ana (2º)" in eqs["equipe1"]["integrantes"] and len(eqs["equipe1"]["integrantes"]) == 5
    from handlers import chamar
    assert chamar("missoes", cabecalhos={"Authorization": f"Bearer {tok}"})[0] == 200  # sem novo login
    with pytest.raises(Erro) as e:
        ex("importar_equipes", db=db)
    assert e.value.status == 409
    assert ex("equipes", db=db)["origem"] == "banco"


def test_editar_excluir_e_regenerar(db):
    ex("importar_equipes", db=db)
    ex("editar_equipe", {"id": "equipe2", "nome": "Vega"}, db)
    with pytest.raises(Erro):
        ex("editar_equipe", {"id": "equipe2", "nome": "equipe 1"}, db)  # nome de outra equipe
    assert arena.equipes(db)["equipe2"]["nome"] == "Vega"

    servico.submeter("equipe1", "B92", gabarito("B92"), ["Ana"], db=db)
    with pytest.raises(Erro) as e:
        ex("excluir_equipe", {"id": "equipe1"}, db)
    assert e.value.status == 409
    ex("excluir_equipe", {"id": "equipe2"}, db)
    assert set(arena.equipes(db)) == {"equipe1"}
    assert all(p["equipe"] != "equipe2" for p in arena.participantes(db).values())

    novo = ex("regenerar_codigo", {"id": "equipe1"}, db)["codigo"]
    assert novo != "TROQUE-ESTE-CODIGO-1" and arena.equipes(db)["equipe1"]["versao"] == 1
    with pytest.raises(Erro):
        servico.login("TROQUE-ESTE-CODIGO-1", db=db)
    assert servico.login(novo, db=db)["equipe"]["id"] == "equipe1"
    lista = ex("equipes", db=db)["equipes"]
    assert lista[0]["codigo"] == novo and lista[0]["pontos"] == 10 and lista[0]["submissoes"] == 1
    assert lista[0]["ultimaSubmissao"]
    assert acoes(db)[:3] == ["codigo_regenerado", "excluir_equipe", "editar_equipe"]


def test_juiz_nao_gerencia_equipes(db):
    ex("importar_equipes", db=db)
    for acao in ("equipes", "criar_equipe", "editar_equipe", "excluir_equipe", "regenerar_codigo", "importar_equipes"):
        with pytest.raises(Erro) as e:
            ex(acao, {"id": "equipe1", "nome": "X"}, db, autor=JUIZ)
        assert e.value.status == 403
    assert arena.equipes(db)["equipe1"]["codigo"] == "TROQUE-ESTE-CODIGO-1"


# ---------------- participantes ----------------

def test_participante_aparece_na_missao_e_pode_trocar_de_equipe(db):
    ex("importar_equipes", db=db)
    pid = ex("salvar_participante", {"equipe": "equipe1", "nome": "Zoe", "semestre": "4º"}, db)["id"]
    assert "Zoe (4º)" in servico.missao("equipe1", "B91", db=db)["integrantes"]
    servico.submeter("equipe1", "B92", gabarito("B92"), ["Zoe (4º)"], db=db)
    ex("salvar_participante", {"id": pid, "equipe": "equipe2", "nome": "Zoe", "semestre": "4º"}, db)
    assert "Zoe (4º)" not in servico.missao("equipe1", "B91", db=db)["integrantes"]
    assert "Zoe (4º)" in servico.missao("equipe2", "B91", db=db)["integrantes"]
    assert servico.submissoes(db=db)[0]["participantes"] == ["Zoe (4º)"]  # submissão feita não muda
    ex("remover_participante", {"id": pid}, db)
    assert "Zoe (4º)" not in servico.missao("equipe2", "B91", db=db)["integrantes"]
    assert acoes(db)[:3] == ["remover_participante", "editar_participante", "criar_participante"]


def test_validacao_de_participante(db):
    ex("importar_equipes", db=db)
    for ruim in ({"equipe": "equipe1", "nome": "", "semestre": "2º"},
                 {"equipe": "equipe1", "nome": "Ana", "semestre": ""},
                 {"equipe": "equipe1", "nome": "Ana", "semestre": "2º", "email": "sem-arroba"},
                 {"equipe": "nao-existe", "nome": "Ana", "semestre": "2º"},
                 {"id": "nao-existe", "equipe": "equipe1", "nome": "Ana", "semestre": "2º"}):
        with pytest.raises(Erro):
            ex("salvar_participante", ruim, db)
    lista = ex("participantes", db=db)["participantes"]
    assert len(lista) == 10 and lista[0]["nomeEquipe"] == "Equipe 1"


# ---------------- ajuste de pontos ----------------

def parcial_b92():
    return gabarito("B92").replace("funcao maior(lista)\n", "funcao maior(lista)\n    se tamanho(lista) > 50 então\n"
                                   "        retorne lista[0]\n    fim_se\n", 1)


def linha(placar, eid="equipe1"):
    return next(l for l in placar["linhas"] if l["id"] == eid)


def test_aplicar_ajustes_e_pura():
    todos = {"B01": {"pontos": 10}}
    aceitas = [{"id": "a", "codigo": "B01", "pontos": 10, "completo": True, "t": 1, "caracteres": 50}]
    out = arena.aplicar_ajustes(aceitas, {"a": {"pontos": 0}}, todos)
    assert out[0]["pontos"] == 0 and out[0]["pontosJuiz"] == 10 and not out[0]["completo"]
    assert aceitas[0]["pontos"] == 10  # não altera a entrada
    assert arena.aplicar_ajustes(aceitas, {"a": {"pontos": 10}}, todos)[0]["completo"]


def test_ajuste_muda_a_melhor_vale_no_freeze_e_pode_ser_desfeito(db, monkeypatch):
    monkeypatch.delenv("ARENA_MODO")
    monkeypatch.delenv("ARENA_REVELAR", raising=False)
    jan = arena.janela()
    antes = jan["freeze"] - 600
    parcial = servico.submeter("equipe1", "B92", parcial_b92(), ["Ana"], db=db, agora=antes)
    completa = servico.submeter("equipe1", "B92", gabarito("B92"), ["Ana"], db=db, agora=antes + 400)
    assert 0 < parcial["pontos"] < 10 and completa["pontos"] == 10 and completa["completo"]
    sid = servico.submissoes(db=db)[0]["id"]  # a completa (mais recente)

    ex("ajustar", {"id": sid, "pontos": 0, "motivo": "integrante sorteado não explicou a solução"}, db, autor=JUIZ)
    congelado = servico.placar(db=db, agora=jan["freeze"] + 60)  # ajuste feito durante o freeze
    assert congelado["congelado"] and linha(congelado)["pontos"] == parcial["pontos"]
    assert linha(congelado)["completos"] == 0
    painel = servico.missoes("equipe1", db=db)
    b92 = next(i for n in painel["niveis"] for i in n["itens"] if i["codigo"] == "B92")
    assert b92["melhor"]["pontos"] == parcial["pontos"] and not b92["completo"]
    assert "motivo" not in json.dumps(painel) and "explicou" not in json.dumps(congelado)  # motivo não vaza

    log = ex("submissoes", db=db, autor=JUIZ)["submissoes"][0]
    assert (log["pontos"], log["pontosEfetivos"]) == (10, 0) and log["ajuste"]["autor"] == "Juiz"
    assert ex("submissao", {"id": sid}, db, autor=JUIZ)["ajuste"]["motivo"].startswith("integrante")

    ex("desfazer_ajuste", {"id": sid}, db, autor=JUIZ)
    vivo = servico.placar(admin=True, db=db, agora=jan["freeze"] + 60)
    assert linha(vivo)["pontos"] == 10 and linha(vivo)["completos"] == 1
    assert acoes(db)[:2] == ["desfazer_ajuste", "ajustar"]


def test_ajuste_validacao(db):
    servico.submeter("equipe1", "B92", gabarito("B92"), ["Ana"], db=db)
    servico.submeter("equipe1", "B92", "algoritmo \"x\"\ninicio\nfim_algoritmo", ["Ana"], db=db, agora=10**10)
    reprovada, aceita = (s["id"] for s in servico.submissoes(db=db))
    for dados in ({"id": aceita, "pontos": 12, "motivo": "acima do máximo"},
                  {"id": aceita, "pontos": -1, "motivo": "negativo demais"},
                  {"id": aceita, "pontos": 2.5, "motivo": "não inteiro"},
                  {"id": aceita, "pontos": 5, "motivo": "   "},
                  {"id": reprovada, "pontos": 0, "motivo": "submissão não aceita"},
                  {"id": "nao-existe", "pontos": 0, "motivo": "inexistente"}):
        with pytest.raises(Erro):
            ex("ajustar", dados, db, autor=JUIZ)
    assert servico.ajustes(db) == {}
    with pytest.raises(Erro) as e:
        ex("desfazer_ajuste", {"id": aceita}, db, autor=JUIZ)
    assert e.value.status == 404


def test_id_da_submissao_igual_no_log_e_em_aceitas(db):
    servico.submeter("equipe1", "B92", gabarito("B92"), ["Ana"], db=db)
    log = servico.submissoes(db=db)[0]
    reg = json.loads(db.lrange(store.k_aceitas("equipe1"), 0, 0)[0])
    assert log["id"] and log["id"] == reg["id"] and log["ajuste"] is None and log["pontosEfetivos"] == 10


# ---------------- placar público x placar real (HTTP) ----------------

def test_placar_publico_segue_o_freeze_mesmo_com_banca_logada(db, monkeypatch):
    from handlers import chamar
    monkeypatch.delenv("ARENA_MODO")
    monkeypatch.delenv("ARENA_REVELAR", raising=False)
    monkeypatch.setenv("ADMIN_TOKEN", "tok-emergencia")
    monkeypatch.setenv("ARENA_ROOT", json.dumps({"google": "root@exemplo.com"}))
    jan = arena.janela()
    servico.submeter("equipe1", "B92", parcial_b92(), ["Ana"], db=db, agora=jan["freeze"] - 600)
    servico.submeter("equipe1", "B92", gabarito("B92"), ["Ana"], db=db, agora=jan["freeze"] + 30)
    monkeypatch.setattr(arena.time, "time", lambda: jan["freeze"] + 60)
    sessao = auth.emitir_sessao({"ids": ["google:root@exemplo.com"], "nome": "Root", "provedor": "google"})
    cab = {"Cookie": f"{auth.COOKIE_SESSAO}={sessao}", "X-Admin-Token": "tok-emergencia"}

    st, _, publico = chamar("placar", caminho="/api/placar?admin=tok-emergencia", cabecalhos=cab)
    assert st == 200 and publico["congelado"] and "submissoes" not in publico
    assert linha(publico)["pontos"] < 10

    for c in ({"Cookie": cab["Cookie"]}, {"X-Admin-Token": "tok-emergencia"}):
        st, _, real = chamar("admin", caminho="/api/admin?acao=placar", cabecalhos=c)
        assert st == 200 and not real["congelado"] and linha(real)["pontos"] == 10
    assert chamar("admin", caminho="/api/admin?acao=placar")[0] == 401
