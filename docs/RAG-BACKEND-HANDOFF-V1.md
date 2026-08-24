# RAG-BACKEND-HANDOFF-V1 | 政策智能问答真实 RAG：AI 开发交接包

> 交接对象：实现真实政策/历史问答检索与生成能力的后端开发者。本文是 B1.5 占位流程后的唯一后端交接基线；任何数据库、模型、供应商或响应合同变更，都必须先创建新的 TECH 与 OpenSpec 并通过授权。

> **AI 交接结论**：本文件已足以让 AI 开始只读勘察和下一阶段方案设计；尚不足以授权 AI 直接实现、迁移、导入或启用真实 RAG。AI 不得自行选择模型、供应商、向量库、迁移方式或质量阈值。

## 0. 给 AI 的首轮任务（可直接复制）

```text
你在 AI 政策服务平台仓库中负责真实政策 RAG 的后续阶段。

开始前不得修改代码、环境、数据库、配置或飞书文档。请依序阅读：
1. DEVELOPMENT_STATUS.md；
2. docs/RAG-BACKEND-HANDOFF-V1.md；
3. docs/PRD-V1-B1-05.md 与 docs/TECH-V1-B1-05.md；
4. backend/app/modules/policy_qa/adapters.py、service.py、schemas.py、router.py；
5. 当前 active OpenSpec 的 proposal.md、specs/、design.md、tasks.md；
6. openspec/config.yaml。

先报告：当前步骤/状态、现有 API 合同、不可改变的安全边界、待确认决策与阻塞项。
随后仅建立下一阶段的 PRD、TECH 和 OpenSpec，严格验证通过前不得编码。
不得执行迁移、数据导入、删除、Auth 写入、索引重建、外网抓取、模型调用，或读取/输出任何密钥。
只有在负责人逐项确认本文件“AI 决策与授权门禁”并明确授权后，才能实施获批范围。
```

AI 的第一轮交付应是“待确认清单 + PRD/TECH/OpenSpec”，而不是 RAG 代码。

## 1. 交付目标与不可变合同

将当前 `PlaceholderPolicyAnswerEngine` 替换为真实 `PolicyAnswerEngine`，使 `POST /api/v1/policy-answers` 能基于深圳已批准语料回答个人与企业政策问题，并返回可追溯的来源。不得改变 URL、认证方式、请求字段、错误信封、`Cache-Control: no-store`、请求 ID、地区范围或前端响应字段。

当前稳定请求：

```http
POST /api/v1/policy-answers
Authorization: Bearer <Supabase access token>
Content-Type: application/json

{"question":"企业可以申请哪些科技创新支持？"}
```

当前和未来稳定响应形状：

```json
{
  "request_id": "opaque-request-id",
  "region_id": "sz",
  "answer_mode": "rag",
  "answer": "基于已检索到的政策材料，……",
  "sources": [
    {
      "source_type": "policy_document",
      "source_id": "uuid",
      "title": "政策标题",
      "source_url": "https://www.sz.gov.cn/...",
      "published_date": "2024-01-01",
      "excerpt": "与回答直接相关的短摘录"
    }
  ],
  "notices": []
}
```

`answer_mode` 仅允许 `placeholder` 与 `rag`。真实引擎成功时必须为 `rag`；不能把失败结果伪装为 `placeholder`。`sources` 最大 5 条，按在回答中的支持度排序；`excerpt` 必须是来源原文的短片段，不得由模型改写后伪装为引用。

## 2. 现有项目架构与集成位置

后端为 FastAPI + Pydantic + SQLAlchemy 2 模块化单体，全部 API 在 `/api/v1` 下。Supabase Auth 的 Bearer JWT 由后端验证，`get_current_identity` 负责读取应用内 profile/role/region/organization 并拒绝不活跃范围。浏览器不得直接读写 `app.*` 表；所有业务读取在 FastAPI 完成。

建议新增或完善以下文件，而非把检索逻辑放进路由：

```text
backend/app/modules/policy_qa/
  adapters.py       # PolicyAnswerEngine protocol、typed input/output、readiness
  service.py        # IAM、输入规范化、错误翻译、response mapping
  router.py         # POST /policy-answers，仅 HTTP 边界
  retrieval.py      # 只读语料检索接口与实现
  generation.py     # LLM provider adapter；不可泄露 provider 异常
  schemas.py        # Pydantic request/response
  ingestion.py      # 后续离线摄取任务，不能在 API 请求中运行
```

保留现有 `app.modules.intelligence` 分类器边界；可调用其分类结果作为可选 rerank/filter 信号，但不要耦合其内部 PyTorch 模型。禁止导入旧项目的 Flask、前端、RAG、FAISS、embedding 或全局状态代码。

### AI 代码地图与实现边界

| 位置 | 当前职责 | 真实 RAG 接入规则 |
|---|---|---|
| `backend/app/modules/policy_qa/adapters.py` | `PolicyAnswerEngine` 协议、typed 问题/结果/来源、placeholder 工厂 | 保持类型及“最多 5 个来源”的不变量；真实引擎只能通过显式、已验证配置选中，不能作为故障 fallback |
| `backend/app/modules/policy_qa/service.py` | IAM 范围、输入规范化、异常脱敏、响应映射 | 不将检索或模型调用塞入路由；不记录问题文本 |
| `backend/app/modules/policy_qa/router.py` | `POST /policy-answers` HTTP 边界、鉴权依赖与 `no-store` | 不改变 URL、认证方式、响应 schema 或缓存语义 |
| `backend/app/modules/policy_qa/schemas.py` | Pydantic 请求/响应 schema | 向后兼容；`excerpt` 最大 800 字符，`sources` 最大 5 条 |
| `backend/app/modules/intelligence/` | 既有分类器 | 仅可作为可选 rerank/filter 信号；不得耦合其 PyTorch 内部实现 |

AI 应先阅读上述实际文件，再设计 `retrieval.py`、`generation.py` 或离线 `ingestion.py`，不得仅根据本文重新猜测现有接口。

## 3. AI 决策与授权门禁

以下事项在负责人确认并写入下一阶段 TECH/OpenSpec 前均为 **blocked**。AI 可分析候选方案，但不得自行选择或实施。

| 待确认事项 | 必须确认的内容 | 未确认时允许的 AI 动作 |
|---|---|---|
| LLM / embedding | 供应商、具体模型、数据处理/出境约束、成本上限、凭据提供方式 | 只写方案；不添加 SDK、配置键或网络调用 |
| 向量存储 | `pgvector` 或独立受管索引、部署责任、备份与成本边界 | 不安装扩展，不创建表、索引或实例 |
| 语料范围 | 完整数据、有效状态筛选、历史问答权重、可激活版本 | 只读小样本做设计/测试；不导入或覆盖数据 |
| 检索策略 | 中文分块、chunk/overlap、top-k、重排、时效与多样性规则 | 提供可测候选参数，不自行定稿 |
| 无依据行为 | `200 rag + 保守说明` 或 `RAG_NO_GROUNDED_ANSWER`，以及前端文案 | 不修改 API/前端行为 |
| 质量门槛 | 标准问题集、引用命中/拒答/不可编造率、时延和成本阈值 | 编写评测计划，不宣称可上线 |
| 数据生命周期 | 是否持久化审计、反馈或会话，以及最小字段、保留期、删除和访问控制 | 默认不保存问答数据 |
| 变更授权 | migration 名称、表/索引、导入批次、启用/回滚窗口 | 不执行迁移、导入、重建或 Auth 操作 |

只有所有与当前实施范围有关的项目都明确为“已确认”，并且负责人授权后，才能从方案阶段进入编码阶段。

## 4. 已存在数据库与可用语料

数据库 schema 是 `app`；当前生产 revision 为 `0004_historical_qa`。下列两张表已经迁移、RLS 已启用、对 `anon`/`authenticated` 没有直接权限，且只可通过服务端读取：

| 表 | 主要字段 | 作为 RAG 来源的用途 |
|---|---|---|
| `app.policy_documents` | `id`, `region_id`, `region_code`, `title`, `document_no`, `issuing_organization`, `source_url`, `document_url`, `published_date`, `content_text`, `content_sha256`, `effective_status`, `reference_count`, `source_years`, `updated_at` | 官方政策全文；优先语料 |
| `app.historical_qa` | `id`, `region_id`, `region_code`, `topic`, `question_text`, `answer_text`, `source_url`, `question_at`, `replied_at`, `publishing_organization`, `legal_basis_name`, `legal_basis_citation`, `adjudication_result`, `content_sha256`, `updated_at` | 经隐私筛选的历史政务答复；辅助语料 |

两个表均强制 `region_code = 'sz'`。目前各有一小批已授权样本；完整数据导入不属于本交接范围。RAG 不得抓取外网、临时扩展到非政府来源、写回原文或修改上述表。所有来源 URL 必须在响应中保留，以便用户回到官方出处。

## 5. 推荐的摄取与索引设计（需新 OpenSpec 与迁移授权）

真实 RAG 应采用“离线摄取、线上只读检索”的流程。推荐新表而不是修改源表。**本节仅为设计输入：创建任何表、扩展、索引、定时任务或进行摄取前，必须有新的 OpenSpec、明确 migration/导入授权与运行验收。**

| 建议表 | 核心字段 | 约束 |
|---|---|---|
| `app.rag_corpus_versions` | `id`, `region_code`, `corpus_kind`, `source_revision`, `embedding_model_version`, `chunking_version`, `status`, `created_at`, `activated_at` | 一次激活仅一个同地区/语料类型版本；不可保存凭据 |
| `app.rag_chunks` | `id`, `corpus_version_id`, `source_type`, `source_id`, `source_sha256`, `chunk_index`, `content`, `content_sha256`, `token_count`, `metadata`, `embedding` 或外部向量键 | `(corpus_version_id, source_type, source_id, chunk_index)` 唯一；源 hash 改变必须重建 |
| `app.rag_query_runs`（可选） | `id`, `request_id`, `region_code`, `corpus_version_id`, `answer_mode`, `latency_ms`, `created_at` | 默认不存问题、回答、JWT、用户 ID；如需审计需另行隐私评审 |

向量库可使用经过批准的 PostgreSQL `pgvector` 或独立受管索引。选择和安装扩展、创建表、索引、定时任务或保留策略都需要单独 TECH/OpenSpec、迁移授权与运行验收。摄取幂等键应基于 `source_type + source_id + source_sha256 + chunking_version + embedding_model_version`。禁止在 API 请求路径中同步嵌入整库。

### AI 推荐工作顺序

1. **只读方案阶段（当前允许）**：检查现有 schema、测试、语料样本和服务边界；创建 PRD、TECH、OpenSpec，并在 TECH 中记录第 3 节所有决策、候选方案及其验收方式。
2. **索引/摄取阶段（需授权）**：获批后先实现 migration、离线摄取、版本激活、幂等重跑和回滚方案；不要先接线上模型。
3. **检索/生成阶段（需授权）**：在固定小型语料上实现确定性检索、引用验证、provider adapter、fail-closed 配置和 API 集成。
4. **质量/上线阶段（需授权）**：运行标准问题集、真实身份验证及完整测试门禁；只有达到已确认指标才把真实引擎标记为可用。

## 6. 检索、生成与引用规则

1. 先用当前身份限定 `region_code='sz'`，再检索已激活语料版本；无跨地区 fallback。
2. 以政策全文为优先来源；历史问答只能作为补充，且应保留其政府原始 URL。
3. 检索后进行去重、来源多样性和时效性处理；不得把 raw vector score 返回浏览器。
4. 将检索片段与问题传给受配置保护的 LLM adapter。系统提示必须要求“仅依据提供来源作答；证据不足时明确说明；不得编造政策、办理条件、期限、网址或引用”。
5. 输出前验证：answer 非空、最多 5 个来源、每个 `source_id` 可映射到已有语料、excerpt 属于对应 chunk、URL 为允许的官方来源 URL、无秘密/令牌/堆栈。
6. 当没有足够证据时，返回 `rag` 加保守说明和空 `sources`，或明确的 `RAG_NO_GROUNDED_ANSWER`；不得改走占位回答或互联网检索。

## 7. 配置、密钥与运行边界

仅后端环境可读取 RAG 配置。不得把 provider key、数据库 URL、索引 endpoint、模型路径、原始 prompt、语料绝对路径或用户身份映射返回 API、前端 runtime config、日志或异常消息。配置键名称、provider 选择、是否使用托管 LLM 和外部向量库均须在后续 TECH 中明确；本项目当前不预设具体供应商。

所有 provider 请求应设严格超时、有限重试和幂等/熔断策略。错误映射建议：`RAG_NOT_READY`（未配置/未激活语料，503）、`RAG_RETRIEVAL_FAILED`（安全失败，503）、`RAG_GENERATION_FAILED`（安全失败，503）、`RAG_NO_GROUNDED_ANSWER`（无证据，200 或 422，须在新规范确定）。不得回显第三方错误正文。

## 8. 权限、隐私和日志

入口仅限活跃深圳 `individual` 与 `enterprise` 角色。`government`、`admin` 若未来需要使用，必须单独调整 PRD/TECH/OpenSpec，而不是在 RAG 代码中放宽。请求文本、会话内容、来源全文、JWT 和 API key 不进入结构化日志。默认无会话历史、无用户画像、无问题持久化。

如业务要求保留问题、回答、反馈或人工转交，必须先完成数据最小化、保留期、删除流程、访问控制、用户告知和迁移授权设计。不能以调试为由直接写 `app.rag_query_runs` 或外部日志平台。

## 9. 测试与上线验收

真实实现至少需要：

- 单元测试：输入规范化、角色/范围、检索过滤、source 映射、引用验证、空证据、provider 超时/错误脱敏。
- 集成测试：固定小型语料下的确定性检索、完整响应 schema、`no-store`、request ID、RLS/无浏览器直连、无写入 API 请求。
- 质量集：带标准来源的中文个人/企业问题；分别度量来源命中、引用可追溯、无依据拒答和不可编造率。阈值必须在新的技术方案中确定，不能口头认定。
- 安全测试：提示注入、越权地区、敏感文本、恶意 URL、空/超长问题、提供商异常均不泄露内部信息。
- 运维验收：配置缺失 fail-closed、已激活语料版本可识别、索引与源 hash 一致、延迟/错误率可观测但不记录原文。

上线前必须完成：新的 OpenSpec strict validate、授权迁移/摄取（如适用）、后端测试、Ruff、前端 build、local/runtime smoke、真实已授权身份验证、文档和 `DEVELOPMENT_STATUS.md` 更新。未经明确授权，不执行任何迁移、批量导入、删除、重建索引或 Auth 操作。

### AI 交付检查表

在请求编码授权、合并或验收时，AI/开发者必须提供以下可复核交付物：

- [ ] 已阅读的文件与当前步骤/状态报告；
- [ ] 第 3 节所有相关决策的确认记录，以及本次获授权的精确范围；
- [ ] 新阶段 PRD、TECH、OpenSpec 与 strict validate 结果；
- [ ] migration/摄取设计（如适用），包含幂等键、激活、失败处理与回滚，不含任何秘密；
- [ ] 引擎、检索、生成、引用验证和配置隔离的测试证据；
- [ ] 固定质量集、已确认阈值和不含原始敏感内容的评测结果；
- [ ] 后端测试、Ruff、前端 build、local/runtime smoke、真实身份验证、飞书回读、`DEVELOPMENT_STATUS.md` 更新和 OpenSpec archive 证据。

任何一项缺失时，真实 RAG 必须保持未启用；当前 `placeholder` 只能作为明确的演示模式，绝不是生产故障的降级路径。

## 10. 明确禁止事项

- 未授权执行 Alembic migration、批量导入、删除、覆盖、向量重建、Auth 写入或数据清理；
- 将真实 RAG 故障改为 placeholder、Mock、外网搜索、缓存答案或跨地区检索；
- 在前端存放 provider key、数据库 URL、索引 endpoint、模型路径、提示词、语料绝对路径或身份映射；
- 将问题、回答、会话、JWT、API key、全文、raw score 或第三方错误原文写入日志；
- 未经新 PRD/TECH/OpenSpec 扩展为多轮记忆、流式响应、反馈、后台管理、问答历史或数据写入；
- 从旧项目复制任何 RAG、前端或服务端实现。

## 变更记录

| 日期 | 版本 | 变化 |
|---|---|---|
| 2026-08-21 | V1.0 | 定义稳定 API、IAM、现有语料、推荐索引/摄取、引用验证与上线门禁。 |
| 2026-08-21 | V1.1 | 重构为 AI 可执行交接包：新增必读顺序、代码地图、决策/授权门禁、实施顺序、交付检查表和可直接复用的 AI 指令。 |
