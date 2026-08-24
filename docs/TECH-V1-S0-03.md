# TECH-V1-S0-03｜API、分页、错误与时间规范

| 项目 | 内容 |
|---|---|
| 文档 ID | `TECH-V1-S0-03` |
| 版本 | `V1.0` |
| 状态 | 已完成并归档 |
| 对应步骤 | `S0.3` |
| OpenSpec change | `standardize-api-contracts` |
| 飞书文档 | [TECH-V1-S0-03](https://a9ihi0un9c.feishu.cn/docx/B2KaddUh6oQME9x4O2cc7GXznue) |
| 前置条件 | `S0.2` 已归档；Supabase/JWT 运行底座可用 |
| 目标 | 在第一批业务接口出现前，冻结所有接口共同遵守的路径、错误、分页和时间格式 |

## 1. 先用大白话说明

这一步不是增加业务功能，而是先把“接口说话的方式”统一起来。以后政策列表、历史问答、咨询和 AI 接口都按同一套规则返回，前端就不用为每个页面重新猜字段、猜错误状态或自己拼分页。

本步骤不新增业务表、不执行迁移、不接入模型，也不制作新的页面。它只提供可以被后续模块直接复用的 API 合同和测试。

## 2. 已冻结的规则

| 规则 | 统一约定 | 例子 |
|---|---|---|
| API 路径 | 所有新接口使用 `/api/v1`；旧的 `/classify` 等历史路由不注册 | `/api/v1/policies` |
| 成功响应 | 单个资源直接返回资源对象；列表使用 `items + meta` | `{ "items": [], "meta": {...} }` |
| 错误响应 | 固定包含 `error.code`、`error.message`、`error.details`、`request_id`；响应头也有 `X-Request-ID` | 422 `VALIDATION_ERROR` |
| 分页 | `page` 从 1 开始，默认 1；`page_size` 默认 20，最大 100 | `?page=2&page_size=20` |
| 分页元数据 | `page`、`page_size`、`total`、`total_pages`、`has_next`、`has_previous` | 空结果的 `total_pages=0` |
| 时间 | API 接收带时区的时间，统一转 UTC；输出 RFC 3339 的 `Z` 结尾 | `2026-08-06T00:00:00Z` |
| OpenAPI | 每个操作有稳定 operation ID、标签、成功模型和适用的错误模型 | `/openapi.json`、`/docs` |

## 3. 数据流转

### 3.1 普通请求

浏览器或脚本 → `/api/v1` 路由 → Pydantic 校验 → 业务 service → typed response。成功时保持直接的资源结构，不额外包一层无意义的 `data`。

### 3.2 分页请求

前端传入 `page` 和 `page_size` → 后端校验范围 → repository 未来按 offset 查询 → service 计算总数和导航信息 → 返回 `items` 与 `meta`。没有数据时返回空数组和明确的零总数，不返回假数据。

### 3.3 错误请求

校验错误、HTTP 方法错误、业务错误或内部异常 → 统一错误处理器 → JSON 安全编码 `details` → 返回稳定错误码和请求 ID。真实服务失败不会转成 Mock 成功响应。

### 3.4 时间字段

带时区的输入先转换为 UTC → 数据库后续使用 UTC 时间类型 → API 输出带 `Z` 的 RFC 3339 字符串 → 前端展示时再转换为中国时区。没有时区的时间直接拒绝，不猜测开发机时区。

## 4. 实现边界

后端共享合同位于 `backend/app/api/contracts.py`，包括错误模型、分页参数/元数据、泛型分页响应和 `UtcDateTime`。错误处理器位于 `backend/app/core/errors.py`；系统路由声明稳定 operation ID 和 OpenAPI 错误响应；应用 OpenAPI 额外公开共享合同模型。

前端仍使用轻量手写 API 客户端，不在当前阶段引入代码生成工具。客户端现在会保留后端错误码、详情、请求 ID 和 HTTP 状态，并导出分页与 UTC 字符串类型，后续业务模块直接复用。

本步骤不改变 Supabase schema、认证行为、权限规则、模型适配器、日志架构或任何成功响应的既有字段。

## 5. 验收标准

- 后端契约测试覆盖分页默认值、边界值、空结果、UTC 偏移归一化、无时区拒绝、错误详情 JSON 安全、405 错误和 OpenAPI operation ID 唯一性。
- `/openapi.json` 中所有当前 API 路径均以 `/api/v1/` 开头，错误响应引用 `ApiErrorResponse`，并公开共享分页模型。
- 旧 `POST /classify` 仍为 404，且错误体和请求 ID规则不变。
- 后端测试、Ruff、前端 TypeScript/Vite build、既有 runtime smoke 和全量 OpenSpec strict validate 全部通过。
- 不执行数据库迁移，不改变 Supabase 数据，不输出密钥或令牌。

## 6. 实施与验证证据

本步骤已完成代码实现和自动化验证，证据如下：

| 检查项 | 命令/方式 | 结果 |
|---|---|---|
| 后端契约与回归测试 | `.venv/bin/pytest` | `28 passed`（仅有 1 条第三方弃用警告） |
| Python 质量检查 | `.venv/bin/ruff check .` | `All checks passed` |
| 前端类型检查与生产构建 | `npm run build` | `tsc -b` 和 Vite build 成功 |
| Supabase/JWKS 运行态 | `.venv/bin/python scripts/runtime_smoke.py` | `database: ok`、`authentication_configuration: ok`、`jwks: ok` |
| OpenAPI 静态与运行态检查 | 导入 `app.openapi()`，并访问 `http://127.0.0.1:8002/openapi.json` | 所有路径均为 `/api/v1/`；5 个 operation ID 唯一；共享错误/分页模型存在；`x-api-version=v1` |
| 运行态存活检查 | `GET http://127.0.0.1:8002/api/v1/health/live` | HTTP 200 |

8001 端口上的旧进程因当前权限无法停止，本步骤没有强行绕过权限；最新代码使用 8002 独立启动并完成运行态验收。没有执行数据库迁移，也没有修改 Supabase 数据。

## 7. 回滚与后续衔接

S0.3 没有数据库迁移，回滚只需撤销共享合同、错误处理器和 OpenAPI 元数据变更。下一步 S0.4 将在这套合同之上继续完善日志、请求 ID、健康检查、功能开关和路由守卫；第一批业务接口必须复用本方案，不得另造分页或错误格式。

## 8. 变更记录

| 日期 | 版本 | 变化 |
|---|---|---|
| 2026-08-06 | V1.0 | 建立 S0.3 API、OpenAPI、分页、错误和 UTC 时间规范及实施方案。 |
| 2026-08-06 | V1.0 | 完成实现、自动化验证和运行态 OpenAPI 验收；创建飞书同步文档。 |
