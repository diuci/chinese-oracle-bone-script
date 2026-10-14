#!/usr/bin/env node
// check-legal.mjs — 法律护栏
//
// 三件事，任何一件失败即 exit 1：
//   1. LICENSE 与 PROVENANCE.md 存在（授权与台账必须摆在明面）。
//   2. 内容里不得出现「绝对安全 / 100% / 百分百 / 保证无版权」这类绝对化表述——
//      我们能做的只是把每篇的依据摆出来，不做「绝对安全」这种担保。
//   3. 必须有侵权联系入口（hi@diuci.com），摆出来才谈得上可复核。
//
// 用法：
//   node tools/check-legal.mjs           # 全仓扫描
//   node tools/check-legal.mjs --selftest # 证明护栏抓得住坏样本

import { readFileSync, existsSync, readdirSync, statSync, writeFileSync, rmSync, mkdtempSync } from 'node:fs'
import { join, resolve } from 'node:path'
import { tmpdir } from 'node:os'

const ROOT = resolve(process.cwd())
let failures = []

// 绝对化表述：出现即失败。CJK 不是 \w，不能用 \b，直接匹配整串。
const ABSOLUTE = /(绝对安全|绝对无版权|百分百无版权|100%无版权|保证无版权|百分之百安全)/gu
const CONTACT = /hi@diuci\.com/

function walk(dir, out = []) {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name)
    const st = statSync(p)
    if (st.isDirectory()) {
      if (name === 'node_modules' || name === '.git') continue
      walk(p, out)
    } else if (p.endsWith('.md')) {
      out.push(p)
    }
  }
  return out
}

function check(root) {
  const failures = []
  // 1. 授权与台账
  if (!existsSync(join(root, 'LICENSE'))) failures.push('缺 LICENSE')
  if (!existsSync(join(root, 'PROVENANCE.md'))) failures.push('缺 PROVENANCE.md')
  // 2+3. 扫描 md
  let contactSeen = false
  for (const p of walk(root)) {
    const text = readFileSync(p, 'utf8')
    for (const m of text.matchAll(ABSOLUTE)) {
      failures.push(`${p.replace(root, '')}：绝对化表述「${m[0]}」`)
    }
    if (CONTACT.test(text)) contactSeen = true
  }
  if (!contactSeen) failures.push('找不到侵权联系入口 hi@diuci.com（PROVENANCE.md 里必须有）')
  return failures
}

function selftest() {
  const bad = mkdtempSync(join(tmpdir(), 'legal-bad-'))
  writeFileSync(join(bad, 'LICENSE'), 'MIT\n')
  writeFileSync(join(bad, 'PROVENANCE.md'), '台账。\n')
  writeFileSync(join(bad, 'bad.md'), '本仓保证 100%无版权 风险。\n')
  const badFail = check(bad)
  rmSync(bad, { recursive: true, force: true })

  const good = mkdtempSync(join(tmpdir(), 'legal-good-'))
  writeFileSync(join(good, 'LICENSE'), 'MIT\n')
  writeFileSync(join(good, 'PROVENANCE.md'), '台账。联系 hi@diuci.com。\n')
  writeFileSync(join(good, 'ok.md'), '我们不做绝对担保，只把依据摆出来。\n')
  const goodFail = check(good)
  rmSync(good, { recursive: true, force: true })

  const problems = []
  if (!badFail.some((f) => f.includes('100%无版权'))) problems.push('没抓到绝对化表述')
  if (goodFail.length) problems.push(`干净样本被误报：${goodFail.join('; ')}`)
  if (problems.length) {
    console.error('check-legal.mjs selftest FAILED:')
    for (const p of problems) console.error('  - ' + p)
    return 1
  }
  console.log('check-legal.mjs selftest ok')
  return 0
}

if (process.argv.includes('--selftest')) {
  process.exit(selftest())
}

failures = check(ROOT)
if (failures.length) {
  console.error('check-legal FAILED:')
  for (const f of failures) console.error('  - ' + f)
  process.exit(1)
}
console.log('check-legal ok')
