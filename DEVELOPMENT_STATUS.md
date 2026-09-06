# AI 政策服务平台｜跨对话开发状态

> 这是项目级进度的唯一记录入口。每次开始新的对话或开发任务，先读取本文件，再读取当前 active change 的 OpenSpec；未完成当前步骤时不得跳到后续步骤。

## 当前指针

| 字段 | 当前值 |
|---|---|
| 基线版本 | AI 政策服务平台 V1.0 `v1.1` |
| 默认路径 | 单人串行；除非明确记录并行授权 |
| 当前步骤 | `B1.8`（阶段功能完善与优化） |
| 当前状态 | `in_progress`（持续收集、修复并验收现有功能问题） |
| 产品/技术方案 | [`PRD-V1-B1-08`](./docs/PRD-V1-B1-08.md)；B18-010/011 见 [`PRD-V1-B1-08-ADMIN-HOMEPAGE-AND-ACCOUNTS`](./docs/PRD-V1-B1-08-ADMIN-HOMEPAGE-AND-ACCOUNTS.md) / [`TECH-V1-B1-08-ADMIN-HOME-ACCOUNTS`](./docs/TECH-V1-B1-08-ADMIN-HOME-ACCOUNTS.md) |
| OpenSpec change | [`2026-09-06-refine-admin-home-and-account-management`](./openspec/changes/archive/2026-09-06-refine-admin-home-and-account-management/)（B18-010/011，已归档） |
| 上一步 | `B1.7` 已归档；第一批联调与演示重置验收通过 |
| 下一步 | B18-010/011 已归档；本次改动准备推送到 GitHub，服务器可拉取 `main` 后执行 `0008` 及后续迁移核对；B1.8 继续按问题驱动收集优化项。 |
| 阻塞项 | 无；B1.5 真实 RAG 仍为独立的外部交接/验收事项，当前交接基线为政策库具体条款检索与生成。 |
| 飞书同步 | [`产品prd`](https://a9ihi0un9c.feishu.cn/drive/folder/Wrq0fzgr4lO4mqdBLyFcKvNJnbb) 已同步 UI1.5：[`TECH-V1-UI-06`](https://a9ihi0un9c.feishu.cn/docx/MRDsdr4WLohFV2xMPYmc2xjpnVy) 以机器人身份创建，父目录归属、正文结构与用户 `full_access` 已回读验证；UI1.4、UI1.3、UI1.2 和 B1.5 文档保持已同步状态 |
| 最近证据 | 2026-09-06：B18-010/011 已完成。管理员登录直接进入 `/homepage`，导航仅首页/政策中心/历史问答，三个管理功能由首页进入，`/admin` 为 404。`0008` 已应用本机 standalone；账号新增、编辑、停用/恢复、登录拒绝/恢复、自停用/占用部门/非管理员拒绝与审计均通过。桌面/移动账号页 14 个账号、无横向溢出；全量测试、Ruff、build、OpenSpec strict 通过。 |
| 最近更新时间 | 2026-09-06 |

本次范围决定：在 B1.7 与 B2.x 之间增加 B1.8“阶段功能完善与优化”。B1.8 只针对 B1.1-B1.7 现有功能持续检查、修复与优化；每个问题都记录到 `PRD-V1-B1-08` 并独立验收，涉及需求合同、API、数据库或权限变化时建立对应 TECH/OpenSpec。

## 状态值

- `pending`：依赖未满足，不能开始；
- `in_progress`：当前对话可以继续；
- `blocked`：有明确阻塞，下一对话先处理阻塞；
- `accepted`：验收通过，等待归档；
- `archived`：已归档，允许进入下一步。

只有当前步骤为 `archived`，才能把下一步骤改为 `in_progress`。并行开发必须写明参与者、范围和合并验收，不改变默认串行顺序。

## 默认串行路线

```text
S0.1 → S0.2 → S0.3 → S0.4 → S0.5 → S0.6
→ B1.1 → UI1.0 → B1.2 → B1.3 → B1.4 → B1.5 → B1.6 → B1.7 → B1.8
→ B2.1 → B2.2 → B2.3 → B2.4 → B2.5 → B2.6 → B2.7
→ B3.1 → B3.2 → B3.3
```

阶段 0 的工程子步骤：

| ID | 内容 | 状态 | 依赖 |
|---|---|---|---|
| S0.1 | 前后端骨架、环境模板、启动说明 | `archived` | 无 |
| S0.2 | 配置真实 Supabase 连接并执行空库迁移、适配当前 JWKS JWT | `archived` | S0.1 |
| S0.3 | `/api/v1`、OpenAPI、分页/错误/时间规范 | `archived` | S0.2 |
| S0.4 | 日志、请求 ID、live/ready、功能开关、路由守卫 | `archived` | S0.3 |
| S0.5 | DepartmentClassifier 适配器边界 | `archived` | S0.4 |
| S0.6 | 初始化、演示重置、冒烟和阶段 0 验收 | `archived` | S0.5 |

第一批核心闭环：

| ID | 内容 | 状态 | 依赖 |
|---|---|---|---|
| B1.1 | 身份、组织、地区与权限 | `archived` | S0.6 |
| UI1.0 | 旧站视觉基线补丁 | `archived` | B1.1 |
| B1.2 | 政策库 | `archived` | UI1.0 |
| B1.3 | 历史问答 | `archived` | B1.1 |
| B1.4 | 分类基础 | `archived` | B1.1 |
| B1.5 | 政策/问答检索与 RAG | `archived`（真实 RAG 后端待外部交接/验收） | B1.2、B1.3、B1.4 |
| B1.6 | 咨询闭环 | `archived`（部署与真实跨账号验收通过；补充说明、多轮消息和消息时间线不在范围内） | B1.1 |
| B1.7 | 第一批联调与演示重置 | `archived`（审计通过；安全重置仅预检，结果 `already_clean`，未执行删除） | B1.1-B1.6 |
| B1.8 | 阶段功能完善与优化 | `in_progress`（持续问题驱动；B18-001 至 B18-011 已完成；阶段收口后再进入 B2.x） | B1.1-B1.7 |

## 跨对话恢复协议

1. 先读本文件，确认 `当前步骤`、`当前状态`、`阻塞项` 和 `active change`。
2. 再读该 change 的 `proposal.md`、`specs/`、`design.md` 和 `tasks.md`，以文件内容而不是聊天记忆为准。
3. 如果状态为 `in_progress`，只继续当前步骤；如果为 `blocked`，先处理阻塞；如果为 `accepted`，先补齐归档证据；如果为 `pending`，先创建对应方案和 change。
4. 每完成一个可验证任务，立即更新 OpenSpec `tasks.md`；每次暂停前更新本文件的证据、下一步、阻塞项和时间。
5. 只有 PRD/技术方案验收通过、测试证据齐全、OpenSpec strict validate 通过并完成 archive，才能推进路线中的下一项。
6. 需求、API、表结构、模型输出或权限变化必须先更新上游文档和 OpenSpec，不能只改代码。

## 完成记录

| 步骤 | 技术/PRD | OpenSpec change | 状态 | 验收证据 | commit/日期 |
|---|---|---|---|---|---|
| S0.1 | `TECH-V1-S0-01` | [`establish-project-foundation`](./openspec/changes/archive/2026-08-05-establish-project-foundation/) | `archived` | strict validate、10 个后端测试、ruff、smoke、前端 build、Vite/ASGI 端到端检查；Supabase 实库迁移待 S0.2 | 未提交 / 2026-08-05 |
| 修复 | `TECH-V1-S0-01` | [`standardize-not-found-errors`](./openspec/changes/archive/2026-08-05-standardize-not-found-errors/) | `archived` | 未注册路由统一返回 `ROUTE_NOT_FOUND` 错误体；后端 10 个测试、Ruff、smoke 和 strict validate 通过 | 未提交 / 2026-08-05 |
| S0.2 | `TECH-V1-S0-02` | [`establish-supabase-runtime`](./openspec/changes/archive/2026-08-05-establish-supabase-runtime/) | `archived` | 真实 Supabase 迁移重复执行成功；当前 ECC/JWKS 可用；22 个后端测试、Ruff、runtime smoke、前端 build、运行态 ready 和 strict validate 通过 | 未提交 / 2026-08-05 |
| S0.3 | [`TECH-V1-S0-03`](./docs/TECH-V1-S0-03.md)（[飞书版](https://a9ihi0un9c.feishu.cn/docx/B2KaddUh6oQME9x4O2cc7GXznue)） | [`standardize-api-contracts`](./openspec/changes/archive/2026-08-06-standardize-api-contracts/) | `archived` | 共享错误、分页、UTC 合同和 OpenAPI 元数据完成；28 个后端测试、Ruff、前端 build、runtime smoke、8002 运行态 OpenAPI 检查及 strict validate 通过；无迁移、无 Supabase 数据变更 | 未提交 / 2026-08-06 |
| S0.4 | [`TECH-V1-S0-04`](./docs/TECH-V1-S0-04.md)（[飞书版](https://a9ihi0un9c.feishu.cn/docx/O6mvdBscTo17PwxKfzLcRaKpnwf)） | [`establish-runtime-observability`](./openspec/changes/archive/2026-08-06-establish-runtime-observability/) | `archived` | JSON 结构化日志及嵌套/消息/异常脱敏、请求 ID 跨 logger 与 CORS 预检传播、错误响应头补齐、Uvicorn 生命周期 JSON 日志、live/ready 语义与 `no-store`、后端功能开关与 `/api/v1/system/features`、前端运行时配置与路由守卫完成；47 个后端测试、Ruff、前端五态 SSR 测试/build、本地 smoke 9 项、Supabase/database/JWKS runtime smoke、真实 Uvicorn 运行态与归档后 strict validate 均通过；无迁移、无 Supabase 数据变更 | 未提交 / 2026-08-06 |
| S0.5 | [`TECH-V1-S0-05`](./docs/TECH-V1-S0-05.md)（[飞书版](https://a9ihi0un9c.feishu.cn/docx/KMLudmKi8ofiY6xUWCacVnh3nOc)） | [`2026-08-06-establish-department-classifier-adapter`](./openspec/changes/archive/2026-08-06-establish-department-classifier-adapter/) | `archived` | 输入 NFKC/空白/地区规范化、显式地区注册表与无 fallback、typed 预测/结果/readiness 不变量、资产 manifest 只读校验、domain error、settings-aware factory、readiness no-store/fail-closed 完成；后端 94 项测试、Ruff、前端守卫/build、本地 smoke 12 项、真实依赖 runtime smoke、8014 运行态、归档前 strict 6/6 和归档后 strict 5/5 通过；无迁移、无 Supabase 数据变更 | 未提交 / 2026-08-06 |
| S0.6 | [`TECH-V1-S0-06`](./docs/TECH-V1-S0-06.md)（[飞书版](https://a9ihi0un9c.feishu.cn/docx/TXHldW57LobLVFxePw3cKXf7nCF)） | [`2026-08-06-complete-stage-zero-acceptance`](./openspec/changes/archive/2026-08-06-complete-stage-zero-acceptance/) | `archived` | 初始化双重门禁及固定 Alembic config/revision/target、reset no-op、ambient-safe smoke、只读 runtime foundation 检查、统一 acceptance 完成；后端 114 项、Ruff、12 项 smoke、前端 5 态/build、runtime/8016/归档前 strict 7/7 和归档后 strict 6/6 通过；无迁移、删除或 Supabase 写入 | 未提交 / 2026-08-06 |
| B1.1 | [`PRD-V1-B1-01`](./docs/PRD-V1-B1-01.md)（[飞书版](https://a9ihi0un9c.feishu.cn/docx/EHjgdMGz0oaYGQxBqGPcXLnDn2c)） / [`TECH-V1-B1-01`](./docs/TECH-V1-B1-01.md)（[飞书版](https://a9ihi0un9c.feishu.cn/docx/AHZpd5sDfoJ56DxBxS4c2HbHnTb)） | [`2026-08-07-establish-identity-access`](./openspec/changes/archive/2026-08-07-establish-identity-access/) | `archived` | `0002_identity_access`、五表 RLS/浏览器拒绝、数据库身份/RBAC、Supabase 前端会话、双重门禁 seed 完成；两次 seed 的第二次完整行/时间戳零变化，计数 `1/4/3/4/4`；四真实账号 4 个允许与 12 个跨角色拒绝通过；移动端退出修正；后端 186、前端 31、Ruff、14 smoke、runtime、acceptance 6/6、归档前后 strict 7/7 通过 | 未提交 / 2026-08-07 |
| UI1.0 | [`PRD-V1-UI-01`](./docs/PRD-V1-UI-01.md)（[飞书版](https://a9ihi0un9c.feishu.cn/docx/MBDudlnbDoLyF8xgBfWcHSUGnMh)） / [`TECH-V1-UI-01`](./docs/TECH-V1-UI-01.md) | [`2026-08-07-align-legacy-visual-baseline`](./openspec/changes/archive/2026-08-07-align-legacy-visual-baseline/) | `archived` | “政通惠”顶部壳、公开双图片入口、登录/角色/显式状态视觉统一；真实个人允许与企业拒绝移动路径通过；前端 34、build 91 modules、后端 186、Ruff、14 smoke、runtime、acceptance 6/6、归档前后 strict 8/8 通过；PRD 飞书同步已回读验证；无数据库或旧源码操作 | 未提交 / 2026-08-07 |
| B1.2 | [`PRD-V1-B1-02`](./docs/PRD-V1-B1-02.md)（[飞书版](https://a9ihi0un9c.feishu.cn/docx/K1szdybv8oCKC0x2CfMciBfrneb)） / [`TECH-V1-B1-02`](./docs/TECH-V1-B1-02.md)（[飞书版](https://a9ihi0un9c.feishu.cn/docx/Ux4EdPaQboXkeRxYSYqciLIInbh)） | [`2026-08-11-establish-policy-library`](./openspec/changes/archive/2026-08-11-establish-policy-library/) | `archived` | 20 条确定性政府源 fixture、严格来源/hash 校验、政策列表/详情 API 与响应式前端完成；后端 200、Ruff、14 smoke、runtime、前端测试、build 91 modules、acceptance 6/6、桌面/移动浏览器和归档前后 strict 9/9 通过；PRD/TECH 飞书同步已回读验证；`0003` migration 与数据库导入未执行 | 未提交 / 2026-08-11 |
| B1.2-D1 | [`PRD-V1-B1-02`](./docs/PRD-V1-B1-02.md) V1.2 / [`TECH-V1-B1-02`](./docs/TECH-V1-B1-02.md) V1.3 | [`2026-08-11-provision-policy-library-sample`](./openspec/changes/archive/2026-08-11-provision-policy-library-sample/) | `archived` | 授权执行精确 `0003` 与 20 条 fixture；二次导入 0 插入且全字段/时间戳不变；真实身份数据库 API 10/20 列表与详情通过；后端 208、Ruff、14 smoke、runtime 5/5、前端测试/build、acceptance 6/6、归档前 10/10 与归档后 9/9 strict 通过；飞书 PRD/TECH 已回读验证；完整 CSV 与一切破坏性/未授权写入未执行 | 未提交 / 2026-08-11 |
| B1.2-P1 | [`TECH-V1-B1-02-P1`](./docs/TECH-V1-B1-02-P1.md)（[飞书版](https://a9ihi0un9c.feishu.cn/docx/VEgKdj6sRoFZh2xHK1vcGDEkn2b)） | [`2026-08-11-optimize-policy-list-performance`](./openspec/changes/archive/2026-08-11-optimize-policy-list-performance/) | `archived` | 请求级共享 Session、列表投影+窗口总数单 SQL、越界 fallback count；真实鉴权冷 `6,774 ms`、暖 `1,822/852/1,594 ms`（中位 `1,594 ms`），满足门槛；后端 213、Ruff、14 smoke、runtime 5/5、前端测试/build、acceptance 6/6、归档前 10/10 与归档后 9/9 strict 通过；无迁移、写入或缓存 | 未提交 / 2026-08-11 |
| B1.3 | [`PRD-V1-B1-03`](./docs/PRD-V1-B1-03.md)（[飞书版](https://a9ihi0un9c.feishu.cn/docx/Z8JNdKetmoolDhxupvlcJmkRnZf)） / [`TECH-V1-B1-03`](./docs/TECH-V1-B1-03.md)（[飞书版](https://a9ihi0un9c.feishu.cn/docx/AALldUP8koymyBx0FyZc3llhncc)） | [`2026-08-11-establish-historical-qa`](./openspec/changes/archive/2026-08-11-establish-historical-qa/) | `archived` | 授权执行 `0004_historical_qa` 与 20 条固定隐私筛选样本；二次导入 0 插入且 20 行审计时间不变；数据库 RLS 开启、浏览器 policy/grant 为 0；四真实身份均完成列表 `10/20` 与详情验证；后端 222、Ruff、14 smoke、runtime 5/5、前端 7 组 render tests/build、acceptance 6/6、归档前后 strict 10/10 通过；飞书同步回读通过；完整导入、删除、覆盖、Auth 写入和功能开关修改未执行 | 未提交 / 2026-08-12 |
| UI1.1 | [`TECH-V1-UI-02`](./docs/TECH-V1-UI-02.md) | [`2026-08-18-remove-stable-workspace-feature-gate`](./openspec/changes/archive/2026-08-18-remove-stable-workspace-feature-gate/) | `archived` | 移除 `policy_workspace` 配置/注册、前端 `FeatureGuard` 和 RuntimeConfigProvider；政策页面直接渲染并保留自身鉴权/加载/错误状态；Mock 开关与后端 API 安全边界保留；后端测试、Ruff、smoke/runtime、前端测试/build、strict 11/11 通过；无数据库写入 | 未提交 / 2026-08-18 |
| B1.4 | [`PRD-V1-B1-04`](./docs/PRD-V1-B1-04.md)（[飞书版](https://a9ihi0un9c.feishu.cn/docx/P6fXdqBkxosd85xTeYlcwi00nCb)） / [`TECH-V1-B1-04`](./docs/TECH-V1-B1-04.md)（[飞书版](https://a9ihi0un9c.feishu.cn/docx/EqxuddpTKoX4UFxiNAcc5Nirnpg)） | [`2026-08-21-establish-classification-foundation`](./openspec/changes/archive/2026-08-21-establish-classification-foundation/) | `archived` | 四资产 manifest、35 类深圳 CPU 分类适配器、鉴权 `/classifications` API 与 `/classify` 工作台完成；后端 238、Ruff、local smoke 14/14、runtime 5/5、前端 7 组 render/build、真实深圳身份两次结果一致、归档后 strict 12/12 通过；飞书回读验证；无迁移、数据库/Auth 写入、删除或 Mock fallback | 未提交 / 2026-08-21 |
| B1.5 | [`PRD-V1-B1-05`](./docs/PRD-V1-B1-05.md)（[飞书版](https://a9ihi0un9c.feishu.cn/docx/RAcsdg7WroHGwTxUxlncCVF7npf)） / [`TECH-V1-B1-05`](./docs/TECH-V1-B1-05.md)（[飞书版](https://a9ihi0un9c.feishu.cn/docx/L8radzyovo1GjUxTAvSc4YFanlc)） / [`RAG-BACKEND-HANDOFF-V1`](./docs/RAG-BACKEND-HANDOFF-V1.md)（本地 V2.0；飞书 V1.1 待同步） | [`2026-08-21-establish-policy-qa-entry`](./openspec/changes/archive/2026-08-21-establish-policy-qa-entry/) | `archived` | 首页与个人/企业问答入口、鉴权 `POST /api/v1/policy-answers`、显式 placeholder 引擎完成；真实 RAG 交接 V2.0 规定一期仅检索 `app.policy_documents` 的深圳具体条款，并以条款+问题生成回答和返回参考条款。后端 242、Ruff、local smoke 14/14、runtime 5/5、前端 8 组 render/build（92 modules）、真实身份 placeholder API、acceptance 6/6、归档前 strict 与归档后全局 strict 13/13 通过；无迁移、数据库/Auth 写入、删除、模型配置、索引或导入 | 未提交 / 2026-08-26 |
| UI1.2 | [`TECH-V1-UI-03`](./docs/TECH-V1-UI-03.md)（[飞书版](https://a9ihi0un9c.feishu.cn/docx/GjTZd8yRToeLhox47yKclDx0ndf)） | [`2026-08-21-align-policy-qa-visual-entry`](./openspec/changes/archive/2026-08-21-align-policy-qa-visual-entry/) | `archived` | 用户授权旧个人服务页面视觉对照后，独立实现首页/个人/企业问答优先的浅蓝画布、几何装饰、渐变问候、Chat 输入与圆形发送；未登录提交仅显示登录提示；后端 242、Ruff、local smoke 14/14、runtime 5/5、前端 8 组 render/build（92 modules）、acceptance 6/6、归档后全局 strict 13/13 通过；TECH 飞书正文/父目录/full_access 回读验证；无旧业务复用、迁移、数据库/Auth 写入、删除、模型或数据操作 | 未提交 / 2026-08-21 |
| UI1.3 | [`TECH-V1-UI-04`](./docs/TECH-V1-UI-04.md)（[飞书版](https://a9ihi0un9c.feishu.cn/docx/XVBUdW4c7oWDCIx01XrcVPXynic)） | [`2026-08-21-simplify-home-by-authentication-state`](./openspec/changes/archive/2026-08-21-simplify-home-by-authentication-state/) | `archived` | 未登录首页仅保留两张真实个人/企业入口（浏览器实测 0 textarea、0 问答组件、2 入口）；个人/企业登录首页直接进入问答主视觉，删除重复欢迎/身份/工作区概览，政府/管理员保留工作区访问；后端 242、Ruff、local smoke 14/14、runtime 5/5、前端 8 组 render/build（92 modules）、acceptance 6/6、归档后全局 strict 13/13 通过；TECH 飞书正文/父目录/full_access 回读验证；无迁移、数据库/Auth 写入、删除、模型或数据操作 | 未提交 / 2026-08-21 |
| UI1.4 | [`TECH-V1-UI-05`](./docs/TECH-V1-UI-05.md)（[飞书版](https://a9ihi0un9c.feishu.cn/docx/O87Qd5Jdlo2N3gxEOXNcRGNfndf)） | [`2026-08-21-center-authenticated-qa-hero`](./openspec/changes/archive/2026-08-21-center-authenticated-qa-hero/) | `archived` | 登录后个人/企业首页问答组于桌面在页头/页脚可用空间垂直居中，小屏自然流式；移除输入框下“从这里开始咨询 / 可咨询政策条件、办理方向或企业发展支持等问题”，保留 Enter/Shift+Enter 提示及加载/错误/回答状态；后端 242、Ruff、local smoke 14/14、runtime 5/5、前端 8 组 render/build（92 modules）、acceptance 6/6、归档后全局 strict 13/13 通过；TECH 飞书正文/父目录/full_access 回读验证；无迁移、数据库/Auth 写入、删除、模型或数据操作 | 未提交 / 2026-08-21 |
| B1.6 | [`PRD-V1-B1-06`](./docs/PRD-V1-B1-06.md) | [`2026-08-23-establish-consultation-workflow`](./openspec/changes/archive/2026-08-23-establish-consultation-workflow/) | `archived` | 单轮咨询闭环、35 个部门绑定、跨账号权限边界及公开投影验收通过；政民互动页面已通过桌面/移动布局核验。范围明确排除补充说明、多轮消息与消息时间线；测试数据仅按精确 B16 验收标记清理，普通咨询保留。 | 未提交 / 2026-08-23 |
| B1.7 | [`PRD-V1-B1-07`](./docs/PRD-V1-B1-07.md) | [`2026-08-23-b1-7-integration-demo-reset`](./openspec/changes/archive/2026-08-23-b1-7-integration-demo-reset/) | `archived` | 只读集成审计覆盖目标绑定、revision、10 张业务表/RLS、浏览器权限边界、35 个部门绑定、核心路由和本地门禁；后端 `241 passed`、Ruff、前端测试/build 通过。受保护演示重置仅预检，`already_clean`、`0/0/0`，未执行删除；归档后全局 strict `15 passed, 0 failed`。 | 未提交 / 2026-08-23 |
| B1.8 | [`PRD-V1-B1-08`](./docs/PRD-V1-B1-08.md) V0.6 | [`2026-08-23-refine-authenticated-home-routing`](./openspec/changes/archive/2026-08-23-refine-authenticated-home-routing/) | `in_progress` | B18-001 至 B18-006 已完成；B18-005/B18-006 前端全量测试、94 modules build、OpenSpec strict 与本地浏览器路由验收通过。阶段继续按问题驱动推进。 | 未提交 / 2026-08-23 |
