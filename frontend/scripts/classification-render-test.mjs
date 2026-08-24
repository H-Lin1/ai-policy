import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const root = resolve(import.meta.dirname, '..')
const page = readFileSync(resolve(root, 'src/app/pages/ClassificationWorkspacePage.tsx'), 'utf8')
const client = readFileSync(resolve(root, 'src/lib/api/client.ts'), 'utf8')
const router = readFileSync(resolve(root, 'src/app/router.tsx'), 'utf8')
const styles = readFileSync(resolve(root, 'src/styles.css'), 'utf8')

function check(condition, name) {
  if (!condition) throw new Error(`FAIL ${name}`)
  console.log(`PASS ${name}`)
}

check(page.includes('textarea') && page.includes('开始分类'), 'classification input and action render')
check(page.includes("status: 'loading'") && page.includes("status: 'empty'") && page.includes("status: 'success'") && page.includes("status: 'error'"), 'classification has explicit states')
check(page.includes('分类结果不会保存') && !page.includes('模型配置') && !page.includes('导入'), 'classification has no persistence or admin controls')
check(client.includes("classify: (text: string, accessToken: string)") && client.includes("method: 'POST'"), 'classification client uses authenticated POST')
check(router.includes("path: 'classify'"), 'classification route registered')
check(styles.includes('.classify-form') && styles.includes('@media (max-width: 640px)'), 'classification responsive styles present')
