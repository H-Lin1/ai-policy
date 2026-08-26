# RAG-BACKEND-HANDOFF-V1 | 政策条款检索与生成：开发交接说明

> **交接对象：** 接续实现真实政策 RAG 的开发者。本文是 B1.5 占位问答后的开发基线。当前项目处于 B1.8“阶段功能完善与优化”，真实 RAG 不属于 B1.8；接手者必须新建一个独立专项变更，不得复用已经归档的 B1.5 OpenSpec。

> **当前事实：** `POST /api/v1/policy-answers` 已存在、已鉴权，但当前固定使用 `PlaceholderPolicyAnswerEngine`，返回明确标识的 `answer_mode="placeholder"`，没有真实检索、向量索引、LLM 调用或 RAG 配置。真实 RAG 尚未开发。

## 1. 本期实现目标

本期真实 RAG 仅使用政策库中的官方政策原文，不混入历史问答、人工咨询或互联网搜索。用户链路必须是：

```text
用户输入问题
  → 在深圳政策库中检索最相关的具体政策条款
  → 对候选条款去重、核验并选择证据
  → 将「用户问题 + 已核验的政策条款」提供给大模型
  → 大模型仅依据这些条款生成回答
  → 返回回答和可追溯的参考条款
```

交付结果不是泛化聊天回答。每次成功的 `rag` 回答都必须能回溯到返回的政策文档和原文条款；参考条款必须来自实际检索到的原文，不得由模型改写后伪装成引用。没有充分政策依据时，系统必须明确说明未检索到足够依据，不能编造、联网搜索、跨地区检索或悄悄改回 placeholder。

## 2. 稳定 API 与用户可见结果

继续使用现有接口，不改变 URL、认证方式、请求字段、统一错误信封、`X-Request-ID` 或 `Cache-Control: no-store`：

```http
POST /api/v1/policy-answers
Authorization: Bearer <Supabase access token>
Content-Type: application/json

{"question":"企业可以申请哪些科技创新支持？"}
```

当前身份范围固定由后端解析为深圳；仅活跃的 `individual` 和 `enterprise` 角色可调用。浏览器不能提交地区、不能直接读取 `app.*` 表，也不能携带模型或检索配置。

真实 RAG 成功响应必须使用 `answer_mode: "rag"`，并返回不超过 5 条、按回答支持度排序的参考条款：

```json
{
  "request_id": "opaque-request-id",
  "region_id": "sz",
  "answer_mode": "rag",
  "answer": "根据深圳市相关政策，……",
  "sources": [
    {
      "source_type": "policy_document",
      "source_id": "政策文档 UUID",
      "title": "政策标题",
      "source_url": "https://www.sz.gov.cn/...",
      "published_date": "2024-01-01",
      "excerpt": "与本次回答直接相关的原始条款或条款片段"
    }
  ],
  "notices": []
}
```

现有 `sources[].excerpt` 最大 800 字符，可作为第一版用户可见的参考条款。开发者应在专项 TECH/OpenSpec 中决定是否新增**向后兼容**的 `clause_reference`（例如“第三条第（二）项”）；如新增，必须同步后端 schema、前端类型/展示、API 文档和回归测试。不得改变现有字段的含义或将 raw score、chunk ID、提示词、模型路径、密钥或内部异常返回浏览器。

`answer_mode` 只允许 `placeholder` 和 `rag`。真实引擎发生配置、检索或生成故障时，必须返回安全的明确失败（建议区分 `RAG_NOT_READY`、`RAG_RETRIEVAL_FAILED`、`RAG_GENERATION_FAILED`），不得用 placeholder 伪装成功。对于“无充分依据”，开发者必须在专项规格中确定并实现唯一行为：例如 `200 + rag + 保守说明 + 空 sources`，或稳定的 `RAG_NO_GROUNDED_ANSWER` 合同。

## 3. 本次关联数据库与数据边界

当前数据库 schema 为 `app`，当前迁移基线为 `0005_consultation_workflow`。所有业务表都由 FastAPI 服务端访问，且既有 RLS 已开启、`anon` 与 `authenticated` 没有直接业务表权限。

### 3.1 一期唯一 RAG 语料来源：`app.policy_documents`

该表是本期的**只读、官方政策原文**来源。RAG 的离线摄取和线上检索都应以它为 source of truth，不得修改其原文、hash 或来源字段。

| 字段 | 用途 |
| --- | --- |
| `id` | 稳定的政策文档 ID；返回为 `sources[].source_id`，并用于 chunk 与源文档映射。 |
| `region_id`、`region_code` | 地区范围；本期只允许 `region_code = 'sz'`，不跨地区 fallback。 |
| `title`、`document_no`、`issuing_organization` | 回答上下文、结果展示和来源辨识。 |
| `source_url`、`document_url` | 官方出处；用户可回到来源核验。开发者须确定两个 URL 的展示优先规则并记录在 TECH。 |
| `published_date`、`effective_status`、`updated_at` | 检索过滤、时效/排序和增量重建依据；具体有效状态规则由开发者在专项方案中写明。 |
| `content_text` | 政策全文；按条款/款项优先或其他可解释规则切块的唯一正文输入。 |
| `content_sha256` | 原文版本识别与离线摄取幂等、增量重建。 |
| `reference_count`、`source_years` | 可选排序或分析信息；是否使用必须在方案中说明，不能隐式影响结果。 |

### 3.2 身份与授权关联表

RAG 不应自行实现身份判断，继续复用现有 `get_current_identity` 与 `policy_qa.service` 边界。以下表间接决定是否允许访问：

| 表 | 本次用途 |
| --- | --- |
| `app.profiles` | 主体是否存在、状态是否有效、所属组织/地区上下文。 |
| `app.user_roles`、`app.roles` | 确认当前主体具备 `individual` 或 `enterprise` 角色。 |
| `app.regions`、`app.organizations` | 确认活动深圳范围和现有组织范围。 |

### 3.3 明确排除的表与来源

| 表或来源 | 本期决定 |
| --- | --- |
| `app.historical_qa` | 不作为本期 RAG 语料。它既包含既有历史政务问答，也可能包含 B1.6 公开咨询投影；后续若要纳入，必须单独扩展 PRD/TECH/OpenSpec。 |
| `app.consultations`、`app.consultation_events`、`app.consultation_departments` | 不读取为 RAG 语料，不返回工单、部门账号或办理信息。 |
| 外网、旧项目 RAG/FAISS/embedding 代码、临时文件 | 禁止抓取、复制或作为检索回退。 |

## 4. 现有代码集成点

后端是 FastAPI + Pydantic + SQLAlchemy 2 的模块化单体，所有 API 位于 `/api/v1`。应在现有 `policy_qa` 模块内扩展，不应把检索、向量调用或模型调用写进路由：

```text
backend/app/modules/policy_qa/
  adapters.py       # 现有 PolicyAnswerEngine、typed input/result/source、placeholder
  service.py        # 现有 IAM、输入规范化、错误脱敏、response mapping
  router.py         # 现有 POST /policy-answers HTTP 边界
  schemas.py        # 现有请求/响应 Pydantic 合同
  retrieval.py      # 新增：只读条款检索边界与实现
  generation.py     # 新增：LLM provider adapter 与安全失败翻译
  ingestion.py      # 新增：离线切块、嵌入、版本激活与幂等重建
```

实现必须保持以下边界：

- `router.py` 只保留 HTTP、认证依赖与 `no-store`；不嵌入检索/模型逻辑。
- `service.py` 继续负责角色/地区、问题规范化、错误映射；不记录问题文本。
- 真实引擎通过显式、可验证的后端配置选中；它不是故障 fallback 的来源。
- 离线摄取与索引构建不得在用户 API 请求中运行。
- 可选择复用 B1.4 分类结果作 rerank/filter 信号，但不得耦合或修改 `app.modules.intelligence` 的 PyTorch 内部实现；是否使用须在方案中证明收益并覆盖测试。

## 5. 开发者必须产出的专项方案（开发者自行决定）

开发者可以自行选择模型、embedding、向量存储、切块、检索和质量指标；但每项选择都必须在**编码前**写入本次新建的 PRD、TECH 与 OpenSpec，不能只凭口头决定或在代码中隐含。选择不要求沿用本文建议，但必须满足本节的记录要求与第 6 节安全边界。

专项方案至少需要包含下列决策及其理由、备选方案、影响、验收方式和回滚方式：

| 决策项 | 方案中必须写清楚 |
| --- | --- |
| LLM 与 embedding | 供应商/模型版本、部署位置、问题与条款是否会离开受控环境、凭据注入方式、超时、重试、限流、成本预估与降级失败行为。 |
| 向量检索存储 | `pgvector`、其他数据库或受管向量库的选择；表/索引/扩展、备份、访问控制、容量与运维责任。 |
| 条款切块 | 如何从 `content_text` 识别“条、款、项”或其他边界；chunk 长度、overlap、保留的条款定位 metadata、无法可靠解析时的处理。 |
| 语料筛选与版本 | `effective_status`、日期与状态的具体过滤规则；源 `content_sha256` 变化时如何增量更新；如何创建、激活、回滚一个语料版本。 |
| 检索与排序 | top-k、关键词/向量/hybrid 策略、重排、去重、时效性、多样性与最低证据门槛；不得把 raw score 返回前端。 |
| 生成与引用核验 | 系统提示的安全约束、回答如何绑定条款、`excerpt`/可选 `clause_reference` 的生成与验证、无依据行为。 |
| 数据生命周期 | 是否保存运行指标、最小字段、保留期、删除与访问控制；默认不保存问题、回答、JWT、用户 ID 或完整 prompt。 |
| 性能、成本与质量 | 固定中文问题集、来源/条款命中率、引用真实性、无依据拒答率、不可编造率、P95 时延、单请求成本及通过阈值。 |

建议新建表而不是修改 `app.policy_documents`。表名可由开发者决定；如采用语料版本与 chunk 表，至少要能够表示语料版本、源文档 ID/hash、chunk 顺序、原文、条款定位 metadata、embedding 或外部向量键、创建/激活状态，并保证源文档变化后可幂等重建和回滚。所有 migration、扩展、索引、导入、激活或重建操作必须先在专项 OpenSpec 的 tasks/design 中列出，并按项目既有门禁执行。

## 6. 不可改变的安全、数据与行为边界

- 只检索深圳 `policy_documents`；不得跨地区、不得检索历史问答/咨询、不得联网搜索。
- 大模型只能依据经过检索与核验的条款回答；证据不足时保守说明，不能补充臆测的政策、资格、期限、金额、网址或条款。
- `sources` 最多 5 条；每一条都必须能映射回 `policy_documents.id`，`excerpt` 必须是对应原文 chunk 的连续短片段。
- 真实 RAG 的配置缺失、索引不可用、provider 超时或生成失败必须安全失败，不能返回 placeholder、Mock 或缓存的旧答案。
- 不得向前端、日志或错误体泄露 provider key、数据库 URL、向量库 endpoint、模型路径、原始 prompt、完整条款、JWT、用户映射、raw score 或第三方错误原文。
- 默认不保存用户问题、模型回答、会话、反馈或个人画像。任何持久化需求都必须在专项 PRD/TECH/OpenSpec 说明最小字段、保留期、删除流程与权限边界。
- 不复制旧项目中的 Flask、RAG、FAISS、embedding、前端、全局状态或启动代码。

## 7. 实施顺序与交付验收

### 7.1 必须的实施顺序

1. 阅读 `DEVELOPMENT_STATUS.md`、本文、`docs/PRD-V1-B1-05.md`、`docs/TECH-V1-B1-05.md`、现有 `policy_qa` 模块、`openspec/config.yaml` 与当前 migration。
2. 新建真实 RAG 专项的 PRD、TECH、OpenSpec（`proposal.md`、能力 specs、`design.md`、`tasks.md`），完整记录第 5 节的技术决策并执行 strict validate。
3. 实现并验证 migration、离线摄取、语料版本/索引激活、幂等重跑和回滚；不得先以线上 API 同步嵌入整库。
4. 实现只读检索、条款映射与引用验证，再接入 LLM provider adapter 和真实 `PolicyAnswerEngine`。
5. 更新前端的真实 RAG 展示、来源条款和无依据/安全失败状态；保持 placeholder 与 `rag` 的状态差异清晰。
6. 执行第 7.2 节测试、真实授权身份验证、文档与 `DEVELOPMENT_STATUS.md` 更新；完成 OpenSpec archive 后交付。

### 7.2 最低交付物与验收证据

- [ ] 新的 PRD、TECH、OpenSpec 和 `openspec validate --all --strict --no-interactive` 通过记录。
- [ ] 数据模型/migration、离线摄取、幂等键、版本激活、增量更新、失败处理和回滚说明；执行数据库写入前遵循项目的明确授权流程。
- [ ] 检索、生成、引用核验、配置隔离和错误映射代码及测试。
- [ ] 固定的中文个人/企业问题质量集；每题具有期望政策文档和条款依据，评测输出不含敏感原文或凭据。
- [ ] 单元与集成测试覆盖：输入规范化、角色/深圳范围、有效状态筛选、条款切块、检索过滤、source 映射、引用真实性、空证据、provider 超时/异常脱敏、`no-store`、request ID、无 API 写入和无浏览器直连。
- [ ] 质量/性能/成本结果达到专项方案预先定义的阈值，且真实 RAG 不把故障伪装成 placeholder。
- [ ] 后端测试、Ruff、前端测试/build、local/runtime smoke、真实已授权身份验收、文档更新与 OpenSpec archive 证据。

## 8. 给接手开发者的首轮指令

```text
你在 AI 政策服务平台仓库中负责“政策条款检索与生成”真实 RAG 专项。

先只读，不修改代码、环境、数据库、配置或飞书文档。依序阅读：
1. DEVELOPMENT_STATUS.md；
2. docs/RAG-BACKEND-HANDOFF-V1.md；
3. docs/PRD-V1-B1-05.md 与 docs/TECH-V1-B1-05.md；
4. backend/app/modules/policy_qa/adapters.py、service.py、schemas.py、router.py；
5. backend/migrations/versions/0003_policy_library.py、0004_historical_qa.py、0005_consultation_workflow.py；
6. openspec/config.yaml。

先报告当前状态、现有 API 合同、相关表/字段、不可改变边界和拟定的实施范围。
然后自行确定 LLM、embedding、向量存储、条款切块、检索、无依据行为、质量指标和回滚策略，并把每项选择、理由、备选方案、成本/安全影响、验收阈值写入新建的 PRD、TECH 与 OpenSpec。
先运行严格 OpenSpec 校验；方案通过后再按 tasks 实施 migration、离线摄取、检索、生成、前端展示和验证。不得将技术选择只留在代码或聊天中。
```

## 9. 变更记录

| 日期 | 版本 | 变化 |
| --- | --- | --- |
| 2026-08-21 | V1.0 | 初始 RAG 后端交接基线。 |
| 2026-08-21 | V1.1 | 增加 AI 交接顺序、决策门禁与交付检查表。 |
| 2026-08-26 | V2.0 | 改为“政策库具体条款检索 → 条款+问题生成 → 回答+参考条款”；一期明确只使用 `app.policy_documents`，迁移基线更新为 `0005_consultation_workflow`，技术选型改由开发者在专项 PRD/TECH/OpenSpec 中自行决定并留档。 |
