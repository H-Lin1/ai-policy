# TECH-V1-S0-02｜Supabase 连接与 JWT 运行底座

| 项目 | 内容 |
|---|---|
| 文档 ID | `TECH-V1-S0-02` |
| 版本 | `V1.0` |
| 状态 | 已完成并归档 |
| 对应步骤 | `S0.2` |
| OpenSpec change | `establish-supabase-runtime` |
| 飞书文档 | [TECH-V1-S0-02｜Supabase 连接与 JWT 运行底座](https://a9ihi0un9c.feishu.cn/docx/AnRudtC8ToSqvexmOvxcfVCpnxb) |
| 前置条件 | `S0.1` 已归档；本地 `.env` 已配置 Supabase URL 和 Session pooler URI |
| 目标 | 在真实 Supabase 项目上完成可重复的空库迁移，并适配当前 ECC/JWKS JWT 验证 |

## 1. 本次要完成什么

S0.1 只验证了“没有数据库也能启动”的边界。S0.2 将连接真实 Supabase，但仍然只建设工程底座，不创建政策、用户、咨询或其他业务表。

完成后，后端应能通过数据库连接检查，重复执行空库迁移，并能验证由 Supabase 当前签名密钥签发的访问令牌。旧的 Legacy HS256 Secret 不作为新系统的长期认证方案。

## 2. 配置项

在项目根目录 `.env` 中配置：

```env
DATABASE_URL="Supabase Session pooler 的 URI"
SUPABASE_URL="https://<project-ref>.supabase.co"
SUPABASE_JWKS_URL=""
SUPABASE_JWT_ISSUER=""
SUPABASE_JWT_AUDIENCE=authenticated
```

`SUPABASE_JWKS_URL` 和 `SUPABASE_JWT_ISSUER` 默认根据 `SUPABASE_URL` 推导；只有使用代理或测试地址时才需要填写。所有密钥只留在服务端 `.env`，不进入前端或 Git。

## 3. 数据和接口流转

| 动作 | 处理 | 验收 |
|---|---|---|
| 启动后端 | 读取 `DATABASE_URL`，通过 `psycopg` 连接 Supabase | 配置正确时 `GET /api/v1/health/ready` 返回 `ready` 和 `database=ok` |
| 执行迁移 | `alembic upgrade head` 执行 `0001_foundation_schema` | 创建 `app` schema；重复执行成功；不创建业务表 |
| 访问受保护接口 | 从 `SUPABASE_URL` 推导 JWKS 和 issuer，验证当前 ECC/RSA JWT | 合法令牌 `/api/v1/me` 返回主体；无效令牌 401；配置缺失 503 |
| 本地开发 bypass | 仅在 development 且 `AUTH_REQUIRED=false` 时启用 | 返回带 `development_bypass=true` 的明确开发主体；production 配置为 bypass 时拒绝就绪 |

## 4. 验收证据

验收日期：2026-08-05。

| 检查 | 结果 |
|---|---|
| Supabase 连接 | `SELECT 1` 和 runtime smoke 均返回 `database=ok` |
| 数据库迁移 | `alembic upgrade head` 首次执行成功；第二次执行无新增迁移 |
| 数据库结构 | `app` schema 存在；Alembic revision 为 `0001_foundation_schema`；`app` 业务表数量为 0 |
| 当前签名密钥 | JWKS 可访问，存在受支持的当前非对称签名密钥；未输出密钥内容 |
| 后端测试 | 22 个测试通过；仅保留上游 TestClient 弃用提示 |
| 代码检查 | Ruff 全部通过 |
| 本地 smoke | live、ready 降级边界、认证、模型边界和旧路由隔离全部通过 |
| 真实运行 smoke | database、authentication configuration、JWKS 全部为 `ok` |
| API 运行检查 | 新进程 `GET /api/v1/health/ready` 返回 HTTP 200、`status=ready`、database/authentication 均为 `ok/configured` |
| 前端回归 | TypeScript 与 Vite production build 通过 |
| 规格校验 | `openspec validate --all --strict --no-interactive`：3 项通过、0 项失败 |
| 密钥保护 | 检查和日志未输出数据库密码、JWT、连接字符串或 JWKS 内容 |

OpenSpec 已归档到 `openspec/changes/archive/2026-08-05-establish-supabase-runtime/`，主规格已同步为 `openspec/specs/supabase-runtime/spec.md`。

## 5. 不在本次范围

本步骤不创建业务表、不做登录页面、不接入旧项目模型、不导入 Excel/FAISS/RAG 数据，也不创建 Supabase signing key。业务表和真实登录流程必须在后续 PRD/OpenSpec 中单独建设。
