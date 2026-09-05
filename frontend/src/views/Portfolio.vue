<script setup>
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { searchStocks, fetchStockScore } from '../api'
import { num, pct, signed, trendClass } from '../utils/format'

const POOL_KEY = 'stock_score_pool_v1'

// 搜索
const keyword = ref('')
const options = ref([])
const searching = ref(false)

// 结果
const result = ref(null)
const loading = ref(false)
let timer = null
let seq = 0

// 观察池
const pool = ref([])

// ---------- 观察池（localStorage） ----------
function loadPool() {
  try {
    const raw = localStorage.getItem(POOL_KEY)
    pool.value = raw ? JSON.parse(raw) : []
  } catch (e) {
    pool.value = []
  }
}
function savePool() {
  localStorage.setItem(POOL_KEY, JSON.stringify(pool.value))
}

function pad(n) {
  return String(n).padStart(2, '0')
}
function fmtDate(d) {
  const x = new Date(d)
  return `${x.getFullYear()}-${pad(x.getMonth() + 1)}-${pad(x.getDate())} ${pad(x.getHours())}:${pad(x.getMinutes())}`
}

function addToPool(r) {
  if (!r) return
  if (pool.value.some((p) => p.code === r.code)) return
  pool.value.push({
    code: r.code,
    name: r.name,
    price: r.price,
    date: fmtDate(new Date()),
  })
  savePool()
}

function removeFromPool(code) {
  pool.value = pool.value.filter((p) => p.code !== code)
  savePool()
  message.success('已从观察池删除')
}

function inPool(code) {
  return pool.value.some((p) => p.code === code)
}

// ---------- 搜索 ----------
async function doSearch(val) {
  const kw = (val || '').trim()
  if (!kw) {
    options.value = []
    return
  }
  searching.value = true
  const id = ++seq
  try {
    const list = await searchStocks(kw, 10)
    if (id !== seq) return
    options.value = list.map((s) => ({
      value: `${s.code} ${s.name}`,
      code: s.code,
      name: s.name,
      pinyin: s.pinyin || '',
      type: s.security_type || s.market_type,
    }))
  } catch (e) {
    if (id !== seq) return
    options.value = []
  } finally {
    if (id === seq) searching.value = false
  }
}
function onSearch(val) {
  clearTimeout(timer)
  timer = setTimeout(() => doSearch(val), 300)
}

function pickOption(value, option) {
  const code = (option && option.code) || String(value).split(' ')[0]
  const name = (option && option.name) || ''
  keyword.value = name ? `${code} ${name}` : code
  evaluate(code)
}

async function evaluate(code) {
  const c = String(code || '').trim()
  if (!/^\d{6}$/.test(c)) {
    message.warning('请输入有效的 6 位股票代码')
    return
  }
  loading.value = true
  result.value = null
  try {
    const data = await fetchStockScore(c)
    result.value = data
    // 策略：值得跟踪则自动放入观察池
    if (data && data.worth_track) {
      addToPool(data)
      message.success(`${data.name}：值得跟踪，已加入观察池`)
    } else if (data) {
      message.info(`${data.name}：综合/买点得分较低，暂不值得跟踪`)
    }
  } catch (e) {
    message.error(e.message)
  } finally {
    loading.value = false
  }
}

function evaluateCurrent() {
  const raw = keyword.value.trim()
  const codeMatch = raw.match(/\b\d{6}\b/)
  const code = codeMatch ? codeMatch[0] : (options.value.length ? options.value[0].code : '')
  if (code) evaluate(code)
  else message.warning('请先输入并选择股票')
}

// 分数条颜色
function scoreColor(s) {
  if (s >= 70) return 'up'
  if (s >= 55) return 'warn'
  if (s >= 40) return 'mid'
  return 'down'
}

const scoreMeta = [
  { key: 'fundamental', label: '① 基础面', sub: '按业绩（估值近似）' },
  { key: 'sector', label: '② 所属板块', sub: '板块热度' },
  { key: 'technical', label: '③ 技术面', sub: '日/周/月趋势强度' },
  { key: 'sentiment', label: '④ 短线情绪', sub: '量价情绪' },
  { key: 'buy_point', label: '⑤ 当前买点', sub: '现价与买点位置' },
]

onMounted(loadPool)
</script>

<template>
  <div class="score-page">
    <!-- 页面头部 -->
    <header class="page-head">
      <div>
        <div class="brand-tag">STOCK SCORING</div>
        <h1 class="page-title">个股打分</h1>
        <div class="page-sub">输入 代码 / 名称 / 拼音首字母（如 600519、贵州茅台、gzmt）自动评分并给出操作建议</div>
      </div>
    </header>

    <!-- 搜索区 -->
    <div class="search-card terminal-card">
      <div class="search-row">
        <a-select
          v-model:value="keyword"
          :options="options"
          show-search
          :filter-option="false"
          :loading="searching"
          placeholder="输入股票代码 / 名称 / 拼音首字母…"
          style="flex: 1"
          @search="onSearch"
          @select="pickOption"
        >
          <template #option="{ name, code, pinyin, type }">
            <div class="opt-row">
              <span class="opt-name">{{ name }}</span>
              <span class="opt-code num">{{ code }}</span>
              <span v-if="pinyin" class="opt-pinyin">{{ pinyin }}</span>
              <span class="opt-type">{{ type }}</span>
            </div>
          </template>
        </a-select>
        <a-button type="primary" @click="evaluateCurrent">开始打分</a-button>
      </div>
    </div>

    <a-spin :spinning="loading">
      <!-- 评分结果 -->
      <div v-if="result" class="result-area">
        <!-- 顶部信息 + 结论 -->
        <div class="quote-card terminal-card">
          <div class="quote-head">
            <div class="quote-left">
              <span class="q-name">{{ result.name }}</span>
              <span class="q-code num">{{ result.code }}</span>
              <span class="q-industry" v-if="result.industry">{{ result.industry }}</span>
              <span class="q-time num">评分时间 {{ result.evaluated_at }}</span>
            </div>
            <div class="quote-right">
              <span class="q-price num" :class="trendClass(result.change_pct)">{{ num(result.price, 2) }}</span>
              <span class="q-pct num" :class="trendClass(result.change_pct)">{{ signed(result.change_pct) }}%</span>
            </div>
          </div>

          <!-- 结论：可买=红字 / 不可买=绿字 -->
          <div class="verdict" :class="result.can_buy ? 'verdict-buy' : 'verdict-nobuy'">
            <div class="verdict-title">{{ result.can_buy ? '✓ 可以买入' : '✗ 当前不宜买入' }}</div>
            <div class="verdict-note">{{ result.can_buy ? '红色提示：当前具备买入条件，可少量分批建仓' : '绿色提示：当前买点不佳，请参考下方给出的等待买点价位' }}</div>
          </div>
        </div>

        <!-- 六维评分 -->
        <div class="scores-grid">
          <div v-for="m in scoreMeta" :key="m.key" class="score-card terminal-card">
            <div class="score-head">
              <span class="score-label">{{ m.label }}</span>
              <span class="score-sub">{{ m.sub }}</span>
            </div>
            <div class="score-num num" :class="scoreColor(result.scores[m.key].score)">{{ result.scores[m.key].score }}</div>
            <div class="score-track">
              <div class="score-fill" :class="scoreColor(result.scores[m.key].score)"
                   :style="{ width: Math.max(2, Math.min(100, result.scores[m.key].score)) + '%' }"></div>
            </div>
            <ul class="score-reasons">
              <li v-for="(r, i) in result.scores[m.key].reasons" :key="i">{{ r }}</li>
            </ul>
          </div>

          <!-- 综合分大卡片 -->
          <div class="score-card composite-card terminal-card">
            <div class="score-head">
              <span class="score-label">⑥ 综合打分</span>
              <span class="score-sub">前五项加权</span>
            </div>
            <div class="composite-num num" :class="scoreColor(result.scores.composite.score)">{{ result.scores.composite.score }}</div>
            <div class="composite-track">
              <div class="score-fill" :class="scoreColor(result.scores.composite.score)"
                   :style="{ width: Math.max(2, Math.min(100, result.scores.composite.score)) + '%' }"></div>
            </div>
            <ul class="score-reasons">
              <li v-for="(r, i) in result.scores.composite.reasons" :key="i">{{ r }}</li>
            </ul>
          </div>
        </div>

        <!-- 操作建议 -->
        <div class="advice-card terminal-card">
          <div class="panel-title">操作建议</div>
          <ul class="advice-list">
            <li v-for="(a, i) in result.advice" :key="i">{{ a }}</li>
          </ul>
        </div>

        <!-- 买点 -->
        <div class="buypoint-card terminal-card">
          <div class="panel-title">{{ result.can_buy ? '当前买点' : '等待买点（含长线 / 短线 / 超短）' }}</div>
          <div class="bp-list">
            <div v-for="(bp, i) in result.buy_points" :key="i" class="bp-item">
              <span class="bp-type">{{ bp.type }}</span>
              <span class="bp-price num">≈ {{ num(bp.price, 2) }}</span>
              <span class="bp-note">{{ bp.note }}</span>
            </div>
          </div>
        </div>

        <!-- 观察池提示 -->
        <div class="pool-tip terminal-card">
          <template v-if="result.worth_track">
            <span class="pool-text">策略：综合 {{ result.scores.composite.score }} / 买点 {{ result.scores.buy_point.score }}，值得跟踪{{ inPool(result.code) ? '（已在观察池）' : '，已自动加入观察池' }}</span>
          </template>
          <template v-else>
            <span class="pool-text">策略：综合 {{ result.scores.composite.score }} / 买点 {{ result.scores.buy_point.score }}，暂不值得跟踪，未加入观察池</span>
          </template>
        </div>
      </div>
    </a-spin>

    <!-- 观察池 -->
    <div class="pool-card terminal-card">
      <div class="pool-head">
        <div class="terminal-card-title">观察池</div>
        <div class="pool-count">共 {{ pool.length }} 只</div>
      </div>
      <div v-if="pool.length" class="pool-table-wrap">
        <table class="pool-table">
          <thead>
            <tr>
              <th class="num">NO.</th>
              <th>股票名称</th>
              <th class="num">日期</th>
              <th class="num">当前股价</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(p, idx) in pool" :key="p.code">
              <td class="num">{{ idx + 1 }}</td>
              <td class="pool-name">{{ p.name }} <span class="num pool-code">{{ p.code }}</span></td>
              <td class="num">{{ p.date }}</td>
              <td class="num">{{ num(p.price, 2) }}</td>
              <td><a-button type="link" danger size="small" @click="removeFromPool(p.code)">删除</a-button></td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else class="pool-empty">暂无观察股票 —— 输入个股打分后，值得跟踪的会自动加入观察池</div>
    </div>

    <footer class="page-foot">
      评分为基于公开行情数据的量化模型输出，仅供学习参考，不构成投资建议 · 红字=可以买入，绿字=不宜买入
    </footer>
  </div>
</template>

<style scoped>
.score-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.brand-tag {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 2px;
  color: var(--accent);
  margin-bottom: 6px;
}
.page-title {
  font-size: 22px;
  font-weight: 700;
  margin: 0 0 6px;
  color: var(--text);
}
.page-sub { color: var(--text-3); font-size: 13px; }

.search-card { padding: 16px 18px; }
.search-row { display: flex; gap: 12px; align-items: center; }
.opt-row { display: flex; align-items: center; gap: 12px; }
.opt-name { font-weight: 600; }
.opt-code { color: var(--text-2); }
.opt-pinyin { color: var(--text-3); font-size: 11px; }
.opt-type { margin-left: auto; color: var(--text-3); font-size: 12px; }

.result-area { display: flex; flex-direction: column; gap: 14px; }
.quote-card { padding: 16px 18px; }
.quote-head { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; }
.quote-left { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.q-name { font-size: 20px; font-weight: 700; color: var(--text); }
.q-code { color: var(--text-2); }
.q-industry { padding: 2px 10px; background: rgba(79,124,255,.12); border-radius: 10px; font-size: 12px; color: var(--accent); }
.q-time { color: var(--text-3); font-size: 12px; }
.quote-right { display: flex; align-items: baseline; gap: 12px; }
.q-price { font-size: 30px; font-weight: 700; }
.q-pct { font-size: 16px; font-weight: 600; }

.verdict { margin-top: 14px; padding: 14px 16px; border-radius: 10px; }
.verdict-buy { color: #ff4d5e; background: rgba(255,77,94,.1); border: 1px solid rgba(255,77,94,.4); }
.verdict-nobuy { color: #00c58e; background: rgba(0,197,142,.1); border: 1px solid rgba(0,197,142,.4); }
.verdict-title { font-size: 20px; font-weight: 800; }
.verdict-note { font-size: 13px; margin-top: 4px; opacity: .9; }

.scores-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 12px; }
.score-card { padding: 14px 16px; }
.composite-card { background: linear-gradient(135deg, rgba(79,124,255,.14), rgba(124,92,255,.1)); }
.score-head { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px; gap: 6px; }
.score-label { font-size: 14px; font-weight: 700; color: var(--text); }
.score-sub { font-size: 11px; color: var(--text-3); }
.score-num { font-size: 30px; font-weight: 800; margin-bottom: 8px; }
.composite-num { font-size: 40px; font-weight: 800; margin-bottom: 8px; }
.score-track { height: 8px; background: var(--panel-2); border-radius: 4px; overflow: hidden; margin-bottom: 10px; }
.composite-track { height: 10px; background: var(--panel-2); border-radius: 5px; overflow: hidden; margin-bottom: 10px; }
.score-fill { height: 100%; border-radius: inherit; transition: width .3s; }
.score-fill.up { background: #ff4d5e; }
.score-fill.warn { background: #f5a623; }
.score-fill.mid { background: #6f6f8a; }
.score-fill.down { background: #00c58e; }
.score-num.up, .composite-num.up { color: #ff4d5e; }
.score-num.warn { color: #f5a623; }
.score-num.mid { color: #9a9ab4; }
.score-num.down, .composite-num.down { color: #00c58e; }
.score-reasons { margin: 0; padding: 0 0 0 16px; font-size: 12px; color: var(--text-2); line-height: 1.7; }
.score-reasons li { margin-bottom: 2px; }

.advice-card, .buypoint-card, .pool-tip { padding: 14px 18px; }
.panel-title { font-size: 15px; font-weight: 700; color: var(--text); margin-bottom: 10px; }
.advice-list { margin: 0; padding: 0 0 0 18px; font-size: 13px; color: var(--text-2); line-height: 1.9; }
.bp-list { display: flex; flex-direction: column; gap: 8px; }
.bp-item { display: flex; align-items: baseline; gap: 12px; padding: 8px 12px; background: var(--panel-2); border-radius: 8px; flex-wrap: wrap; }
.bp-type { font-size: 12px; font-weight: 700; color: var(--accent); width: 60px; flex-shrink: 0; }
.bp-price { font-size: 16px; font-weight: 700; width: 90px; flex-shrink: 0; }
.bp-note { font-size: 12px; color: var(--text-2); flex: 1; min-width: 180px; }
.pool-tip { border: 1px dashed var(--border); }
.pool-text { font-size: 13px; color: var(--text-2); }

.pool-card { overflow: hidden; }
.pool-head { display: flex; justify-content: space-between; align-items: center; padding: 14px 18px; border-bottom: 1px solid var(--border); }
.pool-count { font-size: 12px; color: var(--text-3); }
.pool-table-wrap { overflow-x: auto; }
.pool-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.pool-table th { padding: 10px 14px; text-align: left; background: var(--panel-2); color: var(--text-3); border-bottom: 1px solid var(--border); white-space: nowrap; }
.pool-table td { padding: 10px 14px; border-bottom: 1px solid var(--border); color: var(--text-2); white-space: nowrap; }
.pool-table tbody tr:hover { background: rgba(79,124,255,.06); }
.pool-table tbody tr:last-child td { border-bottom: none; }
.pool-name { font-weight: 600; color: var(--text); }
.pool-code { color: var(--text-3); font-size: 11px; margin-left: 6px; }
.pool-empty { padding: 32px 20px; text-align: center; color: var(--text-3); font-size: 13px; }

.page-foot { margin-top: 12px; padding-top: 16px; border-top: 1px solid var(--border); color: var(--text-3); font-size: 12px; text-align: center; line-height: 1.8; }
</style>
