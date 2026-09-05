[CmdletBinding()]
param([Parameter(Mandatory = $true)] [string] $ProjectRoot)

$ErrorActionPreference = 'Stop'
$project = (Resolve-Path $ProjectRoot).Path
$python = Join-Path $project '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) { throw 'Python virtual environment is missing.' }
Set-Location $project
& $python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --workers 1
