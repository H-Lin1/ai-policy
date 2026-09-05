[CmdletBinding()]
param([string] $TaskName = 'aipolicy-new-api')

$ErrorActionPreference = 'Stop'
$script = 'E:\ai-policy\ai-policy\deploy\windows\Start-CondaApi.ps1'
if (-not (Test-Path $script)) { throw "Startup script is missing: $script" }
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$script`""
$trigger = New-ScheduledTaskTrigger -AtStartup
$settings = New-ScheduledTaskSettingsSet -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit (New-TimeSpan -Days 3650) -StartWhenAvailable
$principal = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null
Start-ScheduledTask -TaskName $TaskName
Start-Sleep -Seconds 6
Write-Output "api_task=$TaskName"
Get-ScheduledTask -TaskName $TaskName | Select-Object TaskName,State
Get-NetTCPConnection -State Listen -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object LocalAddress,LocalPort,OwningProcess
