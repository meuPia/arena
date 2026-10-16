"""Alunos e equipes, sem banco nem HTTP: leitura da listagem/CSV de alunos, semestre no formato curto (`2º`) e
distribuição nivelada em equipes. Usado pelo painel (admin.importar_participantes e admin.montar_equipes)."""

import csv
import io
import math
import random
import re
import unicodedata

MAX_LINHAS = 500
MAX_NOME = 60
_RE_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_RE_ROTULO = re.compile(r"\s*(.+?)\s*\(([^()]{1,20})\)\s*")
_RE_NUMERO = re.compile(r"\d+")
_SEPARADORES = ("\t", ";", ",")
_COL_NOME = {"nome", "aluno", "aluna", "estudante"}
_COL_SEMESTRE = {"semestre", "fase", "periodo", "período"}
_COL_EMAIL = {"email", "e-mail"}


def normalizar_semestre(texto):
    """'2', '2º', '2°', '2o', '2º semestre', 'fase 2', '2ª fase' -> '2º'; outra coisa -> None."""
    t = str(texto or "").strip().lower()
    if not t:
        return None
    resto = re.sub(r"\b(semestre|sem|fase|periodo|período)\b", " ", t)
    resto = re.sub(r"(?<=\d)o\b", " ", resto)  # '2o'
    resto = re.sub(r"[º°ª.]", " ", resto)
    numeros = _RE_NUMERO.findall(resto)
    if len(numeros) != 1 or resto.replace(numeros[0], "").strip():
        return None
    n = int(numeros[0])
    return f"{n}º" if 1 <= n <= 12 else None


def chave_nome(nome):
    """Chave para achar nomes repetidos: sem acentos, sem diferenciar maiúsculas, espaços colapsados."""
    sem_acento = "".join(c for c in unicodedata.normalize("NFKD", str(nome)) if not unicodedata.combining(c))
    return " ".join(sem_acento.casefold().split())


def nivel(semestre):
    """Número do semestre ('6º' -> 6); sem número -> 0 (vai por último na distribuição)."""
    m = _RE_NUMERO.search(str(semestre or ""))
    return int(m.group()) if m else 0


def _separador(linha):
    for s in _SEPARADORES:
        if s in linha:
            return s
    return None


def _cabecalho(campos):
    nomes = [chave_nome(c) for c in campos]
    if not any(n in _COL_NOME for n in nomes) or not any(n in _COL_SEMESTRE for n in nomes):
        return None
    pos = lambda conjunto: next((i for i, n in enumerate(nomes) if n in conjunto), None)  # noqa: E731
    return {"nome": pos(_COL_NOME), "semestre": pos(_COL_SEMESTRE), "email": pos(_COL_EMAIL)}


def ler_listagem(texto, ja_cadastrados=()):
    """(alunos, ignoradas): alunos = [{nome, semestre, email}]; ignoradas = [{linha, texto, motivo}].
    `ja_cadastrados`: nomes existentes no banco (comparados por chave_nome)."""
    texto = str(texto or "").lstrip("﻿")
    linhas = [(i, l) for i, l in enumerate(texto.splitlines(), 1) if l.strip()]
    if len(linhas) > MAX_LINHAS + 1:  # +1: o cabeçalho, se houver
        raise ValueError(f"A listagem tem mais de {MAX_LINHAS} linhas.")
    if not linhas:
        return [], []
    sep = _separador(linhas[0][1])
    colunas = {"nome": 0, "semestre": 1, "email": 2}
    if sep:
        cab = _cabecalho(next(csv.reader([linhas[0][1]], delimiter=sep)))
        if cab:
            colunas, linhas = cab, linhas[1:]
    existentes = {chave_nome(n) for n in ja_cadastrados}
    vistos, alunos, ignoradas = set(), [], []
    for num, linha in linhas:
        def ignorar(motivo):
            ignoradas.append({"linha": num, "texto": linha.strip()[:120], "motivo": motivo})
        s = _separador(linha)
        if s:
            campos = [c.strip() for c in next(csv.reader(io.StringIO(linha), delimiter=s))]
            pega = lambda k: campos[colunas[k]] if colunas.get(k) is not None and colunas[k] < len(campos) else ""  # noqa: E731
            nome, sem, email = pega("nome"), pega("semestre"), pega("email")
        else:
            m = _RE_ROTULO.fullmatch(linha)
            nome, sem, email = (m.group(1), m.group(2), "") if m else (linha.strip(), "", "")
        nome = " ".join(nome.split())
        email = email.strip().lower()
        semestre = normalizar_semestre(sem)
        chave = chave_nome(nome)
        if not nome:
            ignorar("sem nome")
        elif len(nome) > MAX_NOME:
            ignorar(f"nome com mais de {MAX_NOME} caracteres")
        elif not semestre:
            ignorar("semestre não reconhecido")
        elif email and (not _RE_EMAIL.match(email) or len(email) > 120):
            ignorar("e-mail inválido")
        elif chave in existentes:
            ignorar("já cadastrado")
        elif chave in vistos:
            ignorar("repetido na listagem")
        else:
            vistos.add(chave)
            alunos.append({"nome": nome, "semestre": semestre, "email": email})
    return alunos, ignoradas


def distribuir(alunos, tamanho, semente):
    """Equipes niveladas: teto(n/tamanho) equipes; por semestre, do mais avançado ao menos (sem número por
    último), ordem sorteada dentro de cada semestre, e rodízio contínuo (o aluno i vai para a equipe i mod T,
    sem reiniciar ao trocar de semestre). Tamanhos e contagem de cada semestre diferem em no máximo 1."""
    alunos = list(alunos)
    if not alunos:
        return []
    total = math.ceil(len(alunos) / tamanho)
    rng = random.Random(semente)
    grupos = {}
    for a in sorted(alunos, key=lambda a: (chave_nome(a["nome"]), a.get("id", ""))):
        grupos.setdefault(nivel(a["semestre"]), []).append(a)
    fila = []
    for n in sorted(grupos, key=lambda n: (n == 0, -n)):
        g = grupos[n]
        rng.shuffle(g)
        fila.extend(g)
    equipes = [[] for _ in range(total)]
    for i, a in enumerate(fila):
        equipes[i % total].append(a)
    return equipes


def nomes_de_equipes(qtd, palavras, usados=()):
    """[(nome, indice_da_palavra)]: 'Orion', 'Vega'… pulando os usados; esgotadas, 'Orion 2', 'Vega 2'…"""
    usados = {chave_nome(u) for u in usados}
    nomes, rodada = [], 1
    while len(nomes) < qtd:
        for i, p in enumerate(palavras):
            nome = p.capitalize() + (f" {rodada}" if rodada > 1 else "")
            if chave_nome(nome) not in usados:
                usados.add(chave_nome(nome))
                nomes.append((nome, i))
                if len(nomes) == qtd:
                    break
        rodada += 1
    return nomes


def por_semestre(integrantes):
    """{'6º': 1, '4º': 2, ...} na ordem do mais avançado."""
    contagem = {}
    for a in sorted(integrantes, key=lambda a: -nivel(a["semestre"])):
        contagem[a["semestre"]] = contagem.get(a["semestre"], 0) + 1
    return contagem
