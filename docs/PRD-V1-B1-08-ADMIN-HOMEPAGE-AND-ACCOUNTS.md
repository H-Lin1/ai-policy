# PRD-V1-B1-08-M | 管理员首页精炼与账号管理方案

| 字段 | 内容 |
|---|---|
| 所属阶段 | B1.8 |
| 问题编号 | B18-010、B18-011 |
| 版本 / 状态 | V1.2 / 已完成 |
| 数据底座 | standalone PostgreSQL + 本地账号认证 |
| 与 B18-009 关系 | 独立功能方案；政策管理作为管理员首页特殊入口保留 |

## 1. 管理员首页与路由

管理员登录后直接进入 `/homepage`，不再进入独立 `/admin` 页面。`/homepage` 根据身份渲染不同视图：个人/企业继续显示各自首页，政府显示政府办理工作区，管理员显示管理员工作台。`/admin` 前端路由删除，不做重定向。

管理员专属功能使用独立功能路径：

```text
/account-management
/account-management/new
/account-management/:user_id
/registration-applications
/registration-applications/:id
/policy-management
/policy-management/new
```

后端 API 仍可保留 `/api/v1/admin/...` 作为权限边界。

## 2. 管理员导航与首页内容

管理员全局导航只保留：

```text
首页 / 政策中心 / 历史问答
```

移除智能分类、服务状态、平台管理、政策管理和注册申请一级导航。管理员可正常查看 `/policies` 和 `/qa`，首页不显示普通用户问答输入框。

管理员首页显示：

- 个人、企业、政府、管理员账号数量
- 正常/已停用账号数量
- 三个功能入口：账号管理、注册申请审批、政策管理

政策管理不出现在全局导航，只能通过首页入口或政策中心右上角的管理员按钮进入。

## 3. 账号管理

管理员账号管理页面为 `/account-management`。支持按角色（个人/企业/政府/管理员）、状态（正常/已停用）和关键词筛选，并分页展示登录账号、显示名称、角色、组织、部门、状态和创建时间。密码、密码哈希、JWT 和完整敏感联系方式不展示。

管理员可直接新增四类账号：个人、企业、政府、管理员。不同账号使用不同字段表单，服务端事务创建 `users`、`profiles`、`user_roles` 及必要组织/部门关系。政府账号必须从目录选择且遵守一部门一个账号；管理员账号必须绑定平台组织。

允许编辑显示名称、联系方式、职务、企业信息、政府部门、角色和启用状态；第一期不允许修改登录账号，不提供旧密码查看和密码重置。

## 4. 停用而非物理删除

界面中的“删除账号”统一实现为“停用账号”：将 `users.is_active` 设为 false、`profiles.status` 设为 disabled、有效角色设为 inactive；保留咨询、政策、注册申请和审计记录。管理员可恢复账号，恢复时重新校验组织、地区、角色和部门关系。数据库不提供物理删除账号接口。

## 5. API 与审计

```http
GET   /api/v1/admin/accounts
GET   /api/v1/admin/accounts/{user_id}
POST  /api/v1/admin/accounts/individual
POST  /api/v1/admin/accounts/enterprise
POST  /api/v1/admin/accounts/government
POST  /api/v1/admin/accounts/admin
PATCH /api/v1/admin/accounts/{user_id}
POST  /api/v1/admin/accounts/{user_id}/disable
POST  /api/v1/admin/accounts/{user_id}/enable
```

注册审批前端路径从 `/admin/registration-applications` 调整为 `/registration-applications`；后端审批 API 不变。

新增 `app.account_management_events`，记录 `account_created`、`account_updated`、`account_disabled`、`account_enabled`、`role_assigned`、`role_removed`、`organization_bound`、`department_bound`。审计摘要不含密码、JWT、数据库连接信息或完整联系方式。

## 6. 验收

- 管理员登录直接进入 `/homepage`；`/admin` 不存在。
- 管理员导航只有首页、政策中心、历史问答。
- 管理员首页能进入账号管理、注册审批和政策管理。
- 管理员能查看、创建、编辑、停用和恢复四类账号。
- 角色、组织、地区和政府部门唯一性由服务端校验。
- 停用不删除历史数据，非管理员无法访问相关页面/API。
- 所有变更有审计事件，桌面/移动端无横向溢出。

2026-09-06 已完成验收：管理员登录直接进入 `/homepage`，桌面和移动导航均仅含首页、政策中心、历史问答；账号管理、注册审批、政策管理三个首页入口可用，`/admin` 显示 404。`0008_admin_account_management` 已应用到本机 standalone `aipolicy_local`；新增个人/企业/管理员账号、个人编辑/停用/恢复、停用登录拒绝、当前管理员自停用拒绝、占用政府部门拒绝、非管理员 403 和审计事件均通过。账号管理桌面/移动均展示 14 个账号且无横向溢出。
