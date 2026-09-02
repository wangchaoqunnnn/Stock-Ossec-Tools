/* eslint-disable */
// 子路径部署验证：加载 http://127.0.0.1:8899/app/ 并确认指数/行情正常加载
const puppeteer = require('puppeteer-core')

const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

async function main() {
  const browser = await puppeteer.launch({
    executablePath: 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    headless: 'new',
    args: ['--no-sandbox', '--disable-gpu'],
  })
  const page = await browser.newPage()
  const reqs = []
  const errors = []
  page.on('request', (r) => { if (r.url().includes('/api/')) reqs.push(r.url()) })
  page.on('pageerror', (e) => errors.push('pageerror: ' + e.message))
  page.on('console', (m) => { if (m.type() === 'error') errors.push('console: ' + m.text()) })

  const ok = []
  const fail = []

  await page.goto('http://127.0.0.1:8899/app/', { waitUntil: 'networkidle2', timeout: 30000 })
  await page.waitForSelector('.quote-name', { timeout: 15000 }).catch(() => {})
  ok.push(['子路径页面加载（出现行情面板）', await page.evaluate(() => !!document.querySelector('.quote-name'))])

  // 指数区域：等数据渲染
  await page.waitForFunction(() => {
    const cards = document.querySelectorAll('.index-card')
    return cards.length > 0 && document.body.textContent.includes('上证指数')
  }, { timeout: 15000 }).catch(() => {})
  const indexCards = await page.evaluate(() => document.querySelectorAll('.index-card').length)
  const hasShanghai = await page.evaluate(() => document.body.textContent.includes('上证指数'))
  ok.push(['指数卡片渲染（A股6张）', indexCards === 6, `cards=${indexCards}`])
  ok.push(['上证指数数据出现', hasShanghai])

  // 无错误提示
  const errMsg = await page.evaluate(() => /响应解析失败|指数加载失败/.test(document.body.textContent.replace(/\s+/g, '')))
  ok.push(['页面无"响应解析失败/指数加载失败"提示', !errMsg])

  // API 请求都应落在子路径前缀下
  const allPrefixed = reqs.every((u) => u.startsWith('http://127.0.0.1:8899/app/api/'))
  ok.push(['API 请求全部走相对子路径前缀', allPrefixed, JSON.stringify(reqs)])

  // 搜索一个股票验证 quote 接口
  const input = '.ant-select-selection-search-input'
  await page.click(input)
  await page.evaluate((sel) => {
    const el = document.querySelector(sel)
    el.focus()
    const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set
    setter.call(el, '600036')
    el.dispatchEvent(new Event('input', { bubbles: true }))
  }, input)
  await sleep(800)
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('.query-btn')).find((x) => x.textContent.includes('立即查询'))
    if (b) b.click()
  })
  await sleep(3500)
  const quoteName = await page.evaluate(() => document.querySelector('.quote-name')?.textContent || '')
  ok.push(['子路径下搜索查询正常', quoteName.includes('招商银行'), quoteName])

  console.log('\n===== 子路径部署验证 =====')
  for (const [name, pass, extra] of ok) {
    console.log(`${pass ? 'PASS' : 'FAIL'} | ${name}${extra ? ' | ' + extra : ''}`)
    if (!pass) fail.push(name)
  }
  if (errors.length) {
    console.log('JS 错误:')
    errors.forEach((e) => console.log('  ' + e))
  }
  await browser.close()
  console.log(fail.length ? `FAILED: ${fail.join('; ')}` : 'ALL PASS')
  process.exit(fail.length || errors.length ? 1 : 0)
}

main().catch((e) => { console.error('crash:', e.message); process.exit(1) })
