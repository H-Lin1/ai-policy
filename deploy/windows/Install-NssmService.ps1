[CmdletBinding(SupportsShouldProcess)]
param(
  [Parameter(Mandatory = $true)] [string] $NssmPath,
  [Parameter(Mandatory = $true)] [string] $ProjectRoot,
  [string] $ServiceName = 'aipolicy-new-api',
  [switch] $Apply
)

$ErrorActionPreference = 'Stop'
$project = (Resolve-Path $ProjectRoot).Path
$python = Join-Path $project '.venv\Scripts\python.exe'
if (-not (Test-Path $NssmPath)) { throw 'nssm.exe was not found.' }
if (-not (Test-Path $python)) { throw 'Python virtual environment is missing.' }
if (-not $Apply) { Write-Output "nssm_service: preview (service=$ServiceName)"; exit 0 }

& $NssmPath install $ServiceName $python
if ($LASTEXITCODE -ne 0) { throw 'NSSM service creation failed.' }
& $NssmPath set $ServiceName AppParameters '-m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --workers 1'
& $NssmPath set $ServiceName AppDirectory $project
& $NssmPath set $ServiceName Start SERVICE_AUTO_START
& $NssmPath set $ServiceName AppExit Default Restart
& $NssmPath set $ServiceName AppStdout (Join-Path $project 'logs\api.stdout.log')
& $NssmPath set $ServiceName AppStderr (Join-Path $project 'logs\api.stderr.log')
& $NssmPath start $ServiceName
if ($LASTEXITCODE -ne 0) { throw 'NSSM service start failed.' }
Write-Output 'nssm_service: applied'
