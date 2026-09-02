<script setup>
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { searchStocks, fetchQuote } from '../api'
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

// 详情弹窗
const detailVisible = ref(false)
const detailTab = ref('dark')
const detailTabs = [
  { key: 'dark', label: '暗盘信息' },
  { key: 'analysis', label: '个股分析' },
  { key: 'history', label: '暗盘历史' },
  { key: 'anomaly', label: '异动清单' },
]

// 图表状态
const chartRange = ref('classic') // classic / today
const chartPeriod = ref('minute') // minute / day / week / month
const chartRanges = [
  { key: 'classic', label: '经典' },
  { key: 'today', label: '今天' },
]
const chartPeriods = [
  { key: 'minute', label: '分时' },
  { key: 'day', label: '日K' },
  { key: 'week', label: '周K' },
  { key: 'month', label: '月K' },
]

function setChartRange(key) {
  chartRange.value = key
}
function setChartPeriod(key) {
  chartPeriod.value = key
}

// 生成模拟K线数据
function genKlineData(count, basePrice) {
  const data = []
  let price = basePrice
  for (let i = 0; i < count; i++) {
    const open = price
    const change = (Math.random() - 0.48) * basePrice * 0.04
    const close = open + change
    const high = Math.max(open, close) + Math.random() * basePrice * 0.02
    const low = Math.min(open, close) - Math.random() * basePrice * 0.02
    const volume = Math.random() * 1000000 + 500000
    const darkFund = (Math.random() - 0.45) * 50000000
    data.push({ open, close, high, low, volume, darkFund })
    price = close
  }
  return data
}

// 不同周期的模拟数据
const klineData = {
  minute: genKlineData(50, 250),
  day: genKlineData(60, 250),
  week: genKlineData(52, 250),
  month: genKlineData(24, 250),
}

// 暗盘资金统计
const darkFundStats = ref({
  today: { inflow: 2.35, outflow: 1.82, net: 0.53 },
  week: { inflow: 12.6, outflow: 10.8, net: 1.8 },
  month: { inflow: 45.2, outflow: 38.6, net: 6.6 },
})

// 详情模拟数据
const detailData = {
  marketRank: 16,
  marketHeat: 94.80,
  tradeSignal: '买入区间',
  strongLine: '强势线下',
  sector: { name: 'IT服务', change: 1.34 },
  concepts: [
    { name: '互联网服务', change: 1.49 },
    { name: '创投', change: 1.09 },
    { name: '物联网', change: 0.37 },
    { name: '云计算', change: 1.02 },
    { name: '大数据', change: 1.06 },
    { name: '网络安全', change: 1.35 },
    { name: '安防概念', change: 0.72 },
    { name: '5G概念', change: -1.35 },
    { name: '人工智能', change: 0.84 },
    { name: '区块链', change: 2.03 },
    { name: '国产芯', change: 0.56 },
  ],
  companyDesc: '紫光股份主营ICT基础设施与AI算力解决方案，核心子公司新华三提供交换机、服务器等全栈产品。当前市场聚焦AI算力需求爆发，公司超节点与CPO交换机进展积极，2026上半年业绩大幅预增，但短期股价波动需关注验证。',
}

// 个股分析数据
const analysisData = {
  technical: {
    macd: { value: '0.85', signal: '金叉', trend: 'up' },
    kdj: { value: '68.5', signal: '偏强', trend: 'up' },
    rsi: { value: '58.2', signal: '中性偏强', trend: 'flat' },
    boll: { value: '中轨上方', signal: '偏强', trend: 'up' },
    ma5: { value: '38.25', signal: '支撑', trend: 'up' },
    ma10: { value: '37.80', signal: '支撑', trend: 'up' },
    ma20: { value: '36.50', signal: '支撑', trend: 'up' },
    ma60: { value: '34.20', signal: '支撑', trend: 'up' },
  },
  fundamental: {
    pe: '28.5',
    pb: '3.2',
    roe: '12.8%',
    revenue: '385.6亿',
    profit: '28.5亿',
    revenueGrowth: '+18.5%',
    profitGrowth: '+25.3%',
    grossMargin: '22.5%',
    debtRatio: '45.2%',
  },
  capitalFlow: {
    mainNet: '+2.35亿',
    mainInflow: '8.56亿',
    mainOutflow: '6.21亿',
    retailNet: '-0.85亿',
    northNet: '+1.20亿',
    northHolding: '3.85亿股',
    northRatio: '12.5%',
  },
  institution: {
    rating: '买入',
    targetPrice: '45.00',
    ratingCount: 18,
    buyCount: 12,
    holdCount: 5,
    sellCount: 1,
    recentReport: '2026-08-28 中信证券 买入评级',
  },
  score: {
    total: 78,
    technical: 82,
    fundamental: 75,
    capital: 80,
    sentiment: 75,
  },
}

// 暗盘历史数据
const historyData = [
  { date: '2026-09-01', net: 0.53, inflow: 2.35, outflow: 1.82, close: 38.32, change: 1.25 },
  { date: '2026-08-29', net: 1.20, inflow: 5.68, outflow: 4.48, close: 37.85, change: 2.15 },
  { date: '2026-08-28', net: -0.85, inflow: 3.25, outflow: 4.10, close: 37.05, change: -1.32 },
  { date: '2026-08-27', net: 2.15, inflow: 8.92, outflow: 6.77, close: 37.55, change: 3.28 },
  { date: '2026-08-26', net: -1.50, inflow: 4.20, outflow: 5.70, close: 36.35, change: -2.15 },
  { date: '2026-08-25', net: 0.95, inflow: 6.15, outflow: 5.20, close: 37.15, change: 1.85 },
  { date: '2026-08-22', net: 1.80, inflow: 7.85, outflow: 6.05, close: 36.48, change: 2.56 },
  { date: '2026-08-21', net: -0.65, inflow: 3.80, outflow: 4.45, close: 35.57, change: -0.92 },
  { date: '2026-08-20', net: 1.45, inflow: 6.92, outflow: 5.47, close: 35.90, change: 2.05 },
  { date: '2026-08-19', net: -1.20, inflow: 4.55, outflow: 5.75, close: 35.18, change: -1.65 },
  { date: '2026-08-18', net: 2.35, inflow: 9.20, outflow: 6.85, close: 35.77, change: 3.12 },
  { date: '2026-08-15', net: 0.75, inflow: 5.40, outflow: 4.65, close: 34.69, change: 1.15 },
]

// 异动清单数据
const anomalyData = [
  { time: '2026-09-01 14:32', type: '大单买入', price: 38.50, volume: '5200手', amount: '2002万', change: '+1.25%', reason: '主力资金流入' },
  { time: '2026-09-01 13:45', type: '快速拉升', price: 38.35, volume: '3800手', amount: '1457万', change: '+0.85%', reason: '板块联动上涨' },
  { time: '2026-09-01 11:20', type: '放量突破', price: 38.10, volume: '8500手', amount: '3239万', change: '+0.52%', reason: '突破前期高点' },
  { time: '2026-09-01 10:15', type: '大单买入', price: 37.95, volume: '4200手', amount: '1594万', change: '+0.35%', reason: '机构资金建仓' },
  { time: '2026-08-29 14:50', type: '尾盘拉升', price: 37.85, volume: '6800手', amount: '2574万', change: '+2.15%', reason: '主力抢筹' },
  { time: '2026-08-29 13:30', type: '放量上涨', price: 37.50, volume: '12000手', amount: '4500万', change: '+1.56%', reason: '利好消息刺激' },
  { time: '2026-08-28 14:20', type: '大单卖出', price: 37.05, volume: '5500手', amount: '2038万', change: '-1.32%', reason: '获利盘了结' },
  { time: '2026-08-28 11:05', type: '快速下跌', price: 37.20, volume: '4800手', amount: '1786万', change: '-0.85%', reason: '大盘回调影响' },
  { time: '2026-08-27 14:40', type: '涨停板', price: 37.55, volume: '25000手', amount: '9388万', change: '+10.02%', reason: '重大利好公告' },
  { time: '2026-08-27 10:30', type: '放量突破', price: 35.80, volume: '15000手', amount: '5370万', change: '+5.20%', reason: '突破均线压制' },
]

function openDetail() {
  detailVisible.value = true
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
  } catch (e) {
    quote.value = null
    message.error(e.message)
  } finally {
    quoteLoading.value = false
  }
}

onMounted(() => loadQuote('600519'))
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

      <!-- 暗盘信息 -->
      <div v-if="detailTab === 'dark' && quote" class="detail-content">
        <!-- 基本信息 -->
        <div class="detail-header">
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
          <div class="detail-code">代码: {{ quote.code }}</div>
        </div>

        <!-- 四指标 -->
        <div class="detail-metrics">
          <div class="metric-item">
            <div class="metric-label">市场排名</div>
            <div class="metric-value num up">{{ detailData.marketRank }}</div>
          </div>
          <div class="metric-item">
            <div class="metric-label">市场热度</div>
            <div class="metric-value num up">{{ detailData.marketHeat.toFixed(2) }}</div>
          </div>
          <div class="metric-item">
            <div class="metric-label">买卖信号</div>
            <div class="metric-value num up">{{ detailData.tradeSignal }}</div>
          </div>
          <div class="metric-item">
            <div class="metric-label">强弱线</div>
            <div class="metric-value num down">{{ detailData.strongLine }}</div>
          </div>
        </div>

        <!-- 所属板块 -->
        <div class="detail-section">
          <div class="section-label">所属板块</div>
          <div class="section-content">
            <span class="sector-tag">
              {{ detailData.sector.name }}
              <span class="num" :class="detailData.sector.change >= 0 ? 'up' : 'down'">
                {{ detailData.sector.change >= 0 ? '+' : '' }}{{ detailData.sector.change.toFixed(2) }}%
              </span>
            </span>
          </div>
        </div>

        <!-- 所属概念 -->
        <div class="detail-section">
          <div class="section-label">所属概念</div>
          <div class="section-content concepts">
            <span v-for="(c, idx) in detailData.concepts" :key="idx" class="concept-tag">
              {{ c.name }}
              <span class="num" :class="c.change >= 0 ? 'up' : 'down'">
                {{ c.change >= 0 ? '+' : '' }}{{ c.change.toFixed(2) }}%
              </span>
            </span>
          </div>
        </div>

        <!-- 公司简述 -->
        <div class="detail-section">
          <div class="section-label">公司简述</div>
          <div class="section-content desc">{{ detailData.companyDesc }}</div>
        </div>

        <!-- 行情走势 -->
        <div class="detail-section chart-section">
          <div class="section-header">
            <span class="section-label">行情走势</span>
            <div class="chart-controls">
              <button
                v-for="r in chartRanges"
                :key="r.key"
                class="ctrl-btn"
                :class="{ active: chartRange === r.key }"
                @click="setChartRange(r.key)"
              >{{ r.label }}</button>
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
          </div>

          <!-- 暗盘资金统计 -->
          <div class="dark-fund-stats">
            <div class="fund-stat-item">
              <div class="fund-stat-label">今日暗盘净流入</div>
              <div class="fund-stat-value num up">+{{ darkFundStats.today.net }}亿</div>
              <div class="fund-stat-sub">流入 {{ darkFundStats.today.inflow }}亿 / 流出 {{ darkFundStats.today.outflow }}亿</div>
            </div>
            <div class="fund-stat-item">
              <div class="fund-stat-label">本周暗盘净流入</div>
              <div class="fund-stat-value num up">+{{ darkFundStats.week.net }}亿</div>
              <div class="fund-stat-sub">流入 {{ darkFundStats.week.inflow }}亿 / 流出 {{ darkFundStats.week.outflow }}亿</div>
            </div>
            <div class="fund-stat-item">
              <div class="fund-stat-label">本月暗盘净流入</div>
              <div class="fund-stat-value num up">+{{ darkFundStats.month.net }}亿</div>
              <div class="fund-stat-sub">流入 {{ darkFundStats.month.inflow }}亿 / 流出 {{ darkFundStats.month.outflow }}亿</div>
            </div>
          </div>
          <div class="fund-data-note">* 暗盘资金为模拟演示数据，真实数据需接入专用数据源</div>

          <div class="chart-legend">
            <span class="legend-item"><span class="legend-dot blue"></span>收盘价</span>
            <span class="legend-item"><span class="legend-dot orange"></span>均价</span>
            <span class="legend-item"><span class="legend-dot red"></span>暗盘资金</span>
            <span class="legend-item"><span class="legend-dot purple"></span>成交量</span>
          </div>
          <div class="chart-container">
            <!-- 分时图 -->
            <svg v-if="chartPeriod === 'minute'" viewBox="0 0 1000 320" class="chart-svg" preserveAspectRatio="none">
              <g stroke="rgba(255,255,255,0.08)" stroke-width="1">
                <line x1="0" y1="40" x2="1000" y2="40" />
                <line x1="0" y1="80" x2="1000" y2="80" />
                <line x1="0" y1="120" x2="1000" y2="120" />
                <line x1="0" y1="160" x2="1000" y2="160" />
                <line x1="0" y1="200" x2="1000" y2="200" />
              </g>
              <path d="M0,60 L50,45 L100,70 L150,55 L200,80 L250,65 L300,90 L350,75 L400,100 L450,85 L500,110 L550,95 L600,120 L650,105 L700,130 L750,115 L800,140 L850,125 L900,145 L950,135 L1000,150" fill="none" stroke="#3b82f6" stroke-width="2" />
              <path d="M0,70 L50,60 L100,75 L150,68 L200,85 L250,78 L300,95 L350,88 L400,105 L450,98 L500,115 L550,108 L600,125 L650,118 L700,135 L750,128 L800,145 L850,138 L900,150 L950,145 L1000,155" fill="none" stroke="#f59e0b" stroke-width="1.5" stroke-dasharray="4,2" />
              <path d="M0,220 L50,215 L100,225 L150,210 L200,230 L250,218 L300,235 L350,222 L400,240 L450,228 L500,245 L550,232 L600,250 L650,238 L700,255 L750,242 L800,260 L850,248 L900,262 L950,255 L1000,265" fill="none" stroke="#ef4444" stroke-width="1.5" />
              <g>
                <rect v-for="i in 50" :key="i" :x="(i-1)*20" :y="280 + (i % 3) * 8" width="12" :height="20 - (i % 4) * 4" :fill="i % 2 === 0 ? 'rgba(239,68,68,0.6)' : 'rgba(34,197,94,0.6)'" />
              </g>
            </svg>

            <!-- K线图 -->
            <svg v-else viewBox="0 0 1000 320" class="chart-svg" preserveAspectRatio="none">
              <g stroke="rgba(255,255,255,0.08)" stroke-width="1">
                <line x1="0" y1="40" x2="1000" y2="40" />
                <line x1="0" y1="80" x2="1000" y2="80" />
                <line x1="0" y1="120" x2="1000" y2="120" />
                <line x1="0" y1="160" x2="1000" y2="160" />
                <line x1="0" y1="200" x2="1000" y2="200" />
              </g>
              <g v-for="(item, idx) in klineData[chartPeriod].slice(0, 40)" :key="idx">
                <line :x1="idx * 25 + 12" :y1="60 + (250 - item.high) * 0.5" :x2="idx * 25 + 12" :y2="60 + (250 - item.low) * 0.5" :stroke="item.close >= item.open ? '#ef4444' : '#22c55e'" stroke-width="1" />
                <rect :x="idx * 25 + 6" :y="60 + (250 - Math.max(item.open, item.close)) * 0.5" width="12" :height="Math.max(2, Math.abs(item.close - item.open) * 0.5)" :fill="item.close >= item.open ? '#ef4444' : '#22c55e'" />
              </g>
              <path :d="klineData[chartPeriod].slice(0, 40).map((item, idx) => (idx === 0 ? 'M' : 'L') + (idx * 25 + 12) + ',' + (210 + (item.darkFund / 50000000) * 20)).join(' ')" fill="none" stroke="#ef4444" stroke-width="1.5" />
              <g>
                <rect v-for="(item, idx) in klineData[chartPeriod].slice(0, 40)" :key="'v'+idx" :x="idx * 25 + 6" :y="285" width="12" :height="Math.max(3, item.volume / 100000)" :fill="item.close >= item.open ? 'rgba(239,68,68,0.6)' : 'rgba(34,197,94,0.6)'" />
              </g>
            </svg>
            <!-- X轴标签 -->
            <div class="chart-x-axis">
              <template v-if="chartPeriod === 'minute'">
                <span>09:30</span><span>10:00</span><span>10:30</span><span>11:00</span><span>11:30</span><span>13:00</span><span>13:30</span><span>14:00</span><span>14:30</span><span>15:00</span>
              </template>
              <template v-else-if="chartPeriod === 'day'">
                <span>08-01</span><span>08-08</span><span>08-15</span><span>08-22</span><span>08-29</span><span>09-01</span>
              </template>
              <template v-else-if="chartPeriod === 'week'">
                <span>W1</span><span>W5</span><span>W10</span><span>W15</span><span>W20</span><span>W25</span><span>W30</span><span>W35</span><span>W40</span>
              </template>
              <template v-else>
                <span>1月</span><span>3月</span><span>5月</span><span>7月</span><span>9月</span><span>11月</span><span>1月</span><span>3月</span><span>5月</span><span>7月</span><span>9月</span>
              </template>
            </div>
          </div>
        </div>
      </div>

      <!-- 个股分析 -->
      <div v-if="detailTab === 'analysis'" class="detail-content analysis-content">
        <!-- 综合评分 -->
        <div class="score-section">
          <div class="score-main">
            <div class="score-circle">
              <svg viewBox="0 0 120 120" class="score-svg">
                <circle cx="60" cy="60" r="50" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="8" />
                <circle cx="60" cy="60" r="50" fill="none" stroke="url(#scoreGrad)" stroke-width="8" stroke-linecap="round" :stroke-dasharray="`${analysisData.score.total * 3.14} 314`" transform="rotate(-90 60 60)" />
                <defs>
                  <linearGradient id="scoreGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stop-color="#3b82f6" />
                    <stop offset="100%" stop-color="#8b5cf6" />
                  </linearGradient>
                </defs>
              </svg>
              <div class="score-text">
                <div class="score-num">{{ analysisData.score.total }}</div>
                <div class="score-label">综合评分</div>
              </div>
            </div>
          </div>
          <div class="score-dims">
            <div class="score-dim-item">
              <div class="dim-label">技术面</div>
              <div class="dim-bar"><div class="dim-fill" :style="{width: analysisData.score.technical + '%'}"></div></div>
              <div class="dim-value">{{ analysisData.score.technical }}</div>
            </div>
            <div class="score-dim-item">
              <div class="dim-label">基本面</div>
              <div class="dim-bar"><div class="dim-fill" :style="{width: analysisData.score.fundamental + '%'}"></div></div>
              <div class="dim-value">{{ analysisData.score.fundamental }}</div>
            </div>
            <div class="score-dim-item">
              <div class="dim-label">资金面</div>
              <div class="dim-bar"><div class="dim-fill" :style="{width: analysisData.score.capital + '%'}"></div></div>
              <div class="dim-value">{{ analysisData.score.capital }}</div>
            </div>
            <div class="score-dim-item">
              <div class="dim-label">情绪面</div>
              <div class="dim-bar"><div class="dim-fill" :style="{width: analysisData.score.sentiment + '%'}"></div></div>
              <div class="dim-value">{{ analysisData.score.sentiment }}</div>
            </div>
          </div>
        </div>

        <!-- 技术指标 -->
        <div class="analysis-section">
          <div class="section-title">技术指标</div>
          <div class="indicator-grid">
            <div class="indicator-card">
              <div class="ind-name">MACD</div>
              <div class="ind-value num up">{{ analysisData.technical.macd.value }}</div>
              <div class="ind-signal up">{{ analysisData.technical.macd.signal }}</div>
            </div>
            <div class="indicator-card">
              <div class="ind-name">KDJ</div>
              <div class="ind-value num">{{ analysisData.technical.kdj.value }}</div>
              <div class="ind-signal up">{{ analysisData.technical.kdj.signal }}</div>
            </div>
            <div class="indicator-card">
              <div class="ind-name">RSI</div>
              <div class="ind-value num">{{ analysisData.technical.rsi.value }}</div>
              <div class="ind-signal">{{ analysisData.technical.rsi.signal }}</div>
            </div>
            <div class="indicator-card">
              <div class="ind-name">BOLL</div>
              <div class="ind-value num">{{ analysisData.technical.boll.value }}</div>
              <div class="ind-signal up">{{ analysisData.technical.boll.signal }}</div>
            </div>
          </div>
          <div class="ma-section">
            <div class="ma-item" v-for="(ma, key) in {ma5: analysisData.technical.ma5, ma10: analysisData.technical.ma10, ma20: analysisData.technical.ma20, ma60: analysisData.technical.ma60}" :key="key">
              <span class="ma-label">{{ key.toUpperCase() }}</span>
              <span class="ma-value num">{{ ma.value }}</span>
              <span class="ma-signal up">{{ ma.signal }}</span>
            </div>
          </div>
        </div>

        <!-- 基本面 -->
        <div class="analysis-section">
          <div class="section-title">基本面</div>
          <div class="fund-grid">
            <div class="fund-item"><span class="fund-label">市盈率(PE)</span><span class="fund-value num">{{ analysisData.fundamental.pe }}</span></div>
            <div class="fund-item"><span class="fund-label">市净率(PB)</span><span class="fund-value num">{{ analysisData.fundamental.pb }}</span></div>
            <div class="fund-item"><span class="fund-label">净资产收益率</span><span class="fund-value num up">{{ analysisData.fundamental.roe }}</span></div>
            <div class="fund-item"><span class="fund-label">营业收入</span><span class="fund-value num">{{ analysisData.fundamental.revenue }}</span></div>
            <div class="fund-item"><span class="fund-label">净利润</span><span class="fund-value num">{{ analysisData.fundamental.profit }}</span></div>
            <div class="fund-item"><span class="fund-label">营收增长</span><span class="fund-value num up">{{ analysisData.fundamental.revenueGrowth }}</span></div>
            <div class="fund-item"><span class="fund-label">利润增长</span><span class="fund-value num up">{{ analysisData.fundamental.profitGrowth }}</span></div>
            <div class="fund-item"><span class="fund-label">毛利率</span><span class="fund-value num">{{ analysisData.fundamental.grossMargin }}</span></div>
            <div class="fund-item"><span class="fund-label">资产负债率</span><span class="fund-value num">{{ analysisData.fundamental.debtRatio }}</span></div>
          </div>
        </div>

        <!-- 资金流向 -->
        <div class="analysis-section">
          <div class="section-title">资金流向</div>
          <div class="capital-grid">
            <div class="capital-card main">
              <div class="cap-label">主力净流入</div>
              <div class="cap-value num up">{{ analysisData.capitalFlow.mainNet }}</div>
              <div class="cap-sub">流入 {{ analysisData.capitalFlow.mainInflow }} / 流出 {{ analysisData.capitalFlow.mainOutflow }}</div>
            </div>
            <div class="capital-card">
              <div class="cap-label">散户净流入</div>
              <div class="cap-value num down">{{ analysisData.capitalFlow.retailNet }}</div>
            </div>
            <div class="capital-card">
              <div class="cap-label">北向净流入</div>
              <div class="cap-value num up">{{ analysisData.capitalFlow.northNet }}</div>
              <div class="cap-sub">持股 {{ analysisData.capitalFlow.northHolding }} ({{ analysisData.capitalFlow.northRatio }})</div>
            </div>
          </div>
        </div>

        <!-- 机构评级 -->
        <div class="analysis-section">
          <div class="section-title">机构评级</div>
          <div class="institution-section">
            <div class="inst-main">
              <div class="inst-rating">{{ analysisData.institution.rating }}</div>
              <div class="inst-target">目标价 <span class="num up">{{ analysisData.institution.targetPrice }}</span></div>
            </div>
            <div class="inst-stats">
              <div class="inst-stat"><span class="stat-label">评级机构</span><span class="stat-value num">{{ analysisData.institution.ratingCount }}家</span></div>
              <div class="inst-stat"><span class="stat-label">买入</span><span class="stat-value num up">{{ analysisData.institution.buyCount }}家</span></div>
              <div class="inst-stat"><span class="stat-label">持有</span><span class="stat-value num">{{ analysisData.institution.holdCount }}家</span></div>
              <div class="inst-stat"><span class="stat-label">卖出</span><span class="stat-value num down">{{ analysisData.institution.sellCount }}家</span></div>
            </div>
            <div class="inst-report">{{ analysisData.institution.recentReport }}</div>
          </div>
        </div>
      </div>

      <!-- 暗盘历史 -->
      <div v-if="detailTab === 'history'" class="detail-content history-content">
        <div class="history-summary">
          <div class="hist-summary-item">
            <div class="hist-label">近5日累计净流入</div>
            <div class="hist-value num up">+2.98亿</div>
          </div>
          <div class="hist-summary-item">
            <div class="hist-label">近10日累计净流入</div>
            <div class="hist-value num up">+5.23亿</div>
          </div>
          <div class="hist-summary-item">
            <div class="hist-label">近20日累计净流入</div>
            <div class="hist-value num up">+8.56亿</div>
          </div>
          <div class="hist-summary-item">
            <div class="hist-label">连续净流入天数</div>
            <div class="hist-value num up">3天</div>
          </div>
        </div>
        <div class="history-table-wrap">
          <table class="history-table">
            <thead>
              <tr>
                <th>日期</th>
                <th>收盘价</th>
                <th>涨跌幅</th>
                <th>暗盘流入</th>
                <th>暗盘流出</th>
                <th>净流入</th>
                <th>趋势</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, idx) in historyData" :key="idx">
                <td class="num">{{ item.date }}</td>
                <td class="num">{{ item.close.toFixed(2) }}</td>
                <td class="num" :class="item.change >= 0 ? 'up' : 'down'">{{ item.change >= 0 ? '+' : '' }}{{ item.change.toFixed(2) }}%</td>
                <td class="num up">{{ item.inflow.toFixed(2) }}亿</td>
                <td class="num down">{{ item.outflow.toFixed(2) }}亿</td>
                <td class="num" :class="item.net >= 0 ? 'up' : 'down'">{{ item.net >= 0 ? '+' : '' }}{{ item.net.toFixed(2) }}亿</td>
                <td>
                  <div class="trend-bar">
                    <div class="trend-fill" :class="item.net >= 0 ? 'up' : 'down'" :style="{width: Math.min(Math.abs(item.net) * 30, 100) + '%'}"></div>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="data-note">* 暗盘历史数据为模拟演示数据，真实数据需接入专用数据源</div>
      </div>

      <!-- 异动清单 -->
      <div v-if="detailTab === 'anomaly'" class="detail-content anomaly-content">
        <div class="anomaly-summary">
          <div class="anom-summary-item">
            <div class="anom-label">今日异动次数</div>
            <div class="anom-value num">4次</div>
          </div>
          <div class="anom-summary-item">
            <div class="anom-label">大单买入</div>
            <div class="anom-value num up">2次</div>
          </div>
          <div class="anom-summary-item">
            <div class="anom-label">快速拉升</div>
            <div class="anom-value num up">1次</div>
          </div>
          <div class="anom-summary-item">
            <div class="anom-label">放量突破</div>
            <div class="anom-value num up">1次</div>
          </div>
        </div>
        <div class="anomaly-list">
          <div v-for="(item, idx) in anomalyData" :key="idx" class="anomaly-item">
            <div class="anom-left">
              <div class="anom-type" :class="item.type.includes('买') || item.type.includes('涨') || item.type.includes('拉') || item.type.includes('突破') ? 'buy' : 'sell'">
                {{ item.type }}
              </div>
              <div class="anom-time">{{ item.time }}</div>
            </div>
            <div class="anom-middle">
              <div class="anom-price-row">
                <span class="anom-price num">{{ item.price.toFixed(2) }}</span>
                <span class="anom-change num" :class="item.change.startsWith('+') ? 'up' : 'down'">{{ item.change }}</span>
              </div>
              <div class="anom-vol">成交量 {{ item.volume }} / 成交额 {{ item.amount }}</div>
            </div>
            <div class="anom-right">
              <div class="anom-reason">{{ item.reason }}</div>
            </div>
          </div>
        </div>
        <div class="data-note">* 异动清单数据为模拟演示数据，真实数据需接入专用数据源</div>
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
