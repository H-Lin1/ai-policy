[CmdletBinding()]
param(
  [string] $ApiBaseUrl = 'http://127.0.0.1:8000/new-api/v1',
  [string] $PublicBaseUrl = 'https://aipolicy.bnu.edu.cn'
)

$ErrorActionPreference = 'Stop'
$api = $ApiBaseUrl.TrimEnd('/')
$public = $PublicBaseUrl.TrimEnd('/')
$live = Invoke-RestMethod "$api/health/live"
$ready = Invoke-RestMethod "$api/health/ready"
$model = Invoke-RestMethod "$api/ai/readiness"
if ($live.status -ne 'ok') { throw 'API liveness check failed.' }
if ($ready.status -ne 'ready' -or $ready.checks.database -ne 'ok' -or $ready.checks.authentication -ne 'configured') { throw 'API readiness check failed.' }
if ($model.status -ne 'ready') { throw 'Model readiness check failed.' }
foreach ($url in @("$public/", "$public/new/", "$public/new/login", "$public/new-api/v1/health/live")) {
  $response = Invoke-WebRequest -UseBasicParsing $url
  if ($response.StatusCode -ne 200) { throw "Public check failed: $url" }
}
Write-Output 'deployment_test: passed'
