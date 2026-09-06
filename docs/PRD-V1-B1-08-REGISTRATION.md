# PRD-V1-B1-08-R | 三类账号注册与申请方案

| 字段 | 内容 |
|---|---|
| 所属阶段 | B1.8 |
| 问题编号 | B18-007 |
| 版本 / 状态 | V1.1 / 已完成 |
| 数据与认证底座 | standalone PostgreSQL + 本地账号认证；不依赖 Supabase Auth |
| 配套方案 | [管理员审批页面方案](./PRD-V1-B1-08-ADMIN-APPROVAL.md) |

## 1. 总体规则

三个公开入口分别提供不同的账号开通方式：

| 入口 | 用户动作 | 管理员审批 | 角色生效时点 |
|---|---|---|---|
| 个人服务 | 自助注册 | 不需要 | 注册事务提交后获得 `individual` |
| 企业服务 | 提交企业注册申请 | 必须 | 审批通过后创建组织、账号并获得 `enterprise` |
| 政府服务 | 提交政府账号开通申请 | 必须 | 审批通过并绑定部门后获得 `government` |

入口只决定展示哪种表单，不授予角色。所有角色、组织、地区和部门关系由后端事务写入并由现有身份校验读取。

本方案只针对 standalone PostgreSQL。账号、密码哈希、profile、组织、角色和申请记录均保存在本地 PostgreSQL 的 `app` schema 中。

## 2. 页面和路由

```text
/login?role=individual
/login?role=enterprise
/login?role=government
/register?role=individual
/register?role=enterprise
/register?role=government
/registration-status
```

登录页根据入口显示对应的次级操作：

- 个人服务：注册个人账号
- 企业服务：提交企业入驻申请、查询申请状态
- 政府服务：提交政府账号开通申请、查询申请状态

注册页不能通过隐藏字段或篡改请求提交 `role=admin`、组织 ID、部门 ID（政府表单选择除外）或其他权限字段。

## 3. 个人自助注册

### 表单

- 登录账号：手机号或邮箱格式
- 密码
- 确认密码
- 显示名称
- 同意服务条款

第一期不接短信、邮件验证码或第三方实名服务。页面明确提示手机号/邮箱暂不代表实名验证。

### 后端接口

```http
POST /api/v1/iam/registrations/individual
```

后端在一个事务内完成：规范化账号、检查唯一性、创建 `app.users`、写入 scrypt 密码哈希、创建深圳 profile、绑定 `individual` 角色，然后提交事务。

注册成功后跳转登录页，由用户主动登录；注册接口不同时签发登录令牌。

### 边界

- 请求体不接受角色、组织、部门、管理员标记等字段。
- 账号重复、密码不符合规则时返回统一错误，不泄露已有账号详情。
- 个人账号只能获得 `individual`，不能通过注册接口获得企业、政府或管理员权限。

## 4. 企业注册申请

### 表单

企业主体：

- 企业名称
- 统一社会信用代码
- 企业类型
- 注册地址
- 所属地区（第一期固定深圳）

企业使用人：

- 使用人姓名
- 职务
- 联系手机号
- 联系邮箱

登录信息：

- 登录账号
- 密码
- 确认密码

第一期不上传营业执照文件，页面说明证明材料由管理员在审核环节线下核验。

### 后端接口和状态

```http
POST /api/v1/iam/registrations/enterprise
```

提交后只创建 `enterprise` 类型的 `pending` 申请，不创建可登录的企业角色。

申请状态：`pending`、`approved`、`rejected`、`cancelled`。

管理员通过后，在一个事务内创建并激活企业组织、用户、profile，绑定组织和 `enterprise` 角色，再将申请改为 `approved`。拒绝必须记录原因，且不产生有效企业角色。

## 5. 政府注册申请

### 业务规则

- 政府不开放直接注册成为有效政府账号。
- 一个政府部门最多只能申请并启用一个政府账号。
- 部门必须从现有深圳政府部门目录中选择，用户不能自由填写部门 ID 或部门名称。
- 同一部门存在 `pending` 或已生效账号时，新的申请必须被拒绝并给出统一提示。
- 选定部门后，申请人填写使用信息和登录信息；部门选择不能在提交后由客户端偷偷替换。

### 表单

第一步：选择部门

- 从现有政府部门目录选择部门
- 展示部门名称和当前是否可申请
- 已有待审或已启用账号的部门不可继续提交

第二步：填写使用信息

- 使用人姓名
- 职务
- 工作邮箱
- 联系手机号
- 工号或内部识别信息（可选）
- 使用场景/申请理由

第三步：填写登录信息

- 登录账号
- 密码
- 确认密码
- 同意服务条款

### 后端接口和审批结果

```http
POST /api/v1/iam/registrations/government
```

后端必须重新读取部门目录，确认部门有效、属于深圳、处于可申请状态，并在事务锁下检查该部门没有其他 `pending` 申请或有效政府账号。

管理员通过后，在一个事务内创建用户、profile、政府组织绑定、`government` 角色和部门成员关系，然后将申请改为 `approved`。拒绝必须记录原因。

由于本规则明确为“一部门一个账号”，现有 `consultation_departments.government_user_id UNIQUE` 关系继续保留，不在 B18-007 引入多账号部门队列改造。

## 6. 申请状态查询

```http
GET /api/v1/iam/registration-applications/{application_id}/status
```

用户只能查询自己提交的申请。查询结果包含：申请类型、申请编号、状态、提交时间、处理时间和面向用户的审核意见；不返回密码哈希、审核人内部信息或其他申请数据。

为避免枚举，申请编号和联系方式校验失败时统一返回“申请信息不存在或无法查询”。

## 7. 统一数据模型

新增 `app.registration_applications`：

```text
id UUID PRIMARY KEY
application_type CHECK ('enterprise', 'government')
status CHECK ('pending', 'approved', 'rejected', 'cancelled')
region_id
department_id NULL          -- 仅政府申请
login_username
password_hash
form_data JSONB             -- 仅保存已校验的申请字段
submitted_at
reviewed_at
reviewer_user_id NULL
review_reason NULL
created_at
updated_at
```

新增 `app.registration_application_events` 保存 `submitted`、`approved`、`rejected`、`cancelled` 事件和操作人。

个人注册不写入申请表，直接写现有身份表；企业/政府审批通过后才创建正式可用角色。

## 8. 错误和安全要求

统一错误码至少包括：

```text
REGISTRATION_INVALID
REGISTRATION_DUPLICATE_ACCOUNT
REGISTRATION_DUPLICATE_CREDIT_CODE
REGISTRATION_DEPARTMENT_UNAVAILABLE
REGISTRATION_ALREADY_PROCESSED
REGISTRATION_NOT_FOUND
REGISTRATION_APPROVAL_REQUIRED
```

所有注册和申请接口必须：

- 限制请求频率和输入长度；
- 使用统一错误体和 `no-store`；
- 不记录明文密码、密码哈希、完整联系方式或申请表敏感字段到日志；
- 使用数据库唯一约束和事务锁保证重复提交、重复账号和并发审批安全；
- 不改变既有 RoleGuard、RLS 和跨角色拒绝边界。

## 9. 注册方案验收

- 个人可以注册、登录并进入 `/homepage`。
- 个人注册不能伪造企业、政府或管理员角色。
- 企业申请提交后不能登录企业工作区；通过后才可登录。
- 政府申请必须选择目录中的部门；一个部门只能有一个待审或已启用账号。
- 政府申请提交后不能登录政府工作区；通过并绑定部门后才可登录。
- 申请状态查询只能读取本人申请。
- 现有登录、身份、角色、RLS、咨询部门绑定和跨角色测试全部通过。

2026-09-05 已按授权在本机 standalone `aipolicy_local` 完成验收：个人账号通过公开接口注册；企业和政府账号通过申请及管理员审批创建；四类账号均通过本地登录、`/me` 和匹配工作区鉴权；同部门重复申请、非管理员审批和重复审批均被安全拒绝。凭据未写入受 Git 跟踪文件或验收输出。
