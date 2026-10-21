<#
.SYNOPSIS
  Instala e sobe o meuPiá Arena local num Windows 11 SEM internet, a partir do pacote offline.

.DESCRIPTION
  Antes, numa máquina com internet: python3 scripts/preparar_offline.py (gera a pasta offline/).
  Copie a pasta do repositório inteira, com offline/, para o Windows (de preferência no C:).

  O servidor não roda no Windows nativo (o store local usa fcntl; o juiz usa SIGALRM, setitimer,
  resource e preexec_fn), por isso vai numa distribuição WSL própria, importada do pacote:

    1. confere o sha256 de cada arquivo do pacote (offline/manifesto.json);
    2. sem WSL: ativa a Plataforma de Máquina Virtual e instala o WSL do pacote
       (precisa de PowerShell como administrador e, em geral, reiniciar e rodar de novo);
    3. sem a distribuição: importa o Ubuntu 24.04 do pacote (já traz o Python 3.12);
    4. sobe o servidor (modo ensaio, banco em arquivo JSON): o build offline (offline/dist) não
       chama nenhuma CDN, e o juiz usa o meupia-core de offline/python.

  Abra http://localhost:8787 no navegador do Windows (o WSL encaminha o localhost).

.PARAMETER SoInstalar
  Para depois de instalar, sem subir o servidor.

.PARAMETER Distro
  Distribuição do WSL a usar. Padrão: meuPiaArena (importada do pacote). Para usar uma que já existe
  (ex.: Ubuntu, com Python 3.10+), passe o nome dela; o pacote não precisa da imagem do Ubuntu.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\instalar_windows.ps1

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\instalar_windows.ps1 -SoInstalar
#>
[CmdletBinding()]
param(
    [switch]$SoInstalar,
    [string]$Distro = 'meuPiaArena'
)

$ErrorActionPreference = 'Stop'
$Raiz = Split-Path -Parent $PSScriptRoot
$Offline = Join-Path $Raiz 'offline'
$PastaDistro = Join-Path $env:LOCALAPPDATA "meuPiaArena\$Distro"
$REINICIAR = 3010  # código de saída do dism/msiexec quando falta reiniciar

function Passo([string]$texto) { Write-Host "`n==> $texto" -ForegroundColor Cyan }

function Eh-Administrador {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    ([Security.Principal.WindowsPrincipal]$id).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Wsl-Instalado {
    # o wsl.exe que vem no Windows sem o pacote do WSL não conhece --version
    if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) { return $false }
    & wsl.exe --version *> $null
    $LASTEXITCODE -eq 0
}

function Distros-Instaladas {
    # wsl -l -q escreve em UTF-16: sobram NULs quando o PowerShell lê como texto
    $saida = & wsl.exe -l -q 2>$null
    if ($LASTEXITCODE -ne 0) { return @() }
    @($saida | ForEach-Object { ($_ -replace "`0", '').Trim() } | Where-Object { $_ })
}

function Arquivo-Do-Pacote([string]$padrao) {
    Get-ChildItem -Path (Join-Path $Offline 'wsl') -Filter $padrao -ErrorAction SilentlyContinue | Select-Object -First 1
}

Passo "Pacote offline em $Offline"
$manifesto = Join-Path $Offline 'manifesto.json'
if (-not (Test-Path $manifesto)) {
    throw "Pacote offline não encontrado. Numa máquina com internet, rode: python3 scripts/preparar_offline.py"
}
$arquivos = (Get-Content $manifesto -Raw -Encoding UTF8 | ConvertFrom-Json).arquivos
foreach ($item in $arquivos.PSObject.Properties) {
    $caminho = Join-Path $Offline ($item.Name -replace '/', '\')
    if (-not (Test-Path $caminho)) { throw "faltando no pacote: offline/$($item.Name)" }
    if ((Get-FileHash -Algorithm SHA256 $caminho).Hash -ne $item.Value) {
        throw "arquivo corrompido (sha256 diferente): offline/$($item.Name). Copie o pacote de novo."
    }
}
foreach ($necessario in 'dist\ide.html', 'python\meuPia') {
    if (-not (Test-Path (Join-Path $Offline $necessario))) { throw "faltando no pacote: offline\$necessario" }
}
Write-Host "$(@($arquivos.PSObject.Properties).Count) arquivos conferidos."

Passo 'WSL'
if (-not (Wsl-Instalado)) {
    $msi = Arquivo-Do-Pacote 'wsl.*.x64.msi'
    if (-not $msi) { throw 'WSL não instalado e o pacote não tem o instalador (foi gerado com --sem-wsl).' }
    if (-not (Eh-Administrador)) {
        throw 'WSL não instalado. Abra o PowerShell como administrador e rode o script de novo.'
    }
    & dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
    $dism = $LASTEXITCODE
    if ($dism -ne 0 -and $dism -ne $REINICIAR) { throw "dism falhou ao ativar a Plataforma de Máquina Virtual (saída $dism)" }
    Write-Host "Instalando $($msi.Name)..."
    $instalacao = Start-Process msiexec.exe -ArgumentList '/i', "`"$($msi.FullName)`"", '/qn', '/norestart' -Wait -PassThru
    if ($instalacao.ExitCode -ne 0 -and $instalacao.ExitCode -ne $REINICIAR) {
        throw "a instalação do WSL falhou (msiexec saiu com $($instalacao.ExitCode))"
    }
    if ($dism -eq $REINICIAR -or $instalacao.ExitCode -eq $REINICIAR -or -not (Wsl-Instalado)) {
        Write-Host "`nWSL instalado. Reinicie o Windows e rode este script de novo (não precisa ser administrador)." -ForegroundColor Yellow
        exit 0
    }
}
Write-Host ((& wsl.exe --version | Select-Object -First 1) -replace "`0", '')

Passo "Distribuição $Distro"
if ((Distros-Instaladas) -notcontains $Distro) {
    $imagem = Arquivo-Do-Pacote '*.rootfs.tar.gz'
    if (-not $imagem) {
        throw "A distribuição '$Distro' não existe e o pacote não tem a imagem do Ubuntu. Use -Distro com uma que exista (wsl -l)."
    }
    New-Item -ItemType Directory -Force -Path $PastaDistro | Out-Null
    Write-Host "Importando $($imagem.Name) em $PastaDistro (leva um minuto)..."
    & wsl.exe --import $Distro $PastaDistro $imagem.FullName --version 2
    if ($LASTEXITCODE -ne 0) {
        throw @"
wsl --import falhou (saída $LASTEXITCODE). Se o erro falar em virtualização (HCS, 0x80370102):
ative a virtualização na BIOS/UEFI e a 'Plataforma de Máquina Virtual' (rode este script como administrador).
"@
    }
}
$python = (& wsl.exe -d $Distro -- python3 -c "import sys; print('%d.%d' % sys.version_info[:2])") -join ''
if ($LASTEXITCODE -ne 0 -or -not ($python -match '^\d+\.\d+$') -or [version]$python -lt [version]'3.10') {
    throw "A distribuição '$Distro' precisa do Python 3.10+ (python3). Encontrado: '$python'."
}
Write-Host "Python $python no $Distro."

Write-Host "`nInstalação pronta." -ForegroundColor Green
if ($SoInstalar) {
    Write-Host 'Para subir o servidor: powershell -ExecutionPolicy Bypass -File scripts\instalar_windows.ps1'
    exit 0
}

Passo 'Servidor local em http://localhost:8787 (Ctrl+C para parar)'
Write-Host 'Equipes: TROQUE-ESTE-CODIGO-1 / -2  ·  banca: /admin.html, token admin'
# env -u: nunca o banco do evento, mesmo que o WSLENV traga variáveis do Windows
& wsl.exe -d $Distro --cd $Raiz -- env `
    -u SUPABASE_URL -u SUPABASE_SERVICE_ROLE_KEY -u SUPABASE_SECRET_KEY `
    -u KV_REST_API_URL -u KV_REST_API_TOKEN -u UPSTASH_REDIS_REST_URL -u UPSTASH_REDIS_REST_TOKEN `
    ARENA_MODO=ensaio ADMIN_TOKEN=admin ARENA_DIST=offline/dist PYTHONPATH=offline/python `
    python3 scripts/servidor_local.py
