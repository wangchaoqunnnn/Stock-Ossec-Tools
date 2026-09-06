/* eslint-disable */
// 买点语义修复验证：下行趋势股(600118) 现价下方参考 + 上方压力位标注提示
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
  const input = '.score-page .ant-select-selection-search-input'
  await page.click(input)
  await typeInto(page, input, '600118')
  await sleep(2000)
  await page.evaluate(() => { const o = Array.from(document.querySelectorAll('.ant-select-item-option')).find((e) => e.textContent.includes('中国卫星')); if (o) o.click() })
  let ready = false
  for (let i = 0; i < 45; i++) { await sleep(1000); ready = await page.evaluate(() => !!document.querySelector('.buypoint-card')); if (ready) break }
  const data = await page.evaluate(() => {
    const items = Array.from(document.querySelectorAll('.bp-item')).map((el) => ({
      type: el.querySelector('.bp-type') ? el.querySelector('.bp-type').textContent : '',
      price: el.querySelector('.bp-price') ? el.querySelector('.bp-price').textContent : '',
      rel: el.querySelector('.bp-rel') ? el.querySelector('.bp-rel').textContent : '',
    }))
    const hint = document.querySelector('.bp-hint')
    const advice = Array.from(document.querySelectorAll('.advice-list li')).map((e) => e.textContent)
    return { items, hint: hint ? hint.textContent : '', advice }
  })
  rec('评分与买点面板出现', ready)
  rec('存在现价下方低吸参考(超短)', data.items.some((i) => i.type.includes('超短') && i.rel.includes('现价下方')), data.items.map((i) => `${i.type}@${i.price}[${i.rel}]`).join(' , '))
  rec('上方价位带「压力/修复位」标注', data.items.some((i) => i.rel.includes('现价上方')))
  rec('出现「现价上方不是更低买点」说明', data.hint.includes('不是更低的买点'), data.hint.slice(0, 40))
  rec('操作建议回应“低价≠买点到位”', data.advice.some((a) => a.includes('价位低') && a.includes('抄底')), data.advice[1] || '')
  console.log(`\nRESULT ok=${ok.length} fail=${fail.length}`)
  await browser.close()
  process.exit(fail.length ? 1 : 0)
})().catch((e) => { console.error('E2E CRASH', e); process.exit(2) })
