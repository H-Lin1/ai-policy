# TECH-V1-S0-01｜阶段 0 工程基础技术实施方案

| 项目 | 内容 |
|---|---|
| 文档 ID | `TECH-V1-S0-01` |
| 版本 | `V1.1` |
| 状态 | 已实现并归档 |
| 飞书文档 | https://a9ihi0un9c.feishu.cn/docx/GSNtdGZHXoyCdExcXUkcepT0nFg |
| 对应基线 | 阶段 0：工程基础 |
| OpenSpec change | `establish-project-foundation`（已归档）；`standardize-not-found-errors`（已归档） |
| 目标 | 让新项目在本机可重复启动，并给后续业务开发提供清晰边界 |

## 1. 目标和范围

阶段 0 只建设工程底座，不建设业务功能。完成后，开发者应能在一台没有旧项目依赖的新机器上：

1. 安装前后端依赖并分别启动服务；
2. 打开前端工作区和服务状态页；
3. 通过 `/api/v1/health/live`、`/api/v1/health/ready` 检查运行状态；
4. 看到统一错误格式、请求 ID 和认证拒绝结果；
5. 在配置 Supabase 后执行空库迁移；
6. 运行自动化测试和冒烟脚本。

本阶段明确不做：政策库、历史问答、检索、Embedding、FAISS、RAG、咨询、企业画像、政策解读、匹配和管理员业务页面。

## 2. 用户能看到什么

阶段 0 的前端不是完整产品页面，而是可继续扩展的工作区外壳：

- `/`：显示项目当前阶段、导航和下一步建设提示；
- `/health`：请求后端健康接口，显示成功、加载、失败和重试状态；
- 未知路径：显示明确的 404 空态。

页面不使用旧项目的静态业务数组，也不在真实接口失败时显示假的业务结果。

## 3. 数据和接口流转

| 用户/脚本动作 | 接口或命令 | 后端处理 | 数据/依赖去向 | 返回/验收 |
|---|---|---|---|---|
| 浏览器检查服务 | `GET /api/v1/health` | 汇总进程和数据库状态 | 读取运行配置；可选执行 `SELECT 1` | 返回 `ready` 或 `degraded`，不伪装数据库已连接 |
| 运维检查存活 | `GET /api/v1/health/live` | 只检查进程与路由 | 不访问外部依赖 | HTTP 200、`status=ok` |
| 运维检查依赖 | `GET /api/v1/health/ready` | 检查数据库配置和连通性 | Supabase/PostgreSQL | 已配置且可连通为 ready；生产失败为 503 |
| 查看模型状态 | `GET /api/v1/ai/readiness` | 查询分类适配器状态 | 阶段 0 不加载旧权重 | `not_ready` 时给出原因，不返回 Mock 分类 |
| 访问受保护接口 | `GET /api/v1/me` | 验证 Supabase JWT | 读取令牌，不写业务表 | 无令牌 401；显式本地 bypass 会标识开发身份 |
| 初始化空库 | `alembic upgrade head` | 执行迁移 | 创建 `app` schema，不创建业务表 | 可重复执行，失败有明确数据库错误 |

所有 API 响应带 `X-Request-ID`。应用错误统一为：

```json
{
  "error": {
    "code": "AUTH_REQUIRED",
    "message": "需要有效的 Bearer 登录令牌",
    "details": null
  },
  "request_id": "..."
}
```

## 4. 目录和职责

```text
backend/app/core/                   配置、数据库、认证、错误、日志、中间件
backend/app/api/                    /api/v1 路由注册
backend/app/modules/system/         健康检查和 /me
backend/app/modules/intelligence/   DepartmentClassifier 契约和适配器
backend/migrations/                 Alembic 环境和版本
backend/scripts/                    初始化、重置、冒烟
backend/tests/                      阶段 0 自动化测试
frontend/src/app/                   路由、布局、阶段 0 页面
frontend/src/lib/api/               唯一 HTTP 客户端
```

路由只负责 HTTP 转换；业务规则放 service；数据库访问放 repository；模型调用放 intelligence 适配器。旧 `backend/` 不在新项目的 Python path 中。

## 5. 环境变量

必需/常用变量写在根目录 `.env.example`。本地开发可以不填 `DATABASE_URL` 和模型路径，但 ready/readiness 必须显示降级或未就绪。演示环境必须设置：

- `APP_ENV=production`；
- `AUTH_REQUIRED=true`；
- `DATABASE_URL`、`SUPABASE_URL`，以及 S0.2 已冻结的当前非对称 JWKS/issuer/audience 配置；Legacy `SUPABASE_JWT_SECRET` 已废弃，不再作为演示环境要求；
- 明确的 `CORS_ORIGINS`；
- 经验证的分类模型路径和标签绑定路径（在分类 change 中启用）。

任何密钥不得写入 Git、前端 `VITE_*` 变量或构建产物。

## 6. 实施顺序

1. 初始化 OpenSpec 和本技术方案；
2. 建立后端依赖、配置、错误、中间件和健康路由；
3. 建立数据库连接、Alembic 空 schema 迁移和脚本；
4. 建立分类适配器契约与未就绪行为；
5. 建立前端外壳、API 客户端和服务状态页；
6. 运行测试、构建、OpenSpec strict validate 和冒烟检查；
7. 记录证据，进入阶段 0 验收；验收通过后归档 change。

前端只在阶段 0 建骨架；具体业务页面必须在对应 PRD/OpenSpec 的纵向切片中，与数据库、后端 API、权限、错误态和验收一起完成。

## 7. 验收场景

| 编号 | 场景 | 通过标准 |
|---|---|---|
| S0-A1 | 新环境安装并导入后端 | `pytest`、模块导入和 `python scripts/smoke.py` 通过 |
| S0-A2 | 前端构建 | `npm run build` 通过，无旧项目 import |
| S0-A3 | 健康检查 | live 200；开发无数据库时 ready 200 degraded；生产无数据库时 ready 503 |
| S0-A4 | 请求追踪 | 请求 ID 在响应头和错误体中一致 |
| S0-A5 | 认证边界 | `/me` 无令牌 401；健康接口仍公开 |
| S0-A6 | 分类边界 | `/api/v1/ai/readiness` 明确 not_ready；旧 `/classify` 404；无固定答案或相似度 |
| S0-A7 | 空库迁移 | 配置数据库后 `alembic upgrade head` 可执行，且只创建 `app` schema |
| S0-A8 | 未注册路由 | 旧 `POST /classify` 返回 404、`ROUTE_NOT_FOUND` 统一错误体，并保留请求 ID |

当前已在本机完成迁移脚本的 PostgreSQL offline SQL 生成验证；由于尚未提供 Supabase 连接信息，真实云库执行仍是下一项环境门槛，不在本地骨架验收中伪造为已通过。

## 8. 风险和回滚

- 本机 Python 解释器可能有多个版本；系统 Python 3.9.6 低于项目要求，必须先选择 Python 3.11+ 再创建项目 `.venv`，并在启动前打印版本。
- Supabase 暂不可用时不阻塞骨架开发，但不能进入第一批业务数据开发。
- npm audit 发现的依赖风险要在发布前复核；阶段 0 不自动执行可能改变依赖树的 `npm audit fix`。
- 本 change 没有业务数据迁移，回滚只需停止服务并撤销代码/空 schema 迁移。

## 9. 变更记录

| 日期 | 版本 | 变化 |
|---|---|---|
| 2026-08-05 | V1.0 | 建立阶段 0 前后端骨架、OpenSpec change 和验收方案，并补齐未注册路由的统一错误响应。 |
| 2026-08-06 | V1.1 | S0.6 收口勘误：认证配置以 `TECH-V1-S0-02` 的当前 JWKS 方案为准，移除已废弃的 Legacy JWT secret 要求。 |
