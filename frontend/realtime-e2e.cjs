/* eslint-disable */
// 实时刷新专项验证：
// 1) 首页指数速览：来自 /api/indices 实时数据，且停留期间自动轮询
// 2) 主要指数：15s 自动轮询
// 3) 个股行情详情：15s 自动轮询
// 运行：node realtime-e2e.cjs（需后端 :5000 + dist 已构建）
const puppeteer = require('puppeteer-core')

const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
const BASE = 'http://127.0.0.1:5000'
const results = []
const record = (name, ok, extra = '') => {
  results.push({ name, ok })
  console.log(`${ok ? 'PASS' : 'FAIL'} | ${name}${extra ? ' | ' + extra : ''}`)
}

async function countApi(page, pattern, waitMs) {
  let count = 0
  const handler = (r) => { if (r.url().includes(pattern)) count++ }
  page.on('request', handler)
  await sleep(waitMs)
  page.off('request', handler)
  return count
}

async function clickByText(page, selector, text) {
  return page.evaluate((sel, txt) => {
    const norm = (s) => (s || '').replace(/\s+/g, '')
    const target = norm(txt)
    const els = Array.from(document.querySelectorAll(sel))
    const el = els.find((e) => { const t = norm(e.textContent); return t === target || (target && t.includes(target)) })
    if (el) { el.click(); return true }
    return false
  }, selector, text)
}

async function typeInto(page, selector, text) {
  await page.evaluate((sel, txt) => {
    const el = document.querySelector(sel)
    if (!el) return
    el.focus()
    const proto = el instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype
    const setter = Object.getOwnPropertyDescriptor(proto, 'value').set
    setter.call(el, txt)
    el.dispatchEvent(new Event('input', { bubbles: true }))
  }, selector, text)
}

async function main() {
  const browser = await puppeteer.launch({
    executablePath: 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    headless: 'new',
    args: ['--no-sandbox', '--disable-gpu'],
  })
  const page = await browser.newPage()

  try {
    // ---------- 后端真实数据基准（脚本内直接用绝对地址） ----------
    const benchResp = await page.evaluate(async (base) => {
      const r = await fetch(base + '/api/indices?market=cn')
      return (await r.json()).data.items
    }, BASE)
    const bench = {}
    benchResp.forEach((it) => { bench[it.name] = it.now })

    // ============ 1. 首页指数速览 ============
    await page.goto(BASE, { waitUntil: 'networkidle2', timeout: 30000 })
    await page.evaluate(() => localStorage.clear())
    await page.reload({ waitUntil: 'networkidle2', timeout: 30000 })
    await page.waitForSelector('.quote-name', { timeout: 15000 })
    await clickByText(page, '.bottom-nav-item', '首页')
    await page.waitForSelector('.hero-stats .stat-item', { timeout: 15000 })

    const homeStats = await page.evaluate(() =>
      Array.from(document.querySelectorAll('.hero-stats .stat-item')).map((el) => {
        const label = el.querySelector('.stat-label').textContent.trim()
        const value = el.querySelector('.stat-value').textContent.trim()
        return { label, value }
      })
    )
    record('首页显示 4 项指数速览', homeStats.length === 4, JSON.stringify(homeStats))

    const sh = homeStats.find((s) => s.label === '上证指数')
    const benchShanghai = bench['上证指数']
    const match =
      sh && benchShanghai !== undefined && Math.abs(parseFloat(sh.value) - Number(benchShanghai)) < 1.0
    record('首页上证指数与后端实时数据一致', !!match, `${sh ? sh.value : '--'} vs ${benchShanghai}`)

    // 停留 ~33s（> 两个 15s 周期）应出现 ≥2 次轮询
    const homeReqs = await countApi(page, '/api/indices', 33500)
    record('首页停留期间自动轮询指数(>=2次)', homeReqs >= 2, `请求 ${homeReqs} 次`)

    // ============ 2. 主要指数（工具页） ============
    await clickByText(page, '.bottom-nav-item', '工具')
    await sleep(800)
    await page.waitForSelector('.index-card', { timeout: 15000 })
    const toolReqs = await countApi(page, '/api/indices', 33500)
    record('主要指数 15s 自动轮询(>=2次)', toolReqs >= 2, `请求 ${toolReqs} 次`)

    // ============ 3. 个股行情详情 ============
    const input = '.ant-select-selection-search-input'
    await page.click(input)
    await typeInto(page, input, '600036')
    await sleep(700)
    await clickByText(page, '.query-btn', '立即查询')
    await sleep(3000)
    const quoteName = await page.evaluate(() => document.querySelector('.quote-name')?.textContent || '')
    record('查询招商银行行情', quoteName.includes('招商银行'), quoteName)

    const quoteReqs = await countApi(page, 'api/stock/quote?code=600036', 33500)
    record('个股行情 15s 自动轮询(>=2次)', quoteReqs >= 2, `请求 ${quoteReqs} 次`)

    // ============ 4. 关注清单 ============
    await clickByText(page, '.add-watch-btn', '+加关注')
    await sleep(1500)
    // 30s 周期：33s 内应至少触发 1 次
    const batchReqs = await countApi(page, 'api/stock/batch', 33500)
    record('关注清单 30s 自动轮询(>=1次)', batchReqs >= 1, `请求 ${batchReqs} 次`)
  } catch (e) {
    console.error('realtime E2E 崩溃:', e.message)
    results.push({ name: '崩溃', ok: false })
  } finally {
    await browser.close()
    const failed = results.filter((r) => !r.ok)
    console.log('\n通过 ' + (results.length - failed.length) + ' / ' + results.length)
    process.exit(failed.length ? 1 : 0)
  }
}

main().catch((e) => { console.error(e.message); process.exit(1) })
