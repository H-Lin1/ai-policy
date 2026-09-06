# AI 政策服务平台

## 1. 项目概览

AI 政策服务平台面向深圳地区，提供政策查询、历史问答、部门分类、政民互动咨询、个人/企业服务和政府部门工单办理。新版本使用 standalone PostgreSQL 与 FastAPI 本地账号认证，旧版本独立运行，两个版本互不覆盖。

- 新版本：[https://aipolicy.bnu.edu.cn/new](https://aipolicy.bnu.edu.cn/new)
- 旧版本：[https://aipolicy.bnu.edu.cn](https://aipolicy.bnu.edu.cn)
- 代码仓库：[https://github.com/H-Lin1/ai-policy](https://github.com/H-Lin1/ai-policy)

## 2. 技术栈与环境要求

- 前端：React 18、Vite、TypeScript、React Router
- 后端：FastAPI、Pydantic、SQLAlchemy 2、Alembic
- 数据库：PostgreSQL 16+
- 认证：FastAPI 本地账号认证 + JWT；密码使用 scrypt 哈希
- 模型：本地深圳部门 TCN/BERT 分类模型
- 环境：Git、Python 3.11+、Node.js 20+、npm 10+、PostgreSQL 16+
- 磁盘：约 3 GB（依赖和模型）；模型运行需要足够内存

## 3. 目录结构

```text
backend/app/core/                 配置、数据库、本地认证、错误和日志
backend/app/api/                  /api/v1 路由
backend/app/modules/iam/          账号、角色、组织、注册审批和账号管理
backend/app/modules/policy/       政策读取、管理员录入、Markdown 解析和发布
backend/app/modules/consultation/ 政民互动工单
backend/app/modules/intelligence/ 深圳部门分类适配器
backend/migrations/versions/      Alembic 迁移
frontend/src/app/                 前端路由、布局和页面
frontend/src/lib/api/             统一 API 客户端
docs/                             PRD、TECH 和部署资料
openspec/                         主规格和归档变更
deploy/windows/                   Windows Server 部署说明
scripts/                          启动脚本
```

`.env`、`frontend/.env.local`、`backend/models/`、数据库密码、JWT 密钥和测试账号密码不提交到 Git。旧项目源码不属于当前源码边界。

## 4. 如何部署项目到本地

### 4.1 拉取项目

```bash
git clone https://github.com/H-Lin1/ai-policy.git
cd ai-policy
git pull origin main
```

### 4.2 配置 standalone PostgreSQL

```sql
CREATE ROLE aipolicy_app LOGIN PASSWORD 'replace-with-a-strong-password' NOSUPERUSER NOCREATEDB NOCREATEROLE;
CREATE DATABASE aipolicy_new OWNER aipolicy_app ENCODING 'UTF8';
```

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env.local
```

根目录 `.env` 至少配置：

```dotenv
APP_ENV=development
API_PREFIX=/api/v1
AUTH_REQUIRED=true
AUTH_MODE=local
DATABASE_MODE=standalone
DATABASE_URL=postgresql+psycopg://aipolicy_app:REPLACE_WITH_DATABASE_PASSWORD@127.0.0.1:5432/aipolicy_new
LOCAL_AUTH_JWT_SECRET=REPLACE_WITH_RANDOM_SECRET_AT_LEAST_32_CHARS
LOCAL_AUTH_JWT_ISSUER=ai-policy-local
LOCAL_AUTH_JWT_AUDIENCE=aipolicy-api
LOCAL_AUTH_TOKEN_TTL_SECONDS=28800
CORS_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
ENABLE_MOCKS=false
CLASSIFIER_SUPPORTED_REGIONS=sz
```

`frontend/.env.local` 只配置：

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
VITE_APP_BASE_PATH=/
```

### 4.3 向仓库 owner 索要的文件和信息

- 分类模型压缩包，解压后得到 `backend/models/`
- standalone PostgreSQL 连接参数或已初始化数据库信息
- 有权限使用的个人、企业、政府和管理员测试账号
- Windows Server 的域名、IIS/NSSM 配置和备份目录（如需要部署）

### 4.4 创建运行环境

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e 'backend[dev]'
npm --prefix frontend ci
```

### 4.5 放置模型

```text
backend/models/
├── hfl_chinese_bert_wwm/
└── sz/
    ├── sz_classifier.pth
    ├── department_label_bindings.json
    └── 10000szdepartment_embeddings.pth
```

在 `.env` 中配置四个 `CLASSIFIER_*_PATH` 路径。

### 4.6 执行迁移和启动

```bash
cd backend
python -m alembic -c alembic.ini upgrade head
cd ..
npm run dev
```

当前迁移 head 为 `0008_admin_account_management`。默认地址：

- 前端：http://127.0.0.1:5173/
- API 文档：http://127.0.0.1:8000/docs
- 存活：http://127.0.0.1:8000/api/v1/health/live
- 就绪：http://127.0.0.1:8000/api/v1/health/ready
- 模型：http://127.0.0.1:8000/api/v1/ai/readiness

## 5. 注意事项

- 当前业务范围固定为深圳；standalone PostgreSQL 是唯一推荐数据库和认证方式。
- 前端不直接写入 `app.*` 表；管理员 API 由后端执行角色校验。
- 账号删除实际为停用，不物理删除历史数据。
- 政府账号一个部门最多绑定一个账号。
- 普通用户只能读取已发布政策。
- 真实 RAG 尚未接入，当前问答为明确标识的 placeholder。
- 不要未经授权执行迁移、账号创建、政策导入或数据清理。
- 新旧版本独立部署，不要修改旧版本目录、端口或 IIS catch-all 规则。

## 6. 主要页面与主要 API

页面：

```text
/                           公开首页
/login?role=admin           管理员登录
/register?role=individual   个人注册
/register?role=enterprise   企业注册申请
/register?role=government   政府账号申请
/homepage                   登录后的身份首页
/policies                   政策中心
/qa                         历史问答
/consultations              政民互动
/account-management         管理员账号管理
/registration-applications 管理员注册申请审批
/policy-management          管理员政策管理
```

API：

```text
POST /api/v1/iam/login
GET  /api/v1/me
GET  /api/v1/policies
GET  /api/v1/qa
GET  /api/v1/consultations
POST /api/v1/consultations
POST /api/v1/classifications
POST /api/v1/policy-answers
POST /api/v1/iam/registrations/individual
POST /api/v1/iam/registrations/enterprise
POST /api/v1/iam/registrations/government
GET/POST/PATCH /api/v1/admin/accounts...
GET/POST       /api/v1/admin/registration-applications...
GET/POST       /api/v1/admin/policies...
```

## 7. 项目当前开发状态

- 当前阶段：B1.8 阶段功能完善与优化
- 已完成：S0.1-S0.6、B1.1-B1.7、B18-001 至 B18-011
- 当前数据库迁移基线：`0008_admin_account_management`
- 已完成能力：本地账号注册和审批、管理员首页、账号管理、政策手工/Markdown 批量发布、政民互动、政策中心、历史问答和部门分类
- 真实 RAG：尚未接入，当前为 placeholder，后续需独立交接和验收
- 状态记录：[`DEVELOPMENT_STATUS.md`](./DEVELOPMENT_STATUS.md)

质量门禁：

```bash
cd backend && python -m pytest && python -m ruff check --no-cache . && cd ..
npm test
npm run build
openspec validate --all --strict --no-interactive
```

Windows Server standalone PostgreSQL、IIS、NSSM 和备份方案见 [`deploy/windows/README.md`](./deploy/windows/README.md)。
