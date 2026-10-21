"""Monta o pacote offline em offline/ para rodar a Arena local num Windows sem internet.

Roda numa máquina COM internet, Node e as dependências do npm (macOS, Linux ou Windows):
  python3 scripts/preparar_offline.py            # tudo (~750 MB, a maior parte é WSL + Ubuntu)
  python3 scripts/preparar_offline.py --sem-wsl  # só a Arena, para quem já tem WSL

Depois copie a pasta do repositório inteira (com offline/) e rode no Windows:
  powershell -ExecutionPolicy Bypass -File scripts\\instalar_windows.ps1

Conteúdo de offline/:
  dist/      build com ARENA_OFFLINE=1 (vite.config.js troca CDN e PyPI por /vendor) + dist/vendor/:
             Pyodide 0.25.0 (núcleo, micropip, packaging), wheels meupia-core/testes/grid, lucide, split.js
  python/    meupia-core extraído, para o juiz (vai no PYTHONPATH; o Ubuntu já traz o Python 3.12)
  wsl/       instalador do WSL (GitHub microsoft/WSL) e imagem do Ubuntu 24.04 (cloud-images.ubuntu.com)
  manifesto.json  sha256 de cada arquivo baixado, conferido pelo instalar_windows.ps1
Downloads já feitos (mesmo sha256) não são baixados de novo.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
import zipfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OFFLINE = os.path.join(RAIZ, "offline")
DIST = os.path.join(OFFLINE, "dist")
VENDOR = os.path.join(DIST, "vendor")

PYODIDE = "https://cdn.jsdelivr.net/pyodide/v0.25.0/full/"
PYODIDE_NUCLEO = ["pyodide.js", "pyodide.asm.js", "pyodide.asm.wasm", "python_stdlib.zip", "pyodide-lock.json"]
PYODIDE_PACOTES = ["micropip", "packaging"]  # o que loadPackage("micropip") busca
EXTRAS = {
    "lucide.min.js": "https://unpkg.com/lucide@0.469.0/dist/umd/lucide.min.js",
    "split.min.js": "https://cdnjs.cloudflare.com/ajax/libs/split.js/1.6.5/split.min.js",
    "wheels/meupia_grid-1.0.2-py3-none-any.whl":
        "https://cdn.jsdelivr.net/gh/meuPia/grid@main/dist/meupia_grid-1.0.2-py3-none-any.whl",
}
UBUNTU = "https://cloud-images.ubuntu.com/wsl/releases/24.04/current/"
UBUNTU_IMAGEM = "ubuntu-noble-wsl-amd64-wsl.rootfs.tar.gz"
WSL_RELEASE = "https://api.github.com/repos/microsoft/WSL/releases/latest"

manifesto = {}


def sha256(caminho):
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def ler_url(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "meupia-arena"})) as r:
        return r.read()


def baixar(url, destino, esperado=None):
    """Baixa para destino (caminho absoluto) e registra no manifesto. Com sha256 esperado, confere."""
    rel = os.path.relpath(destino, OFFLINE).replace(os.sep, "/")
    if os.path.exists(destino) and esperado and sha256(destino) == esperado:
        print(f"  já baixado  {rel}")
    else:
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        print(f"  baixando    {rel}")
        temporario = destino + ".parcial"
        req = urllib.request.Request(url, headers={"User-Agent": "meupia-arena"})
        with urllib.request.urlopen(req) as r, open(temporario, "wb") as f:
            shutil.copyfileobj(r, f, 1 << 20)
        os.replace(temporario, destino)
    obtido = sha256(destino)
    if esperado and obtido != esperado:
        os.remove(destino)
        sys.exit(f"ERRO: sha256 diferente em {rel}")
    manifesto[rel] = obtido
    return destino


def versao_core():
    req = open(os.path.join(RAIZ, "requirements.txt"), encoding="utf-8").read()
    wasm = open(os.path.join(RAIZ, "src", "engine", "wasm.js"), encoding="utf-8").read()
    v_req = re.search(r"^meupia-core==(\S+)", req, re.M).group(1)
    v_nav = re.search(r'let version = "([^"]+)"', wasm).group(1)
    if v_req != v_nav:
        sys.exit(f"ERRO: meupia-core {v_req} em requirements.txt e {v_nav} em src/engine/wasm.js")
    return v_req


def wheel_pypi(nome, versao):
    dados = json.loads(ler_url(f"https://pypi.org/pypi/{nome}/{versao}/json"))
    wheel = next(u for u in dados["urls"] if u["packagetype"] == "bdist_wheel")
    return wheel["url"], wheel["filename"], wheel["digests"]["sha256"]


def construir():
    print("Build offline (vite)")
    env = dict(os.environ, ARENA_OFFLINE="1")
    npx = "npx.cmd" if os.name == "nt" else "npx"
    subprocess.run([npx, "vite", "build", "--outDir", DIST, "--emptyOutDir"], cwd=RAIZ, env=env, check=True)


def vendor(core):
    print("Pyodide e bibliotecas do navegador")
    for nome in PYODIDE_NUCLEO:
        baixar(PYODIDE + nome, os.path.join(VENDOR, "pyodide", nome))
    trava = json.load(open(os.path.join(VENDOR, "pyodide", "pyodide-lock.json"), encoding="utf-8"))
    for nome in PYODIDE_PACOTES:
        pacote = trava["packages"][nome]
        baixar(PYODIDE + pacote["file_name"], os.path.join(VENDOR, "pyodide", pacote["file_name"]), pacote["sha256"])
    for rel, url in EXTRAS.items():
        baixar(url, os.path.join(VENDOR, rel))
    wheels = {}
    for nome, versao in (("meupia-core", core), ("meupia-testes", "1.0.0")):
        url, arquivo, digest = wheel_pypi(nome, versao)
        wheels[nome] = baixar(url, os.path.join(VENDOR, "wheels", arquivo), digest)
    return wheels


def python_do_juiz(wheel_core):
    print("meupia-core para o juiz (offline/python)")
    destino = os.path.join(OFFLINE, "python")
    shutil.rmtree(destino, ignore_errors=True)
    with zipfile.ZipFile(wheel_core) as z:
        z.extractall(destino)


def wsl():
    print("WSL e Ubuntu 24.04")
    somas = dict(reversed(linha.split()) for linha in ler_url(UBUNTU + "SHA256SUMS").decode().splitlines() if linha.strip())
    baixar(UBUNTU + UBUNTU_IMAGEM, os.path.join(OFFLINE, "wsl", UBUNTU_IMAGEM), somas[UBUNTU_IMAGEM])
    release = json.loads(ler_url(WSL_RELEASE))
    msi = next(a for a in release["assets"] if re.fullmatch(r"wsl\.[\d.]+\.x64\.msi", a["name"]))
    esperado = (msi.get("digest") or "").removeprefix("sha256:") or None
    destino = os.path.join(OFFLINE, "wsl", msi["name"])
    for antigo in os.listdir(os.path.dirname(destino)):
        if antigo.endswith(".msi") and antigo != msi["name"]:
            os.remove(os.path.join(os.path.dirname(destino), antigo))
    if os.path.exists(destino) and os.path.getsize(destino) == msi["size"] and not esperado:
        print(f"  já baixado  wsl/{msi['name']}")
        manifesto[f"wsl/{msi['name']}"] = sha256(destino)
    else:
        baixar(msi["browser_download_url"], destino, esperado)


def principal():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--sem-wsl", action="store_true", help="não baixa o instalador do WSL nem a imagem do Ubuntu")
    args = p.parse_args()

    core = versao_core()
    anterior = os.path.join(OFFLINE, "manifesto.json")
    if os.path.exists(anterior):
        # preserva o que não for baixado de novo nesta rodada (ex.: --sem-wsl depois de um completo)
        manifesto.update({k: v for k, v in json.load(open(anterior, encoding="utf-8"))["arquivos"].items()
                          if k.startswith("wsl/") and os.path.exists(os.path.join(OFFLINE, k))})
    construir()
    wheels = vendor(core)
    python_do_juiz(wheels["meupia-core"])
    if not args.sem_wsl:
        wsl()
    with open(anterior, "w", encoding="utf-8") as f:
        json.dump({"meupiaCore": core, "arquivos": dict(sorted(manifesto.items()))}, f, indent=2)
    total = sum(os.path.getsize(os.path.join(OFFLINE, k)) for k in manifesto)
    print(f"\nPacote offline pronto em {OFFLINE} ({total / 1e6:.0f} MB). Copie a pasta do repositório inteira.")


if __name__ == "__main__":
    principal()
