import os
import sys
import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "api"))

from _lib import arena, turmas  # noqa: E402


# ---------------- semestre e nomes ----------------

@pytest.mark.parametrize("texto", ["2", "2º", "2°", "2o", "2º semestre", "fase 2", "2ª fase", " 2 ", "Fase 2", "2.",
                                   "semestre 2"])
def test_semestre_reconhecido(texto):
    assert turmas.normalizar_semestre(texto) == "2º"


@pytest.mark.parametrize("texto", ["9x", "abc", "0", "13", "", None, "2 e 4", "semestre 9x", "segundo"])
def test_semestre_nao_reconhecido(texto):
    assert turmas.normalizar_semestre(texto) is None


def test_chave_de_nome_ignora_acento_caixa_e_espacos():
    assert turmas.chave_nome("  Ána   Souza ") == turmas.chave_nome("ana souza") == "ana souza"


# ---------------- leitura da listagem ----------------

def test_planilha_com_cabecalho_em_qualquer_ordem():
    linhas = ["E-mail;Nome;Fase"] + [f"a{i}@x.com;Aluno {i};{(2, 4, 6)[i % 3]}" for i in range(39)]
    linhas.append(";Aluno Ruim;semestre 9x")
    alunos, ignoradas = turmas.ler_listagem("﻿" + "\n".join(linhas))
    assert len(alunos) == 39 and {a["semestre"] for a in alunos} == {"2º", "4º", "6º"}
    assert alunos[0] == {"nome": "Aluno 0", "semestre": "2º", "email": "a0@x.com"}
    assert ignoradas == [{"linha": 41, "texto": ";Aluno Ruim;semestre 9x", "motivo": "semestre não reconhecido"}]


def test_listagem_colada_em_varios_formatos():
    alunos, ignoradas = turmas.ler_listagem("Ana Souza, 2\nBruno Lima (6º)\nCarla Dias\t4\n\n")
    assert [(a["nome"], a["semestre"]) for a in alunos] == [("Ana Souza", "2º"), ("Bruno Lima", "6º"),
                                                            ("Carla Dias", "4º")]
    assert ignoradas == []


def test_csv_com_aspas_e_virgula_no_nome():
    alunos, _ = turmas.ler_listagem('nome,semestre\n"Souza, Ana",2º\n')
    assert alunos == [{"nome": "Souza, Ana", "semestre": "2º", "email": ""}]


def test_motivos_das_linhas_ignoradas():
    texto = "\n".join([",2", "x" * 61 + ",2", "Ana,2,sem-arroba", "Bruno,4", "BRUNO ,4", "Carla Dias,6", "Sozinho"])
    alunos, ignoradas = turmas.ler_listagem(texto, ja_cadastrados=["carla  dias"])
    assert [a["nome"] for a in alunos] == ["Bruno"]
    assert [(i["linha"], i["motivo"]) for i in ignoradas] == [
        (1, "sem nome"), (2, "nome com mais de 60 caracteres"), (3, "e-mail inválido"),
        (5, "repetido na listagem"), (6, "já cadastrado"), (7, "semestre não reconhecido")]


def test_limite_de_linhas():
    turmas.ler_listagem("\n".join(f"A{i},2" for i in range(turmas.MAX_LINHAS)))
    with pytest.raises(ValueError):
        turmas.ler_listagem("\n".join(f"A{i},2" for i in range(turmas.MAX_LINHAS + 2)))


# ---------------- distribuição ----------------

def turma(**por_semestre):
    return [{"id": f"{s}-{i}", "nome": f"Aluno {s} {i}", "semestre": s.replace("s", "") + "º"}
            for s, n in por_semestre.items() for i in range(n)]


def contagens(equipes, semestre):
    return [sum(1 for a in e if a["semestre"] == semestre) for e in equipes]


def test_quarenta_alunos_em_equipes_de_cinco():
    equipes = turmas.distribuir(turma(s6=8, s4=14, s2=18), 5, semente=7)
    assert [len(e) for e in equipes] == [5] * 8
    assert contagens(equipes, "6º") == [1] * 8
    assert set(contagens(equipes, "4º")) == {1, 2} and set(contagens(equipes, "2º")) == {2, 3}


def test_poucos_alunos_avancados():
    equipes = turmas.distribuir(turma(s6=2, s4=4, s2=7), 4, semente=1)
    assert len(equipes) == 4 and {len(e) for e in equipes} == {3, 4}
    assert max(contagens(equipes, "6º")) == 1 and contagens(equipes, "4º") == [1] * 4
    assert all(any(a["semestre"] != "2º" for a in e) for e in equipes)


def test_mesma_semente_mesmo_resultado():
    alunos = turma(s6=5, s4=9, s2=11)
    ids = lambda eqs: [[a["id"] for a in e] for e in eqs]  # noqa: E731
    assert ids(turmas.distribuir(alunos, 5, 42)) == ids(turmas.distribuir(list(reversed(alunos)), 5, 42))
    assert ids(turmas.distribuir(alunos, 5, 42)) != ids(turmas.distribuir(alunos, 5, 43))


def test_menos_alunos_que_o_tamanho_vira_uma_equipe():
    assert [len(e) for e in turmas.distribuir(turma(s2=3), 5, 0)] == [3]
    assert turmas.distribuir([], 5, 0) == []


def test_propriedades_da_distribuicao():
    for tamanho in range(2, 11):
        for n in range(1, 61):
            for semente in range(0, 50, 7):
                alunos = turma(s6=n // 5, s4=n // 3, s2=n - n // 5 - n // 3)
                alunos.append({"id": "x", "nome": "Sem número", "semestre": "?"})
                equipes = turmas.distribuir(alunos, tamanho, semente)
                tamanhos = [len(e) for e in equipes]
                assert max(tamanhos) <= tamanho and max(tamanhos) - min(tamanhos) <= 1
                assert sorted(a["id"] for e in equipes for a in e) == sorted(a["id"] for a in alunos)
                for s in ("6º", "4º", "2º", "?"):
                    c = contagens(equipes, s)
                    assert max(c) - min(c) <= 1


def test_semestre_sem_numero_vai_por_ultimo():
    alunos = turma(s2=2) + [{"id": "x", "nome": "X", "semestre": "esp"}]
    equipes = turmas.distribuir(alunos, 3, 0)
    assert equipes[0][-1]["id"] == "x"


# ---------------- nomes ----------------

def test_nomes_pulam_os_usados_e_ganham_numero():
    nomes = turmas.nomes_de_equipes(3, arena.PALAVRAS, usados=["orion", "Lyra"])
    assert nomes == [("Vega", 1), ("Nova", 3), ("Atlas", 4)]
    todos = turmas.nomes_de_equipes(18, arena.PALAVRAS)
    assert todos[15] == ("Hydra", 15) and todos[16:] == [("Orion 2", 0), ("Vega 2", 1)]


def test_contagem_por_semestre():
    assert turmas.por_semestre(turma(s2=2, s6=1)) == {"6º": 1, "2º": 2}
    assert list(turmas.por_semestre(turma(s2=1, s6=1, s4=1))) == ["6º", "4º", "2º"]
