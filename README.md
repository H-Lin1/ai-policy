# AI 政策服务平台

这是从旧项目重新组织的 V1.0 新项目。当前已完成阶段 0 的项目骨架和 Supabase/JWT 运行底座，旧项目目录不属于本项目源码，也不会被运行时导入。

## 当前状态

- 阶段：阶段 0 与 B1.1-B1.7 已验收归档；当前进入 B1.8“阶段功能完善与优化”，持续检查、修复和验收现有功能
- 产品记录：B1.8 统一记录于 [`PRD-V1-B1-08`](./docs/PRD-V1-B1-08.md)；涉及需求合同、API、数据库或权限的具体问题分别建立 TECH/OpenSpec 变更
- 前端：React + Vite + TypeScript
- 后端：FastAPI + Pydantic + SQLAlchemy + Alembic
- 数据平台：Supabase/PostgreSQL；开发环境未配置时允许降级启动，真实业务开发使用已配置的 Supabase
- 分类能力：深圳部门分类已接入经验证的本地 TCN/BERT 模型资产；模型权重不提交到 Git，需要由仓库 owner 单独提供。

开发顺序和跨对话恢复规则见 [`DEVELOPMENT_STATUS.md`](./DEVELOPMENT_STATUS.md)。当前 B1.8 的范围、问题台账和阶段验收依据见 [`PRD-V1-B1-08`](./docs/PRD-V1-B1-08.md)。

## 部署指南

本节面向第一次从 GitHub 获取项目的协作者。按下面步骤完成后，可在本机启动前端和后端，并使用已授权的测试账号登录、访问政策中心、历史问答、政民互动和部门分类等现有功能。

### 1. 前置环境

- Git
- Python 3.11 或更高版本
- Node.js 20 或更高版本及 npm 10 或更高版本
- 至少约 3 GB 可用磁盘空间：模型压缩包约 868 MB，解压后的 `backend/models/` 约 868 MB，安装 Python/Node 依赖还会占用额外空间。

macOS 可先确认版本：

```bash
git --version
python3 --version
node --version
npm --version
```

### 2. 从 GitHub 获取代码

```bash
git clone https://github.com/H-Lin1/ai-policy.git
cd ai-policy
```

仓库不会包含 `.env`、`frontend/.env.local`、`backend/models/`，也不会包含测试账号密码或数据库凭据；这些文件被有意排除在 Git 之外。

### 3. 向仓库 owner 索要的文件和信息

在安装或启动前，请通过安全渠道向仓库 owner 索要下列内容；不要通过 Git commit、Issue、聊天记录截图或公开网盘泄露它们。

| 需要内容 | 用途与放置位置 |
| --- | --- |
| 后端环境配置值 | 按 [`.env.example`](./.env.example) 创建项目根目录 `.env`，由 owner 提供 `SUPABASE_URL`、`DATABASE_URL` 和 JWT 相关配置。这些值用于后端鉴权和访问既有 Supabase/PostgreSQL 数据。 |
| 前端环境配置值 | 按 [`frontend/.env.example`](./frontend/.env.example) 创建 `frontend/.env.local`，由 owner 提供 `VITE_SUPABASE_URL` 和 `VITE_SUPABASE_ANON_KEY`。只可填写匿名键，绝不可填写 Supabase service-role key。 |
| `ai-policy-backend-models-YYYYMMDD.zip` | 模型压缩包由 owner 单独发送。解压后必须得到 `backend/models/`，其中包含 `hfl_chinese_bert_wwm/` 与 `sz/` 两个目录。 |
| 可登录的测试账号 | 个人、企业或政府入口所需的账号和密码。账号必须已由 owner 授权并存在于共享 Supabase 项目中；没有账号时仍可打开公开首页，但无法验证登录后的业务功能。 |

如果只需要查看公开首页或进行纯前端界面开发，可暂不索要模型和测试账号；但要完整运行登录、业务列表、互动和分类功能，以上内容均需要可用。

`IAM_DEMO_*_USER_ID` 仅供 owner 在初始化身份映射时使用；普通协作者连接已经初始化的共享环境时应保持为空，不需要索要或填写。

### 4. 放置模型并创建环境文件

将 owner 提供的模型压缩包保存到任意临时位置，然后在项目根目录执行（把路径替换成实际文件位置）：

```bash
unzip /实际路径/ai-policy-backend-models-YYYYMMDD.zip -d backend
```

解压后的目录必须是：

```text
backend/models/
├── hfl_chinese_bert_wwm/
└── sz/
```

接着创建环境文件：

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env.local
```

将 owner 给出的值填入对应文件。启用本地部门分类时，项目根 `.env` 至少需要以下四项（路径相对于项目根目录）：

```dotenv
CLASSIFIER_MODEL_PATH=backend/models/sz/szTCN变为2个一维卷积3best.model.pth
CLASSIFIER_TOKENIZER_PATH=backend/models/hfl_chinese_bert_wwm
CLASSIFIER_LABEL_BINDINGS_PATH=backend/models/sz/department_label_bindings.json
CLASSIFIER_DEPARTMENT_EMBEDDINGS_PATH=backend/models/sz/10000szdepartment_embeddings.pth
```

不要执行 README 中的数据库迁移、初始化、导入或 reset 命令，除非 owner 已明确授权并说明目标环境；普通协作者连接现有共享环境时不需要这些写操作。

### 5. 安装依赖并启动

在项目根目录执行：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e 'backend[dev]'
npm --prefix frontend ci
npm run dev
```

`npm run dev` 会同时启动：

- 前端：`http://127.0.0.1:5173/`
- 后端：`http://127.0.0.1:8000/`
- 后端 API 文档：`http://127.0.0.1:8000/docs`

保持该终端运行；按 `Ctrl+C` 会同时停止前后端。若 `5173` 或 `8000` 已被其他程序占用，先停止占用进程，或改用：

```bash
FRONTEND_PORT=5175 BACKEND_PORT=8001 npm run dev
```

使用自定义端口时，还要把项目根 `.env` 中的 `CORS_ORIGINS` 增加为实际前端地址，例如 `http://127.0.0.1:5175`；前端启动脚本会自动指向对应的后端端口。

### 6. 启动后检查

浏览器打开 `http://127.0.0.1:5173/`，应看到无导航栏的“政通惠”公开首页和个人、企业、政府三个入口。再检查以下地址：

```text
http://127.0.0.1:8000/api/v1/health/live
http://127.0.0.1:8000/api/v1/health/ready
http://127.0.0.1:8000/api/v1/ai/readiness
```

- `health/live` 返回 `ok` 表示后端进程已启动。
- 已正确提供 Supabase 与数据库配置时，`health/ready` 应显示数据库和认证已就绪。
- 模型已正确解压且四个 `CLASSIFIER_*` 路径均正确时，`ai/readiness` 应显示模型 `ready`。

然后从与账号角色匹配的入口登录：个人账号选“个人服务”、企业账号选“企业服务”、政府账号选“政府服务”。入口与账号角色不一致时，系统会阻止自动跳转并提示进入正确服务或切换账号。

## 运行时行为

- 日志：默认输出单行 JSON，字段含 `timestamp`、`level`、`logger`、`message`、`request_id`；访问日志额外含方法、路径、状态码和耗时。设置 `LOG_FORMAT=text` 可切换为本地易读格式。结构化字段、嵌套值、消息和异常堆栈中的常见令牌、密码、密钥和连接串形式都会被替换为 `***`；Uvicorn 生命周期日志也使用相同格式。
- 请求追踪：合法的 `X-Request-ID` 原样保留，否则自动生成；成功、失败和 CORS 预检响应都带该响应头，且与错误体中的 `request_id` 一致。请求期间任何应用 logger 的记录都会带上同一个请求 ID。
- 健康检查：`/api/v1/health/live` 只回答进程与路由是否可用，不访问数据库、JWKS 或模型；`/api/v1/health/ready` 报告依赖状态和生效的功能开关快照。三个健康接口都返回 `Cache-Control: no-store`。
- 功能开关：由后端集中管理，通过 `GET /api/v1/system/features` 暴露环境名、是否需要认证和布尔快照，不返回任何配置值。未注册的开关名按关闭处理；`ENABLE_MOCKS` 在生产环境强制关闭，并在就绪检查中标记为不合规配置。
- 前端访问控制：登录后首页为 `/homepage`，公开首页固定为 `/`；个人、企业、政府的入口意图不会授予权限，实际角色始终由后端 `/me` 确认。角色不匹配时不会静默进入其他工作区。
- 分类适配器：深圳分类服务使用本地 TCN/BERT 模型，需配置四项 `CLASSIFIER_*_PATH` 并放置 owner 提供的模型资产；`CLASSIFIER_SUPPORTED_REGIONS` 默认只注册 `sz`。输入在适配器边界规范化，未知地区返回 `REGION_NOT_SUPPORTED`，资产缺失或无效返回明确 not-ready reason，不跨地区回退、不返回 Mock 分类。`/api/v1/ai/readiness` 为 `no-store` 安全探针。
- 身份与权限：Supabase JWT 只证明登录主体；`/api/v1/me` 和 `/api/v1/iam/workspaces/{role}` 从 `app.profiles/user_roles/roles/regions/organizations` 读取业务角色与深圳范围。JWT 角色声明和前端状态都不能授予权限；未配置、停用、无角色或跨角色访问明确返回 403/503，不回退 Mock。

## 运行环境

- Python 3.11+（本机项目虚拟环境使用 Python 3.14.6；macOS 系统自带 Python 3.9.6 不满足要求）
- Node.js 20+、npm 10+
- Supabase/PostgreSQL：阶段 0 本地启动可暂不配置，业务功能开始前必须配置

## 快速启动

完整的首次部署、owner 交付物、模型解压和启动后验证，请使用上方[部署指南](#部署指南)。已经拿到 `.env`、`frontend/.env.local` 和模型、且已安装依赖的协作者，可在项目根目录直接执行：

```bash
npm run dev
```

`npm run dev` 会同时启动前端 Vite（`http://127.0.0.1:5173`）和后端 FastAPI（`http://127.0.0.1:8000`）；按 `Ctrl+C` 会一并停止。若端口已被占用，命令会明确失败而不会悄悄改用其他端口。需要临时指定端口时可执行：

```bash
FRONTEND_PORT=5175 BACKEND_PORT=8001 npm run dev
```

仍可按需单独启动：`npm run dev:frontend` 启动前端，`npm run dev:backend` 启动后端。

浏览器访问：

- 前端：`http://127.0.0.1:5173/`
- OpenAPI：`http://127.0.0.1:8000/docs`
- 存活检查：`http://127.0.0.1:8000/api/v1/health/live`
- 就绪检查：`http://127.0.0.1:8000/api/v1/health/ready`
- 模型检查：`http://127.0.0.1:8000/api/v1/ai/readiness`

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
