$ErrorActionPreference = 'Stop'
$frontendRoot = Join-Path $PSScriptRoot 'frontend'
Set-Location -LiteralPath $frontendRoot

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw 'npm was not found. Install Node.js and npm, then open a new terminal.'
}
if (-not (Test-Path -LiteralPath (Join-Path $frontendRoot 'node_modules'))) {
    throw 'Frontend dependencies are missing. Run: npm install'
}

npm run dev
