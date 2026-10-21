"""Monta a IDE das equipes em versão PORTÁTIL para Windows: roda de um pendrive, sem instalar nada.

Roda numa máquina com internet (macOS, Linux ou Windows), DEPOIS do build offline:
  python3 scripts/preparar_offline.py --sem-wsl       # build com o Pyodide local (offline/dist)
  python3 scripts/copiar_supabase.py offline/arena.sqlite3 --publico
  python3 scripts/preparar_portatil.py                # -> offline/meupia-arena-portatil/ e .zip

No Windows: copie a pasta (ou descompacte o .zip) e dê dois cliques em INICIAR.bat.

O pacote leva o Python "embeddable" oficial do python.org (com sqlite3, sem instalar), o build offline, o
servidor local e um banco NOVO só com a parte pública dos desafios: os registros são relidos e regravados um a
um, então testes extras, gabaritos, equipes, perfis e submissões nunca entram, mesmo que o banco de origem os
tenha. Modo offline: sem login nem submissão; as equipes salvam o .por (pontuar_equipe.py, na banca).
"""
import argparse
import hashlib
import os
import shutil
import sys
import urllib.request
import zipfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OFFLINE = os.path.join(RAIZ, "offline")
DIST = os.path.join(OFFLINE, "dist")
NOME = "meupia-arena-portatil"
SAIDA = os.path.join(OFFLINE, NOME)

# Última 3.12 com binários para Windows (as seguintes são só de segurança, em código-fonte)
PYTHON_VERSAO = "3.12.10"
PYTHON_ZIP = f"python-{PYTHON_VERSAO}-embed-amd64.zip"
PYTHON_URL = f"https://www.python.org/ftp/python/{PYTHON_VERSAO}/{PYTHON_ZIP}"

sys.path.insert(0, os.path.join(RAIZ, "api"))
from _lib import store  # noqa: E402

INICIAR_BAT = r"""@echo off
chcp 65001 >nul
title meuPia Arena (modo offline)
cd /d "%~dp0"
rem O banco vai para a pasta temporaria: o pendrive pode ser somente leitura e varias maquinas podem usar o mesmo.
set "ARENA_SQLITE=%TEMP%\meupia-arena-aluno.sqlite3"
del /q "%ARENA_SQLITE%" "%ARENA_SQLITE%-wal" "%ARENA_SQLITE%-shm" 2>nul
copy /y "%~dp0arena.sqlite3" "%ARENA_SQLITE%" >nul
if errorlevel 1 (
  echo Nao consegui copiar o banco para %TEMP%.
  pause
  exit /b 1
)
"%~dp0python\python.exe" "%~dp0scripts\iniciar_offline.py" --abrir
echo.
echo A Arena foi encerrada.
pause
"""

LEIA_ME = """meuPiá Arena — IDE das equipes (modo offline, portátil)

COMO USAR
  1. Dê dois cliques em INICIAR.bat (Windows 10/11, 64 bits). Nada é instalado.
  2. O navegador abre em http://localhost:8787. Deixe a janela preta aberta durante a prova.
  3. Escolha a missão, programe e use RODAR para os testes de exemplo.
  4. Use SALVAR .POR (Ctrl+Shift+Enter) a cada melhoria. O arquivo vai para a pasta Downloads
     (B01.por, B01 (1).por...). A banca recolhe os arquivos e pontua o mais recente de cada missão.

SE ALGO DER ERRADO
  - Página de login ou tela antiga: recarregue sem cache (Ctrl+F5).
  - "porta ocupada": feche a outra janela da Arena e abra o INICIAR.bat de novo.
  - Windows avisou sobre o arquivo (SmartScreen): "Mais informações" > "Executar assim mesmo".
  - O rascunho do código fica no navegador desta máquina; o que vale para a nota é o .por salvo.
"""


def sha256(caminho):
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def conferir_build():
    if not os.path.exists(os.path.join(DIST, "vendor", "pyodide", "pyodide.js")):
        sys.exit("sem build offline: rode antes `python3 scripts/preparar_offline.py --sem-wsl`")
    feito = os.path.getmtime(os.path.join(DIST, "index.html"))
    fontes = [os.path.join(r, n) for pasta in ("src",) for r, _, ns in os.walk(os.path.join(RAIZ, pasta)) for n in ns]
    fontes += [os.path.join(RAIZ, n) for n in ("index.html", "ide.html", "placar.html", "admin.html", "vite.config.js")]
    novos = [os.path.relpath(f, RAIZ) for f in fontes if os.path.exists(f) and os.path.getmtime(f) > feito]
    if novos:
        sys.exit("offline/dist é mais velho que o código (" + ", ".join(novos[:3]) + "...): "
                 "rode de novo `python3 scripts/preparar_offline.py --sem-wsl`")


def ler_desafios(origem, permitir_exemplos):
    if not os.path.exists(origem):
        if permitir_exemplos:
            return {}
        sys.exit(f"{origem} não existe: rode `python3 scripts/copiar_supabase.py {os.path.relpath(origem, RAIZ)} --publico`")
    desafios = store.Sqlite(origem).hgetall(store.k_desafios())
    if not desafios and not permitir_exemplos:
        sys.exit(f"{origem} não tem desafios (a IDE mostraria os de EXEMPLO). Use --exemplos para um pacote de teste.")
    return desafios


def banco_publico(desafios, destino):
    novo = store.Sqlite(destino)
    novo.carregar([(store.k_desafios(), c, v) for c, v in desafios.items()], [])
    with novo._con() as c:
        c.execute("pragma wal_checkpoint(truncate)")
        c.execute("pragma journal_mode = delete")  # um arquivo só, sem -wal/-shm
    return sorted(desafios)


def python_portatil(destino):
    cache = os.path.join(OFFLINE, "cache", PYTHON_ZIP)
    if not os.path.exists(cache):
        os.makedirs(os.path.dirname(cache), exist_ok=True)
        print(f"  baixando {PYTHON_URL}")
        with urllib.request.urlopen(urllib.request.Request(PYTHON_URL, headers={"User-Agent": "meupia-arena"})) as r, \
                open(cache + ".parcial", "wb") as f:
            shutil.copyfileobj(r, f, 1 << 20)
        os.replace(cache + ".parcial", cache)
    with zipfile.ZipFile(cache) as z:
        nomes = z.namelist()
        if "python.exe" not in nomes or not any(n.startswith("_sqlite3") for n in nomes):
            sys.exit(f"{PYTHON_ZIP} inesperado (sem python.exe ou sqlite3): apague offline/cache e tente de novo")
        z.extractall(destino)
    return sha256(cache)


def copiar(rel, destino_rel=None):
    origem, destino = os.path.join(RAIZ, rel), os.path.join(SAIDA, destino_rel or rel)
    if os.path.isdir(origem):
        shutil.copytree(origem, destino, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))
    else:
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        shutil.copy2(origem, destino)


def escrever(rel, texto, crlf=False):
    with open(os.path.join(SAIDA, rel), "w", encoding="utf-8", newline="\r\n" if crlf else "\n") as f:
        f.write(texto)


def principal():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--banco", default=os.path.join(OFFLINE, "arena.sqlite3"),
                   help="banco público de origem (padrão: offline/arena.sqlite3)")
    p.add_argument("--exemplos", action="store_true", help="aceita banco sem desafios (pacote de teste)")
    p.add_argument("--sem-zip", action="store_true")
    a = p.parse_args()

    conferir_build()
    desafios = ler_desafios(os.path.abspath(a.banco), a.exemplos)
    shutil.rmtree(SAIDA, ignore_errors=True)
    os.makedirs(SAIDA)
    print(f"Montando {os.path.relpath(SAIDA, RAIZ)}")
    codigos = banco_publico(desafios, os.path.join(SAIDA, "arena.sqlite3"))
    print(f"  banco público: {len(codigos)} desafio(s) {' '.join(codigos)}" if codigos
          else "  banco público VAZIO: pacote de teste com os desafios de EXEMPLO")
    print(f"  Python portátil {PYTHON_VERSAO} (sha256 {python_portatil(os.path.join(SAIDA, 'python'))[:16]}…)")
    copiar("api")
    for rel in ("arena/config.json", "arena/equipes.exemplo.json", "arena/exemplos",
                "scripts/servidor_local.py", "scripts/iniciar_offline.py"):
        copiar(rel)
    copiar(os.path.relpath(DIST, RAIZ), "dist")
    escrever("INICIAR.bat", INICIAR_BAT, crlf=True)
    escrever("LEIA-ME.txt", LEIA_ME, crlf=True)

    total = sum(os.path.getsize(os.path.join(r, n)) for r, _, ns in os.walk(SAIDA) for n in ns)
    print(f"Pasta pronta: {SAIDA} ({total / 1e6:.0f} MB)")
    if not a.sem_zip:
        arquivo = shutil.make_archive(SAIDA, "zip", OFFLINE, NOME)
        print(f"Zip: {arquivo} ({os.path.getsize(arquivo) / 1e6:.0f} MB)")
    print("No Windows: copie a pasta para o pendrive (ou descompacte o zip) e dê dois cliques em INICIAR.bat.")


if __name__ == "__main__":
    principal()
