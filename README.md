# AI 政策服务平台

这是从旧项目重新组织的 V1.0 新项目。当前已完成阶段 0 的项目骨架和 Supabase/JWT 运行底座，旧项目目录不属于本项目源码，也不会被运行时导入。

## 当前状态

- 阶段：阶段 0 与 B1.1-B1.7 已验收归档；当前进入 B1.8“阶段功能完善与优化”，持续检查、修复和验收现有功能
- 产品记录：B1.8 统一记录于 [`PRD-V1-B1-08`](./docs/PRD-V1-B1-08.md)；涉及需求合同、API、数据库或权限的具体问题分别建立 TECH/OpenSpec 变更
- 前端：React + Vite + TypeScript
- 后端：FastAPI + Pydantic + SQLAlchemy + Alembic
- 数据平台：Supabase/PostgreSQL；开发环境未配置时允许降级启动，真实业务开发使用已配置的 Supabase
- 旧代码边界：只有经验证的旧 `classify` 计算逻辑未来可以进入 `DepartmentClassifier`；本阶段尚未迁移任何旧模型代码。

开发顺序和跨对话恢复规则见 [`DEVELOPMENT_STATUS.md`](./DEVELOPMENT_STATUS.md)。当前 B1.8 的范围、问题台账和阶段验收依据见 [`PRD-V1-B1-08`](./docs/PRD-V1-B1-08.md)。

## 运行时行为

- 日志：默认输出单行 JSON，字段含 `timestamp`、`level`、`logger`、`message`、`request_id`；访问日志额外含方法、路径、状态码和耗时。设置 `LOG_FORMAT=text` 可切换为本地易读格式。结构化字段、嵌套值、消息和异常堆栈中的常见令牌、密码、密钥和连接串形式都会被替换为 `***`；Uvicorn 生命周期日志也使用相同格式。
- 请求追踪：合法的 `X-Request-ID` 原样保留，否则自动生成；成功、失败和 CORS 预检响应都带该响应头，且与错误体中的 `request_id` 一致。请求期间任何应用 logger 的记录都会带上同一个请求 ID。
- 健康检查：`/api/v1/health/live` 只回答进程与路由是否可用，不访问数据库、JWKS 或模型；`/api/v1/health/ready` 报告依赖状态和生效的功能开关快照。三个健康接口都返回 `Cache-Control: no-store`。
- 功能开关：由后端集中管理，通过 `GET /api/v1/system/features` 暴露环境名、是否需要认证和布尔快照，不返回任何配置值。未注册的开关名按关闭处理；`ENABLE_MOCKS` 在生产环境强制关闭，并在就绪检查中标记为不合规配置。
- 前端路由守卫：受开关控制的路由（阶段 0 为 `/policies`）在开关关闭、快照加载中或后端不可达时都不渲染业务内容，也不显示占位假数据。
- 分类适配器：`CLASSIFIER_SUPPORTED_REGIONS` 默认只注册 `sz`；输入在适配器边界规范化，未知地区返回 `REGION_NOT_SUPPORTED`，未验证模型和无效资产返回明确 not-ready reason，不跨地区回退、不返回 Mock 分类。`/api/v1/ai/readiness` 为 `no-store` 安全探针。
- 身份与权限：Supabase JWT 只证明登录主体；`/api/v1/me` 和 `/api/v1/iam/workspaces/{role}` 从 `app.profiles/user_roles/roles/regions/organizations` 读取业务角色与深圳范围。JWT 角色声明和前端状态都不能授予权限；未配置、停用、无角色或跨角色访问明确返回 403/503，不回退 Mock。

## 运行环境

- Python 3.11+（本机项目虚拟环境使用 Python 3.14.6；macOS 系统自带 Python 3.9.6 不满足要求）
- Node.js 20+、npm 10+
- Supabase/PostgreSQL：阶段 0 本地启动可暂不配置，业务功能开始前必须配置

## 快速启动

在项目根目录执行：

```bash
cp .env.example .env
# 先确认这里输出 3.11 或更高版本；否则请先安装/选择新版 Python
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e 'backend[dev]'

cd frontend
cp .env.example .env.local
npm install
# 在 .env.local 配置公开的 VITE_SUPABASE_URL、VITE_SUPABASE_ANON_KEY
cd ..
npm run dev
```

`npm run dev` 会同时启动前端 Vite（`http://127.0.0.1:5173`）和后端 FastAPI（`http://127.0.0.1:8000`）；按 `Ctrl+C` 会一并停止。若端口已被占用，命令会明确失败而不会悄悄改用其他端口。需要临时指定端口时可执行：

```bash
FRONTEND_PORT=5175 BACKEND_PORT=8001 npm run dev
```

仍可按需单独启动：`npm run dev:frontend` 启动前端，`npm run dev:backend` 启动后端。

浏览器访问：

- 前端：`http://localhost:5173`
- OpenAPI：`http://localhost:8000/docs`
- 存活检查：`http://localhost:8000/api/v1/health/live`
- 就绪检查：`http://localhost:8000/api/v1/health/ready`
- 功能开关：`http://localhost:8000/api/v1/system/features`

## 初始化与数据库迁移

在 `backend/` 目录先运行安全预检。裸命令只报告目标是否已配置，不连接数据库、不执行迁移，也不显示连接信息：

```bash
python scripts/init_demo.py
```

只有已获授权且已核对 PostgreSQL 目标的操作人员才可显式执行：

```bash
python scripts/init_demo.py --apply-foundation-migration --confirm
```

该命令固定只执行 `0001_foundation_schema`，不会使用 `head` 顺带运行未来业务迁移；它不属于自动验收。阶段 0 的迁移只创建 `app` schema，不创建业务表。第一批业务表必须由对应 PRD/OpenSpec change 的迁移建立。

阶段 0 没有业务种子数据。下面的 reset 只是需要确认的 no-op，不访问数据库、不删除文件或数据：

```bash
python scripts/reset_demo.py --confirm
```

## B1.1 IAM 迁移与初始化

`0002_identity_access` 只创建 `regions`、`roles`、`organizations`、`profiles`、`user_roles` 五张 `app` 表，启用 RLS，并撤销 `anon`/`authenticated` 直接权限；它不创建浏览器 policy，也不创建或修改 `auth.users`。它是外部数据库写操作；只有获得明确授权并确认目标后，操作人员才可在 `backend/` 目录执行精确 revision：

```bash
python -m alembic -c alembic.ini upgrade 0002_identity_access
```

Alembic、runtime smoke 和 IAM initializer 共用 fail-closed 目标门禁：标准 Supabase API host 必须与数据库直连 host 或 pooler username 推导出同一 project ref。缺失、无法推导或不一致时命令会在迁移/seed 前失败，并且不会输出任一目标值。

IAM initializer 默认只预检，不连接数据库、不 seed：

```bash
python scripts/init_iam.py
```

先通过统一服务端 Settings（项目根/后端 `.env` 或进程环境）提供四个已存在的 Supabase Auth 用户 UUID；无需也不应在 shell 中 `source` 含数据库配置的文件。授权写入后，使用双重确认执行映射。脚本在一个加锁事务内复核 revision、Auth 用户和所有固定记录：缺失记录才插入，完全一致的重复执行是零写入；ID/code 冲突、非 demo/disabled Profile、额外或失效角色、旧 UUID 映射一律失败，不覆盖或重新激活数据。脚本不会创建 Auth 账号、读取密码、运行迁移或删除数据：

```bash
python scripts/init_iam.py --apply-iam-seed --confirm
```

当前配置库已在独立明确授权下执行两次 initializer：最终五表计数为 `1/4/3/4/4`，第二次执行前后每一行字段及时间戳均不变。四个真实账户的 `/me`、匹配工作区和全部十二个跨角色拒绝均已通过；验收不输出或持久化账户密码、JWT。

## 检查命令

```bash
# 一条命令运行全部非破坏性本地验收（不包含迁移、reset 或外部 runtime smoke）
cd backend
python scripts/acceptance.py

# 单项诊断命令
python -m pytest
python -m ruff check --no-cache .
python scripts/smoke.py
python scripts/runtime_smoke.py  # 单独显式执行；只读检查已配置的 PostgreSQL/Supabase/JWKS

# 前端
cd ../frontend
npm test
npm run build

# OpenSpec
cd ..
openspec validate --all --strict --no-interactive
```

`runtime_smoke.py` 只执行只读连通性、Supabase project 绑定、当前 `0002_identity_access` revision、精确五表/RLS、无浏览器 policy/直接权限、认证配置和 JWKS 检查。当前配置库已完成授权 `0002` upgrade，全部 runtime checks 应为 `ok`；任何 revision/schema 漂移仍会明确失败。所有脚本只输出稳定状态名，不输出 `.env`、project ref、连接串、UUID 映射、JWT、密钥或异常文本。

## 目录边界

```text
backend/app/core/                 配置、数据库、认证、错误、日志
backend/app/api/                  版本化路由和依赖
backend/app/modules/system/       阶段 0 健康检查、功能开关快照与模型状态
backend/app/modules/iam/          B1.1 数据库身份、组织地区范围与 RBAC
backend/app/modules/intelligence/ 模型适配器契约，不直接放旧 Flask 逻辑
frontend/src/app/                 应用入口、路由和布局
frontend/src/app/runtime/         运行时配置（功能开关快照）
frontend/src/app/guards/          功能开关路由守卫
frontend/src/lib/api/             统一 API 客户端
docs/                             技术实施方案和验收资料
openspec/                         可校验的变更规格
```
