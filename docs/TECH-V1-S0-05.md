# TECH-V1-S0-05｜DepartmentClassifier 适配器边界

| 项目 | 内容 |
|---|---|
| 文档 ID | `TECH-V1-S0-05` |
| 版本 | `V1.0` |
| 状态 | 已完成并归档 |
| 对应步骤 | `S0.5` |
| OpenSpec change | [`2026-08-06-establish-department-classifier-adapter`](../openspec/changes/archive/2026-08-06-establish-department-classifier-adapter/) |
| 前置条件 | `S0.4` 已归档；运行时日志、请求 ID、健康检查和功能开关合同可用 |
| 目标 | 在不迁移旧分类实现的前提下，冻结可验证、可注入、无跨地区回退的部门分类适配器边界 |

## 1. 本阶段要解决什么

现有工程已经有最小 `DepartmentClassifier` Protocol 和始终未就绪的占位实现，但它只证明“不会返回假分类”。S0.5 要进一步明确未来真实实现必须遵守的边界：输入如何规范化、地区如何选择、结果怎样判定有效、模型资产怎样影响 readiness，以及领域失败由谁翻译成 HTTP 错误。

本阶段仍不加载模型、不复制旧计算、不创建分类业务接口。即使三个资产路径都存在，只要经过批准的计算实现尚未接入，readiness 仍必须是 `not_ready`，分类调用仍必须明确失败。

## 2. 范围与非目标

本阶段完成：

1. 输入、预测、结果和 readiness 的不可变类型及领域不变量；
2. 深圳演示环境的显式地区注册表，默认稳定 ID 为 `sz`；
3. 只检查路径存在性/regular-file/readability 的无副作用资产 manifest；
4. settings-aware factory 和 FastAPI 依赖注入边界；
5. `/api/v1/ai/readiness` 的安全 reason、`no-store` 和失败关闭行为；
6. 单元、API、smoke 和运行态验收。

本阶段明确不做：旧模型计算迁移、模型/Tokenizer/标签内容加载、`POST /classify` 或新的 classify API、AI run 记录、业务表或迁移、Supabase 写入、前端业务页面、Mock 分类结果。

## 3. 适配器合同

### 3.1 输入规范化

| 字段 | 规则 | 失败码 |
|---|---|---|
| `text` | Unicode NFKC；去首尾空白；连续空白折叠为一个空格 | 空值为 `TEXT_REQUIRED` |
| `region_id` | Unicode NFKC；trim；转小写；只允许稳定 ASCII 字母、数字、`_`、`-` | 空值为 `REGION_REQUIRED`；格式错误为 `REGION_INVALID` |
| 地区支持 | 只查显式 `CLASSIFIER_SUPPORTED_REGIONS` 注册表 | 未注册为 `REGION_NOT_SUPPORTED`，不得 fallback |

验证顺序固定为：文本与地区语法 → 支持地区 → 模型 readiness。这样未知但合法的地区不会被笼统的 `MODEL_NOT_READY` 掩盖。

### 3.2 输出不变量

- `ClassificationResult.region_id` 必须与规范化请求地区相同；
- 至少一个 prediction；部门 ID 非空、无空白且不重复；
- confidence 必须是 finite 数值且位于闭区间 `[0, 1]`；
- prediction 按 confidence 降序、部门 ID 升序形成确定顺序；
- `model_version` 非空且为有限长度的 ASCII metadata token（只允许字母、数字和 `._:+-`）；
- 任一不变量失败都产生 `CLASSIFIER_CONTRACT_INVALID`，不能把坏结果交给业务 service；适配器模板在返回前重建并再次校验第三方实现给出的结果，避免绕过 frozen dataclass 构造校验。

### 3.3 错误边界

intelligence 层使用独立的 classifier domain error，只携带稳定 code、安全消息和可选安全详情，不依赖 `AppError`、FastAPI 或 Flask。未来 application service 负责把 `TEXT_REQUIRED`、`REGION_NOT_SUPPORTED`、`MODEL_NOT_READY` 等领域码映射到共享 HTTP 错误信封和状态码。

## 4. Readiness 与资产状态

三个配置值为 `CLASSIFIER_MODEL_PATH`、`CLASSIFIER_TOKENIZER_PATH` 和 `CLASSIFIER_LABEL_BINDINGS_PATH`。S0.5 只做文件边界检查，不读取内容、不导入模型库。

| 状态 | readiness | 安全 reason |
|---|---|---|
| 三项均未配置 | `not_ready` | `verified_model_not_configured` |
| 部分配置、路径不存在、不是普通文件或不可读 | `not_ready` | `model_assets_invalid` |
| 三项文件检查通过但无批准的实现 | `not_ready` | `verified_adapter_not_implemented` |
| 地区注册表为空或无有效 ID | `not_ready` | `no_supported_regions_configured` |
| factory/readiness 出现非预期异常 | `not_ready` | `classifier_configuration_invalid` 或 `readiness_check_failed` |

reason、adapter 标识和 model version 都必须是有限长度的安全 metadata token；reason 只允许注册的稳定代码，不得包含文件路径、异常文本、连接串、令牌或密钥。S0.5 没有任何可返回 `ready` 的默认实现；真实 ready 只能由后续经 OpenSpec 审批、验证资产和计算的 adapter 提供。

## 5. API、数据与权限决定

`GET /api/v1/ai/readiness` 保留现有字段 `status`、`adapter`、`model_version`、`reason`，增加 `Cache-Control: no-store`。成功的 `not_ready` 响应仍为 HTTP 200，表示“探针本身工作正常且模型状态明确”；非预期检查异常也降为安全 `not_ready`，不泄露堆栈。

本步骤不增加 classify API，因此不增加认证/RBAC 决策。以后 classify service 必须拥有认证、授权、地区与部门 ID 映射、AI run 记录和 HTTP 错误翻译。旧 `POST /classify` 继续返回统一 404。

没有数据库或数据流变化：不执行 Alembic、不访问或写入 Supabase、不创建或重置业务数据。

## 6. 配置与代码职责

```text
backend/app/core/config.py                       地区注册表与既有资产路径配置
backend/app/modules/intelligence/adapters.py     领域类型、规范化、资产 manifest、factory、未就绪 adapter
backend/app/modules/system/router.py             settings 注入与 readiness HTTP 翻译
backend/tests/test_classifier_adapter.py         适配器领域合同和资产矩阵
backend/tests/test_security_and_contract.py      readiness API、安全响应和旧路由隔离
backend/scripts/smoke.py                         可重复阶段 0 分类边界 smoke
```

环境模板新增：

```env
CLASSIFIER_SUPPORTED_REGIONS=sz
```

这是公开稳定 ID 列表，不是密钥。模型路径仍是服务端变量，前端不得接收。

## 7. 验收标准

- NFKC、空白折叠和地区小写规范化可重复；空/非法输入返回稳定领域码。
- 未支持地区在模型未就绪之前返回 `REGION_NOT_SUPPORTED`，且无跨地区 fallback。
- prediction/result/readiness 的所有不变量有回归测试。
- 空、部分、无效、可读资产三态分别给出稳定 reason；即使文件有效也不伪装 ready。
- `/api/v1/ai/readiness` 返回 `no-store`，仅包含安全字段，并保留请求 ID 响应头。
- 旧 `/classify` 不注册；intelligence 模块无 Flask、旧 payload、全局可变路由状态或 Mock 结果。
- 后端全量测试、Ruff、前端守卫测试/build、本地 smoke、真实依赖 runtime smoke、绑定端口运行态和 OpenSpec strict validate 全部通过。
- 没有执行迁移、数据库写入或模型/旧代码导入。

## 8. 风险与回滚

- 文件检查只能证明资产路径可访问，不能证明三者语义兼容；因此后续真实实现完成前始终保持 not ready。
- ASCII 地区 ID 是内部稳定 ID，不直接承载中文显示名；外部名称应由 service 映射。
- 每次探针构造 adapter 会重复少量路径检查；在没有性能证据前不引入可变全局缓存。
- 回滚只撤销适配器、配置、路由和测试变更；本阶段无数据库和外部数据回滚。

## 9. 实施与验证证据

验收日期：2026-08-06。

| 检查项 | 命令/方式 | 结果 |
|---|---|---|
| 后端全量测试 | `'/Users/hlin/Documents/ai policy/ai-policy/.venv/bin/python' -m pytest` | 收集 94 项，全部通过；仅有上游 Starlette/httpx 弃用提示 |
| Python 质量检查 | `ruff check --no-cache .` | `All checks passed` |
| 前端守卫五态 | `npm run test:feature-guard` | loading、error、disabled、missing-flag、enabled 共 5 项通过 |
| 前端生产构建 | `npm run build` | `tsc -b` 通过，Vite 转换 37 个模块并构建成功 |
| 本地 smoke | `backend/scripts/smoke.py` | live、ready、auth、model、model_not_cacheable、classifier_no_mock、classifier_region_boundary、legacy_route_absent、health_not_cacheable、features_snapshot、error_request_id_header、cors_preflight_request_id 共 12 项 `ok` |
| 真实依赖 runtime smoke | `backend/scripts/runtime_smoke.py` | `database: ok`、`authentication_configuration: ok`、`jwks: ok` |
| 绑定端口运行态 | Uvicorn `127.0.0.1:8014` + HTTP | live/readiness 200；readiness `no-store`、请求 ID；CORS 预检请求 ID；OpenAPI 200；应用和 Uvicorn 生命周期日志均为 JSON；进程正常关闭 |
| 安全回归 | classifier/API 测试与独立复核 | 未知地区不回退；非法结果/置信度/版本、伪造 `ready` 状态、伪造嵌套 prediction 和恶意 readiness 字段均 fail-closed；路径和异常文本不进入响应 |
| OpenSpec 规划与实现校验 | `openspec validate --all --strict --no-interactive` | 归档前 active change 与 5 个主规格共 6 项通过、0 项失败；规格同步与归档后主规格 5 项通过、0 项失败 |
| 数据边界 | 命令审计 | 未执行 Alembic 迁移、未写入 Supabase、未读取旧分类源码或复制模型资产 |

## 10. 变更记录

| 日期 | 版本 | 变化 |
|---|---|---|
| 2026-08-06 | V1.0 | 建立 S0.5 DepartmentClassifier 适配器边界、失败模型和验收方案。 |
| 2026-08-06 | V1.0 | 完成规范化、地区注册表、资产 manifest、domain error、settings-aware factory、readiness 安全探针和完整验收。 |
| 2026-08-06 | V1.0 | 同步主规格并归档 OpenSpec；归档后 strict validate 通过。 |
