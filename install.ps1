<#
.SYNOPSIS
    Cross-platform (Windows) installer for Obsidia (cognis-vanguard).
.DESCRIPTION
    Idempotent: safe to re-run. Creates a local .venv and installs the CLI
    in editable mode, then verifies the 'obsidia' console script.
#>
$ErrorActionPreference = 'Stop'

$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Here

# 1. Pick a Python interpreter (prefer 'python', fall back to 'py -3').
$PyExe = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $PyExe = 'python'
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $PyExe = 'py'
} else {
    Write-Error "Python 3.9+ is required but was not found on PATH. Install from https://www.python.org/downloads/ (check 'Add python.exe to PATH') and re-run install.ps1."
}

Write-Host ">> Using interpreter: $(& $PyExe --version) ($PyExe)"

# 2. Create the virtual environment if it does not already exist.
if (-not (Test-Path ".venv")) {
    Write-Host ">> Creating virtual environment at .venv"
    & $PyExe -m venv .venv
} else {
    Write-Host ">> Reusing existing virtual environment at .venv"
}

$VenvPy = Join-Path $Here ".venv\Scripts\python.exe"

# 3. Upgrade pip tooling.
Write-Host ">> Upgrading pip"
& $VenvPy -m pip install --upgrade pip | Out-Null

# 4. Install runtime deps from requirements*.txt if any exist.
foreach ($req in @("requirements.txt", "requirements-dev.txt")) {
    if (Test-Path $req) {
        Write-Host ">> Installing from $req"
        & $VenvPy -m pip install -r $req
    }
}

# 5. Editable install. Include the 'dev' extra only if it is declared.
$pyproject = Get-Content pyproject.toml -Raw -ErrorAction SilentlyContinue
if ($pyproject -match '\[project\.optional-dependencies\]') {
    Write-Host ">> Installing package (editable) with dev extra"
    try { & $VenvPy -m pip install -e ".[dev]" }
    catch { & $VenvPy -m pip install -e . }
} else {
    Write-Host ">> Installing package (editable)"
    & $VenvPy -m pip install -e .
}

# 6. Verify the console script is callable.
$Obsidia = Join-Path $Here ".venv\Scripts\obsidia.exe"
Write-Host ">> Verifying installation: obsidia --help"
& $Obsidia --help | Out-Null
Write-Host ">> OK: 'obsidia' console script is installed and runnable."

# 7. Next steps.
Write-Host @"

============================================================
 Obsidia (cognis-vanguard) is installed.
============================================================
 Activate the virtual environment:
   PowerShell :   .\.venv\Scripts\Activate.ps1
   cmd.exe    :   .\.venv\Scripts\activate.bat

 Then run the CLI:
   obsidia --help
   obsidia demo                 # end-to-end demo on bundled reporting
   obsidia demo-fusion          # full multi-INT fusion / COP demo

 Or without activating:
   .\.venv\Scripts\obsidia.exe demo
============================================================
"@
