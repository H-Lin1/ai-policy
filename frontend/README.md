# AI Policy frontend

这是新项目的 React、Vite、TypeScript 和 React Router 前端。阶段 0 应用外壳之上已实现 B1.1 Supabase 会话、数据库身份和四角色工作区守卫；UI1.0 基于公开运行页面独立重建“政通惠”视觉语言，并本地化两张已授权入口图。旧项目的 JavaScript、CSS、组件、路由、状态与调用方式不迁移。

当前统一视觉采用白色紧凑顶栏、浅蓝灰页面、蓝紫强调和个人/企业双图片入口。未登录入口固定在公开根路径，登录后的个人/企业用户统一进入 `/homepage`，四角色导航仍由 `/me` 返回的数据库角色过滤，工作区内容仍须通过后端授权。

## 本地运行

```bash
cp .env.example .env.local
npm install
npm run dev
```

默认开发地址为 `http://localhost:5173`。浏览器端 API 地址由 `VITE_API_BASE_URL` 配置，默认值为 `http://localhost:8000/api/v1`。B1.1 登录还需要公开的 `VITE_SUPABASE_URL` 和 `VITE_SUPABASE_ANON_KEY`；禁止把 service-role key 或其他服务端密钥放入 `VITE_*`。配置缺失或后端身份不可用时页面明确失败，不创建本地假身份。

## 当前路由

- `/`：未登录时显示个人、企业、政府三类服务入口；登录后自动替换到 `/homepage`
- `/homepage`：登录后的统一首页；个人/企业显示政策智能问答入口，其他已授权角色显示可用工作区
- `/login`：Supabase Auth 登录页
- `/personal`、`/enterprise`、`/government`、`/admin`：后端二次确认的四角色工作区；`/personal` 对应后端角色码 `individual`，未授权内容不挂载
- `/health`：后端健康检查页
- `/policies`：由后端 `policy_workspace` 开关控制的守卫路由；阶段 0 不渲染业务内容或 Mock 数据

后续每个业务功能都按 PRD → OpenSpec → 数据库/API → 前端真实调用 → 验收的纵向切片方式加入，不在骨架阶段预埋业务 Mock。

## 验证

```bash
npm test
npm run build
```

`npm test` 直接驱动生产使用的会话与角色授权协调器，覆盖会话恢复、登录/退出、token 刷新、重试、过期异步结果隔离、四类角色的允许/拒绝/服务错误状态，以及 UI1.0 品牌壳、角色导航过滤、本地入口图和移动端账户/退出可见性。

完整启动、受控数据库初始化和验收说明见项目根目录 [`README.md`](../README.md)、[`docs/TECH-V1-S0-06.md`](../docs/TECH-V1-S0-06.md)、[`docs/TECH-V1-B1-01.md`](../docs/TECH-V1-B1-01.md) 和 [`docs/TECH-V1-UI-01.md`](../docs/TECH-V1-UI-01.md)。
