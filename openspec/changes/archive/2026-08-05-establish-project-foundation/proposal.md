## Why

旧项目把页面、Flask 路由、模型初始化、检索和业务规则集中在少数文件中，无法作为新项目稳定的开发入口。阶段 0 需要先建立一个可重复启动、可测试、可分层扩展的模块化单体，并为唯一允许迁移的旧 `classify` 后端计算逻辑划出清晰适配器边界。

本 change 对应技术实施方案 `TECH-V1-S0-01` 和开发基线阶段 0。它只负责工程基础，不实现政策库、问答检索、RAG、咨询或其他业务功能。

## What Changes

- 创建 React + Vite + TypeScript 前端骨架，包含应用布局、路由、统一 API 客户端和服务状态页。
- 创建 FastAPI 后端骨架，统一使用 `/api/v1` 前缀，并提供 live、ready 和聚合健康检查。
- 建立环境配置、结构化日志、请求 ID、统一错误响应、CORS 和功能开关的最小实现。
- 建立 Supabase/PostgreSQL 连接和 Alembic 迁移入口；未配置数据库时，本地开发可以明确显示降级状态，不伪装为数据库已就绪。
- 建立认证依赖边界：健康检查公开，其余受保护接口在启用认证时拒绝无令牌请求。
- 建立 `DepartmentClassifier` 适配器接口和未配置模型时的明确 `MODEL_NOT_READY` 行为。
- 编写初始化、演示数据重置和冒烟检查脚本；阶段 0 不导入旧 Excel、FAISS 或前端代码。
- 增加 README、环境变量示例、测试配置和跨对话开发状态台账。

## Capabilities

### New Capabilities

- `project-foundation`: 提供新项目的启动、健康检查、统一错误、请求追踪、配置和前端工程外壳。
- `department-classifier-adapter`: 定义分类模型适配器的稳定边界、就绪状态和未配置模型时的失败行为。

### Modified Capabilities

- 无。项目当前尚无已归档的业务 capability。

## Impact

- 新增 `frontend/` React 应用和 `backend/app/` FastAPI 模块化单体。
- 新增 Python 依赖、前端依赖、环境变量模板、Alembic 迁移入口和本地脚本。
- 新增 `/api/v1/health/live`、`/api/v1/health/ready`、`/api/v1/health` 和受保护的 `/api/v1/me`；旧 `/classify` 路由不会创建。
- 新增后续业务模块可以依赖的 `core`、`api` 和 `intelligence` 目录边界。
- 不修改旧 `backend/`，不迁移旧 Flask 路由、请求响应结构、检索/RAG/Embedding/FAISS 实现或前端。
