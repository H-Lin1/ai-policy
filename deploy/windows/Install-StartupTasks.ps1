[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$newScript = 'E:\ai-policy\ai-policy\deploy\windows\start-new-api.cmd'
$legacyScript = 'E:\ai-policy\ai-policy\deploy\windows\start-legacy-site.cmd'
foreach ($path in @($newScript, $legacyScript)) {
  if (-not (Test-Path $path)) { throw "Startup script is missing: $path" }
}

# PostgreSQL is a native automatic Windows service.  The two Python processes
# are long-running console applications, so Task Scheduler launches them at
# startup without requiring an interactive Administrator session.
$principal = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet `
  -RestartCount 3 `
  -RestartInterval (New-TimeSpan -Minutes 1) `
  -ExecutionTimeLimit (New-TimeSpan -Days 3650) `
  -StartWhenAvailable

$legacyAction = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument "/d /c `"$legacyScript`""
$legacyTrigger = New-ScheduledTaskTrigger -AtStartup
$legacyTrigger.Delay = 'PT30S'
Register-ScheduledTask -TaskName 'aipolicy-legacy-site' -Action $legacyAction -Trigger $legacyTrigger -Settings $settings -Principal $principal -Force | Out-Null

$newAction = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument "/d /c `"$newScript`""
$newTrigger = New-ScheduledTaskTrigger -AtStartup
$newTrigger.Delay = 'PT2M'
Register-ScheduledTask -TaskName 'aipolicy-new-api' -Action $newAction -Trigger $newTrigger -Settings $settings -Principal $principal -Force | Out-Null

Get-ScheduledTask -TaskName 'aipolicy-legacy-site','aipolicy-new-api' | Select-Object TaskName,State
