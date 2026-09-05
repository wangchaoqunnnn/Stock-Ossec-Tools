/* eslint-disable */
// 个股打分页面 E2E：搜索(拼音/代码/名称) -> 评分展示 -> 观察池加入/删除
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
  const browser = await puppeteer.launch({
    executablePath: 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    headless: 'new',
    args: ['--no-sandbox', '--disable-gpu'],
  })
  const page = await browser.newPage()
  const errors = []
  page.on('pageerror', (e) => errors.push('pageerror: ' + e.message))
  const ok = []
  const fail = []
  const rec = (n, p, x = '') => { (p ? ok : fail).push(n); console.log(`${p ? 'PASS' : 'FAIL'} | ${n}${x ? ' | ' + x : ''}`) }

  await page.goto('http://127.0.0.1:5000/', { waitUntil: 'networkidle2', timeout: 30000 })
  await page.evaluate(() => localStorage.clear())
  await page.reload({ waitUntil: 'networkidle2', timeout: 30000 })
  await page.waitForSelector('.bottom-nav-item', { timeout: 20000 })

  // 导航到打分
  await page.evaluate(() => {
    const els = Array.from(document.querySelectorAll('.bottom-nav-item'))
    const el = els.find((e) => e.textContent.includes('打分'))
    if (el) el.click()
  })
  await sleep(1000)
  rec('导航到个股打分页', await page.evaluate(() => document.body.textContent.includes('个股打分')))

  // 拼音搜索 gzmt
  const input = '.score-page .ant-select-selection-search-input'
  await page.click(input)
  await typeInto(page, input, 'gzmt')
  await sleep(1500)
  const opt = await page.evaluate(() => Array.from(document.querySelectorAll('.ant-select-item-option')).map((e) => e.textContent.replace(/\s+/g, '')))
  rec('拼音检索出现下拉', opt.some((t) => t.includes('贵州茅台')), opt.join(','))
  await page.evaluate(() => {
    const o = Array.from(document.querySelectorAll('.ant-select-item-option')).find((e) => e.textContent.includes('贵州茅台'))
    if (o) o.click()
  })

  // 等待评分结果（多次打分上游调用，可能较慢）
  let gotResult = false
  for (let i = 0; i < 30; i++) {
    await sleep(1000)
    gotResult = await page.evaluate(() => !!document.querySelector('.scores-grid'))
    if (gotResult) break
  }
  rec('评分结果渲染（六维打分卡片）', gotResult)
  if (gotResult) {
    const names = await page.evaluate(() =>
      Array.from(document.querySelectorAll('.score-label')).map((e) => e.textContent.replace(/\s+/g, ''))
    )
    rec('包含六个维度打分', names.length === 6, names.join(','))
    const verdict = await page.evaluate(() => document.querySelector('.verdict-title')?.textContent.replace(/\s+/g, '') || '')
    rec('给出买卖结论（红可买/绿不可买）', verdict.length > 0, verdict)
    const poolIn = await page.evaluate(() => document.body.textContent.includes('观察池'))
    rec('观察池渲染', poolIn)
    const poolRows = await page.evaluate(() => document.querySelectorAll('.pool-table tbody tr').length)
    rec('值得跟踪自动入池(行>=1)', poolRows >= 1, `${poolRows} 行`)
    // 删除
    if (poolRows >= 1) {
      await page.evaluate(() => {
        const b = document.querySelector('.pool-table .ant-btn-dangerous')
        if (b) b.click()
      })
      await sleep(800)
      const after = await page.evaluate(() => document.querySelectorAll('.pool-table tbody tr').length)
      rec('观察池删除功能', after === poolRows - 1, `${poolRows} -> ${after}`)
    }
  }
  console.log('JS errors:', JSON.stringify(errors))
  await browser.close()
  console.log(`通过 ${ok.length}/${ok.length + fail.length}`)
  process.exit(fail.length || errors.length ? 1 : 0)
})().catch((e) => { console.error('crash:', e.message); process.exit(1) })
