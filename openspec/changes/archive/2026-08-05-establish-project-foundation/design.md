## Context

本 change 是开发基线阶段 0 的工程实现，目标项目目录为本仓库的 `ai-policy/`。旧项目位于同级的 `backend/`，不属于新项目源码边界。新项目需要在 macOS 本地开发，并保持后续可在 Windows 或 Linux 上运行；因此路径、端口、数据库和模型位置都必须配置化。

## Goals / Non-Goals

**Goals:**

- 用模块化单体建立清晰的 React/FastAPI/Supabase 工程边界。
- 让没有 Supabase 或模型文件的本地环境也能启动进程，并通过 ready 检查明确显示降级原因。
- 统一 `/api/v1`、错误响应、请求 ID、日志和认证依赖，供后续 PRD/OpenSpec 复用。
- 用 `DepartmentClassifier` 接口隔离唯一允许迁移的旧分类计算逻辑；本 change 只放置未配置适配器，不复制旧模型代码。
- 用最小 Alembic 迁移证明空数据库可以初始化，并提供可重复的冒烟脚本。

**Non-Goals:**

- 不实现政策库、历史问答、相似检索、Embedding、FAISS、RAG、政策解读、咨询或企业能力。
- 不创建旧 `/classify` 路由，不复制旧 Flask 应用、全局初始化、前端或 Mock 数据。
- 不在阶段 0 建立第一批业务表；业务表按后续 PRD/OpenSpec 迁移。
- 不引入微服务、消息队列或生产级高可用编排。

## Decisions

### 1. Repository layout

```text
ai-policy/
  backend/
    app/
      main.py                 # FastAPI factory and lifespan
      core/                   # settings, db, auth, errors, middleware
      api/                    # versioned router and dependencies
      modules/
        system/               # health and /me for stage 0
        intelligence/         # model adapter contracts only
    migrations/               # Alembic environment and versions
    scripts/                  # init, reset, smoke
    tests/
  frontend/
    src/
      app/                    # router, layout, pages
      lib/api/                # one fetch client boundary
  docs/
    TECH-V1-S0-01.md
  openspec/
  DEVELOPMENT_STATUS.md
```

Routes only translate HTTP to application calls. Business rules belong in services, database access belongs in repositories, and model calls belong in `intelligence` adapters. The skeleton keeps those boundaries even where a module currently has only a health endpoint.

### 2. Configuration and environment

Use `pydantic-settings` with a single `Settings` object. `.env.example` documents safe local defaults; `.env` and `.env.local` are ignored by Git. `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_JWT_SECRET`, model paths, CORS origins, and feature flags are injected at runtime. Frontend variables use the `VITE_` prefix only for public values; no secret is accepted in frontend configuration.

### 3. HTTP contract

FastAPI mounts a root `/api/v1` router. The system module exposes:

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/api/v1/health/live` | public | Process and routing liveness |
| GET | `/api/v1/health/ready` | public | Dependency readiness |
| GET | `/api/v1/health` | public | Browser-friendly aggregate check |
| GET | `/api/v1/ai/readiness` | public | Model adapter readiness |
| GET | `/api/v1/me` | bearer token when enabled | Authenticated principal echo |

Errors use `{ "error": { "code", "message", "details" }, "request_id" }`. Pydantic validation errors are normalized into the same envelope. A middleware generates or preserves `X-Request-ID` and adds it to every response.

### 4. Database and Supabase

SQLAlchemy creates an engine only when `DATABASE_URL` is configured. The readiness probe executes `SELECT 1`; in development without a URL it reports `not_configured`, while production returns 503. Alembic's first migration creates the `app` schema only. No unapproved business table is introduced by the foundation change; first-batch tables arrive through their own PRDs and migrations.

Supabase Auth remains the identity source. The foundation verifies HS256 Supabase JWTs when a secret is configured. The local bypass is opt-in through `AUTH_REQUIRED=false`, returns a visibly marked development principal, and is forbidden in the demonstration deployment configuration.

### 5. Classifier adapter

Define a Protocol/ABC with typed `ClassifierInput`, `ClassificationResult`, `DepartmentPrediction`, and `AdapterReadiness`. The default implementation is `UnavailableDepartmentClassifier`, which raises a typed `MODEL_NOT_READY` error. It contains no legacy imports. A later change may add a verified implementation that extracts only the pure computation from `backend/app0723.py`; the new service will map labels to stable organization IDs and record `ai_runs`.

### 6. Frontend shell

The Vite app uses React Router with an application layout, root workspace placeholder, and health page. The API client has one base URL, JSON error parsing, and retry action at the page level. The shell contains no business Mock data. Later features add pages only as vertical slices after their PRD/OpenSpec and API are ready.

### 7. Logging and safety

Use standard-library logging with JSON-like key/value fields, request ID, method, path, status, and duration. Never log authorization headers, tokens, model secrets, or full user questions. CORS is restricted to configured origins; a wildcard is allowed only in explicit local development mode.

## Risks / Trade-offs

- **[Risk]** Python or Node dependencies are not installed on a fresh machine → **Mitigation:** pin compatible major versions, document versions, and run an import/build smoke check in CI/local scripts.
- **[Risk]** A missing Supabase URL could be mistaken for a healthy service → **Mitigation:** separate live and ready checks and return an explicit degraded/not-configured state.
- **[Risk]** A future developer copies the legacy route into the adapter → **Mitigation:** keep the adapter contract free of Flask types, add a test asserting `/classify` is absent, and record the migration boundary in README and status ledger.
- **[Risk]** Frontend and backend paths drift → **Mitigation:** expose the base URL through one environment variable and test the health page against the versioned route.
- **[Risk]** The staging path differs from the user's requested external folder because of the current sandbox → **Mitigation:** keep the project self-contained and provide a single move command after implementation; no source files depend on the parent path.

## Migration Plan

1. Run the documented dependency installation commands.
2. Copy `.env.example` to the local environment file and fill only the required values.
3. Run `alembic upgrade head` when a Supabase/PostgreSQL URL is available; without one, run the db-less smoke check.
4. Start `uvicorn app.main:app --reload` from `backend/` and `npm run dev` from `frontend/`.
5. Verify live, ready, model readiness, protected endpoint, frontend build, and smoke tests.
6. Roll back by stopping the processes and reverting the foundation migration; no business data is created by this change.

