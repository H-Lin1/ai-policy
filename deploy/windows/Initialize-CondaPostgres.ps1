[CmdletBinding()]
param(
  [string] $ProjectRoot = 'E:\ai-policy\ai-policy',
  [string] $PostgresPrefix = 'C:\ProgramData\miniconda3\envs\aipolicy-db',
  [string] $DataDirectory = 'E:\ai-policy\postgres-data',
  [string] $ServiceName = 'aipolicy-postgresql'
)

$ErrorActionPreference = 'Stop'
$pgBin = Join-Path $PostgresPrefix 'Library\bin'
$initDb = Join-Path $pgBin 'initdb.exe'
$pgCtl = Join-Path $pgBin 'pg_ctl.exe'
$psql = Join-Path $pgBin 'psql.exe'
foreach ($path in @($initDb, $pgCtl, $psql, $ProjectRoot)) {
  if (-not (Test-Path $path)) { throw "Required path is missing: $path" }
}
if (Test-Path $DataDirectory) { throw "Data directory already exists: $DataDirectory" }
if (Get-Service -Name $ServiceName -ErrorAction SilentlyContinue) {
  throw "Windows service already exists: $ServiceName"
}

function New-RandomHex([int] $ByteCount) {
  $bytes = New-Object byte[] $ByteCount
  $rng = New-Object System.Security.Cryptography.RNGCryptoServiceProvider
  try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
  return ([BitConverter]::ToString($bytes)).Replace('-', '').ToLowerInvariant()
}

function Save-ProtectedSecret([string] $Value, [string] $Path) {
  ConvertTo-SecureString $Value -AsPlainText -Force | Export-Clixml -LiteralPath $Path
}

function Set-EnvValue([string[]] $Lines, [string] $Key, [string] $Value) {
  $pattern = '^' + [regex]::Escape($Key) + '='
  $found = $false
  for ($index = 0; $index -lt $Lines.Count; $index++) {
    if ($Lines[$index] -match $pattern) {
      $Lines[$index] = "$Key=$Value"
      $found = $true
    }
  }
  if (-not $found) { $Lines += "$Key=$Value" }
  return ,$Lines
}

$secretDirectory = Join-Path (Split-Path $ProjectRoot -Parent) 'secrets'
New-Item -ItemType Directory -Force -Path $secretDirectory | Out-Null
$postgresPassword = New-RandomHex 32
$applicationPassword = New-RandomHex 32
$jwtSecret = New-RandomHex 48
$demoPassword = New-RandomHex 16
Save-ProtectedSecret $postgresPassword (Join-Path $secretDirectory 'postgres-admin.clixml')
Save-ProtectedSecret $demoPassword (Join-Path $secretDirectory 'demo-password.clixml')

$passwordFile = Join-Path $env:TEMP ("aipolicy-pg-" + [guid]::NewGuid().ToString('N') + '.txt')
[IO.File]::WriteAllText($passwordFile, $postgresPassword, (New-Object Text.UTF8Encoding($false)))
try {
  & $initDb -D $DataDirectory -U postgres --pwfile=$passwordFile --auth-host=scram-sha-256 --auth-local=scram-sha-256 --encoding=UTF8 --locale=C
  if ($LASTEXITCODE -ne 0) { throw 'initdb failed.' }
} finally {
  Remove-Item $passwordFile -Force -ErrorAction SilentlyContinue
}

$postgresConfig = Join-Path $DataDirectory 'postgresql.conf'
Add-Content -LiteralPath $postgresConfig -Value "`nlisten_addresses = '127.0.0.1'`nport = 5432`npassword_encryption = 'scram-sha-256'`n"
& $pgCtl register -N $ServiceName -D $DataDirectory -S auto
if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL service registration failed.' }
Start-Service -Name $ServiceName

$env:PGPASSWORD = $postgresPassword
try {
  & $psql -h 127.0.0.1 -p 5432 -U postgres -d postgres -v ON_ERROR_STOP=1 -c "CREATE ROLE aipolicy_app LOGIN PASSWORD '$applicationPassword' NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT"
  if ($LASTEXITCODE -ne 0) { throw 'Application role creation failed.' }
  & $psql -h 127.0.0.1 -p 5432 -U postgres -d postgres -v ON_ERROR_STOP=1 -c 'CREATE DATABASE aipolicy_new OWNER aipolicy_app ENCODING ''UTF8'''
  if ($LASTEXITCODE -ne 0) { throw 'Application database creation failed.' }
} finally {
  Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
}

$envFile = Join-Path $ProjectRoot '.env'
if (Test-Path $envFile) {
  $backup = "$envFile.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
  Copy-Item -LiteralPath $envFile -Destination $backup
  $lines = @(Get-Content -LiteralPath $envFile)
} else {
  $lines = @()
}
$settings = [ordered]@{
  APP_ENV = 'production'
  API_PREFIX = '/new-api/v1'
  HOST = '127.0.0.1'
  PORT = '8000'
  DATABASE_MODE = 'standalone'
  DATABASE_URL = "postgresql+psycopg://aipolicy_app:$applicationPassword@127.0.0.1:5432/aipolicy_new"
  AUTH_REQUIRED = 'true'
  AUTH_MODE = 'local'
  LOCAL_AUTH_JWT_SECRET = $jwtSecret
  LOCAL_AUTH_JWT_ISSUER = 'aipolicy-new'
  LOCAL_AUTH_JWT_AUDIENCE = 'aipolicy-new-api'
  LOCAL_AUTH_TOKEN_TTL_SECONDS = '28800'
  CORS_ORIGINS = 'https://aipolicy.bnu.edu.cn'
  ALLOW_CORS_WILDCARD = 'false'
  ENABLE_MOCKS = 'false'
  CLASSIFIER_MODEL_PATH = 'E:/ai-policy/ai-policy/backend/models/sz/sz_classifier.pth'
  CLASSIFIER_TOKENIZER_PATH = 'E:/ai-policy/ai-policy/backend/models/hfl_chinese_bert_wwm'
  CLASSIFIER_LABEL_BINDINGS_PATH = 'E:/ai-policy/ai-policy/backend/models/sz/department_label_bindings.json'
  CLASSIFIER_DEPARTMENT_EMBEDDINGS_PATH = 'E:/ai-policy/ai-policy/backend/models/sz/10000szdepartment_embeddings.pth'
  CLASSIFIER_MODEL_VERSION = 'sz-tcn-bert-v1'
  CLASSIFIER_SUPPORTED_REGIONS = 'sz'
}
foreach ($entry in $settings.GetEnumerator()) {
  $lines = Set-EnvValue $lines $entry.Key $entry.Value
}
[IO.File]::WriteAllLines($envFile, $lines, (New-Object Text.UTF8Encoding($false)))

Write-Output 'conda_postgres_init: applied'
Write-Output "postgres_service=$ServiceName"
Write-Output 'postgres_listener=127.0.0.1:5432'
Write-Output "protected_admin_secret=$(Join-Path $secretDirectory 'postgres-admin.clixml')"
Write-Output "protected_demo_password=$(Join-Path $secretDirectory 'demo-password.clixml')"
