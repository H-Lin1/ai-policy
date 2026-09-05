[CmdletBinding(SupportsShouldProcess)]
param(
  [Parameter(Mandatory = $true)] [string] $PostgresBin,
  [string] $DatabaseName = 'aipolicy_new',
  [string] $ApplicationRole = 'aipolicy_app',
  [string] $DatabaseHost = '127.0.0.1',
  [int] $DatabasePort = 5432,
  [switch] $Apply
)

$ErrorActionPreference = 'Stop'
$psql = Join-Path $PostgresBin 'psql.exe'
if (-not (Test-Path $psql)) { throw "psql.exe was not found under PostgresBin." }

if (-not $Apply) {
  Write-Output "postgres_init: preview (pass -Apply to create role and database)"
  Write-Output "postgres_init: database=$DatabaseName role=$ApplicationRole host=$DatabaseHost port=$DatabasePort"
  exit 0
}

$rolePassword = Read-Host 'Enter a new password for the application database role' -AsSecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($rolePassword)
try { $plainPassword = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr) }
finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
if ([string]::IsNullOrWhiteSpace($plainPassword) -or $plainPassword.Length -lt 24) {
  throw 'Use a database password of at least 24 characters.'
}

# The command uses psql variable substitution: neither the application password
# nor the DSN is stored in this script or in project source control.
$sql = @"
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'role_name') THEN
    EXECUTE format('CREATE ROLE %I LOGIN PASSWORD %L NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT', :'role_name', :'role_password');
  END IF;
END \$\$;
"@

& $psql -h $DatabaseHost -p $DatabasePort -U postgres -d postgres --set=ON_ERROR_STOP=1 --set=role_name=$ApplicationRole --set=role_password=$plainPassword -c $sql
if ($LASTEXITCODE -ne 0) { throw 'Application role creation failed.' }
$databaseExists = (& $psql -h $DatabaseHost -p $DatabasePort -U postgres -d postgres --set=ON_ERROR_STOP=1 -tAc "SELECT EXISTS (SELECT 1 FROM pg_database WHERE datname = '$DatabaseName')").Trim()
if ($LASTEXITCODE -ne 0) { throw 'Database existence check failed.' }
if ($databaseExists -ne 't') {
  & $psql -h $DatabaseHost -p $DatabasePort -U postgres -d postgres --set=ON_ERROR_STOP=1 -c "CREATE DATABASE $DatabaseName OWNER $ApplicationRole ENCODING 'UTF8'"
  if ($LASTEXITCODE -ne 0) { throw 'Database creation failed.' }
}
Write-Output 'postgres_init: applied'
