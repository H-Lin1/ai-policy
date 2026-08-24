# TECH-V1-S0-04｜可观测性、功能开关与路由守卫

| 项目 | 内容 |
|---|---|
| 文档 ID | `TECH-V1-S0-04` |
| 版本 | `V1.1` |
| 状态 | 已完成并归档 |
| 对应步骤 | `S0.4` |
| OpenSpec change | `establish-runtime-observability` |
| 前置条件 | `S0.3` 已归档；共享 API 合同、错误信封和请求 ID 行为可用 |
| 目标 | 让服务的日志、请求追踪、存活/就绪语义、功能开关和前端路由守卫在第一批业务功能进入前形成一套可验证的运行时约定 |

## 1. 先用大白话说明

S0.3 统一了“接口怎么说话”。S0.4 统一“服务怎么被观察和被开关控制”：

1. 每条日志都能对应到一个请求，出问题时可以按请求 ID 串起来；
2. 日志是结构化 JSON，且不会把令牌、密码、连接串打进日志；
3. `live` 只回答“进程还活着”，`ready` 只回答“依赖能不能干活”，两者都不被缓存；
4. 哪些功能对外开放由后端功能开关决定，前端不自己猜；
5. 未开放的页面由前端路由守卫拦下来，明确显示“未开放”，而不是渲染空壳或假数据。

本步骤不新增业务表、不执行数据库迁移、不接入模型、不做登录页面，也不实现任何真实业务功能。

## 2. 已确认并修复的缺陷

| 缺陷 | 现状（已在本机复现） | 处理 |
|---|---|---|
| 未处理异常响应缺少请求 ID 响应头 | `GET` 触发未捕获异常时，错误体里有 `request_id`，但响应头没有 `X-Request-ID`，因为该响应由最外层的 `ServerErrorMiddleware` 直接返回，不再经过请求上下文中间件 | 所有错误处理器在返回时显式携带 `X-Request-ID` 头 |
| 非中间件日志丢失请求上下文 | `ai_policy.errors` 等 logger 打出的记录为 `request_id=-`，无法和同一请求的访问日志关联 | 用 `contextvar` 保存请求 ID，日志过滤器统一从上下文取值 |
| CORS 预检缺少请求 ID | `CORSMiddleware` 在请求上下文之外直接返回预检响应，导致响应没有 `X-Request-ID` | 调整中间件顺序，让请求上下文包住 CORS，并向浏览器暴露请求 ID 响应头 |
| 异常与消息文本可能泄露敏感值 | 原脱敏只处理顶层结构化字段；异常消息、堆栈或嵌套对象里的凭据表示可原样进入日志 | 对嵌套字段、消息、对象表示和异常堆栈统一做有界脱敏 |
| 真实进程混入非结构化日志 | Uvicorn 启停与访问日志沿用独立文本 handler；其重复访问日志还发生在请求上下文清理后，无法关联请求 ID | Uvicorn 生命周期日志进入统一 JSON 管道；关闭无法关联的重复 access logger，保留应用访问日志 |

## 3. 运行时约定

### 3.1 结构化日志

| 规则 | 约定 |
|---|---|
| 格式 | 单行 JSON，字段固定包含 `timestamp`、`level`、`logger`、`message`、`request_id` |
| 请求字段 | 访问日志额外包含 `method`、`path`、`status_code`、`duration_ms` |
| 请求关联 | 请求 ID 存放在 `contextvar`，任何 logger 的记录都能自动带上；请求外的记录为 `-` |
| 脱敏 | `authorization`、`token`、`password`、`secret`、`api_key`、`database_url`、`cookie` 等结构化键名及嵌套值统一替换为 `***`；消息、对象表示和异常文本再清理常见键值、Bearer、JWT 与数据库连接串形式 |
| 异常 | 未处理异常在服务端保留经过脱敏的堆栈，响应体只返回稳定错误码，不含堆栈 |
| 真实进程 | Uvicorn 生命周期日志复用相同 JSON/text formatter；请求访问只由带上下文的 `ai_policy.http` 记录，避免重复且无请求 ID 的 Uvicorn access 行 |
| 级别 | 由 `LOG_LEVEL` 控制，默认 `INFO` |

日志格式可通过 `LOG_FORMAT` 选择 `json`（默认）或 `text`（本地阅读用）。两种格式都经过同一套脱敏。

### 3.2 请求 ID

沿用 S0.1 的规则：合法的调用方 `X-Request-ID` 原样保留，否则生成。S0.4 补齐四点：请求 ID 进入 `contextvar`；所有成功、失败和 CORS 预检响应都带 `X-Request-ID` 头；浏览器可以读取该响应头；请求结束后清理上下文，避免串号。

### 3.3 存活与就绪语义

| 接口 | 语义 | 依赖访问 | 缓存 |
|---|---|---|---|
| `GET /api/v1/health/live` | 进程和路由层可用 | 不访问数据库、JWKS 或模型 | `Cache-Control: no-store` |
| `GET /api/v1/health/ready` | 依赖可用性；开发缺配置为降级、生产不可用为 503 | 数据库连通性检查、认证配置状态 | `Cache-Control: no-store` |
| `GET /api/v1/health` | 浏览器友好聚合视图，不用于运维判活 | 同 ready | `Cache-Control: no-store` |

`ready` 的检查项在本步骤增加功能开关快照，用于确认运行环境实际生效的开关，仍不返回任何密钥或连接串。生产环境如果开启了演示 Mock 开关，`ready` 必须显式给出不合规状态，不允许静默通过。

### 3.4 功能开关

开关从环境变量读取，集中在一处注册，禁止在业务代码里散落布尔判断。

| 开关 | 环境变量 | 默认 | 含义 |
|---|---|---|---|
| `mocks` | `ENABLE_MOCKS` | `false` | 演示用 Mock 数据总闸。生产强制视为关闭，并在就绪检查中标记为不合规配置 |
| `policy_workspace` | `ENABLE_POLICY_WORKSPACE` | `false` | 首批政策业务工作区是否对外开放。阶段 0 保持关闭 |

新增只读接口 `GET /api/v1/system/features`，返回运行环境、认证是否必需和开关快照，供前端路由守卫使用。该接口是系统能力，不返回业务数据，也不返回任何配置值本身。

请求未知开关名时按关闭处理，不抛异常、不默认开启。

### 3.5 前端路由守卫

前端在启动时读取一次 `GET /api/v1/system/features`，把结果放入运行时配置上下文，路由守卫据此决定渲染：

| 状态 | 页面表现 |
|---|---|
| 加载中 | 显示加载态，不渲染受保护内容 |
| 开关关闭 | 显示“功能尚未开放”，说明依据来自后端开关，不渲染任何业务内容或占位假数据 |
| 后端不可达 | 显示连接错误和重试操作，不假设功能开放 |
| 开关开启 | 渲染受保护内容 |

阶段 0 用 `/policies` 这条受 `policy_workspace` 控制的路由验证守卫行为；该路由在阶段 0 只有守卫和未开放说明，真实政策页面属于 B1.x 的纵向切片。

## 4. 实现边界

```text
backend/app/core/context.py        请求 ID contextvar
backend/app/core/logging.py        JSON/text 格式化、脱敏、上下文注入
backend/app/core/middleware.py     请求上下文写入与清理、访问日志
backend/app/core/errors.py         错误处理器补齐 X-Request-ID 响应头
backend/app/core/features.py       开关注册表和快照
backend/app/modules/system/        features 接口、健康响应缓存头
frontend/src/lib/api/client.ts     features 请求
frontend/src/app/runtime/          运行时配置上下文
frontend/src/app/guards/           功能开关路由守卫
frontend/scripts/                  可重复执行的守卫 SSR 验收
```

不改动：Supabase schema、认证验证逻辑、共享分页与 UTC 合同、错误码语义、既有成功响应字段、模型适配器行为。

## 5. 验收标准

- 请求 ID 在成功响应、CORS 预检、4xx、5xx 的响应头和错误体中一致，并出现在同一请求的所有应用访问日志记录中。
- 应用和 Uvicorn 生命周期日志均为可解析的 JSON；结构化字段、消息和异常堆栈中的常见敏感值被替换；未处理异常的响应体不含堆栈。
- `live` 不触发数据库或 JWKS 访问；`live`、`ready`、`health` 均返回 `Cache-Control: no-store`。
- 生产环境开启 Mock 开关时，就绪检查给出显式不合规状态。
- `GET /api/v1/system/features` 返回开关快照；未知开关按关闭处理。
- 前端在开关关闭、缺失、加载中和后端不可达状态下都不渲染受保护内容，且不出现假数据；五态测试可由仓库命令重复执行。
- 后端测试、Ruff、前端守卫测试与 `npm run build`、本地和真实依赖 runtime smoke、绑定端口运行态检查、OpenSpec strict validate 全部通过。
- 不执行数据库迁移，不修改 Supabase 数据，不输出密钥、令牌或连接串。

## 6. 实施与验证证据

验收日期：2026-08-06。

| 检查项 | 命令/方式 | 结果 |
|---|---|---|
| 后端测试 | `.venv/bin/python -m pytest` | `47 passed`（S0.3 为 28，新增 19 条 S0.4 测试；仅剩 1 条第三方弃用警告） |
| Python 质量检查 | `.venv/bin/ruff check --no-cache .` | `All checks passed` |
| 前端类型检查与生产构建 | `npm run build` | `tsc -b` 无错误；Vite 转换 37 个模块并构建成功 |
| 前端守卫五态 | `npm run test:feature-guard` | loading、error、disabled、missing-flag、enabled 共 5 项通过；前四态均不渲染受保护内容；无需新增依赖 |
| 本地 smoke | `.venv/bin/python scripts/smoke.py` | live、ready、auth、model、legacy_route_absent、health_not_cacheable、features_snapshot、error_request_id_header、cors_preflight_request_id 共 9 项 `ok` |
| 真实依赖 runtime smoke | `.venv/bin/python scripts/runtime_smoke.py` | database、authentication_configuration、JWKS 均为 `ok` |
| 绑定端口运行态 | Uvicorn 绑定 `127.0.0.1:8013` 后用 HTTP 访问 | live、ready、CORS 预检和 OpenAPI 均通过；CORS 预检回显请求 ID；进程已正常关闭 |
| 运行态日志 | 采集真实 Uvicorn stdout 并逐行 `json.loads` | 应用及 Uvicorn 生命周期行全部为合法 JSON；应用访问日志关联请求 ID；重复且无法关联的 Uvicorn access logger 已关闭；敏感值隔离测试通过 |
| 运行态 OpenAPI | 访问 `/openapi.json` | 6 个 operation ID 唯一，含 `systemFeatures`；所有路径均为 `/api/v1/` |
| 功能开关接口 | `GET /api/v1/system/features` | 只返回环境名、`auth_required` 和布尔快照；配置了数据库连接串和 Supabase URL 时响应中均不出现 |
| OpenSpec 校验 | `openspec validate --all --strict` | 归档后 5 项通过、0 项失败 |
| 数据边界 | 无迁移命令、无 Supabase 写入 | 未执行迁移，未修改 Supabase 数据 |

### 6.1 本次修复的缺陷已验证

除原有 500 头体一致和跨 logger 请求 ID 关联测试外，新增回归覆盖 CORS 预检请求 ID 与浏览器可见响应头、嵌套/消息/异常堆栈脱敏，以及 Uvicorn logger 的统一 JSON 管道。五项守卫状态由 `frontend/scripts/feature-guard-render-test.mjs` 直接渲染验证。

### 6.2 环境复验结论

此前记录为环境受限的真实 Supabase/JWKS 连通性和端口绑定已在本次验收中重新执行并通过。前端守卫测试使用项目既有的 Vite、React 和 `react-dom/server`，没有下载新依赖，也不再依赖一次性手工命令。

## 7. 风险与回滚

- 日志格式变化可能影响本地阅读习惯：保留 `LOG_FORMAT=text` 选项。
- 功能开关快照如果包含过多运行信息会有信息泄露风险：只暴露布尔开关、环境名和认证是否必需，不暴露 URL、密钥或连接串。
- 前端启动时多一次接口请求，失败会阻塞受保护路由：守卫必须提供重试，且不因该请求失败影响公开页面。
- 本步骤没有数据库迁移，回滚只需撤销日志、上下文、开关和守卫相关代码。

## 8. 变更记录

| 日期 | 版本 | 变化 |
|---|---|---|
| 2026-08-06 | V1.0 | 建立 S0.4 日志、请求追踪、健康语义、功能开关和前端路由守卫方案。 |
| 2026-08-06 | V1.0 | 完成实现与自动化验证；修复未处理异常缺少请求 ID 响应头和非中间件日志丢失请求上下文两个缺陷；记录沙箱导致的未验证项。 |
| 2026-08-06 | V1.1 | 完成独立复验修正：补齐 CORS 预检请求 ID、消息/异常脱敏、Uvicorn JSON 日志和可重复守卫五态测试；真实依赖与端口运行态复验通过。 |
