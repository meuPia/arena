"""Entregas do modo offline: os .por que as equipes salvam na IDE (src/arena/entrega.js), pontuados pela banca
pelo painel (aba Entregas, admin.pontuar_entregas) ou pelo terminal (scripts/pontuar_equipe.py). Funções puras."""
import os
import re
import unicodedata

CABECALHO = re.compile(r"^\s*//\s*arena:\s*([A-Za-z]\d{2})\b")
NOME = re.compile(r"^([A-Za-z]\d{2})(?![0-9])")
LINHA_EQUIPE = re.compile(r"^\s*//\s*equipe:\s*(.*?)\s*$")


def codigo(nome, texto):
    """Desafio do arquivo: a 1ª linha que a IDE grava (`// arena: B01`) ou, sem ela, o nome (B01.por,
    "B01 (2).por"). None se não der para saber."""
    m = CABECALHO.match(texto.splitlines()[0] if texto.strip() else "") or NOME.match(os.path.basename(nome))
    return m.group(1).upper() if m else None


def equipe(texto):
    """Equipe gravada na 2ª linha do .por (`// equipe: <nome>`, logo abaixo do código) ou None."""
    linhas = texto.splitlines()
    if len(linhas) < 2 or not CABECALHO.match(linhas[0]):
        return None
    m = LINHA_EQUIPE.match(linhas[1])
    return (m.group(1) or None) if m else None


def mesma_equipe(a, b):
    """Compara nomes de equipe sem diferenciar acento, caixa nem espaços extras."""
    def base(s):
        s = unicodedata.normalize("NFD", " ".join(str(s).split()))
        return "".join(c for c in s if unicodedata.category(c) != "Mn").casefold()
    return base(a) == base(b)


def escolher(arquivos):
    """arquivos: [(nome, texto, modificado)] -> ({codigo: (nome, texto, modificado)}, [avisos]).
    Vários arquivos do mesmo desafio: vale o modificado por último (a equipe salva a cada melhoria)."""
    escolhidos, avisos = {}, []
    for item in arquivos:
        nome, texto, _ = item
        cod = codigo(nome, texto)
        if not cod:
            avisos.append(f"ignorado (sem código do desafio na 1ª linha nem no nome): {nome}")
            continue
        if cod in escolhidos:
            velho, novo = sorted([escolhidos[cod], item], key=lambda x: x[2])
            avisos.append(f"{cod}: vale {os.path.basename(novo[0])} (mais recente); "
                          f"ignorado {os.path.basename(velho[0])}")
            escolhidos[cod] = novo
        else:
            escolhidos[cod] = item
    return escolhidos, avisos
