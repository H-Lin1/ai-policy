import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

import postcss from 'postcss'

const css = await readFile(new URL('../src/styles.css', import.meta.url), 'utf8')
const root = postcss.parse(css)

function declarations(rule) {
  const values = new Map()
  rule.walkDecls((declaration) => values.set(declaration.prop, declaration.value))
  return values
}

function matchingRule(container, selector) {
  let match
  container.walkRules((rule) => {
    if (!match && rule.selectors.includes(selector)) match = rule
  })
  return match
}

const baseAccountPanel = matchingRule(root, '.account-panel')
const signOutButton = matchingRule(root, '.sign-out-button')
assert.ok(baseAccountPanel, 'account panel styles must exist')
assert.ok(signOutButton, 'sign-out button styles must exist')
assert.equal(declarations(baseAccountPanel).get('display'), 'flex')
assert.notEqual(declarations(signOutButton).get('display'), 'none')

const mobile = root.nodes.find(
  (node) => node.type === 'atrule' && node.name === 'media' && node.params === '(max-width: 720px)',
)
assert.ok(mobile, 'mobile breakpoint must exist')
const mobileAccountPanel = matchingRule(mobile, '.account-panel')
assert.ok(mobileAccountPanel, 'mobile account panel styles must remain explicit')
const mobileDeclarations = declarations(mobileAccountPanel)
assert.notEqual(mobileDeclarations.get('display'), 'none')
assert.notEqual(mobileDeclarations.get('visibility'), 'hidden')
assert.notEqual(mobileDeclarations.get('opacity'), '0')

const mismatchPage = matchingRule(root, '.role-mismatch-page')
const mismatchDialog = matchingRule(root, '.role-mismatch-dialog')
const mismatchActions = matchingRule(root, '.role-mismatch-actions')
assert.ok(mismatchPage, 'role mismatch overlay styles must exist')
assert.ok(mismatchDialog, 'role mismatch dialog styles must exist')
assert.ok(mismatchActions, 'role mismatch actions must exist')
assert.equal(declarations(mismatchPage).get('position'), 'fixed')
assert.equal(declarations(mismatchPage).get('overflow-y'), 'auto')
assert.equal(declarations(mismatchDialog).get('width'), 'min(100%, 520px)')

const mobileMismatchActions = matchingRule(mobile, '.role-mismatch-actions')
assert.ok(mobileMismatchActions, 'mobile role mismatch actions must remain explicit')
assert.equal(declarations(mobileMismatchActions).get('grid-template-columns'), '1fr')

process.stdout.write('PASS responsive auth controls remain available on mobile\n')
