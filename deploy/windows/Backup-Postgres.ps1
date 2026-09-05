[CmdletBinding(SupportsShouldProcess)]
param(
  [Parameter(Mandatory = $true)] [string] $PostgresBin,
  [Parameter(Mandatory = $true)] [string] $BackupDirectory,
  [string] $DatabaseName = 'aipolicy_new',
  [string] $DatabaseHost = '127.0.0.1',
  [int] $DatabasePort = 5432,
  [string] $DatabaseUser = 'aipolicy_app',
  [int] $KeepDays = 14,
  [switch] $Apply
)

$ErrorActionPreference = 'Stop'
$pgDump = Join-Path $PostgresBin 'pg_dump.exe'
if (-not (Test-Path $pgDump)) { throw 'pg_dump.exe was not found.' }
if (-not $Apply) { Write-Output "postgres_backup: preview (database=$DatabaseName, retention=$KeepDays days)"; exit 0 }
New-Item -ItemType Directory -Force -Path $BackupDirectory | Out-Null
$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$target = Join-Path $BackupDirectory "$DatabaseName-$timestamp.dump"
& $pgDump -h $DatabaseHost -p $DatabasePort -U $DatabaseUser -Fc -f $target $DatabaseName
if ($LASTEXITCODE -ne 0) { throw 'pg_dump failed.' }
Get-ChildItem $BackupDirectory -Filter "$DatabaseName-*.dump" | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-$KeepDays) } | Remove-Item -Force
Write-Output "postgres_backup: created $target"
