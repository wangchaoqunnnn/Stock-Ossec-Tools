/* eslint-disable */
// 个股打分页「询问能否以当前市价买入」E2E：评分 -> 点分时量价分析 -> 结论与形态展示
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

  await page.evaluate(() => {
    const els = Array.from(document.querySelectorAll('.bottom-nav-item'))
    const el = els.find((e) => e.textContent.includes('打分'))
    if (el) el.click()
  })
  await sleep(1000)
  rec('导航到个股打分页', await page.evaluate(() => document.body.textContent.includes('个股打分')))

  async function scoreAndAsk(code, pickText) {
    const input = '.score-page .ant-select-selection-search-input'
    await page.click(input)
    await typeInto(page, input, code)
    await sleep(1800)
    const optTexts = await page.evaluate(() => Array.from(document.querySelectorAll('.ant-select-item-option')).map((e) => e.textContent.replace(/\s+/g, '')))
    const hit = optTexts.find((t) => t.includes(pickText))
    rec(`${code} 检索出现结果`, !!hit, (hit || '').slice(0, 30))
    await page.evaluate((txt) => {
      const o = Array.from(document.querySelectorAll('.ant-select-item-option')).find((e) => e.textContent.replace(/\s+/g, '').includes(txt))
      if (o) o.click()
    }, pickText)

    let gotResult = false
    for (let i = 0; i < 40; i++) {
      await sleep(1000)
      gotResult = await page.evaluate(() => !!document.querySelector('.ask-card'))
      if (gotResult) break
    }
    rec(`${code} 评分结果 + 询问卡片出现`, gotResult)

    // 点击分时量价分析
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('.ask-card button'))
      const b = btns.find((x) => x.textContent.includes('分时量价分析') || x.textContent.includes('重新分析'))
      if (b) b.click()
    })
    let gotAsk = false
    for (let i = 0; i < 40; i++) {
      await sleep(1000)
      gotAsk = await page.evaluate(() => !!document.querySelector('.ask-card .ask-verdict'))
      if (gotAsk) break
    }
    const out = await page.evaluate(() => {
      const v = document.querySelector('.ask-card .ask-verdict')
      const chips = Array.from(document.querySelectorAll('.ask-card .ask-chip-name')).map((e) => e.textContent)
      const suggest = document.querySelector('.ask-card .ask-suggest')
      const levels = document.querySelector('.ask-card .ask-levels')
      const note = document.querySelector('.ask-card .ask-note')
      return {
        verdict: v ? v.textContent.replace(/\s+/g, ' ').trim() : '',
        chips,
        suggest: suggest ? suggest.textContent.replace(/\s+/g, ' ').trim() : '',
        levels: levels ? levels.textContent.replace(/\s+/g, ' ').trim() : '',
        note: note ? note.textContent.trim() : '',
      }
    })
    rec(`${code} 分析结论出现`, gotAsk, out.verdict)
    if (out.verdict) console.log(`  结论: ${out.verdict}`)
    if (out.chips.length) console.log(`  形态: ${out.chips.join(' / ')}`)
    if (out.suggest) console.log(`  建议: ${out.suggest}`)
    if (out.levels) console.log(`  价位: ${out.levels}`)
    console.log(`  说明: ${out.note}`)
    return out
  }

  await scoreAndAsk('600519', '贵州茅台')
  await scoreAndAsk('000938', '紫光股份')

  if (errors.length) console.log('JS errors:', errors.join(' | '))
  console.log(`\nRESULT ok=${ok.length} fail=${fail.length}`)
  await browser.close()
  process.exit(fail.length ? 1 : 0)
})().catch((e) => { console.error('E2E CRASH', e); process.exit(2) })
