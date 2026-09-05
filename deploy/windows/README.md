# Windows Server deployment: standalone PostgreSQL

This directory deploys the new system without changing the old site.  It assumes:

```text
https://aipolicy.bnu.edu.cn/          old website (unchanged)
https://aipolicy.bnu.edu.cn/new/      new Vite frontend
https://aipolicy.bnu.edu.cn/new-api/  new FastAPI backend
```

## Server layout

```text
D:\apps\aipolicy-old\              existing site: do not move or edit
D:\apps\aipolicy-new\              this repository checkout
D:\apps\aipolicy-new\backend\models\  supplied model files
D:\apps\aipolicy-new\.env          server-only configuration
D:\apps\aipolicy-backups\          PostgreSQL dumps (not under the app folder)
```

Install PostgreSQL 16 or later, Python 3.11 x64, Node.js 20 LTS, and IIS URL
Rewrite plus Application Request Routing (ARR). PostgreSQL must listen only on
`127.0.0.1:5432`; never open TCP 5432 in Windows Firewall.

## Production `.env`

Create `D:\apps\aipolicy-new\.env` from `.env.example` and set absolute Windows
paths with forward slashes.  Do not commit this file.

```dotenv
APP_ENV=production
API_PREFIX=/new-api/v1
HOST=127.0.0.1
PORT=8000
DATABASE_MODE=standalone
DATABASE_URL=postgresql+psycopg://aipolicy_app:REPLACE_WITH_DATABASE_PASSWORD@127.0.0.1:5432/aipolicy_new
AUTH_REQUIRED=true
AUTH_MODE=local
LOCAL_AUTH_JWT_SECRET=REPLACE_WITH_A_RANDOM_SECRET_OF_AT_LEAST_32_CHARACTERS
LOCAL_AUTH_JWT_ISSUER=aipolicy-new
LOCAL_AUTH_JWT_AUDIENCE=aipolicy-new-api
LOCAL_AUTH_TOKEN_TTL_SECONDS=28800
CORS_ORIGINS=https://aipolicy.bnu.edu.cn
ALLOW_CORS_WILDCARD=false
ENABLE_MOCKS=false
CLASSIFIER_MODEL_PATH=D:/apps/aipolicy-new/backend/models/sz/sz_classifier.pth
CLASSIFIER_TOKENIZER_PATH=D:/apps/aipolicy-new/backend/models/hfl_chinese_bert_wwm
CLASSIFIER_LABEL_BINDINGS_PATH=D:/apps/aipolicy-new/backend/models/sz/department_label_bindings.json
CLASSIFIER_DEPARTMENT_EMBEDDINGS_PATH=D:/apps/aipolicy-new/backend/models/sz/10000szdepartment_embeddings.pth
CLASSIFIER_MODEL_VERSION=sz-tcn-bert-v1
CLASSIFIER_SUPPORTED_REGIONS=sz
```

`LOCAL_AUTH_JWT_SECRET` can be made in elevated PowerShell with:

```powershell
$bytes = New-Object byte[] 48
[System.Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
[Convert]::ToBase64String($bytes)
```

## Install and initialize

Run elevated PowerShell only for PostgreSQL/IIS/service tasks.  Do not paste
passwords into source files, command history, or screenshots.

```powershell
cd D:\apps\aipolicy-new
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .\backend
npm --prefix frontend ci
```

Initialize the database only after `.env` is ready. `Initialize-Postgres.ps1`
prompts for the database password and does not store it:

```powershell
.\deploy\windows\Initialize-Postgres.ps1 -PostgresBin 'C:\Program Files\PostgreSQL\16\bin'
.\deploy\windows\Initialize-Application.ps1 -ProjectRoot 'D:\apps\aipolicy-new' -DemoPassword 'choose-a-temporary-password' -LoadFixtures -Apply
```

Build the frontend for the `/new/` path:

```powershell
$env:VITE_APP_BASE_PATH='/new/'
$env:VITE_API_BASE_URL='/new-api/v1'
npm --prefix frontend run build
Remove-Item Env:VITE_APP_BASE_PATH, Env:VITE_API_BASE_URL
```

## Run and verify locally

Start FastAPI interactively once:

```powershell
.\deploy\windows\Start-Api.ps1 -ProjectRoot 'D:\apps\aipolicy-new'
```

In another PowerShell window:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/new-api/v1/health/live
Invoke-RestMethod http://127.0.0.1:8000/new-api/v1/health/ready
Invoke-RestMethod http://127.0.0.1:8000/new-api/v1/ai/readiness
```

The ready endpoint must report `database=ok` and `authentication=configured`;
model readiness must be `ready`. Keep one Uvicorn worker: every worker loads its
own model copy.

## IIS routes

First back up the current IIS/site settings.  The old catch-all route must stay
last. Create a **new IIS application** named `new` under the existing
`aipolicy.bnu.edu.cn` site, whose physical path is:

```text
D:\apps\aipolicy-new\frontend\dist
```

Place `iis-new-site-web.config` in that `dist` folder as `web.config`.

Create an IIS URL Rewrite rule at the parent site **before the legacy catch-all
rule**:

```text
Match URL: ^new-api/(.*)$
Action: Rewrite
Rewrite URL: http://127.0.0.1:8000/new-api/{R:1}
Append query string: true
Stop processing: true
```

Enable ARR proxy at server level. Do not proxy `/new/` to FastAPI: it is served
as static files by the IIS `new` application. Do not alter `/`, `/health`,
`/classify`, or the old program's port/rules.

## Make FastAPI persistent

Use the school's standard service manager. With NSSM, install a service named
`aipolicy-new-api`:

```powershell
.\deploy\windows\Install-NssmService.ps1 -NssmPath 'C:\tools\nssm\win64\nssm.exe' -ProjectRoot 'D:\apps\aipolicy-new' -Apply
```

The script configures stdout/stderr logs under `D:\apps\aipolicy-new\logs\`,
automatic restart and automatic startup. Do not run Uvicorn as a Windows
administrator account.

## Backup and rollback

Create a scheduled daily task using:

```powershell
.\deploy\windows\Backup-Postgres.ps1 -PostgresBin 'C:\Program Files\PostgreSQL\16\bin' -BackupDirectory 'D:\apps\aipolicy-backups' -Apply
```

Keep backups outside both the PostgreSQL data directory and the Git checkout.
To roll back the new deployment: stop only `aipolicy-new-api`, remove/disable
the `/new-api/` rewrite rule and `/new` application, then restore the backed-up
old IIS configuration. The legacy site remains untouched throughout.

Run the final internal and public checks after IIS and the service are live:

```powershell
.\deploy\windows\Test-Deployment.ps1
```
