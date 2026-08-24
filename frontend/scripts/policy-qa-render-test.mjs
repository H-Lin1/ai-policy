import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const root = resolve(import.meta.dirname, '..')
const page = readFileSync(resolve(root, 'src/app/pages/PolicyQaWorkbench.tsx'), 'utf8')
const home = readFileSync(resolve(root, 'src/app/pages/WorkspaceHomePage.tsx'), 'utf8')
const roles = readFileSync(resolve(root, 'src/app/pages/RoleWorkspacePage.tsx'), 'utf8')
const client = readFileSync(resolve(root, 'src/lib/api/client.ts'), 'utf8')
const styles = readFileSync(resolve(root, 'src/styles.css'), 'utf8')

function check(condition, name) {
  if (!condition) throw new Error(`FAIL ${name}`)
  console.log(`PASS ${name}`)
}

check(page.includes('textarea') && page.includes('policy-qa-send') && page.includes('提交问题'), 'policy QA input and accessible submit action render')
check(page.includes("status: 'empty'") && page.includes("status: 'loading'") && page.includes("status: 'success'") && page.includes("status: 'error'"), 'policy QA has explicit states')
check(page.includes('演示流程') && page.includes('当前演示流程不展示政策来源'), 'placeholder answer is visibly labelled')
check(!page.includes('历史记录') && !page.includes('模型配置') && !page.includes('导入'), 'policy QA has no history or admin controls')
check(!home.includes('variant="public"') && home.includes('variant="workspace"') && roles.includes('variant="workspace"'), 'QA workbench is absent from signed-out home and remains on eligible entries')
check(home.includes('qaEligible') && home.includes('non-qa-home') && home.includes('authenticatedHomePath') && home.includes('Navigate') && !home.includes('authenticated-hero'), 'authenticated homepage is separated from signed-out root while retaining non-QA role access')
check(page.includes("answerState.status === 'empty' && variant !== 'workspace'") && page.includes('按 Enter 发送，Shift + Enter 换行'), 'workspace initial Q&A removes redundant post-input copy while retaining keyboard guidance')
check(client.includes('answerPolicyQuestion') && client.includes("'/policy-answers'"), 'policy QA client uses policy answer endpoint')
check(page.includes("event.key === 'Enter' && !event.shiftKey") && page.includes("status: 'sign_in'"), 'policy QA preserves keyboard submission and signed-out request safety')
check(styles.includes('.qa-home > .policy-qa-workbench.is-workspace-entry') && styles.includes('justify-content: center') && styles.includes('@media (max-width: 640px)'), 'policy QA centered and responsive styles present')
const workspaceEntryRules = [...styles.matchAll(/\.policy-qa-workbench\.is-workspace-entry\s*\{([^}]*)\}/g)].map((match) => match[1])
check(workspaceEntryRules.some((rule) => rule.includes('width: 100%') && rule.includes('max-width: none') && rule.includes('margin-inline: 0') && !rule.includes('50vw')), 'workspace QA uses its full parent width without viewport-relative offset or compact-width cap')
check(styles.includes('width: min(100%, 720px); margin-right: auto; margin-left: auto;'), 'workspace QA inner surfaces remain centered with bounded width')
