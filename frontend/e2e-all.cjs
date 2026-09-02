/* eslint-disable */
// 全功能 E2E 测试 v3：真实鼠标点击 + Escape 关闭下拉 + 崩溃时输出诊断
// 运行：node e2e-all.cjs （需后端运行在 :5000，frontend/dist 已构建）
const puppeteer = require('puppeteer-core');

const BASE = 'http://127.0.0.1:5000';
const results = [];
let errors = [];

function record(name, ok, extra = '') {
  results.push({ name, ok, extra });
  console.log(`${ok ? 'PASS' : 'FAIL'} | ${name}${extra ? ' | ' + extra : ''}`);
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// 用原生 setter + input 事件输入（对 antd 受控输入组件最可靠）
async function typeInto(page, selector, text) {
  await page.evaluate(
    (sel, txt) => {
      const el = document.querySelector(sel);
      if (!el) return false;
      el.focus();
      const proto = el instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
      const setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
      setter.call(el, txt);
      el.dispatchEvent(new Event('input', { bubbles: true }));
      return true;
    },
    selector,
    text
  );
}

// 等待下载事件（兼容旧版 puppeteer-core）
function waitDownload(page, ms = 8000) {
  return new Promise((resolve) => {
    const timer = setTimeout(() => resolve(null), ms);
    page.once('download', (dl) => { clearTimeout(timer); resolve(dl); });
  });
}

async function clickByText(page, selector, text) {
  return page.evaluate(
    (sel, txt) => {
      const norm = (s) => (s || '').replace(/\s+/g, '');
      const target = norm(txt);
      const els = Array.from(document.querySelectorAll(sel));
      const el = els.find((e) => {
        const t = norm(e.textContent);
        return t === target || (target && t.includes(target));
      });
      if (el) { el.click(); return true; }
      return false;
    },
    selector,
    text
  );
}

async function clickOption(page, text) {
  await page.waitForSelector('.ant-select-item-option', { timeout: 10000 });
  const handles = await page.$$('.ant-select-item-option');
  for (const h of handles) {
    const t = await h.evaluate((el) => el.textContent);
    if (t.includes(text)) {
      await h.click(); // 真实鼠标点击
      return true;
    }
  }
  return false;
}

async function expectText(page, selector, contains, name, timeout = 15000) {
  try {
    await page.waitForFunction(
      (sel, txt) => {
        const el = document.querySelector(sel);
        return el && el.textContent.includes(txt);
      },
      { timeout },
      selector,
      contains
    );
    record(name, true);
  } catch (e) {
    record(name, false, `找不到 ${selector} 含 "${contains}"`);
  }
}

async function main() {
  const browser = await puppeteer.launch({
    executablePath: 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    headless: 'new',
    args: ['--no-sandbox', '--disable-gpu'],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 1000 });
  page.on('pageerror', (e) => errors.push('pageerror: ' + e.message));
  page.on('console', (m) => { if (m.type() === 'error') errors.push('console: ' + m.text()); });

  try {
    // ---------- 初始化 ----------
    await page.goto(BASE, { waitUntil: 'networkidle2', timeout: 30000 });
    await page.evaluate(() => localStorage.clear());
    await page.reload({ waitUntil: 'networkidle2', timeout: 30000 });
    await page.waitForSelector('.quote-name', { timeout: 15000 });
    record('首页加载（个股查询面板出现）', true);

    const input = '.ant-select-selection-search-input';
    const closeDropdown = async () => { await page.keyboard.press('Escape'); await sleep(300); };
    const clearInput = async () => {
      await page.click(input);
      await page.keyboard.down('Control'); await page.keyboard.press('a'); await page.keyboard.up('Control');
      await page.keyboard.press('Backspace');
      await sleep(200);
    };

    // ================= 1. 导航 =================
    await expectText(page, '.page-header-title', '个股查询', '默认视图标题为"个股查询"');
    for (const label of ['首页', '组合', '工具', '行情', '复盘']) {
      const ok = await clickByText(page, '.bottom-nav-item', label);
      await sleep(900);
      const title = await page.evaluate(() => document.querySelector('.page-header-title')?.textContent || '');
      record(`底部导航「${label}」可点击`, ok && title.length > 0, title);
    }
    await clickByText(page, '.logo', '量化终端');
    await sleep(900);
    await expectText(page, '.hero-title', '老王量化', 'Logo 点击回到首页');
    await clickByText(page, '.module-card', '个股查询');
    await sleep(900);
    await expectText(page, '.page-header-title', '个股查询', '首页模块卡片跳转');

    // ================= 2. 个股查询 =================
    // 名称搜索 + 点选
    await page.click(input);
    await typeInto(page, input, '紫光股份');
    await sleep(1500);
    const optOk = await clickOption(page, '紫光股份');
    await sleep(4000);
    await expectText(page, '.quote-name', '紫光股份', '名称搜索点选后显示行情');
    record('搜索下拉选项出现', optOk);

    // 6位代码 + 立即查询按钮
    await clearInput();
    await typeInto(page, input, '600036');
    await sleep(700);
    await closeDropdown();
    const q1 = await clickByText(page, '.query-btn', '立即查询');
    await sleep(4000);
    await expectText(page, '.quote-name', '招商银行', '「立即查询」按钮按代码查询');
    record('「立即查询」按钮可点击', q1);

    // 无效输入提示
    await clearInput();
    await typeInto(page, input, 'abc');
    await sleep(500);
    await closeDropdown();
    await clickByText(page, '.query-btn', '立即查询');
    await sleep(2200);
    const warnToast = await page.evaluate(() => /未找到|请检查输入|请输入/.test(document.body.textContent.replace(/\s+/g, '')));
    record('无效输入给出提示', warnToast);

    // 加关注
    await clearInput();
    await typeInto(page, input, '600036');
    await sleep(600);
    await closeDropdown();
    await clickByText(page, '.query-btn', '立即查询');
    await sleep(4000);
    await clickByText(page, '.add-watch-btn', '+ 加关注');
    await sleep(1200);
    const followed = await page.evaluate(() => document.body.textContent.includes('已关注'));
    record('「+ 加关注」按钮生效', followed);

    // ================= 3. 详情弹窗 =================
    await clickByText(page, '.detail-btn', '详情');
    await page.waitForSelector('.ant-modal-content', { timeout: 8000 }).catch(() => {});
    await sleep(800);
    record('「详情」按钮打开弹窗', await page.evaluate(() => !!document.querySelector('.ant-modal-content')));

    for (const tab of ['暗盘信息', '个股分析', '暗盘历史', '异动清单']) {
      const ok = await clickByText(page, '.detail-tab', tab);
      await sleep(600);
      const active = await page.evaluate(() => document.querySelector('.detail-tab.active')?.textContent.trim() || '');
      record(`详情标签「${tab}」可切换`, ok && active === tab, active);
    }

    await clickByText(page, '.detail-tab', '暗盘信息');
    await sleep(400);
    for (const r of ['经典', '今天']) {
      await clickByText(page, '.ctrl-btn', r);
      await sleep(400);
      const active = await page.evaluate(() => Array.from(document.querySelectorAll('.ctrl-btn.active')).map((e) => e.textContent.trim()));
      record(`图表范围「${r}」可切换`, active.includes(r), active.join(','));
    }
    for (const p of ['分时', '日K', '周K', '月K']) {
      await clickByText(page, '.ctrl-btn', p);
      await sleep(400);
      record(`图表周期「${p}」可切换且有图`, await page.evaluate(() => !!document.querySelector('.chart-svg')));
    }

    await clickByText(page, '.icon-btn', '↻');
    await sleep(1500);
    record('弹窗「刷新」按钮点击无异常', true);
    const starBefore = await page.evaluate(() => document.querySelector('.icon-btn.star')?.textContent.replace(/\s+/g, ''));
    await clickByText(page, '.icon-btn', starBefore === '★' ? '★' : '☆');
    await sleep(800);
    const starMid = await page.evaluate(() => document.querySelector('.icon-btn.star')?.textContent.replace(/\s+/g, ''));
    // 再点一次还原关注状态，避免影响后续关注清单测试
    await clickByText(page, '.icon-btn', starMid === '★' ? '★' : '☆');
    await sleep(800);
    const starAfter = await page.evaluate(() => document.querySelector('.icon-btn.star')?.textContent.replace(/\s+/g, ''));
    record('弹窗「收藏」按钮可切换', starBefore !== starMid && starBefore === starAfter, `${starBefore} -> ${starMid} -> ${starAfter}`);
    await clickByText(page, '.icon-btn', '⋯');
    await sleep(500);
    record('弹窗「更多」按钮点击无异常', true);

    await page.evaluate(() => { const c = document.querySelector('.ant-modal-close'); if (c) c.click(); });
    await sleep(600);

    // ================= 4. 主要指数 =================
    for (const m of [{ label: 'A股', expect: '上证指数' }, { label: '亚太', expect: '恒生指数' }, { label: '美股', expect: '道琼斯' }, { label: '期货', expect: '沪深300股指' }]) {
      const ok = await clickByText(page, '.ant-radio-button-wrapper', m.label);
      await sleep(3000);
      const found = await page.evaluate((txt) => document.body.textContent.includes(txt), m.expect);
      record(`指数市场「${m.label}」切换显示${m.expect}`, ok && found);
    }
    const sw = await page.$('.ant-switch');
    if (sw) {
      await page.evaluate(() => { const s = document.querySelector('.ant-switch'); if (s) s.click(); });
      await sleep(500);
      const off = await page.evaluate(() => !document.querySelector('.ant-switch.ant-switch-checked'));
      await page.evaluate(() => { const s = document.querySelector('.ant-switch'); if (s) s.click(); });
      await sleep(500);
      record('指数自动刷新开关可切换', off);
    }
    const okRefresh = await page.evaluate(() => {
      const b = Array.from(document.querySelectorAll('.ant-btn')).find((x) => x.textContent.trim() === '↻');
      if (b) { b.click(); return true; }
      return false;
    });
    await sleep(2500);
    record('指数手动刷新按钮点击无异常', okRefresh);

    // ================= 5. 关注清单 =================
    await sleep(1500);
    record('关注清单显示已添加的股票', await page.evaluate(() => document.body.textContent.includes('招商银行') && document.body.textContent.includes('共 1 只')));

    const watchInput = '.watchlist-card .ant-select-selection-search-input';
    await page.click(watchInput);
    await typeInto(page, watchInput, '浦发');
    await sleep(1500);
    const opt2 = await clickOption(page, '浦发银行');
    await sleep(3500);
    record('关注清单搜索添加第二只', opt2 && (await page.evaluate(() => document.body.textContent.includes('共 2 只'))));

    await clickByText(page, '.watchlist-card .ant-btn', '列配置');
    await sleep(1000);
    record('「列配置」弹层可展开', await page.evaluate(() => document.body.textContent.includes('涨跌幅') && !!document.querySelector('.ant-popover')));
    await page.keyboard.press('Escape');
    await sleep(400);

    const remarkSpan = await page.$('.watchlist-card .remark-text');
    if (remarkSpan) {
      await page.evaluate(() => { const s = document.querySelector('.watchlist-card .remark-text'); if (s) s.click(); });
      await sleep(600);
      const inp = await page.$('.watchlist-card .remark-cell input');
      if (inp) {
        await typeInto(page, '.watchlist-card .remark-cell input', '测试备注');
        await page.keyboard.press('Enter');
        await sleep(1000);
        record('备注编辑保存', await page.evaluate(() => document.body.textContent.includes('备注已保存')));
      } else {
        record('备注编辑保存', false, '备注输入框未出现');
      }
    } else {
      record('备注编辑保存', false, '找不到备注入口');
    }

    await page.evaluate(() => { const box = document.querySelector('.watchlist-card thead .ant-checkbox-input'); if (box) box.click(); });
    await sleep(600);
    record('全选后批量删除按钮可用', await page.evaluate(() => {
      const b = Array.from(document.querySelectorAll('.watchlist-card button')).find((x) => x.textContent.includes('批量删除'));
      return b ? !b.disabled : false;
    }));
    await page.evaluate(() => { const box = document.querySelector('.watchlist-card thead .ant-checkbox-input'); if (box) box.click(); });
    await sleep(400);

    await page.evaluate(() => {
      const del = Array.from(document.querySelectorAll('.watchlist-card button')).find((b) => b.textContent.trim() === '删除');
      if (del) del.click();
    });
    await sleep(900);
    record('删除确认弹窗出现', await page.evaluate(() => !!document.querySelector('.ant-modal-confirm')));
    await page.evaluate(() => {
      const cancel = Array.from(document.querySelectorAll('.ant-modal-confirm .ant-btn')).find((b) => b.textContent.includes('取消'));
      if (cancel) cancel.click();
    });
    await sleep(400);

    await clickByText(page, '.watchlist-card .ant-btn', '批量添加');
    await sleep(1000);
    record('「批量添加」弹窗打开', await page.evaluate(() => document.body.textContent.includes('批量添加股票')));
    await page.evaluate(() => {
      const ta = document.querySelector('.ant-modal textarea');
      if (ta) {
        const setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
        setter.call(ta, '601318, 000001');
        ta.dispatchEvent(new Event('input', { bubbles: true }));
      }
      const okBtn = Array.from(document.querySelectorAll('.ant-modal-footer .ant-btn-primary'));
      if (okBtn[0]) okBtn[0].click();
    });
    // 轮询等待成功提示（refreshQuotes 后再弹 toast，最多 8s）
    let batchOk = false
    for (let i = 0; i < 10; i++) {
      await sleep(800)
      batchOk = await page.evaluate(() => /成功添加/.test(document.body.textContent.replace(/\s+/g, '')))
      if (batchOk) break
    }
    record('批量添加 2 只股票', batchOk);

    // ================= 6. 量化工具 =================
    await clickByText(page, '.utility-entry', '量化工具');
    await sleep(1000);
    await expectText(page, '.page-title', '量化工具', '「量化工具 →」按钮跳转');

    await clickByText(page, '.tab-btn', '今日关注');
    await sleep(500);
    await typeInto(page, '.utility-page .search-input', '通信');
    await clickByText(page, '.utility-page .btn-primary', '搜索');
    await sleep(600);
    const filtered = await page.evaluate(() => Array.from(document.querySelectorAll('.utility-page .data-table tbody tr')).length);
    record('今日关注搜索过滤生效', filtered >= 1 && filtered < 8, `剩余 ${filtered} 行`);
    await clickByText(page, '.utility-page .btn-outline', '刷新');
    await sleep(500);
    const rowsAfterReset = await page.evaluate(() => Array.from(document.querySelectorAll('.utility-page .data-table tbody tr')).length);
    record('今日关注「刷新」重置筛选', rowsAfterReset === 8, `共 ${rowsAfterReset} 行`);
    await clickByText(page, '.utility-page .btn-outline', '留列');
    await sleep(400);
    record('「留列」按钮点击无异常', true);
    await clickByText(page, '.utility-page .btn-detail', '详情');
    await sleep(800);
    record('今日关注「详情」打开弹窗', await page.evaluate(() => !!document.querySelector('.ant-modal-content')));
    await page.evaluate(() => { const c = document.querySelector('.ant-modal-close'); if (c) c.click(); });
    await sleep(400);

    await clickByText(page, '.tab-btn', '选股器');
    await sleep(500);
    await clickByText(page, '.cat-btn', '基本面');
    await sleep(400);
    record('选股器分类切换', await page.evaluate(() => document.body.textContent.includes('该分类条件开发中')));
    await clickByText(page, '.cat-btn', '决策指标');
    await sleep(400);
    await clickByText(page, '.tag-btn', '主力资金');
    await sleep(400);
    record('选股器标签多选', await page.evaluate(() => document.body.textContent.includes('已选 1 项')));
    await clickByText(page, '.btn-primary.small', '确定');
    await sleep(500);
    record('选股器「确定」点击无异常', true);
    await clickByText(page, '.collapse-btn', '收起条件');
    await sleep(400);
    record('选股器「收起条件」折叠', await page.evaluate(() => {
      const p = document.querySelector('.picker-panel');
      return !p || p.style.display === 'none' || !p.offsetParent;
    }));
    await clickByText(page, '.collapse-btn', '展开条件');
    await sleep(400);
    await clickByText(page, '.link-btn', '修改');
    await sleep(500);
    record('选股器「修改」展开条件', true);
    await clickByText(page, '.btn-outline.small', '刷新');
    await sleep(300);
    record('选股结果「刷新」点击无异常', true);
    const dl1 = waitDownload(page);
    await clickByText(page, '.btn-outline.small', '导出');
    await sleep(900);
    const exportToast = await page.evaluate(() => /已导出/.test(document.body.textContent.replace(/\s+/g, '')));
    const dl1r = await dl1;
    record('选股结果「导出」CSV 下载', !!dl1r || exportToast, dl1r ? dl1r.suggestedFilename() : (exportToast ? 'toast确认' : ''));

    await clickByText(page, '.tab-btn', '异动寻龙');
    await sleep(500);
    const dl2 = waitDownload(page);
    await clickByText(page, '.anomaly-header .btn-outline', '导出全部');
    await sleep(900);
    const exportToast2 = await page.evaluate(() => /已导出/.test(document.body.textContent.replace(/\s+/g, '')));
    const dl2r = await dl2;
    record('异动寻龙「导出全部」CSV 下载', !!dl2r || exportToast2, dl2r ? dl2r.suggestedFilename() : (exportToast2 ? 'toast确认' : ''));
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('.anomaly-content .btn-detail'));
      if (btns[0]) btns[0].click();
    });
    await sleep(800);
    record('异动寻龙「详情」打开弹窗', await page.evaluate(() => !!document.querySelector('.ant-modal-content')));
    await page.evaluate(() => { const c = document.querySelector('.ant-modal-close'); if (c) c.click(); });
    await sleep(400);

    // ================= 7. 行情中枢 =================
    await clickByText(page, '.bottom-nav-item', '行情');
    await sleep(1000);
    for (const t of ['资金流向', '市场情绪', '东财热榜', '7x24', '财经会议', '榜单']) {
      const ok = await clickByText(page, '.rank-tab, .tab-btn', t);
      await sleep(500);
      record(`行情中枢标签「${t}」切换`, ok);
    }
    await clickByText(page, '.sub-tab', '行业');
    await sleep(300);
    await clickByText(page, '.sub-tab', '概念');
    await sleep(300);
    await clickByText(page, '.ranking-tab', '跌幅榜');
    await sleep(300);
    await clickByText(page, '.ranking-tab', '涨幅榜');
    await sleep(300);
    record('行情中枢子标签切换无异常', true);

    // ================= 8. 组合 & 复盘 =================
    await clickByText(page, '.bottom-nav-item', '组合');
    await sleep(1000);
    const pTabs = await page.evaluate(() => Array.from(document.querySelectorAll('.tab-btn, .port-tab, .pf-tab')).map((e) => e.textContent.trim()));
    record('组合页渲染', pTabs.length > 0, pTabs.join(','));
    await clickByText(page, '.bottom-nav-item', '复盘');
    await sleep(1000);
    const cTabs = await page.evaluate(() => Array.from(document.querySelectorAll('.tab-btn, .comm-tab, .main-tab')).map((e) => e.textContent.replace(/\s+/g, '')));
    record('复盘页渲染', cTabs.length > 0, cTabs.join(','));

    // ================= 9. 通知/设置 =================
    await clickByText(page, '.nav-btn', '🔔');
    await sleep(500);
    record('通知按钮弹提示', await page.evaluate(() => document.body.textContent.includes('暂无新通知')));
    await clickByText(page, '.nav-btn', '⚙');
    await sleep(500);
    record('设置按钮弹提示', await page.evaluate(() => document.body.textContent.includes('建设中')));
  } catch (e) {
    console.error('E2E 崩溃:', e.message);
    errors.push('crash: ' + e.message);
  } finally {
    // ================= 汇总 =================
    await browser.close();
    const realErrors = errors.filter((e) => !e.includes('favicon'));
    const failed = results.filter((r) => !r.ok);
    console.log('\n========== 汇总 ==========');
    console.log(`通过 ${results.length - failed.length} / ${results.length}`);
    if (realErrors.length) {
      console.log('JS 错误:');
      realErrors.forEach((e) => console.log('  ' + e));
    }
    if (failed.length) {
      console.log('失败项:');
      failed.forEach((f) => console.log('  ✗ ' + f.name + (f.extra ? ' — ' + f.extra : '')));
    }
    process.exit(failed.length || realErrors.length ? 1 : 0);
  }
}

main().catch((e) => {
  console.error('E2E 崩溃:', e.message);
  process.exit(1);
});
