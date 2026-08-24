## Context

应用当前用一个 `AppLayout` 为所有路由渲染页头。未登录首页的两张卡片链接受保护角色路由，由角色守卫再引导 `/login`。B18-001 要求公开首页成为无导航的三类服务选择页，同时登录后仍进入真实角色工作区。

## Decisions

1. `AppLayout` 根据当前路径和身份状态隐藏公开首页页头；已登录用户在 `/` 的问答/工作区首页仍保留既有导航。页脚保持不变。
2. `PublicLanding` 渲染品牌标题、副标题和三张相同 DOM/CSS 结构的卡片。三张卡片的 `href` 均为 `/login`，通过 React Router location state 携带 `intendedRole`，不引入角色查询参数。
3. `LoginPage` 只接受 `individual`、`enterprise`、`government` 三种入口意图。身份变为 ready 后，只有后端 `/me` 返回角色包含该意图时才导航到对应工作区；否则回到 `/`，由现有身份页面呈现真实可用入口。
4. 登录提交、busy/disabled/error、配置缺失、Supabase session 和后端 workspace 授权不变。入口状态只决定成功后的目标，不能授予角色或绕过 `RoleGuard`。
5. 桌面使用三列等宽网格，平板按可用宽度调整，移动端单列；卡片使用稳定 `aspect-ratio`。政府入口暂复用已有本地企业服务图片并使用不同裁切，不增加外部依赖。

## Risks And Mitigations

- 入口意图可能与实际账号角色不符：登录后核对 `/me` 角色，不匹配时不进入目标角色页。
- 首页隐藏页头可能影响已登录问答首页：隐藏条件同时限定根路径和非 ready 身份。
- 三列卡片文本拥挤：缩短描述并用桌面、窄屏断点和浏览器截图验证。

## Rollback

恢复 `AppLayout` 的恒定页头、两卡入口和原登录重定向即可；无数据、API 或迁移回滚。
