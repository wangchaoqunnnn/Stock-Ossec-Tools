<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { message } from 'ant-design-vue'
import { searchStocks, fetchQuote, fetchKline, fetchMinute, fetchIndicators } from '../api'
import { trendClass, signed, pct, num, mv, volume } from '../utils/format'

const emit = defineEmits(['add-to-watchlist'])

const keyword = ref('')
const searchInput = ref('')
const options = ref([])
const searching = ref(false)
const quote = ref(null)
const quoteLoading = ref(false)
const sourceLabel = { eastmoney: '东方财富', tencent: '腾讯行情' }
const inWatchlist = ref(false)

// 详情弹窗（真实行情数据）
const detailVisible = ref(false)
const detailTab = ref('chart')
const detailTabs = [
  { key: 'chart', label: '行情走势' },
  { key: 'indicators', label: '技术指标' },
  { key: 'fundamental', label: '基本面' },
]

// 图表状态
const chartPeriod = ref('minute') // minute / day / week / month
const chartPeriods = [
  { key: 'minute', label: '分时' },
  { key: 'day', label: '日K' },
  { key: 'week', label: '周K' },
  { key: 'month', label: '月K' },
]

// 真实行情数据
const klineData = ref([])
const minuteData = ref([])
const indicators = ref(null)
const chartLoading = ref(false)

function setChartPeriod(key) {
  chartPeriod.value = key
  loadChart()
}

// 分时折线坐标（归一化到 viewBox 1000x320）
function minutePoints() {
  const arr = minuteData.value || []
  if (!arr.length) return ''
  const prices = arr.map((p) => p.price).filter((v) => v !== null && v !== undefined)
  if (!prices.length) return ''
  const max = Math.max(...prices)
  const min = Math.min(...prices)
  const range = max - min || 1
  const step = 1000 / (arr.length - 1 || 1)
  return arr
    .map((p, i) => `${(i * step).toFixed(1)},${(30 + ((max - p.price) / range) * 250).toFixed(1)}`)
    .join(' ')
}

// K 线蜡烛坐标
function klineBars() {
  const bars = klineData.value || []
  if (!bars.length) return []
  const highs = bars.map((b) => b.high).filter((v) => v !== null && v !== undefined)
  const lows = bars.map((b) => b.low).filter((v) => v !== null && v !== undefined)
  if (!highs.length || !lows.length) return []
  const max = Math.max(...highs)
  const min = Math.min(...lows)
  const range = max - min || 1
  const step = 1000 / bars.length
  const w = Math.max(2, step * 0.55)
  const y = (v) => 30 + ((max - v) / range) * 250
  return bars.map((b, i) => ({
    x: i * step + step / 2,
    up: (b.close ?? 0) >= (b.open ?? 0),
    highY: y(b.high),
    lowY: y(b.low),
    topY: y(Math.max(b.open ?? 0, b.close ?? 0)),
    botY: y(Math.min(b.open ?? 0, b.close ?? 0)),
    w,
  }))
}

async function loadChart() {
  if (!quote.value) return
  const code = quote.value.code
  chartLoading.value = true
  try {
    if (chartPeriod.value === 'minute') {
      minuteData.value = await fetchMinute(code)
      klineData.value = []
    } else {
      klineData.value = await fetchKline(code, chartPeriod.value, 120)
      minuteData.value = []
    }
  } catch (e) {
    klineData.value = []
    minuteData.value = []
  } finally {
    chartLoading.value = false
  }
}

async function loadIndicators() {
  if (!quote.value) return
  try {
    indicators.value = await fetchIndicators(quote.value.code, 'day')
  } catch (e) {
    indicators.value = null
  }
}

function openDetail() {
  detailVisible.value = true
  loadChart()
  loadIndicators()
}

let timer = null
let seq = 0

const WATCHLIST_KEY = 'stock_watchlist_v1'

function checkWatchlist(code) {
  try {
    const raw = localStorage.getItem(WATCHLIST_KEY)
    if (raw) {
      const list = JSON.parse(raw)
      inWatchlist.value = list.some((item) => item.code === code)
      return
    }
  } catch (e) {}
  inWatchlist.value = false
}

function addToWatchlist() {
  if (!quote.value) return
  try {
    const raw = localStorage.getItem(WATCHLIST_KEY)
    const list = raw ? JSON.parse(raw) : []
    if (list.some((item) => item.code === quote.value.code)) {
      message.warning('该股票已在关注清单中')
      return
    }
    list.push({
      code: quote.value.code,
      name: quote.value.name,
      remark: '',
      addedAt: new Date().toISOString(),
    })
    localStorage.setItem(WATCHLIST_KEY, JSON.stringify(list))
    inWatchlist.value = true
    message.success(`已将 ${quote.value.name} 添加到关注清单`)
    emit('add-to-watchlist', quote.value.code)
    window.dispatchEvent(new CustomEvent('watchlist-changed'))
  } catch (e) {
    message.error('添加失败，请重试')
  }
}

function removeFromWatchlist() {
  if (!quote.value) return
  try {
    const raw = localStorage.getItem(WATCHLIST_KEY)
    const list = raw ? JSON.parse(raw) : []
    const next = list.filter((item) => item.code !== quote.value.code)
    localStorage.setItem(WATCHLIST_KEY, JSON.stringify(next))
    inWatchlist.value = false
    message.success(`已将 ${quote.value.name} 移出关注清单`)
    window.dispatchEvent(new CustomEvent('watchlist-changed'))
  } catch (e) {
    message.error('操作失败，请重试')
  }
}

function toggleFavorite() {
  if (!quote.value) return
  if (inWatchlist.value) {
    removeFromWatchlist()
  } else {
    addToWatchlist()
  }
}

// 详情弹窗操作
function refreshDetail() {
  if (!quote.value) return
  loadQuote(quote.value.code)
}

function moreAction() {
  message.info('更多功能建设中')
}

async function doSearch(val) {
  const kw = (val || '').trim()
  if (!kw) {
    options.value = []
    return
  }
  searching.value = true
  const id = ++seq
  try {
    const list = await searchStocks(kw)
    if (id !== seq) return
    options.value = list.map((s) => ({
      value: `${s.code} ${s.name}`,
      code: s.code,
      name: s.name,
      type: s.security_type || s.market_type,
    }))
  } catch (e) {
    if (id !== seq) return
    options.value = []
    message.error(e.message)
  } finally {
    if (id === seq) searching.value = false
  }
}

function onSearch(val) {
  // antd 在关闭下拉（Escape / 外部点击）时会触发 @search('')，
  // 空值不覆盖已输入的文本，避免丢失用户刚输入的查询词
  if (val) searchInput.value = val
  clearTimeout(timer)
  timer = setTimeout(() => doSearch(val), 300)
}

async function onSelect(value, option) {
  searchInput.value = ''
  const code = (option && option.code) || String(value).split(' ')[0]
  await loadQuote(code)
}

async function onPressEnter(rawText) {
  const kw = (rawText || '').trim()
  if (!kw) return
  if (/^\d{6}$/.test(kw)) {
    await loadQuote(kw)
    return
  }
  if (options.value.length) {
    await loadQuote(options.value[0].code)
  } else {
    await doSearch(kw)
    if (options.value.length) await loadQuote(options.value[0].code)
  }
}

function onInputKeyDown(e) {
  if (e && e.key === 'Enter') {
    e.preventDefault()
    onPressEnter(e.target && e.target.value)
  }
}

async function handleQuery() {
  // 优先读取输入框实时文本（antd 选中/关闭下拉时会清空输入框，
  // 但 @mousedown 已在清空前把文本存入 searchInput）
  const inputEl = document.querySelector('.ant-select-selection-search-input')
  const raw = (inputEl && inputEl.value) || searchInput.value || keyword.value
  const kw = String(raw || '').trim()
  if (!kw) {
    message.warning('请输入股票代码或名称')
    return
  }
  if (/^\d{6}$/.test(kw)) {
    await loadQuote(kw)
    return
  }
  if (options.value.length) {
    await loadQuote(options.value[0].code)
  } else {
    await doSearch(kw)
    if (options.value.length) await loadQuote(options.value[0].code)
    else message.warning('未找到匹配的股票，请检查输入')
  }
}

function captureInput() {
  // antd 在下拉关闭（Escape / 外部点击）时会清空搜索输入框，
  // 这里在按钮 mousedown（清空发生前）把当前文本存入 searchInput
  const el = document.querySelector('.ant-select-selection-search-input')
  if (el && el.value) searchInput.value = el.value
}

async function loadQuote(code) {
  const c = String(code || '').trim()
  if (!/^\d{6}$/.test(c)) {
    message.warning('请输入有效的 6 位股票代码')
    return
  }
  quoteLoading.value = true
  try {
    const data = await fetchQuote(c)
    quote.value = data
    checkWatchlist(c)
    startQuoteAutoRefresh() // 展示后进入实时刷新
  } catch (e) {
    quote.value = null
    stopQuoteAutoRefresh()
    message.error(e.message)
  } finally {
    quoteLoading.value = false
  }
}

// 已展示的个股行情定时刷新（15s），保证价格实时更新
const QUOTE_REFRESH_MS = 15000
let quoteRefreshTimer = null

function startQuoteAutoRefresh() {
  stopQuoteAutoRefresh()
  if (!quote.value || !quote.value.code) return
  quoteRefreshTimer = setInterval(async () => {
    const code = quote.value && quote.value.code
    if (!code) return
    try {
      const data = await fetchQuote(code)
      // 防竞态：仅当当前展示的还是同一只股票时更新
      if (quote.value && quote.value.code === code) {
        quote.value = data
      }
    } catch (e) {
      // 静默失败，保留旧数据，下轮重试
    }
  }, QUOTE_REFRESH_MS)
}

function stopQuoteAutoRefresh() {
  if (quoteRefreshTimer) {
    clearInterval(quoteRefreshTimer)
    quoteRefreshTimer = null
  }
}

onMounted(() => loadQuote('600519'))
onUnmounted(stopQuoteAutoRefresh)
</script>

<template>
  <section class="hero terminal-card">
    <div class="hero-head">
      <div>
        <div class="terminal-card-title">股票查询</div>
        <div class="hero-tip">输入股票代码或名称快速查询，支持添加到关注清单</div>
      </div>
    </div>

    <div class="hero-body">
      <div class="search-row">
        <div class="search-input-wrap">
          <a-select
            v-model:value="keyword"
            :options="options"
            show-search
            :filter-option="false"
            :loading="searching"
            placeholder="输入股票代码或名称，如 601318 / 中国平安"
            style="width: 100%"
            @search="onSearch"
            @select="onSelect"
            @input-key-down="onInputKeyDown"
          >
            <template #option="{ value: v, code, name, type }">
              <div class="opt-row">
                <span class="opt-name">{{ name }}</span>
                <span class="opt-code num">{{ code }}</span>
                <span class="opt-type">{{ type }}</span>
              </div>
            </template>
          </a-select>
        </div>
        <a-button type="primary" size="large" class="query-btn" @mousedown="captureInput" @click="handleQuery">
          立即查询
        </a-button>
      </div>

      <a-spin :spinning="quoteLoading">
        <div v-if="quote" class="quote-panel">
          <div class="quote-top">
            <div class="quote-name-row">
              <span class="quote-name">{{ quote.name }}</span>
              <span class="quote-code num">{{ quote.code }}</span>
              <a-tag v-if="quote.source" size="small" color="blue" class="quote-source">
                {{ sourceLabel[quote.source] || quote.source }}
              </a-tag>
              <a-button
                v-if="!inWatchlist"
                size="small"
                class="add-watch-btn"
                @click="addToWatchlist"
              >
                + 加关注
              </a-button>
              <a-tag v-else size="small" color="green">已关注</a-tag>
              <a-button size="small" class="detail-btn" @click="openDetail">
                详情
              </a-button>
            </div>
            <div class="quote-price-row">
              <span class="quote-price num" :class="trendClass(quote.change_pct)">
                {{ num(quote.now_price, 2) }}
              </span>
              <span class="quote-change num" :class="trendClass(quote.change_pct)">
                {{ signed(quote.change) }} &nbsp; {{ pct(quote.change_pct) }}
              </span>
            </div>
          </div>

          <a-descriptions :column="4" size="small" bordered class="quote-desc">
            <a-descriptions-item label="今开"><span class="num">{{ num(quote.open) }}</span></a-descriptions-item>
            <a-descriptions-item label="最高"><span class="num up">{{ num(quote.high) }}</span></a-descriptions-item>
            <a-descriptions-item label="最低"><span class="num down">{{ num(quote.low) }}</span></a-descriptions-item>
            <a-descriptions-item label="昨收"><span class="num">{{ num(quote.prev_close) }}</span></a-descriptions-item>
            <a-descriptions-item label="成交量"><span class="num">{{ volume(quote.volume) }}</span></a-descriptions-item>
            <a-descriptions-item label="成交额"><span class="num">{{ mv(quote.amount) }}</span></a-descriptions-item>
            <a-descriptions-item label="换手率"><span class="num">{{ pct(quote.turnover) }}</span></a-descriptions-item>
            <a-descriptions-item label="量比"><span class="num">{{ num(quote.volume_ratio, 2) }}</span></a-descriptions-item>
            <a-descriptions-item label="市盈率(TTM)"><span class="num">{{ num(quote.pe, 2) }}</span></a-descriptions-item>
            <a-descriptions-item label="市净率"><span class="num">{{ num(quote.pb, 2) }}</span></a-descriptions-item>
            <a-descriptions-item label="振幅"><span class="num">{{ pct(quote.amplitude) }}</span></a-descriptions-item>
            <a-descriptions-item label="更新时间"><span class="num">{{ quote.time || '--' }}</span></a-descriptions-item>
            <a-descriptions-item label="总市值"><span class="num">{{ mv(quote.total_mv) }}</span></a-descriptions-item>
            <a-descriptions-item label="流通市值"><span class="num">{{ mv(quote.float_mv) }}</span></a-descriptions-item>
          </a-descriptions>
        </div>
        <div v-else class="quote-empty">输入代码或名称后点击"立即查询"，即可查看个股行情详情</div>
      </a-spin>
    </div>

    <!-- 股票详情弹窗 -->
    <a-modal
      v-model:open="detailVisible"
      :title="quote ? `${quote.name}[${quote.code}] - 详情` : '详情'"
      :footer="null"
      width="1100px"
      class="stock-detail-modal"
    >
      <!-- 标签导航 -->
      <div class="detail-tabs">
        <button
          v-for="tab in detailTabs"
          :key="tab.key"
          class="detail-tab"
          :class="{ active: detailTab === tab.key }"
          @click="detailTab = tab.key"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- 共享头部 -->
      <div v-if="quote" class="detail-header">
        <div class="detail-title-row">
          <span class="detail-name">{{ quote.name }}</span>
          <span class="detail-price num" :class="trendClass(quote.change_pct)">{{ num(quote.now_price, 2) }}</span>
          <span class="detail-change num" :class="trendClass(quote.change_pct)">{{ pct(quote.change_pct) }}</span>
          <div class="detail-actions">
            <button class="icon-btn" title="刷新" @click="refreshDetail">↻</button>
            <button class="icon-btn star" title="收藏" @click="toggleFavorite">{{ inWatchlist ? '★' : '☆' }}</button>
            <button class="icon-btn" title="更多" @click="moreAction">⋯</button>
          </div>
        </div>
        <div class="detail-code">代码: {{ quote.code }} · 数据来源: {{ sourceLabel[quote.source] || quote.source }}</div>
      </div>

      <!-- 行情走势 -->
      <div v-if="detailTab === 'chart'" class="detail-content">
        <a-spin :spinning="chartLoading">
          <div class="chart-section">
            <div class="section-header">
              <span class="section-label">行情走势（真实 K 线 / 分时）</span>
              <div class="chart-period">
                <button
                  v-for="p in chartPeriods"
                  :key="p.key"
                  class="ctrl-btn"
                  :class="{ active: chartPeriod === p.key }"
                  @click="setChartPeriod(p.key)"
                >{{ p.label }}</button>
              </div>
            </div>

            <div class="chart-container">
              <svg v-if="chartPeriod === 'minute' && minuteData.length" viewBox="0 0 1000 320" class="chart-svg" preserveAspectRatio="none">
                <g stroke="rgba(255,255,255,0.08)" stroke-width="1">
                  <line x1="0" y1="40" x2="1000" y2="40" />
                  <line x1="0" y1="105" x2="1000" y2="105" />
                  <line x1="0" y1="170" x2="1000" y2="170" />
                  <line x1="0" y1="235" x2="1000" y2="235" />
                </g>
                <polyline :points="minutePoints()" fill="none" stroke="#3b82f6" stroke-width="1.6" />
              </svg>

              <svg v-else-if="chartPeriod !== 'minute' && klineData.length" viewBox="0 0 1000 320" class="chart-svg" preserveAspectRatio="none">
                <g stroke="rgba(255,255,255,0.08)" stroke-width="1">
                  <line x1="0" y1="40" x2="1000" y2="40" />
                  <line x1="0" y1="105" x2="1000" y2="105" />
                  <line x1="0" y1="170" x2="1000" y2="170" />
                  <line x1="0" y1="235" x2="1000" y2="235" />
                </g>
                <g v-for="(b, i) in klineBars()" :key="i">
                  <line :x1="b.x" :y1="b.highY" :x2="b.x" :y2="b.lowY" :stroke="b.up ? '#ff4d5e' : '#00c58e'" stroke-width="1" />
                  <rect :x="b.x - b.w / 2" :y="b.topY" :width="b.w" :height="Math.max(1.5, b.botY - b.topY)" :fill="b.up ? '#ff4d5e' : '#00c58e'" />
                </g>
              </svg>

              <div v-else class="empty-state">暂无走势数据</div>
            </div>

            <div class="chart-x-axis">
              <template v-if="chartPeriod === 'minute'">
                <span>09:30</span><span>10:30</span><span>11:30/13:00</span><span>14:00</span><span>15:00</span>
              </template>
              <template v-else-if="klineData.length">
                <span class="num">{{ klineData[0].date }}</span>
                <span>→</span>
                <span class="num">{{ klineData[klineData.length - 1].date }}</span>
                <span class="dim">共 {{ klineData.length }} 根</span>
              </template>
            </div>
          </div>
        </a-spin>
      </div>

      <!-- 技术指标 -->
      <div v-if="detailTab === 'indicators'" class="detail-content">
        <div v-if="indicators" class="indicator-grid">
          <div class="indicator-card">
            <div class="ind-name">MACD</div>
            <div class="ind-value num" :class="trendClass(indicators.indicators.macd.value)">{{ indicators.indicators.macd.value }}</div>
            <div class="ind-signal" :class="trendClass(indicators.indicators.macd.value)">{{ indicators.indicators.macd.signal }}</div>
          </div>
          <div class="indicator-card">
            <div class="ind-name">KDJ</div>
            <div class="ind-value num">K{{ indicators.indicators.kdj.k }} D{{ indicators.indicators.kdj.d }}</div>
            <div class="ind-signal">{{ indicators.indicators.kdj.signal }}</div>
          </div>
          <div class="indicator-card">
            <div class="ind-name">RSI(14)</div>
            <div class="ind-value num">{{ indicators.indicators.rsi.value }}</div>
            <div class="ind-signal">{{ indicators.indicators.rsi.signal }}</div>
          </div>
          <div class="indicator-card">
            <div class="ind-name">BOLL</div>
            <div class="ind-value num">{{ indicators.indicators.boll.mid !== null && indicators.indicators.boll.mid !== undefined ? num(indicators.indicators.boll.mid, 2) : '--' }}</div>
            <div class="ind-signal">{{ indicators.indicators.boll.signal }}</div>
          </div>
        </div>
        <div v-if="indicators" class="ma-section">
          <div class="ma-item">
            <span class="ma-label">MA5</span>
            <span class="ma-value num">{{ num(indicators.indicators.ma.ma5, 2) }}</span>
          </div>
          <div class="ma-item">
            <span class="ma-label">MA10</span>
            <span class="ma-value num">{{ num(indicators.indicators.ma.ma10, 2) }}</span>
          </div>
          <div class="ma-item">
            <span class="ma-label">MA20</span>
            <span class="ma-value num">{{ num(indicators.indicators.ma.ma20, 2) }}</span>
          </div>
          <div class="ma-item">
            <span class="ma-label">MA60</span>
            <span class="ma-value num">{{ num(indicators.indicators.ma.ma60, 2) }}</span>
          </div>
        </div>
        <div v-if="!indicators" class="empty-state">暂无技术指标数据（需足够历史 K 线）</div>
        <div class="data-note">技术指标基于真实前复权 K 线计算，仅供技术分析参考</div>
      </div>

      <!-- 基本面 -->
      <div v-if="detailTab === 'fundamental'" class="detail-content">
        <div v-if="quote" class="fund-grid">
          <div class="fund-item"><span class="fund-label">现价</span><span class="fund-value num" :class="trendClass(quote.change_pct)">{{ num(quote.now_price, 2) }}</span></div>
          <div class="fund-item"><span class="fund-label">涨跌幅</span><span class="fund-value num" :class="trendClass(quote.change_pct)">{{ pct(quote.change_pct) }}</span></div>
          <div class="fund-item"><span class="fund-label">换手率</span><span class="fund-value num">{{ pct(quote.turnover) }}</span></div>
          <div class="fund-item"><span class="fund-label">量比</span><span class="fund-value num">{{ num(quote.volume_ratio, 2) }}</span></div>
          <div class="fund-item"><span class="fund-label">市盈率(TTM)</span><span class="fund-value num">{{ num(quote.pe, 2) }}</span></div>
          <div class="fund-item"><span class="fund-label">市净率</span><span class="fund-value num">{{ num(quote.pb, 2) }}</span></div>
          <div class="fund-item"><span class="fund-label">总市值</span><span class="fund-value num">{{ mv(quote.total_mv) }}</span></div>
          <div class="fund-item"><span class="fund-label">流通市值</span><span class="fund-value num">{{ mv(quote.float_mv) }}</span></div>
          <div class="fund-item"><span class="fund-label">振幅</span><span class="fund-value num">{{ pct(quote.amplitude) }}</span></div>
          <div class="fund-item"><span class="fund-label">今开</span><span class="fund-value num">{{ num(quote.open, 2) }}</span></div>
          <div class="fund-item"><span class="fund-label">最高</span><span class="fund-value num up">{{ num(quote.high, 2) }}</span></div>
          <div class="fund-item"><span class="fund-label">最低</span><span class="fund-value num down">{{ num(quote.low, 2) }}</span></div>
          <div class="fund-item"><span class="fund-label">昨收</span><span class="fund-value num">{{ num(quote.prev_close, 2) }}</span></div>
          <div class="fund-item"><span class="fund-label">成交量</span><span class="fund-value num">{{ volume(quote.volume) }}</span></div>
          <div class="fund-item"><span class="fund-label">成交额</span><span class="fund-value num">{{ mv(quote.amount) }}</span></div>
        </div>
        <div class="data-note">财务数据（营收/利润/ROE）、资金流向、机构评级、暗盘资金等需接入专用数据源，暂不展示。</div>
      </div>
    </a-modal>
  </section>
</template>

<style scoped>
/* ========== 基础布局 ========== */
.hero-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid #1e293b;
  flex-wrap: wrap;
  gap: 6px;
}
.hero-tip {
  color: #64748b;
  font-size: 12px;
  margin-top: 2px;
}
.hero-body {
  padding: 18px;
}
.search-row {
  display: flex;
  gap: 12px;
  align-items: stretch;
}
.search-input-wrap {
  flex: 1;
}
.query-btn {
  min-width: 110px;
  font-weight: 600;
  height: 40px;
}
.opt-row {
  display: flex;
  align-items: center;
  gap: 12px;
}
.opt-name {
  font-weight: 600;
}
.opt-code {
  color: #94a3b8;
}
.opt-type {
  margin-left: auto;
  color: #64748b;
  font-size: 12px;
}

/* ========== 行情面板 ========== */
.quote-panel {
  margin-top: 18px;
}
.quote-top {
  margin-bottom: 14px;
}
.quote-name-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.quote-name {
  font-size: 20px;
  font-weight: 700;
  color: #f1f5f9;
}
.quote-code {
  color: #94a3b8;
  font-size: 14px;
}
.quote-source {
  margin-left: 4px;
}
.add-watch-btn {
  margin-left: 8px;
}
.quote-price-row {
  display: flex;
  align-items: baseline;
  gap: 16px;
  margin-top: 8px;
}
.quote-price {
  font-size: 36px;
  font-weight: 700;
  line-height: 1.1;
}
.quote-change {
  font-size: 16px;
}
.quote-empty {
  margin-top: 18px;
  padding: 32px 0;
  text-align: center;
  color: #64748b;
  font-size: 14px;
}
.quote-desc {
  margin-top: 8px;
}
:deep(.ant-descriptions-item-label) {
  background: #1e293b !important;
  color: #94a3b8 !important;
  font-weight: 500;
}
:deep(.ant-descriptions-item-content) {
  background: #0f172a !important;
  color: #f1f5f9 !important;
}
:deep(.ant-descriptions-bordered .ant-descriptions-view) {
  border: 1px solid #1e293b !important;
}
:deep(.ant-descriptions-bordered .ant-descriptions-view > table) {
  border-color: #1e293b !important;
}
:deep(.ant-descriptions-bordered .ant-descriptions-item-label),
:deep(.ant-descriptions-bordered .ant-descriptions-item-content) {
  border-color: #1e293b !important;
}
.detail-btn {
  margin-left: 8px;
}

/* ========== 详情弹窗 - 统一专业配色 ========== */
.stock-detail-modal :deep(.ant-modal-content) {
  background: #0f172a !important;
  border: 1px solid #1e293b !important;
  border-radius: 12px !important;
  box-shadow: 0 20px 60px rgba(0,0,0,0.5) !important;
}
.stock-detail-modal :deep(.ant-modal-header) {
  background: #1e293b !important;
  border-bottom: 1px solid #334155 !important;
  padding: 16px 24px !important;
}
.stock-detail-modal :deep(.ant-modal-title) {
  color: #f1f5f9 !important;
  font-size: 17px !important;
  font-weight: 600 !important;
}
.stock-detail-modal :deep(.ant-modal-close) {
  color: #94a3b8 !important;
}
.stock-detail-modal :deep(.ant-modal-close:hover) {
  color: #f1f5f9 !important;
}
.stock-detail-modal :deep(.ant-modal-body) {
  padding: 0 !important;
  max-height: 75vh;
  overflow-y: auto;
}

/* 标签导航 */
.detail-tabs {
  display: flex;
  background: #1e293b;
  border-bottom: 1px solid #334155;
  padding: 0 8px;
}
.detail-tab {
  flex: 1;
  padding: 14px 16px;
  background: none;
  border: none;
  color: #64748b;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border-bottom: 2px solid transparent;
}
.detail-tab:hover {
  color: #94a3b8;
}
.detail-tab.active {
  color: #3b82f6;
  border-bottom-color: #3b82f6;
  font-weight: 600;
  background: rgba(59, 130, 246, 0.06);
}

/* 内容区域 */
.detail-content {
  padding: 20px 24px;
  min-height: 400px;
  background: #0f172a;
}

/* 暗盘信息 - 头部 */
.detail-header {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 10px;
  padding: 16px 18px;
  margin-bottom: 16px;
}
.detail-title-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.detail-name {
  font-size: 20px;
  font-weight: 700;
  color: #f1f5f9;
}
.detail-price {
  font-size: 24px;
  font-weight: 700;
}
.detail-change {
  font-size: 16px;
  font-weight: 600;
}
.detail-actions {
  margin-left: auto;
  display: flex;
  gap: 8px;
}
.icon-btn {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  background: #0f172a;
  border: 1px solid #334155;
  color: #94a3b8;
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}
.icon-btn:hover {
  border-color: #3b82f6;
  color: #3b82f6;
}
.icon-btn.star {
  color: #f59e0b;
  border-color: rgba(245,158,11,0.3);
}
.detail-code {
  margin-top: 6px;
  font-size: 13px;
  color: #64748b;
}

/* 四指标卡片 */
.detail-metrics {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}
.metric-item {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 10px;
  padding: 14px 16px;
}
.metric-label {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 6px;
}
.metric-value {
  font-size: 18px;
  font-weight: 700;
}

/* 通用区块 */
.detail-section {
  margin-bottom: 16px;
}
.section-label {
  font-size: 13px;
  color: #94a3b8;
  margin-bottom: 8px;
  font-weight: 500;
}
.section-content {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.sector-tag {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.25);
  border-radius: 6px;
  font-size: 13px;
  color: #f1f5f9;
}
.concepts {
  gap: 6px;
}
.concept-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 4px;
  font-size: 12px;
  color: #94a3b8;
}
.desc {
  font-size: 13px;
  line-height: 1.7;
  color: #94a3b8;
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 10px;
  padding: 14px 16px;
}

/* 图表区块 */
.chart-section {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 12px;
  padding: 16px;
}
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.chart-controls {
  display: flex;
  align-items: center;
  gap: 10px;
}
.ctrl-btn {
  padding: 4px 12px;
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 4px;
  color: #64748b;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}
.ctrl-btn:hover {
  color: #94a3b8;
  border-color: #475569;
}
.ctrl-btn.active {
  background: #3b82f6;
  border-color: #3b82f6;
  color: #fff;
}
.chart-period {
  display: flex;
  gap: 4px;
  padding: 2px;
  background: #0f172a;
  border-radius: 4px;
}

/* 暗盘资金统计 */
.dark-fund-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 12px;
}
.fund-stat-item {
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 8px;
  padding: 12px 14px;
}
.fund-stat-label {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 6px;
}
.fund-stat-value {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 4px;
}
.fund-stat-sub {
  font-size: 11px;
  color: #64748b;
}
.fund-data-note {
  font-size: 11px;
  color: #64748b;
  margin-bottom: 12px;
}

/* 图表图例 */
.chart-legend {
  display: flex;
  gap: 20px;
  margin-bottom: 12px;
  justify-content: center;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #94a3b8;
}
.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}
.legend-dot.blue { background: #3b82f6; }
.legend-dot.orange { background: #f59e0b; }
.legend-dot.red { background: #ef4444; }
.legend-dot.purple { background: #8b5cf6; }
.chart-container {
  position: relative;
}
.chart-svg {
  width: 100%;
  height: 280px;
  display: block;
}
.chart-x-axis {
  display: flex;
  justify-content: space-between;
  padding: 6px 0 0;
  font-size: 11px;
  color: #64748b;
}

/* ========== 个股分析 ========== */
.analysis-content {
  background: #0f172a;
}
.score-section {
  display: flex;
  gap: 32px;
  align-items: center;
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 16px;
}
.score-main {
  flex-shrink: 0;
}
.score-circle {
  position: relative;
  width: 110px;
  height: 110px;
}
.score-svg {
  width: 100%;
  height: 100%;
}
.score-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}
.score-num {
  font-size: 28px;
  font-weight: 800;
  color: #3b82f6;
}
.score-label {
  font-size: 11px;
  color: #64748b;
  margin-top: 2px;
}
.score-dims {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.score-dim-item {
  display: flex;
  align-items: center;
  gap: 12px;
}
.dim-label {
  width: 50px;
  font-size: 13px;
  color: #94a3b8;
}
.dim-bar {
  flex: 1;
  height: 6px;
  background: #334155;
  border-radius: 3px;
  overflow: hidden;
}
.dim-fill {
  height: 100%;
  background: #3b82f6;
  border-radius: 3px;
}
.dim-value {
  width: 30px;
  text-align: right;
  font-size: 14px;
  font-weight: 600;
  color: #f1f5f9;
}

.analysis-section {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 12px;
  padding: 16px 18px;
  margin-bottom: 14px;
}
.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #f1f5f9;
  margin-bottom: 14px;
  padding-left: 10px;
  border-left: 3px solid #3b82f6;
}
.indicator-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  margin-bottom: 12px;
}
.indicator-card {
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 8px;
  padding: 12px;
  text-align: center;
}
.ind-name {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 6px;
}
.ind-value {
  font-size: 17px;
  font-weight: 700;
  margin-bottom: 4px;
  color: #f1f5f9;
}
.ind-signal {
  font-size: 11px;
  color: #64748b;
}
.ind-signal.up { color: #ef4444; }
.ma-section {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}
.ma-item {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 6px;
  padding: 8px 10px;
}
.ma-label {
  font-size: 12px;
  font-weight: 600;
  color: #3b82f6;
  width: 40px;
}
.ma-value {
  font-size: 13px;
  font-weight: 600;
  flex: 1;
  color: #f1f5f9;
}
.ma-signal {
  font-size: 11px;
  color: #ef4444;
}
.fund-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}
.fund-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 6px;
  padding: 10px 12px;
}
.fund-label {
  font-size: 12px;
  color: #64748b;
}
.fund-value {
  font-size: 13px;
  font-weight: 600;
  color: #f1f5f9;
}
.capital-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}
.capital-card {
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 8px;
  padding: 14px;
}
.capital-card.main {
  border-color: rgba(239,68,68,0.3);
  background: rgba(239,68,68,0.05);
}
.cap-label {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 8px;
}
.cap-value {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 4px;
}
.cap-sub {
  font-size: 11px;
  color: #64748b;
}
.institution-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.inst-main {
  display: flex;
  align-items: center;
  gap: 20px;
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 10px;
  padding: 16px 20px;
}
.inst-rating {
  font-size: 24px;
  font-weight: 800;
  color: #ef4444;
}
.inst-target {
  font-size: 14px;
  color: #94a3b8;
}
.inst-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}
.inst-stat {
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 6px;
  padding: 10px;
  text-align: center;
}
.stat-label {
  display: block;
  font-size: 11px;
  color: #64748b;
  margin-bottom: 4px;
}
.stat-value {
  font-size: 15px;
  font-weight: 700;
  color: #f1f5f9;
}
.inst-report {
  font-size: 12px;
  color: #64748b;
  background: #0f172a;
  border-radius: 6px;
  padding: 10px 12px;
}

/* ========== 暗盘历史 ========== */
.history-content {
  background: #0f172a;
}
.history-summary {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  margin-bottom: 16px;
}
.hist-summary-item {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 10px;
  padding: 14px;
  text-align: center;
}
.hist-label {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 8px;
}
.hist-value {
  font-size: 18px;
  font-weight: 700;
}
.history-table-wrap {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 10px;
  overflow: hidden;
}
.history-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.history-table th {
  background: #0f172a;
  color: #94a3b8;
  font-weight: 600;
  padding: 10px 12px;
  text-align: left;
  border-bottom: 1px solid #334155;
  white-space: nowrap;
}
.history-table td {
  padding: 10px 12px;
  border-bottom: 1px solid rgba(255,255,255,0.04);
  color: #94a3b8;
}
.history-table tbody tr:hover {
  background: rgba(59,130,246,0.04);
}
.history-table tbody tr:last-child td {
  border-bottom: none;
}
.trend-bar {
  width: 70px;
  height: 5px;
  background: #334155;
  border-radius: 3px;
  overflow: hidden;
}
.trend-fill {
  height: 100%;
  border-radius: 3px;
}
.trend-fill.up { background: #ef4444; }
.trend-fill.down { background: #22c55e; }

/* ========== 异动清单 ========== */
.anomaly-content {
  background: #0f172a;
}
.anomaly-summary {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  margin-bottom: 16px;
}
.anom-summary-item {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 10px;
  padding: 14px;
  text-align: center;
}
.anom-label {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 8px;
}
.anom-value {
  font-size: 18px;
  font-weight: 700;
  color: #f1f5f9;
}
.anomaly-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.anomaly-item {
  display: flex;
  align-items: center;
  gap: 16px;
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 10px;
  padding: 12px 16px;
  transition: all 0.2s;
}
.anomaly-item:hover {
  border-color: #475569;
}
.anom-left {
  flex-shrink: 0;
  width: 130px;
}
.anom-type {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  margin-bottom: 6px;
}
.anom-type.buy {
  background: rgba(239,68,68,0.12);
  color: #ef4444;
  border: 1px solid rgba(239,68,68,0.25);
}
.anom-type.sell {
  background: rgba(34,197,94,0.12);
  color: #22c55e;
  border: 1px solid rgba(34,197,94,0.25);
}
.anom-time {
  font-size: 11px;
  color: #64748b;
}
.anom-middle {
  flex: 1;
}
.anom-price-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 4px;
}
.anom-price {
  font-size: 16px;
  font-weight: 700;
  color: #f1f5f9;
}
.anom-change {
  font-size: 12px;
  font-weight: 600;
}
.anom-vol {
  font-size: 11px;
  color: #64748b;
}
.anom-right {
  flex-shrink: 0;
  width: 150px;
  text-align: right;
}
.anom-reason {
  font-size: 11px;
  color: #94a3b8;
  background: #0f172a;
  border-radius: 4px;
  padding: 6px 8px;
  display: inline-block;
}
.data-note {
  margin-top: 14px;
  font-size: 11px;
  color: #64748b;
  text-align: center;
}
.empty-state {
  padding: 48px 20px;
  text-align: center;
  color: #64748b;
  font-size: 14px;
}
.empty-tab {
  padding: 60px 0;
  text-align: center;
  color: #64748b;
  font-size: 14px;
}

/* 涨跌颜色 */
.num.up { color: #ef4444; }
.num.down { color: #22c55e; }

/* 响应式 */
@media (max-width: 768px) {
  .detail-metrics {
    grid-template-columns: repeat(2, 1fr);
  }
  .indicator-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .fund-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .capital-grid {
    grid-template-columns: 1fr;
  }
  .history-summary {
    grid-template-columns: repeat(2, 1fr);
  }
  .anomaly-summary {
    grid-template-columns: repeat(2, 1fr);
  }
  .score-section {
    flex-direction: column;
  }
  .search-row {
    flex-direction: column;
  }
  .query-btn {
    width: 100%;
  }
  .quote-price {
    font-size: 28px;
  }
}
</style>
