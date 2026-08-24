## Why

B1.8 问题 B18-003 发现，登录后的顶部导航仍混合公共工具、角色工作区和运行状态入口，个人与企业用户需要在较少的核心入口中完成主要任务；企业用户还缺少查看已授权企业基本信息的独立入口。

## What Changes

- 个人用户导航固定为：首页、政策中心、历史问答、政民互动。
- 企业用户导航固定为：首页、政策中心、历史问答、政民互动、我的企业。
- 企业新增只读 /my-enterprise 页面，展示 /me 返回的组织和当前账号基本信息。
- 保留政府/管理员现有导航能力；不改变 API、数据库、RLS 或企业信息写入能力。

## Capabilities

### Modified Capabilities
- frontend-visual-baseline: authenticated role navigation and enterprise profile entry.

## Impact

- 修改 AppLayout、路由、企业信息页面、样式和前端渲染测试。
- 复用既有 MeResponse.organization、region、display name 和 email；不新增后端接口或迁移。
- 企业页面继续由 enterprise RoleGuard 保护，非企业用户不渲染内容。
