[CmdletBinding(SupportsShouldProcess)]
param(
  [Parameter(Mandatory = $true)] [string] $ProjectRoot,
  [Parameter(Mandatory = $true)] [string] $DemoPassword,
  [switch] $LoadFixtures,
  [switch] $Apply
)

$ErrorActionPreference = 'Stop'
$project = (Resolve-Path $ProjectRoot).Path
$python = Join-Path $project '.venv\Scripts\python.exe'
$backend = Join-Path $project 'backend'
$envFile = Join-Path $project '.env'
foreach ($path in @($python, $backend, $envFile)) {
  if (-not (Test-Path $path)) { throw "Required path is missing: $path" }
}
if (-not $Apply) {
  Write-Output 'application_init: preview (pass -Apply to run migrations and create demo users)'
  exit 0
}

# Settings loads .env from the project root.  Demo password exists only in the
# process environment for this invocation and is never written to .env.
$env:LOCAL_DEMO_PASSWORD = $DemoPassword
Push-Location $backend
try {
  & $python -m alembic -c alembic.ini upgrade head
  if ($LASTEXITCODE -ne 0) { throw 'Alembic migration failed.' }
  & $python -m scripts.init_local_demo --apply-local-demo --confirm
  if ($LASTEXITCODE -ne 0) { throw 'Local demo initialization failed.' }
  if ($LoadFixtures) {
    & $python -m scripts.init_policy --apply-policy-fixture --confirm
    if ($LASTEXITCODE -ne 0) { throw 'Policy fixture initialization failed.' }
    & $python -m scripts.init_qa --apply-qa-fixture --confirm
    if ($LASTEXITCODE -ne 0) { throw 'Historical Q&A fixture initialization failed.' }
  }
} finally {
  Remove-Item Env:LOCAL_DEMO_PASSWORD -ErrorAction SilentlyContinue
  Pop-Location
}
Write-Output 'application_init: applied'
