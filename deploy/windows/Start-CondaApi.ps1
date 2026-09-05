$ErrorActionPreference = 'Stop'
$project = 'E:\ai-policy\ai-policy'
$python = 'C:\ProgramData\miniconda3\envs\aipolicy-py\python.exe'
if (-not (Test-Path $python)) { throw 'aipolicy-py Python is missing.' }
Set-Location $project
& $python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --workers 1
exit $LASTEXITCODE
