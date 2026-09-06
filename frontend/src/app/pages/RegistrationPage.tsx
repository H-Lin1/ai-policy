import { useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { ApiError, apiClient } from '../../lib/api/client'

type RegistrationRole = 'individual' | 'enterprise' | 'government'
const labels: Record<RegistrationRole, string> = { individual: '个人服务', enterprise: '企业服务', government: '政府服务' }

export function RegistrationPage() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const role = (['individual', 'enterprise', 'government'] as const).includes(params.get('role') as RegistrationRole) ? params.get('role') as RegistrationRole : 'individual'
  const [form, setForm] = useState<Record<string, string | boolean>>({ terms_accepted: false })
  const [result, setResult] = useState<{ id?: string | null; status: 'created' | 'pending'; message: string } | null>(null)
  const [redirectSeconds, setRedirectSeconds] = useState(3)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [departments, setDepartments] = useState<Array<{ department_id: string; department_name: string }>>([])
  useEffect(() => { if (role !== 'government') return; void apiClient.getRegistrationDepartments().then(setDepartments).catch(() => setDepartments([])) }, [role])
  useEffect(() => {
    if (role !== 'individual' || result?.status !== 'created') return
    setRedirectSeconds(3)
    const redirect = window.setTimeout(() => navigate('/login?role=individual', { replace: true }), 3000)
    const countdown = window.setInterval(() => setRedirectSeconds((current) => Math.max(1, current - 1)), 1000)
    return () => { window.clearTimeout(redirect); window.clearInterval(countdown) }
  }, [navigate, result, role])
  const set = (key: string, value: string | boolean) => setForm((current) => ({ ...current, [key]: value }))
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setResult(null); setError(null)
    try {
      const payload = { ...form }
      const result = role === 'individual' ? await apiClient.registerIndividual(payload as never) : role === 'enterprise' ? await apiClient.registerEnterprise(payload) : await apiClient.registerGovernment(payload)
      setResult(result)
    } catch (cause) { setError(cause instanceof ApiError ? cause.message : '注册服务暂不可用。') } finally { setBusy(false) }
  }
  const common = <>
    <label><span>登录账号</span><input required value={String(form.username ?? '')} onChange={(e) => set('username', e.target.value)} /></label>
    <label><span>密码</span><input required minLength={12} type="password" value={String(form.password ?? '')} onChange={(e) => set('password', e.target.value)} /></label>
    <label><span>确认密码</span><input required minLength={12} type="password" value={String(form.password_confirmation ?? '')} onChange={(e) => set('password_confirmation', e.target.value)} /></label>
  </>
  if (role === 'individual' && result?.status === 'created') {
    return <section className="page-content registration-page registration-complete-page"><div className="registration-success-card" role="status" aria-live="polite"><span className="registration-success-icon" aria-hidden="true">✓</span><div className="eyebrow">Registration complete</div><h1>个人账号注册成功</h1><p>你的账号已经创建，可以使用刚才设置的账号和密码登录个人服务。</p><Link className="button button-primary" to="/login?role=individual">立即前往登录</Link><span className="registration-redirect-note">{redirectSeconds} 秒后自动跳转到登录页面</span></div></section>
  }
  return <section className="page-content registration-page"><div className="login-intro registration-intro"><div className="eyebrow">政通惠 · 账号开通</div><h1>{labels[role]}<span className="accent-text">{role === 'individual' ? '注册' : '注册申请'}</span></h1><p className="lead">{role === 'individual' ? '注册后即可登录个人服务。' : '提交后由平台管理员审核，审核通过后才可登录对应工作区。'}</p></div><div className="login-panel registration-panel"><form className="login-form" onSubmit={submit}><div className="login-form-heading"><span className="section-label">Registration</span><h2>{role === 'individual' ? '注册个人账号' : role === 'enterprise' ? '企业入驻申请' : '政府账号开通申请'}</h2></div>{role === 'individual' ? <><label><span>显示名称</span><input required value={String(form.display_name ?? '')} onChange={(e) => set('display_name', e.target.value)} /></label>{common}</> : role === 'enterprise' ? <><label><span>企业名称</span><input required value={String(form.enterprise_name ?? '')} onChange={(e) => set('enterprise_name', e.target.value)} /></label><label><span>统一社会信用代码</span><input required value={String(form.unified_social_credit_code ?? '')} onChange={(e) => set('unified_social_credit_code', e.target.value)} /></label><label><span>企业类型</span><input required value={String(form.enterprise_type ?? '')} onChange={(e) => set('enterprise_type', e.target.value)} /></label><label><span>注册地址</span><input required value={String(form.registered_address ?? '')} onChange={(e) => set('registered_address', e.target.value)} /></label><label><span>使用人姓名</span><input required value={String(form.user_name ?? '')} onChange={(e) => set('user_name', e.target.value)} /></label><label><span>职务</span><input required value={String(form.job_title ?? '')} onChange={(e) => set('job_title', e.target.value)} /></label><label><span>联系电话</span><input required value={String(form.contact_phone ?? '')} onChange={(e) => set('contact_phone', e.target.value)} /></label><label><span>联系邮箱</span><input required type="email" value={String(form.contact_email ?? '')} onChange={(e) => set('contact_email', e.target.value)} /></label>{common}</> : <><label><span>政府部门</span><select required value={String(form.department_id ?? '')} onChange={(e) => set('department_id', e.target.value)}><option value="">请选择部门</option>{departments.map((department) => <option key={department.department_id} value={department.department_id}>{department.department_name}</option>)}</select></label><label><span>使用人姓名</span><input required value={String(form.user_name ?? '')} onChange={(e) => set('user_name', e.target.value)} /></label><label><span>职务</span><input required value={String(form.job_title ?? '')} onChange={(e) => set('job_title', e.target.value)} /></label><label><span>工作邮箱</span><input required type="email" value={String(form.work_email ?? '')} onChange={(e) => set('work_email', e.target.value)} /></label><label><span>联系电话</span><input required value={String(form.contact_phone ?? '')} onChange={(e) => set('contact_phone', e.target.value)} /></label><label><span>使用场景</span><textarea required value={String(form.usage_scenario ?? '')} onChange={(e) => set('usage_scenario', e.target.value)} /></label><label><span>申请理由</span><textarea required value={String(form.application_reason ?? '')} onChange={(e) => set('application_reason', e.target.value)} /></label>{common}</>}<label className="terms-check"><input type="checkbox" checked={Boolean(form.terms_accepted)} onChange={(e) => set('terms_accepted', e.target.checked)} required /><span>我已阅读并同意服务条款</span></label>{result ? <p className="success-message" role="status">{result.id ? `${result.message} 申请编号：${result.id}` : result.message}</p> : null}{error ? <p className="error-message" role="alert">{error}</p> : null}<button className="button button-primary" type="submit" disabled={busy}>{busy ? '正在提交…' : role === 'individual' ? '注册账号' : '提交申请'}</button><p className="muted"><Link to={`/login?role=${role}`}>已有账号，返回登录</Link></p></form></div></section>
}
