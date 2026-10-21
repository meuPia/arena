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
    monkeypatch.setenv("ARENA_SQLITE", str(tmp_path / "db.sqlite3"))
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


# ---------------- alunos sem equipe, importação e montagem ----------------

def turma(seis, quatro, dois):
    return "\n".join(["Nome;Fase"] + [f"Aluno {s} {i};{s}" for s, n in ((6, seis), (4, quatro), (2, dois))
                                       for i in range(n)])


def integrantes(db):
    return {e["nome"]: e["integrantes"] for e in arena.equipes(db).values()}


def test_participante_sem_equipe_nao_aparece_em_nenhuma_equipe(db):
    ex("importar_equipes", db=db)
    ex("salvar_participante", {"equipe": "", "nome": "Bruno", "semestre": "6º"}, db)
    r = ex("participantes", db=db)
    assert r["semEquipe"] == 1 and r["participantes"][0]["nome"] == "Bruno" and r["participantes"][0]["nomeEquipe"] == ""
    assert all("Bruno (6º)" not in i for i in integrantes(db).values())
    assert "Bruno (6º)" not in servico.missao("equipe1", "B91", db=db)["integrantes"]
    assert "sem equipe" in ex("auditoria", db=db)["auditoria"][0]["resumo"]


def test_excluir_equipe_devolve_os_participantes(db):
    ex("importar_equipes", db=db)
    antes = {p["id"] for p in ex("participantes", db=db)["participantes"] if p["equipe"] == "equipe2"}
    ex("excluir_equipe", {"id": "equipe2"}, db)
    depois = ex("participantes", db=db)
    assert {p["id"] for p in depois["participantes"] if not p["nomeEquipe"]} == antes and depois["semEquipe"] == 5


def test_importar_alunos_com_previa_e_confirmacao(db):
    ex("importar_equipes", db=db)
    existente = ex("participantes", db=db)["participantes"][0]["nome"]
    texto = turma(2, 2, 2) + f"\nRuim;semestre 9x\n{existente.upper()};2"
    previa = ex("importar_participantes", {"texto": texto}, db)
    assert len(previa["alunos"]) == 6 and [i["motivo"] for i in previa["ignoradas"]] == [
        "semestre não reconhecido", "já cadastrado"]
    assert ex("participantes", db=db)["semEquipe"] == 0 and acoes(db) == ["importar_equipes"]  # prévia não grava
    r = ex("importar_participantes", {"texto": texto, "confirmar": True}, db)
    assert r["criados"] == 6 and ex("participantes", db=db)["semEquipe"] == 6
    assert acoes(db)[0] == "importar_participantes"
    assert ex("auditoria", db=db)["auditoria"][0]["resumo"].startswith("6 aluno(s)")
    again = ex("importar_participantes", {"texto": texto}, db)  # reimportar: todos já cadastrados
    assert again["alunos"] == [] and len(again["ignoradas"]) == 8
    with pytest.raises(Erro) as e:
        ex("importar_participantes", {"texto": "  "}, db)
    assert e.value.status == 400


def test_importar_e_montar_sao_so_do_admin_e_por_post(db):
    for acao in ("importar_participantes", "montar_equipes"):
        with pytest.raises(Erro) as e:
            ex(acao, {"texto": "Ana,2", "tamanho": 5}, db, autor=JUIZ)
        assert e.value.status == 403
        with pytest.raises(Erro) as e:
            admin.executar(acao, ROOT, {"texto": "Ana,2", "tamanho": 5}, db, metodo="GET")
        assert e.value.status == 405
    assert ex("participantes", db=db)["participantes"] == []


def test_montar_equipes_niveladas_e_entrar_com_o_codigo(db):
    ex("importar_participantes", {"texto": turma(8, 14, 18), "confirmar": True}, db)
    previa = ex("montar_equipes", {"tamanho": 5}, db)
    assert [len(e["integrantes"]) for e in previa["equipes"]] == [5] * 8
    assert all(e["porSemestre"]["6º"] == 1 for e in previa["equipes"])
    assert [e["nome"] for e in previa["equipes"]][:3] == ["Orion", "Vega", "Lyra"]
    assert ex("participantes", db=db)["semEquipe"] == 40  # prévia não grava
    outra = ex("montar_equipes", {"tamanho": 5}, db)
    assert outra["semente"] != previa["semente"]
    ex("montar_equipes", {"tamanho": 5, "semente": previa["semente"], "assinatura": previa["assinatura"],
                          "confirmar": True}, db)
    assert integrantes(db) == {e["nome"]: sorted(e["integrantes"], key=str.lower) for e in previa["equipes"]}
    orion = next(e for e in ex("equipes", db=db)["equipes"] if e["nome"] == "Orion")
    assert orion["codigo"].startswith("ORION-") and servico.login(orion["codigo"], db=db)["equipe"]["nome"] == "Orion"
    assert ex("participantes", db=db)["semEquipe"] == 0
    aud = ex("auditoria", db=db)["auditoria"][0]
    assert aud["acao"] == "montar_equipes" and aud["resumo"] == "8 equipe(s), 40 aluno(s), tamanho 5"
    assert not any(e["codigo"] in json.dumps(ex("auditoria", db=db)) for e in ex("equipes", db=db)["equipes"])


def test_montar_nao_mexe_nas_equipes_existentes(db):
    ex("criar_equipe", {"nome": "Orion"}, db)
    ex("criar_equipe", {"nome": "vega"}, db)
    eid = next(e["id"] for e in ex("equipes", db=db)["equipes"] if e["nome"] == "Orion")
    ex("salvar_participante", {"equipe": eid, "nome": "Zoe", "semestre": "4º"}, db)
    antes = {e["id"]: e["codigo"] for e in ex("equipes", db=db)["equipes"]}
    ex("importar_participantes", {"texto": turma(2, 3, 5), "confirmar": True}, db)
    p = ex("montar_equipes", {"tamanho": 5}, db)
    ex("montar_equipes", {**p, "confirmar": True}, db)
    depois = {e["id"]: e for e in ex("equipes", db=db)["equipes"]}
    assert all(depois[i]["codigo"] == c for i, c in antes.items())
    assert depois[eid]["integrantes"] == ["Zoe (4º)"]
    assert sorted(e["nome"] for i, e in depois.items() if i not in antes) == ["Lyra", "Nova"]


def test_previa_desatualizada_e_validacoes_da_montagem(db):
    with pytest.raises(Erro) as e:
        ex("montar_equipes", {"tamanho": 5}, db)
    assert e.value.status == 409  # sem alunos sem equipe
    ex("importar_participantes", {"texto": turma(1, 1, 3), "confirmar": True}, db)
    for t in (1, 11, "x", None):
        with pytest.raises(Erro) as e:
            ex("montar_equipes", {"tamanho": t}, db)
        assert e.value.status == 400
    p = ex("montar_equipes", {"tamanho": 5}, db)
    assert len(p["equipes"]) == 1
    ex("importar_participantes", {"texto": "Novata;2", "confirmar": True}, db)
    with pytest.raises(Erro) as e:
        ex("montar_equipes", {**p, "confirmar": True}, db)
    assert e.value.status == 409 and "nova prévia" in str(e.value)
    assert arena.equipes_do_banco(db) == {} and ex("participantes", db=db)["semEquipe"] == 6  # nada gravado


def test_montar_exige_importar_quando_ha_equipes_no_arquivo(db, monkeypatch):
    monkeypatch.setenv("ARENA_EQUIPES", json.dumps([{"id": "a", "nome": "A", "codigo": "A-1"}]))
    ex("importar_participantes", {"texto": "Ana;2", "confirmar": True}, db)
    with pytest.raises(Erro) as e:
        ex("montar_equipes", {"tamanho": 2}, db)
    assert e.value.status == 409


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


# ---------------- GET só lê (CSRF) ----------------

def test_get_aceita_so_acoes_de_leitura(db):
    escrita = set(admin.PERMISSOES) - admin.LEITURA
    assert admin.LEITURA <= set(admin.PERMISSOES)
    assert {"salvar_evento", "salvar_perfil", "excluir_equipe", "ajustar", "exportar_desafios"} <= escrita
    for acao in escrita:
        with pytest.raises(Erro) as e:
            admin.executar(acao, ROOT, {}, db, metodo="GET")
        assert e.value.status == 405, acao
    assert ex("auditoria", db=db)["auditoria"] == []


def test_get_com_acao_de_escrita_e_recusado_sem_gravar(db, monkeypatch):
    from handlers import chamar
    monkeypatch.setenv("ADMIN_TOKEN", "tok-emergencia")
    cab = {"X-Admin-Token": "tok-emergencia"}
    inicio = arena.config(db)["inicio"]
    for caminho in ("/api/admin?acao=salvar_evento&inicio=2030-01-01T10:00",
                    "/api/admin?acao=salvar_perfil&email=x@exemplo.com&nome=X&papel=admin",
                    "/api/admin?acao=criar_equipe&nome=Intrusa"):
        st, _, r = chamar("admin", caminho=caminho, cabecalhos=cab)
        assert st == 405 and "POST" in r["erro"], caminho
    assert arena.config(db)["inicio"] == inicio
    assert "x@exemplo.com" not in auth.perfis(db)
    assert all(e["nome"] != "Intrusa" for e in ex("equipes", db=db)["equipes"])
    assert ex("auditoria", db=db)["auditoria"] == []
    st, _, r = chamar("admin", caminho="/api/admin?acao=evento", cabecalhos=cab)
    assert st == 200 and r["inicio"] == inicio
    st, _, r = chamar("admin", metodo="POST", cabecalhos=cab, corpo={"acao": "salvar_evento", "inicio": "2030-01-01T10:00"})
    assert st == 200 and r["inicio"].startswith("2030-01-01T10:00")
    assert acoes(db) == ["horário do evento"]


# ---------------- produção nunca usa /tmp nem as equipes de exemplo ----------------

def test_producao_sem_banco_falha_alto(monkeypatch):
    for v in ("SUPABASE_URL", "KV_REST_API_URL", "UPSTASH_REDIS_REST_URL"):
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setenv("VERCEL_ENV", "production")
    with pytest.raises(RuntimeError, match="SUPABASE_URL"):
        store.abrir()


def test_producao_nao_usa_equipes_de_exemplo(db, monkeypatch):
    monkeypatch.setenv("VERCEL_ENV", "production")
    assert arena.equipes_arquivo() == ([], "nenhuma")
    with pytest.raises(Erro):
        servico.login("TROQUE-ESTE-CODIGO-1", db=db)
    assert ex("equipes", db=db) == {"origem": "nenhuma", "equipes": []}
    with pytest.raises(Erro) as e:
        ex("importar_equipes", db=db)
    assert e.value.status == 409
    ex("criar_equipe", {"nome": "Orion"}, db)  # sem fonte antiga: criar direto no painel
    assert [e["nome"] for e in arena.equipes(db).values()] == ["Orion"]


# ---------------- desafios (painel) ----------------

def exemplo(cod="B91", **kw):
    d = dict(arena._exemplos()[cod])
    d.update(kw)
    return d


def test_juiz_nao_ve_nem_edita_desafios(db):
    for acao in ("desafios", "desafio", "salvar_desafio", "validar_desafio", "validar_todos",
                 "exportar_desafios", "importar_desafios"):
        with pytest.raises(Erro) as e:
            ex(acao, {"codigo": "B91", "desafio": exemplo()}, db, autor=JUIZ)
        assert e.value.status == 403
    assert db.hgetall(store.k_desafios()) == {}


def test_criar_validar_e_aparecer_para_as_equipes(db):
    novo = exemplo(codigo="B94", id="arena_b94", titulo="Dobro, de novo")
    assert ex("validar_desafio", {"desafio": novo}, db)["validacao"]["ok"]  # formulário: não grava
    assert db.hgetall(store.k_desafios()) == {}
    ex("salvar_desafio", {"desafio": novo, "novo": True}, db)
    assert "B94" in arena.desafios(db)  # cache limpo: as equipes veem na hora neste processo
    assert servico.missao("equipe1", "B94", db=db)["titulo"] == "Dobro, de novo"
    assert "testesExtras" not in servico.missao("equipe1", "B94", db=db)
    with pytest.raises(Erro) as e:
        ex("salvar_desafio", {"desafio": novo, "novo": True}, db)  # código já existe
    assert e.value.status == 409
    r = ex("validar_desafio", {"codigo": "B94"}, db)["validacao"]
    assert r["ok"] and r["gabarito"].startswith("aceito 3/3 15/15")
    lista = ex("desafios", db=db)["desafios"]
    assert lista == [{"codigo": "B94", "nivel": "Bronze", "pontos": 10, "titulo": "Dobro, de novo",
                      "modulo": novo["modulo"], "extras": 15, "validacao": lista[0]["validacao"]}]
    assert lista[0]["validacao"]["ok"]
    d = ex("desafio", {"codigo": "b94"}, db)["desafio"]
    assert d["gabarito"] == novo["gabarito"] and d["testesExtras"] == novo["testesExtras"]


@pytest.mark.parametrize("campo,valor", [
    ("codigo", "b-4"), ("nivel", "Platina"), ("pontos", 0), ("pontos", "dez"), ("titulo", ""),
    ("testesExtras", 'esperar_igual(dobro(1), 2, "a")\nescreva(1)'),
    ("testesExtras", 'esperar_igual(dobro(1), 2, "a\\b")'),
    ("testesPublicos", 'esperar_igual(dobro(1), 2, "a"b")'),
])
def test_salvar_exige_formato(db, campo, valor):
    with pytest.raises(Erro) as e:
        ex("salvar_desafio", {"desafio": exemplo(**{"codigo": "B94", campo: valor}), "novo": True}, db)
    assert e.value.status == 400
    assert db.hgetall(store.k_desafios()) == {}


def test_edicao_auditada_sem_conteudo_e_confirmacao_com_submissoes(db):
    ex("importar_desafios", {"arquivo": conteudo_export(), "confirmar": True}, db)
    novos = exemplo("B92")["testesExtras"] + "\nesperar_igual(maior([7, 3]), 7, \"extra novo\")"
    ex("salvar_desafio", {"desafio": exemplo("B92", testesExtras=novos)}, db)
    a = ex("auditoria", db=db)["auditoria"][0]
    assert (a["acao"], a["alvo"], a["resumo"]) == ("editar_desafio", "B92", "(testesExtras)")
    assert "extra novo" not in json.dumps(ex("auditoria", db=db))

    servico.submeter("equipe1", "B92", gabarito("B92"), ["Ana"], db=db)
    with pytest.raises(Erro) as e:
        ex("salvar_desafio", {"desafio": exemplo("B92", titulo="Outro título")}, db)
    assert e.value.status == 409 and "rejulga" in e.value.mensagem
    ex("salvar_desafio", {"desafio": exemplo("B92", titulo="Outro título"), "confirmarSubmissoes": True}, db)
    assert arena.desafios(db)["B92"]["titulo"] == "Outro título"


def conteudo_export():
    from _lib import conteudo
    return {"formato": conteudo.FORMATO, "versao": 1, "desafios": list(arena._exemplos().values())}


def test_exportar_importar_com_previa_e_confirmacao(db):
    arquivo = conteudo_export()
    arquivo["desafios"].append(exemplo(codigo="B95", gabarito=exemplo()["codigoInicial"]))  # inválido
    previa = ex("importar_desafios", {"arquivo": arquivo}, db)["previa"]
    assert db.hgetall(store.k_desafios()) == {}  # prévia não grava
    assert {p["codigo"]: (p["acao"], p["ok"]) for p in previa}["B95"] == ("criar", False)
    r = ex("importar_desafios", {"arquivo": arquivo, "confirmar": True}, db)
    assert sorted(r["gravados"]) == sorted(arena._exemplos()) and "B95" not in arena.desafios(db)
    assert all(p["acao"] == "igual" for p in ex("importar_desafios", {"arquivo": conteudo_export()}, db)["previa"])

    exp = ex("exportar_desafios", db=db)
    assert exp["formato"] == "meupia-challenge/desafios" and len(exp["desafios"]) == 7
    assert all(d["testesExtras"] and d["gabarito"] for d in exp["desafios"])
    assert acoes(db)[:2] == ["exportar_desafios", "importar_desafios"]
    with pytest.raises(Erro):
        ex("importar_desafios", {"arquivo": {"formato": "outro"}}, db)


def test_validar_todos(db):
    ex("importar_desafios", {"arquivo": conteudo_export(), "confirmar": True}, db)
    r = ex("validar_todos", db=db)
    assert r["ok"] and len(r["validacoes"]) == 7


# ---------------- horário do evento ----------------

def test_evento_mostra_horario_do_arquivo(db):
    r = ex("evento", db=db, autor=JUIZ)
    assert r["origem"] == "arquivo" and r["duracaoMinutos"] == 160 and r["freezeMinutos"] == 20


def test_salvar_inicio_no_fuso_do_evento_e_auditar(db):
    r = ex("salvar_evento", {"inicio": "2026-10-21T19:30"}, db=db)
    assert r["inicio"] == "2026-10-21T19:30-03:00"
    ev = ex("evento", db=db)
    assert ev["origem"] == "banco" and ev["fim"].startswith("2026-10-21T22:10")
    a = ex("auditoria", db=db)["auditoria"][0]
    assert a["acao"] == "horário do evento" and "19:10" in a["resumo"] and "19:30" in a["resumo"]


def test_voltar_ao_horario_do_arquivo(db):
    ex("salvar_evento", {"inicio": "2026-10-21T19:30"}, db=db)
    r = ex("salvar_evento", {"inicio": None, "voltarAoArquivo": True}, db=db)
    assert r["origem"] == "arquivo" and ex("evento", db=db)["inicio"] == arena.config()["inicio"]


def test_juiz_nao_altera_horario(db):
    with pytest.raises(Erro) as e:
        ex("salvar_evento", {"inicio": "2026-10-21T19:30"}, db=db, autor=JUIZ)
    assert e.value.status == 403


@pytest.mark.parametrize("valor", ["", "amanhã às 7", "2026-13-40T99:99"])
def test_data_invalida_recusada(db, valor):
    with pytest.raises(Erro) as e:
        ex("salvar_evento", {"inicio": valor}, db=db)
    assert e.value.status == 400
    assert ex("evento", db=db)["origem"] == "arquivo"
