$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$env:PYTHONPATH = $projectRoot

$venvPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
$pythonExecutable = $null
if (Test-Path -LiteralPath $venvPython) {
    & $venvPython -c 'import fastapi, uvicorn' *> $null
    if ($LASTEXITCODE -eq 0) { $pythonExecutable = $venvPython }
}

if (-not $pythonExecutable) {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        & $pythonCommand.Source -c 'import fastapi, uvicorn' *> $null
        if ($LASTEXITCODE -eq 0) { $pythonExecutable = $pythonCommand.Source }
    }
}

if (-not $pythonExecutable) {
    throw 'FastAPI and Uvicorn are not installed. Run: python -m pip install -r requirements.txt'
}

& $pythonExecutable -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
