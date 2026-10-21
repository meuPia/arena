<#
.SYNOPSIS
  Prepara um Windows para rodar o meuPiá Arena local (npm run local), via WSL.

.DESCRIPTION
  O servidor não roda no Windows nativo: o store local usa fcntl (o login já falha) e o juiz usa
  SIGALRM, setitimer, resource e preexec_fn. Por isso o script usa o WSL (Ubuntu):

    1. sem WSL/Ubuntu: instala (precisa de PowerShell como administrador e, às vezes, reiniciar);
    2. no Ubuntu, como root: python3, python3-venv, pip e Node.js 22 (NodeSource) se faltar;
    3. na pasta do repositório: npm install, .venv com requirements-dev.txt e confere se o
       meupia-core é a mesma versão do navegador (src/engine/wasm.js).

  O WSL encaminha o localhost: com -Rodar, abra http://localhost:8787 no navegador do Windows.

.PARAMETER Rodar
  Depois de instalar, sobe o servidor local (modo ensaio, banco em arquivo JSON, sem Supabase).

.PARAMETER Distro
  Distribuição do WSL (padrão: Ubuntu).

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\instalar_windows.ps1

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\instalar_windows.ps1 -Rodar
#>
[CmdletBinding()]
param(
    [switch]$Rodar,
    [string]$Distro = 'Ubuntu'
)

$ErrorActionPreference = 'Stop'
$Raiz = Split-Path -Parent $PSScriptRoot

function Passo([string]$texto) { Write-Host "`n==> $texto" -ForegroundColor Cyan }

function Eh-Administrador {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    ([Security.Principal.WindowsPrincipal]$id).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Distros-Instaladas {
    # wsl -l -q escreve em UTF-16: sobram NULs quando o PowerShell lê como texto
    $saida = & wsl.exe -l -q 2>$null
    if ($LASTEXITCODE -ne 0) { return @() }
    @($saida | ForEach-Object { ($_ -replace "`0", '').Trim() } | Where-Object { $_ })
}

# Roda um script bash no WSL, na pasta do repositório. Vai em base64 para não depender de aspas
# nem de CRLF na linha de comando do wsl.exe.
function No-Wsl([string]$script, [switch]$Root) {
    $bytes = [Text.Encoding]::UTF8.GetBytes(($script -replace "`r", ''))
    $b64 = [Convert]::ToBase64String($bytes)
    $argumentos = @('-d', $Distro)
    if ($Root) { $argumentos += @('-u', 'root') }
    $argumentos += @('--cd', $Raiz, '--', 'bash', '-c', "echo $b64 | base64 -d | bash")
    & wsl.exe @argumentos
    if ($LASTEXITCODE -ne 0) { throw "o passo no WSL falhou (saída $LASTEXITCODE)" }
}

$SistemaBash = @'
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update -q
apt-get install -y -q ca-certificates curl python3 python3-venv python3-pip
# Vite 8 pede Node 20.19+ ou 22.12+
if ! command -v node >/dev/null || ! node -e 'const [a,b]=process.versions.node.split(".").map(Number); process.exit(a>22||(a===22&&b>=12)||(a===20&&b>=19)?0:1)'; then
  curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
  apt-get install -y -q nodejs
fi
echo "node $(node --version), npm $(npm --version), $(python3 --version)"
'@

$ProjetoBash = @'
set -euo pipefail
# node_modules instalado pelo npm do Windows tem binários win32 (rolldown/esbuild): refaz no Linux
if compgen -G 'node_modules/@*/*win32*' >/dev/null; then
  echo "node_modules veio do Windows: reinstalando no Linux"
  rm -rf node_modules
fi
npm install
[ -x .venv/bin/python ] || python3 -m venv .venv
.venv/bin/python -m pip install -q --upgrade pip
.venv/bin/python -m pip install -q -r requirements-dev.txt
core=$(.venv/bin/python -c "import importlib.metadata as m; print(m.version('meupia-core'))")
navegador=$(sed -n 's/.*let version = "\(.*\)".*/\1/p' src/engine/wasm.js)
echo "meupia-core $core (navegador: $navegador)"
if [ "$core" != "$navegador" ]; then
  echo "ERRO: requirements.txt e src/engine/wasm.js com versões diferentes do meupia-core" >&2
  exit 1
fi
'@

$RodarBash = @'
set -euo pipefail
. .venv/bin/activate
# garante o banco em arquivo JSON local, nunca o do evento
unset SUPABASE_URL SUPABASE_SERVICE_ROLE_KEY SUPABASE_SECRET_KEY KV_REST_API_URL KV_REST_API_TOKEN UPSTASH_REDIS_REST_URL UPSTASH_REDIS_REST_TOKEN
npm run local
'@

Passo "WSL ($Distro)"
if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue) -or (Distros-Instaladas) -notcontains $Distro) {
    if (-not (Eh-Administrador)) {
        throw "WSL/$Distro não encontrado. Abra o PowerShell como administrador e rode o script de novo."
    }
    & wsl.exe --install -d $Distro
    if ($LASTEXITCODE -ne 0) { throw "wsl --install falhou (saída $LASTEXITCODE)" }
    Write-Host @"

WSL instalado. Agora:
  1. reinicie o Windows, se ele pedir;
  2. abra o '$Distro' no menu Iniciar uma vez e crie o usuário e a senha do Linux;
  3. rode este script de novo (não precisa ser como administrador).
"@ -ForegroundColor Yellow
    exit 0
}

$uid = (& wsl.exe -d $Distro -- id -u) -join ''
if ($uid.Trim() -eq '0') {
    Write-Warning "O usuário padrão do $Distro é o root. Abra o '$Distro' uma vez e crie o usuário do Linux."
}

Passo 'Node.js e Python no Linux (como root)'
No-Wsl $SistemaBash -Root

Passo "Dependências do projeto em $Raiz"
No-Wsl $ProjetoBash

Write-Host "`nPronto." -ForegroundColor Green
if (-not $Rodar) {
    Write-Host "Para subir o servidor: powershell -ExecutionPolicy Bypass -File scripts\instalar_windows.ps1 -Rodar"
    Write-Host "Ou, dentro do WSL, na pasta do repositório: . .venv/bin/activate && npm run local"
    exit 0
}

Passo 'Servidor local em http://localhost:8787 (Ctrl+C para parar)'
Write-Host 'Equipes: TROQUE-ESTE-CODIGO-1 / -2  ·  banca: /admin.html, token admin'
No-Wsl $RodarBash
