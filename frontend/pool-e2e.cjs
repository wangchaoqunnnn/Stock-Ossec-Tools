/* eslint-disable */
// 观察池语义验证：判定不可买(600685)不入池；可买(600519)入池；结论区说明给出具体不满足项
const puppeteer = require('puppeteer-core')
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
async function typeInto(page, selector, text) {
  await page.evaluate((sel, txt) => {
    const el = document.querySelector(sel)
    if (!el) return
    el.focus()
    const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set
    setter.call(el, txt)
    el.dispatchEvent(new Event('input', { bubbles: true }))
  }, selector, text)
}
;(async () => {
  const browser = await puppeteer.launch({ executablePath: 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe', headless: 'new', args: ['--no-sandbox', '--disable-gpu'] })
  const page = await browser.newPage()
  const ok = [], fail = []
  const rec = (n, p, x = '') => { (p ? ok : fail).push(n); console.log(`${p ? 'PASS' : 'FAIL'} | ${n}${x ? ' | ' + x : ''}`) }
  await page.goto('http://127.0.0.1:5000/', { waitUntil: 'networkidle2', timeout: 30000 })
  await page.evaluate(() => localStorage.clear())
  await page.reload({ waitUntil: 'networkidle2', timeout: 30000 })
  await page.waitForSelector('.bottom-nav-item', { timeout: 20000 })
  await page.evaluate(() => { const el = Array.from(document.querySelectorAll('.bottom-nav-item')).find((e) => e.textContent.includes('打分')); if (el) el.click() })
  await sleep(1200)

  async function scoreStock(code, name) {
    const input = '.score-page .ant-select-selection-search-input'
    await page.click(input)
    await typeInto(page, input, code)
    await sleep(2000)
    await page.evaluate((nm) => { const o = Array.from(document.querySelectorAll('.ant-select-item-option')).find((e) => e.textContent.includes(nm)); if (o) o.click() }, name)
    for (let i = 0; i < 45; i++) { await sleep(1000); if (await page.evaluate(() => !!document.querySelector('.verdict-title'))) break }
    await sleep(300)
  }

  async function poolCodes() {
    return page.evaluate(() => Array.from(document.querySelectorAll('.pool-table tbody tr .pool-name')).map((e) => e.textContent))
  }

  // 1) 600685 中船防务：判定不宜买入 -> 不入池
  await scoreStock('600685', '中船防务')
  let title = await page.evaluate(() => document.querySelector('.verdict-title').textContent)
  rec('600685 判定为不宜买入', title.includes('不宜买入'), title)
  const note1 = await page.evaluate(() => document.querySelector('.verdict-note').textContent)
  rec('结论说明点明「买点分 50 < 55」原因', note1.includes('买点分 50 < 55'), note1.slice(0, 80))
  const pool1 = await poolCodes()
  rec('600685 未加入观察池', !pool1.some((t) => t.includes('中船防务')), pool1.join(','))
  const tip1 = await page.evaluate(() => document.querySelector('.pool-tip').textContent)
  rec('池提示说明未入池原因', tip1.includes('未加入观察池'), tip1.slice(0, 60))

  // 2) 600519 贵州茅台：判定可买 -> 入池
  await scoreStock('600519', '贵州茅台')
  title = await page.evaluate(() => document.querySelector('.verdict-title').textContent)
  rec('600519 判定为可以买入', title.includes('可以买入'), title)
  const pool2 = await poolCodes()
  rec('600519 已加入观察池', pool2.some((t) => t.includes('贵州茅台')), pool2.join(','))
  const tip2 = await page.evaluate(() => document.querySelector('.pool-tip').textContent)
  rec('池提示说明已入池', tip2.includes('已自动加入观察池') || tip2.includes('已在观察池'), tip2.slice(0, 60))

  console.log(`\nRESULT ok=${ok.length} fail=${fail.length}`)
  await browser.close()
  process.exit(fail.length ? 1 : 0)
})().catch((e) => { console.error('E2E CRASH', e); process.exit(2) })
