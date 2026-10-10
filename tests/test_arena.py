import json
import os
import sys

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "api"))

from _lib import arena, servico, store, validacao  # noqa: E402
from _lib.web import Erro, emitir_token, ler_token  # noqa: E402


# Os testes usam só os desafios fictícios de arena/exemplos (os reais ficam no banco).
EXEMPLOS = arena._exemplos()


def gabarito(cod):
    return EXEMPLOS[cod]["gabarito"]


@pytest.fixture
def db(tmp_path, monkeypatch):
    monkeypatch.setenv("ARENA_MODO", "ensaio")
    monkeypatch.delenv("KV_REST_API_URL", raising=False)
    monkeypatch.delenv("UPSTASH_REDIS_REST_URL", raising=False)
    monkeypatch.delenv("SUPABASE_URL", raising=False)  # testes nunca gravam no banco real
    monkeypatch.setenv("ARENA_ARQUIVO_LOCAL", str(tmp_path / "db.json"))
    arena.limpar_cache()
    yield store.abrir()
    arena.limpar_cache()


# ---------------- regras ----------------

def test_config_padroes_e_valores_invalidos():
    cfg = arena.validar_config({})
    assert cfg["pontuacao"]["modo"] == "proporcional" and cfg["desbloqueioConta"] == "aceito"
    with pytest.raises(ValueError):
        arena.validar_config({"pontuacao": {"modo": "metade"}})
    with pytest.raises(ValueError):
        arena.validar_config({"desbloqueioConta": "tudo"})
    assert arena.config()["pontuacao"]["modo"] == "proporcional"


def ac(t, codigo, pontos, completo=False, caracteres=100):
    return {"t": t, "codigo": codigo, "pontos": pontos, "completo": completo, "caracteres": caracteres}


def test_pontuacao_proporcional_com_piso():
    cfg, todos = arena.config(), EXEMPLOS
    assert arena.pontos_submissao(todos["B91"], 14, 20, cfg) == 7
    assert arena.pontos_submissao(todos["G91"], 19, 20, cfg) == 33  # 35 × 19/20 = 33,25
    assert arena.pontos_submissao(todos["B91"], 20, 20, cfg) == 10
    assert arena.pontos_submissao(todos["B91"], 0, 20, cfg) == 0


def test_pontuacao_modo_completo():
    cfg, todos = arena.validar_config({"pontuacao": {"modo": "completo"}}), EXEMPLOS
    assert arena.pontos_submissao(todos["B91"], 19, 20, cfg) == 0
    assert arena.pontos_submissao(todos["B91"], 20, 20, cfg) == 10


def test_melhor_submissao_mantida_e_empate_por_caracteres():
    aceitas = [ac(10, "B91", 7, caracteres=150), ac(20, "B91", 5, caracteres=90)]
    assert arena.melhores(aceitas)["B91"]["pontos"] == 7          # pior não reduz
    aceitas += [ac(30, "B91", 10, True, 142), ac(40, "B91", 10, True, 118), ac(50, "B91", 10, True, 130)]
    m = arena.melhores(aceitas)["B91"]
    assert (m["pontos"], m["caracteres"], m["t"]) == (10, 118, 40)  # completa maior não substitui
    assert arena.melhores(aceitas + [ac(60, "B91", 10, True, 118)])["B91"]["t"] == 40  # empate total: a mais antiga


def test_ultima_melhoria_ignora_reducao_de_caracteres():
    aceitas = [ac(10, "B91", 7), ac(20, "B91", 10, True, 142), ac(30, "B91", 10, True, 100), ac(40, "B92", 0)]
    assert arena.tempo_ultima_melhoria(aceitas) == 20
    assert arena.tempo_ultima_melhoria(aceitas, ate=15) == 10
    assert arena.tempo_ultima_melhoria([ac(5, "B91", 0)]) is None


def test_desbloqueio_conta_aceitos_ou_completos():
    cfg, todos = arena.config(), EXEMPLOS
    m = arena.melhores([ac(1, "B91", 7), ac(2, "B92", 10, True)])
    cont = arena.contagem_desbloqueio(m, todos, cfg)
    assert arena.nivel_liberado("Bronze", {}, cfg)
    assert not arena.nivel_liberado("Silver", arena.contagem_desbloqueio({}, todos, cfg), cfg)
    assert arena.nivel_liberado("Silver", cont, cfg)  # parcial conta (padrão "aceito")
    assert not arena.nivel_liberado("Gold", cont, cfg)
    assert "2 Silver" in arena.falta_para_liberar("Gold", cont, cfg)

    cfg_c = dict(cfg, desbloqueioConta="completo")
    cont_c = arena.contagem_desbloqueio(m, todos, cfg_c)
    assert not arena.nivel_liberado("Silver", cont_c, cfg_c)
    assert arena.falta_para_liberar("Silver", cont_c, cfg_c) == "Recupere mais 1 Bronze para desbloquear."


def test_cooldown():
    cfg = arena.config()
    assert arena.cooldown_restante(2, 1000, cfg, agora=1001) == 0
    assert arena.cooldown_restante(3, 1000, cfg, agora=1001) == 179
    assert arena.cooldown_restante(3, 1000, cfg, agora=1200) == 0


EQUIPES = {"a": {"nome": "A"}, "b": {"nome": "B"}, "c": {"nome": "C"}, "d": {"nome": "D"}}


def ids(linhas):
    return [l["id"] for l in linhas]


def test_placar_ordem_pontos_completos_caracteres_tempo_nome():
    cfg, todos = arena.config(), EXEMPLOS
    # a e b: 20 pts; a com 2 completos, b com 1 completo + 2 parciais
    aceitas = {
        "a": [ac(100, "B91", 10, True, 300), ac(200, "B92", 10, True, 300)],
        "b": [ac(50, "B91", 10, True, 100), ac(60, "B92", 5), ac(70, "B93", 5)],
    }
    assert ids(arena.placar(EQUIPES, aceitas, todos, cfg))[:2] == ["a", "b"]
    # c empata com a em pontos e completos, mas com menos caracteres
    aceitas["c"] = [ac(900, "B91", 10, True, 200), ac(950, "B93", 10, True, 250)]
    assert ids(arena.placar(EQUIPES, aceitas, todos, cfg))[:3] == ["c", "a", "b"]
    # d empata com c em tudo, mas chegou antes à pontuação
    aceitas["d"] = [ac(10, "B92", 10, True, 200), ac(20, "B93", 10, True, 250)]
    linhas = arena.placar(EQUIPES, aceitas, todos, cfg)
    assert ids(linhas) == ["d", "c", "a", "b"]
    assert linhas[0]["modulos"]["Bronze"] == [None, "completo", "completo"]
    assert arena.placar(EQUIPES, aceitas, todos, cfg)[3]["modulos"]["Bronze"] == ["completo", "parcial", "parcial"]
    # empate total: nome
    iguais = {"b": [ac(5, "B91", 10, True, 100)], "a": [ac(5, "B91", 10, True, 100)]}
    assert ids(arena.placar({"b": {"nome": "B"}, "a": {"nome": "A"}}, iguais, todos, cfg)) == ["a", "b"]


def test_placar_freeze_mostra_melhor_ate_o_freeze():
    cfg, todos = arena.config(), EXEMPLOS
    aceitas = {"a": [ac(100, "B91", 7, False, 150), ac(500, "B91", 10, True, 120)], "b": [ac(200, "B91", 8)]}
    vivo = {l["id"]: l for l in arena.placar(EQUIPES, aceitas, todos, cfg)}
    congelado = {l["id"]: l for l in arena.placar(EQUIPES, aceitas, todos, cfg, ate=300)}
    assert (vivo["a"]["pontos"], vivo["a"]["completos"], vivo["a"]["caracteres"]) == (10, 1, 120)
    assert (congelado["a"]["pontos"], congelado["a"]["completos"], congelado["a"]["caracteres"]) == (7, 0, 0)
    assert congelado["a"]["modulos"]["Bronze"][0] == "parcial"
    assert ids(arena.placar(EQUIPES, aceitas, todos, cfg, ate=300))[:2] == ["b", "a"]


def test_token():
    assert ler_token(emitir_token("equipe1")) == "equipe1"
    assert ler_token(emitir_token("equipe1") + "x") is None


# ---------------- armazenamento ----------------

def test_store_lista_de_aceitas(db):
    db.lpush(store.k_aceitas("e1"), json.dumps(ac(1, "B91", 7)))
    db.lpush(store.k_aceitas("e1"), json.dumps(ac(2, "B91", 10, True)))
    lidas = [json.loads(x) for x in db.lrange(store.k_aceitas("e1"), 0, -1)]
    assert [r["t"] for r in lidas] == [2, 1]
    assert db.lrange(store.k_aceitas("e2"), 0, -1) == []


# ---------------- fluxo completo ----------------

def parcial_b92(limite=50):
    """Acerta os exemplos, mas devolve o primeiro item quando a lista passa de `limite` elementos."""
    fonte = gabarito("B92").replace("funcao maior(lista)\n",
                                    f"funcao maior(lista)\n    se tamanho(lista) > {limite} então\n"
                                    "        retorne lista[0]\n    fim_se\n", 1)
    assert fonte != gabarito("B92")
    return fonte


def gabarito_curto_b92():
    return "\n".join(l for l in gabarito("B92").splitlines() if "escreva(" not in l)


ERRADO_B92 = 'algoritmo "x"\nfuncao maior(l)\n    retorne 0\nfim_funcao\ninicio\nfim_algoritmo'


def test_fluxo_submissao(db):
    eid = "equipe1"
    with pytest.raises(Erro):
        servico.missao(eid, "S91", db=db)  # Silver trancado

    r = servico.submeter(eid, "B92", parcial_b92(), ["Ana (2º)"], db=db, agora=1000)
    assert r["status"] == "aceito" and not r["completo"]
    assert 0 < r["extras"]["aprovados"] < r["extras"]["total"]
    assert r["pontos"] == 10 * r["extras"]["aprovados"] // r["extras"]["total"]
    assert r["melhor"] == {"pontos": r["pontos"], "completo": False, "caracteres": r["caracteres"]}
    assert r["pontosModulo"] == 10 and "testes" not in r
    parcial = r["pontos"]

    r = servico.submeter(eid, "B93", gabarito("B93"), ["Bruno"], db=db, agora=1010)
    assert r["status"] == "aceito" and r["completo"] and r["pontos"] == 10
    s91 = servico.missao(eid, "S91", db=db)  # Silver liberado com um Bronze parcial
    assert s91["codigo"] == "S91" and s91["melhor"] is None
    assert "testesExtras" not in s91 and "gabarito" not in s91

    painel = servico.missoes(eid, db=db)
    assert painel["equipe"]["pontos"] == parcial + 10
    b92 = next(m for m in painel["niveis"][0]["itens"] if m["codigo"] == "B92")
    assert b92["melhor"]["pontos"] == parcial and not b92["completo"] and b92["tentativas"] == 1
    assert painel["niveis"][1]["liberado"] and not painel["niveis"][2]["liberado"]


def test_submissao_pior_nao_reduz_e_completo_pode_reduzir_codigo(db):
    eid = "equipe1"
    r = servico.submeter(eid, "B92", gabarito("B92"), ["Ana"], db=db, agora=1000)
    assert r["completo"] and r["pontos"] == 10
    chars = r["caracteres"]

    r = servico.submeter(eid, "B92", parcial_b92(), ["Ana"], db=db, agora=1001)
    assert r["status"] == "aceito" and r["pontos"] < 10
    assert r["melhor"] == {"pontos": 10, "completo": True, "caracteres": chars}

    r = servico.submeter(eid, "B92", gabarito_curto_b92(), ["Ana"], db=db, agora=1002)
    assert r["completo"] and r["caracteres"] < chars
    assert r["melhor"]["caracteres"] == r["caracteres"]
    assert servico.missao(eid, "B92", db=db)["melhor"]["caracteres"] == r["caracteres"]


def test_reprovado_nos_exemplos_nao_pontua_e_conta_para_o_cooldown(db):
    eid = "equipe2"
    for i in range(3):
        r = servico.submeter(eid, "B92", ERRADO_B92, ["Gabi"], db=db, agora=2000 + i)
        assert r["status"] == "reprovado_exemplos" and r["pontos"] == 0 and r["melhor"] is None
    r = servico.submeter(eid, "B92", ERRADO_B92, ["Gabi"], db=db, agora=2010)
    assert r["status"] == "cooldown" and r["espera"] > 0
    assert servico.missoes(eid, db=db)["equipe"]["pontos"] == 0
    assert servico.submeter(eid, "B92", gabarito("B92"), ["Gabi"], db=db, agora=2300)["status"] == "aceito"


def test_submissao_exige_participantes(db):
    with pytest.raises(Erro):
        servico.submeter("equipe1", "B92", gabarito("B92"), [], db=db)


def test_log_guarda_participantes_e_resultado(db):
    servico.submeter("equipe1", "B92", parcial_b92(), ["Ana (2º)", "Carla (6º)"], db=db)
    log = servico.submissoes(db=db)
    assert log[0]["participantes"] == ["Ana (2º)", "Carla (6º)"]
    assert log[0]["exemplos"] == {"aprovados": 3, "total": 3}
    assert log[0]["extras"]["total"] >= 15 and log[0]["pontos"] > 0 and log[0]["caracteres"] > 0
    assert json.dumps(log)  # serializável


def test_placar_publico_congela_e_admin_ve_melhoria(db, monkeypatch):
    monkeypatch.delenv("ARENA_MODO", raising=False)
    monkeypatch.delenv("ARENA_REVELAR", raising=False)
    jan = arena.janela()
    antes, depois = jan["freeze"] - 600, jan["freeze"] + 60
    r = servico.submeter("equipe1", "B92", parcial_b92(), ["Ana"], db=db, agora=antes)
    servico.submeter("equipe1", "B92", gabarito("B92"), ["Ana"], db=db, agora=depois)

    publico = servico.placar(db=db, agora=depois + 1)
    linha = next(l for l in publico["linhas"] if l["id"] == "equipe1")
    assert publico["congelado"] and linha["pontos"] == r["pontos"] and linha["completos"] == 0
    assert "fonte" not in json.dumps(publico) and "participantes" not in json.dumps(publico)

    admin = servico.placar(admin=True, db=db, agora=depois + 1)
    linha = next(l for l in admin["linhas"] if l["id"] == "equipe1")
    assert not admin["congelado"] and linha["pontos"] == 10 and linha["completos"] == 1

    monkeypatch.setenv("ARENA_REVELAR", "1")
    assert next(l for l in servico.placar(db=db, agora=depois + 1)["linhas"] if l["id"] == "equipe1")["pontos"] == 10


def test_exemplos_validam_com_o_juiz(db):
    todos = arena.desafios(db)
    assert sorted(todos) == ["B91", "B92", "B93", "G91", "S91", "S92", "X91"]
    for cod in todos:
        r = validacao.validar(arena.desafio_completo(db, cod))
        assert r["ok"], (cod, r["erros"])


def test_exemplos_tem_formato_de_exportacao_e_explicam_a_pontuacao():
    cfg = arena.config()
    for cod, d in EXEMPLOS.items():
        assert set(arena.CAMPOS_REGISTRO + arena.CAMPOS_SEGREDO) <= set(d), cod
        assert "testesOcultos" not in d and d["nivel"] in cfg["niveis"], cod
        assert len(d["testesPublicos"].splitlines()) == 3, cod
        assert 15 <= len(d["testesExtras"].splitlines()) <= 25, cod
        assert "**Como pontua**" in d["descricao"] and "menor código" in d["descricao"], cod
        assert not set(arena.CAMPOS_SEGREDO) & set(arena.publico(d)), cod


# ---------------- desafios no banco ----------------

class RemotoVazio:
    """Imita um banco remoto (Supabase/Upstash) sem desafios."""

    base = "https://remoto-vazio"

    def hgetall(self, chave):
        return {}

    def hget(self, chave, campo):
        return None


def test_local_vazio_usa_exemplos_e_remoto_vazio_nao(db):
    assert "B91" in arena.desafios(db)
    assert arena.segredos(db, "B91")["gabarito"]
    assert arena.desafios(RemotoVazio()) == {}
    assert arena.segredos(RemotoVazio(), "B91") is None


def test_registro_publico_nao_tem_segredos(db):
    for d in arena.desafios(db).values():
        assert not set(arena.CAMPOS_SEGREDO) & set(d)


def test_desafios_do_banco_substituem_os_exemplos_e_cache(db):
    novo = dict(EXEMPLOS["B91"], codigo="B01", titulo="Real")
    arena.gravar_desafio(db, novo)
    assert list(arena.desafios(db)) == ["B01"]  # banco com desafios: exemplos somem
    assert arena.segredos(db, "B01")["gabarito"] == novo["gabarito"]
    assert arena.desafio_completo(db, "B01")["testesExtras"] == novo["testesExtras"]
    # Escrita por fora (outra instância): só aparece depois do cache expirar.
    db.hset(store.k_desafios(), "B01", json.dumps(dict(arena.desafios(db)["B01"], titulo="Editado")))
    assert arena.desafios(db)["B01"]["titulo"] == "Real"
    for item in arena._CACHE.values():
        item["expira"] = 0
    assert arena.desafios(db)["B01"]["titulo"] == "Editado"


def test_painel_e_missao_nao_leem_segredos(db, monkeypatch):
    def proibido(*a):
        raise AssertionError("segredos lidos fora do julgamento")
    monkeypatch.setattr(arena, "segredos", proibido)
    servico.missoes("equipe1", db=db)
    m = servico.missao("equipe1", "B91", db=db)
    assert not set(arena.CAMPOS_SEGREDO) & set(m)
    servico.placar(db=db)


def test_submissao_sem_bateria_extra_e_recusada(db):
    d = dict(EXEMPLOS["B91"], codigo="B01")
    arena.gravar_desafio(db, dict(d, testesExtras=""))
    with pytest.raises(Erro) as e:
        servico.submeter("equipe1", "B01", gabarito("B91"), ["Ana"], db=db)
    assert e.value.status == 503
    assert db.hgetall(store.k_tentativas("equipe1")) == {}  # não conta tentativa


def test_versao_do_core_igual_no_navegador_e_no_juiz():
    import re
    wasm = open(os.path.join(RAIZ, "src", "engine", "wasm.js"), encoding="utf-8").read()
    req = open(os.path.join(RAIZ, "requirements.txt"), encoding="utf-8").read()
    navegador = re.search(r'let version\s*=\s*"([^"]+)"', wasm).group(1)
    juiz_ = re.search(r"meupia-core==([\w.]+)", req).group(1)
    assert navegador == juiz_, f"navegador usa {navegador}, juiz usa {juiz_}"
