<script setup>
import { ref, computed } from 'vue'
import { message } from 'ant-design-vue'
import { fetchMarketBreadth, fetchIndustryFlow, fetchConceptFlow, fetchFlowMinute as fetchFlowMinuteApi, fetchStockRank } from '../api'
import { useAutoRefresh } from '../composables/useAutoRefresh'
import { num, pct, mv, trendClass } from '../utils/format'

const topTabs = [
  { key: 'fundflow', label: '资金流向' },
  { key: 'sentiment', label: '市场情绪' },
  { key: 'ranking', label: '榜单' },
]
const activeTab = ref('fundflow')

const fundKinds = [
  { key: 'industry', label: '行业' },
  { key: 'concept', label: '概念' },
]
const activeFundKind = ref('industry')

const rankKinds = [
  { key: 'gainers', label: '涨幅榜' },
  { key: 'losers', label: '跌幅榜' },
  { key: 'amount', label: '成交额榜' },
  { key: 'turnover', label: '换手率榜' },
]
const activeRankKind = ref('gainers')

// 数据
const breadth = ref(null)
const industryFlow = ref([])
const conceptFlow = ref([])
const rankList = ref([])
const loading = ref(false)
const lastUpdate = ref('')

// 分钟级资金流
const selectedFlow = ref(null) // { code, market, name }
const minuteFlow = ref([])
const minuteHover = ref(null)
const minuteLoading = ref(false)

// 防并发竞态
let seq = 0

async function loadBreadth() {
  const id = ++seq
  try {
    const data = await fetchMarketBreadth()
    if (id !== seq) return
    breadth.value = data
  } catch (e) {
    if (id !== seq) return
    breadth.value = null
  }
}

async function loadIndustryFlow() {
  const id = ++seq
  try {
    const data = await fetchIndustryFlow(20)
    if (id !== seq) return
    industryFlow.value = data || []
    if (activeFundKind.value === 'industry' && data && data.length && !selectedFlow.value) {
      fetchFlowMinute(data[0])
    }
  } catch (e) {
    if (id !== seq) return
    industryFlow.value = []
  }
}

async function loadConceptFlow() {
  const id = ++seq
  try {
    const data = await fetchConceptFlow(20)
    if (id !== seq) return
    conceptFlow.value = data || []
    if (activeFundKind.value === 'concept' && data && data.length && !selectedFlow.value) {
      fetchFlowMinute(data[0])
    }
  } catch (e) {
    if (id !== seq) return
    conceptFlow.value = []
  }
}

async function loadRanking() {
  const id = ++seq
  try {
    const data = await fetchStockRank(activeRankKind.value, 20)
    if (id !== seq) return
    rankList.value = data || []
  } catch (e) {
    if (id !== seq) return
    rankList.value = []
  }
}

async function loadActive() {
  loading.value = true
  try {
    if (activeTab.value === 'sentiment') await loadBreadth()
    else if (activeTab.value === 'fundflow') {
      if (activeFundKind.value === 'industry') await loadIndustryFlow()
      else await loadConceptFlow()
    } else await loadRanking()
    lastUpdate.value = new Date().toLocaleTimeString('zh-CN', { hour12: false })
  } finally {
    loading.value = false
  }
}

function switchTab(key) {
  activeTab.value = key
  loadActive()
}

function switchFundKind(key) {
  activeFundKind.value = key
  loadActive()
  // 切换后默认展示第一项的分钟资金流
  const list = key === 'industry' ? industryFlow.value : conceptFlow.value
  if (list.length) fetchFlowMinute(list[0])
}

function switchRankKind(kind) {
  activeRankKind.value = kind
  loadRanking()
}

// 分钟资金流
async function fetchFlowMinute(item) {
  if (!item || !item.code) return
  selectedFlow.value = item
  minuteLoading.value = true
  try {
    const data = await fetchFlowMinuteApi(item.code, item.market || '90')
    minuteFlow.value = data || []
  } catch (e) {
    minuteFlow.value = []
  } finally {
    minuteLoading.value = false
  }
}

// 每分钟一根柱：红=净流入（向上）、绿=净流出（向下）
function minuteBars() {
  const arr = minuteFlow.value || []
  if (!arr.length) return []
  const absVals = arr.map((d) => Math.abs(d.main_net || 0))
  const maxAbs = Math.max(1, ...absVals)
  const step = 1000 / arr.length
  const w = Math.max(1, step * 0.7)
  return arr.map((d, i) => {
    const h = ((d.main_net || 0) / maxAbs) * 140
    return {
      x: i * step + step / 2,
      up: (d.main_net || 0) >= 0,
      h: Math.max(1, Math.abs(h)),
      w,
      time: d.time,
      net: d.main_net,
    }
  })
}

// 当日累计净流入（分钟求和 = 收盘总净流入）
const minuteSum = computed(() => {
  const arr = minuteFlow.value || []
  return arr.reduce((s, d) => s + (d.main_net || 0), 0)
})

function handleMinuteMouseMove(event) {
  const svg = event.currentTarget
  const rect = svg.getBoundingClientRect()
  const bars = minuteBars()
  if (!bars.length) return
  const ratio = (event.clientX - rect.left) / rect.width
  const index = Math.max(0, Math.min(bars.length - 1, Math.floor(ratio * bars.length)))
  const b = bars[index]
  minuteHover.value = {
    x: event.clientX,
    y: event.clientY,
    time: b.time,
    net: b.net,
    up: b.up,
  }
}

// 涨跌分布
function distBars() {
  const dist = (breadth.value && breadth.value.dist) || {}
  const keys = Object.keys(dist).map(Number).sort((a, b) => a - b)
  const max = Math.max(1, ...keys.map((k) => dist[k] || 0))
  return keys.map((k) => {
    const v = dist[k] || 0
    return {
      key: k,
      label: k > 0 ? `+${k}` : String(k),
      value: v,
      pct: (v / max) * 100,
      cls: k > 0 ? 'up' : k < 0 ? 'down' : 'flat',
    }
  })
}

useAutoRefresh(loadActive, 15000)

// 初始加载
loadIndustryFlow()
loadConceptFlow()
loadBreadth()
</script>

<template>
  <div class="rankings-page">
    <!-- 页面头部 -->
    <header class="page-head">
      <div>
        <div class="brand-tag">MARKET DATA TERMINAL</div>
        <h1 class="page-title">行情中枢</h1>
        <div class="page-sub">市场情绪 · 行业/概念资金流向 · 涨跌榜 —— 数据实时刷新
          <span v-if="lastUpdate" class="update-time">更新于 {{ lastUpdate }}</span>
        </div>
      </div>
    </header>

    <!-- 顶部标签 -->
    <div class="tab-nav">
      <button
        v-for="tab in topTabs"
        :key="tab.key"
        class="tab-btn"
        :class="{ active: activeTab === tab.key }"
        @click="switchTab(tab.key)"
      >{{ tab.label }}</button>
    </div>

    <!-- ============ 资金流向 ============ -->
    <div v-if="activeTab === 'fundflow'" class="fundflow-view">
      <div class="sub-tabs">
        <button
          v-for="k in fundKinds"
          :key="k.key"
          class="sub-tab-btn"
          :class="{ active: activeFundKind === k.key }"
          @click="switchFundKind(k.key)"
        >{{ k.label }}</button>
      </div>

      <a-spin :spinning="loading">
        <!-- 分钟级资金流 -->
        <div class="chart-panel">
          <div class="panel-title-row">
            <span class="panel-title">分时主力净流入（分钟级）</span>
            <span v-if="selectedFlow" class="panel-note">{{ selectedFlow.name }} · 红=净流入，绿=净流出 · 累计 {{ minuteSum >= 0 ? '+' : '' }}{{ (minuteSum / 1e8).toFixed(2) }}亿</span>
          </div>
          <a-spin :spinning="minuteLoading">
            <div v-if="minuteFlow.length" class="chart-body">
              <div class="chart-container">
                <svg viewBox="0 0 1000 350" class="trend-chart" preserveAspectRatio="none" @mousemove="handleMinuteMouseMove" @mouseleave="minuteHover = null">
                  <g stroke="rgba(255,255,255,0.08)" stroke-width="1">
                    <line x1="0" y1="0" x2="1000" y2="0" />
                    <line x1="0" y1="87.5" x2="1000" y2="87.5" />
                    <line x1="0" y1="175" x2="1000" y2="175" />
                    <line x1="0" y1="262.5" x2="1000" y2="262.5" />
                    <line x1="0" y1="350" x2="1000" y2="350" />
                  </g>
                  <line x1="0" y1="175" x2="1000" y2="175" stroke="rgba(255,255,255,0.3)" stroke-width="1" stroke-dasharray="4,2" />
                  <g v-for="(b, i) in minuteBars()" :key="i">
                    <rect v-if="b.up" :x="b.x - b.w / 2" :y="175 - b.h" :width="b.w" :height="b.h" fill="#ff4d5e" opacity="0.85" />
                    <rect v-else :x="b.x - b.w / 2" :y="175" :width="b.w" :height="b.h" fill="#00c58e" opacity="0.85" />
                  </g>
                </svg>
              </div>
              <div class="x-axis-labels">
                <span>09:30</span><span>10:30</span><span>11:30/13:00</span><span>14:00</span><span>15:00</span>
              </div>
              <div v-if="minuteHover" class="hover-tooltip" :style="{ left: minuteHover.x + 'px', top: minuteHover.y + 'px' }">
                <div class="hover-time">{{ minuteHover.time }}</div>
                <div class="hover-item">
                  <span class="hover-dot" :style="{ background: minuteHover.up ? '#ff4d5e' : '#00c58e' }"></span>
                  <span class="hover-name">主力净流入</span>
                  <span class="hover-value" :class="minuteHover.up ? 'up' : 'down'">{{ minuteHover.net >= 0 ? '+' : '' }}{{ (minuteHover.net / 1e8).toFixed(2) }}亿</span>
                </div>
              </div>
            </div>
            <div v-else class="empty-state">暂无分钟资金流数据，请稍后刷新</div>
          </a-spin>
        </div>

        <!-- 净流入排名 -->
        <div class="ranking-panel">
          <div class="panel-title">{{ activeFundKind === 'industry' ? '行业' : '概念' }}主力净流入排名（点击查看分钟资金流）</div>
          <div v-if="activeFundKind === 'industry'" class="ranking-list">
            <div
              v-for="(item, idx) in industryFlow"
              :key="item.code"
              class="ranking-item"
              :class="{ selected: selectedFlow && selectedFlow.code === item.code }"
              @click="fetchFlowMinute(item)"
            >
              <span class="rank-num" :class="idx < 3 ? 'top' : ''">{{ idx + 1 }}</span>
              <span class="rank-name">{{ item.name }}</span>
              <span class="rank-change" :class="trendClass(item.pct)">{{ pct(item.pct) }}</span>
              <span class="rank-net" :class="trendClass(item.net_inflow)">{{ item.net_inflow >= 0 ? '+' : '' }}{{ mv(item.net_inflow) }}</span>
              <span class="rank-arrow">›</span>
            </div>
          </div>
          <div v-else class="ranking-list">
            <div
              v-for="(item, idx) in conceptFlow"
              :key="item.code"
              class="ranking-item"
              :class="{ selected: selectedFlow && selectedFlow.code === item.code }"
              @click="fetchFlowMinute(item)"
            >
              <span class="rank-num" :class="idx < 3 ? 'top' : ''">{{ idx + 1 }}</span>
              <span class="rank-name">{{ item.name }}</span>
              <span class="rank-change" :class="trendClass(item.pct)">{{ pct(item.pct) }}</span>
              <span class="rank-net" :class="trendClass(item.net_inflow)">{{ item.net_inflow >= 0 ? '+' : '' }}{{ mv(item.net_inflow) }}</span>
              <span class="rank-arrow">›</span>
            </div>
          </div>
          <div v-if="!industryFlow.length && !conceptFlow.length" class="empty-state">暂无资金流数据，请稍后刷新</div>
        </div>
      </a-spin>
    </div>

    <!-- ============ 市场情绪 ============ -->
    <div v-if="activeTab === 'sentiment'" class="sentiment-view">
      <a-spin :spinning="loading">
        <template v-if="breadth">
          <div class="overview-grid">
            <div class="overview-card">
              <div class="overview-label">上涨家数</div>
              <div class="overview-value num up">{{ breadth.up }}</div>
              <div class="overview-sub">占比 {{ breadth.total ? Math.round(breadth.up / breadth.total * 100) : 0 }}%</div>
            </div>
            <div class="overview-card">
              <div class="overview-label">平盘家数</div>
              <div class="overview-value num flat">{{ breadth.flat }}</div>
              <div class="overview-sub">横盘整理</div>
            </div>
            <div class="overview-card">
              <div class="overview-label">下跌家数</div>
              <div class="overview-value num down">{{ breadth.down }}</div>
              <div class="overview-sub">占比 {{ breadth.total ? Math.round(breadth.down / breadth.total * 100) : 0 }}%</div>
            </div>
            <div class="overview-card">
              <div class="overview-label">涨停 / 跌停</div>
              <div class="overview-value num">
                <span class="up">{{ breadth.limit_up }}</span>
                <span class="dim"> / </span>
                <span class="down">{{ breadth.limit_down }}</span>
              </div>
              <div class="overview-sub">含 20cm 板</div>
            </div>
          </div>

          <div class="dist-panel">
            <div class="panel-title">涨跌分布（家数）</div>
            <div class="dist-bars">
              <div v-for="bar in distBars()" :key="bar.key" class="dist-bar-row">
                <span class="dist-label num">{{ bar.label }}</span>
                <div class="dist-track">
                  <div class="dist-fill" :class="bar.cls" :style="{ width: bar.pct + '%' }"></div>
                </div>
                <span class="dist-value num">{{ bar.value }}</span>
              </div>
            </div>
            <div class="panel-note">横轴为涨跌幅档位（%），纵轴为该档位股票家数</div>
          </div>
        </template>
        <div v-else class="empty-state">暂无市场情绪数据，请稍后刷新</div>
      </a-spin>
    </div>

    <!-- ============ 榜单 ============ -->
    <div v-if="activeTab === 'ranking'" class="ranking-view">
      <div class="sub-tabs">
        <button
          v-for="k in rankKinds"
          :key="k.key"
          class="sub-tab-btn"
          :class="{ active: activeRankKind === k.key }"
          @click="switchRankKind(k.key)"
        >{{ k.label }}</button>
      </div>

      <a-spin :spinning="loading">
        <div v-if="rankList.length" class="table-wrap">
          <table class="ranking-table">
            <thead>
              <tr>
                <th class="col-rank">排名</th>
                <th>代码</th>
                <th>名称</th>
                <th class="num">现价</th>
                <th class="num">涨跌幅</th>
                <th class="num">换手率</th>
                <th class="num">成交额</th>
                <th>行业</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, idx) in rankList" :key="item.code">
                <td class="col-rank"><span class="rank-badge" :class="`rank-${idx + 1}`">{{ idx + 1 }}</span></td>
                <td class="num code-cell">{{ item.code }}</td>
                <td class="name-cell">{{ item.name }}</td>
                <td class="num">{{ num(item.price, 2) }}</td>
                <td class="num" :class="trendClass(item.pct)">{{ pct(item.pct) }}</td>
                <td class="num">{{ pct(item.turnover) }}</td>
                <td class="num">{{ mv(item.amount) }}</td>
                <td class="industry-cell">{{ item.industry || '--' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="empty-state">暂无榜单数据，请稍后刷新</div>
      </a-spin>
    </div>

    <footer class="page-foot">
      数据来源于东方财富公开接口，仅供学习参考，不构成投资建议 · 行情可能存在延迟或误差
    </footer>
  </div>
</template>

<style scoped>
.rankings-page {
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
.page-sub {
  color: var(--text-3);
  font-size: 13px;
}
.update-time { color: var(--text-3); margin-left: 8px; }

.tab-nav, .sub-tabs {
  display: flex;
  gap: 0;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 10px;
  overflow: hidden;
}
.tab-btn, .sub-tab-btn {
  flex: 1;
  padding: 12px 16px;
  background: none;
  border: none;
  color: var(--text-3);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border-bottom: 2px solid transparent;
}
.tab-btn:hover, .sub-tab-btn:hover { color: var(--text-2); }
.tab-btn.active, .sub-tab-btn.active {
  color: var(--accent);
  border-bottom-color: var(--accent);
  font-weight: 600;
  background: rgba(79, 124, 255, 0.06);
}

.fundflow-view, .sentiment-view, .ranking-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 图表面板 */
.chart-panel, .dist-panel, .ranking-panel {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 16px 18px;
}
.panel-title-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 14px;
}
.panel-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
}
.panel-note {
  font-size: 12px;
  color: var(--text-3);
}
.chart-body { position: relative; }
.chart-container { position: relative; }
.trend-chart { width: 100%; height: 320px; display: block; }
.x-axis-labels {
  display: flex;
  justify-content: space-between;
  padding: 6px 0 0;
  font-size: 11px;
  color: var(--text-3);
}

/* 悬停提示（跟随鼠标） */
.hover-tooltip {
  position: fixed;
  background: rgba(15, 23, 42, 0.95);
  border: 1px solid #334155;
  border-radius: 8px;
  padding: 10px 12px;
  z-index: 1000;
  min-width: 150px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  pointer-events: none;
  transform: translate(14px, 14px);
}
.hover-time {
  font-size: 13px;
  font-weight: 600;
  color: #f1f5f9;
  margin-bottom: 6px;
  padding-bottom: 6px;
  border-bottom: 1px solid #334155;
}
.hover-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}
.hover-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.hover-name { color: #94a3b8; }
.hover-value { font-weight: 600; margin-left: auto; }

/* 排名列表 */
.ranking-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 12px;
}
.ranking-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  background: var(--panel-2);
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}
.ranking-item:hover { background: var(--panel); }
.ranking-item.selected {
  background: rgba(59, 130, 246, 0.12);
  outline: 1px solid rgba(59, 130, 246, 0.4);
}
.rank-num {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 700;
  background: var(--panel);
  color: var(--text-2);
  flex-shrink: 0;
}
.rank-num.top { background: var(--up); color: #fff; }
.rank-name { flex: 1; font-size: 13px; color: var(--text); font-weight: 500; }
.rank-change { width: 80px; text-align: right; font-size: 13px; }
.rank-net { width: 90px; text-align: right; font-size: 13px; font-weight: 600; }
.rank-arrow { color: var(--text-3); }

/* 市场情绪 */
.overview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px;
}
.overview-card {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 16px 18px;
}
.overview-label { font-size: 12px; color: var(--text-3); margin-bottom: 8px; }
.overview-value { font-size: 26px; font-weight: 700; margin-bottom: 4px; }
.overview-value .dim { color: var(--text-3); font-size: 16px; }
.overview-sub { font-size: 12px; color: var(--text-3); }

.dist-bars {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 12px;
}
.dist-bar-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.dist-label {
  width: 32px;
  text-align: right;
  font-size: 12px;
  color: var(--text-2);
  flex-shrink: 0;
}
.dist-track {
  flex: 1;
  height: 14px;
  background: var(--panel-2);
  border-radius: 4px;
  overflow: hidden;
}
.dist-fill { height: 100%; border-radius: 4px; transition: width 0.3s; }
.dist-fill.up { background: var(--up); }
.dist-fill.down { background: var(--down); }
.dist-fill.flat { background: #6f6f8a; }
.dist-value { width: 40px; font-size: 12px; color: var(--text-2); flex-shrink: 0; }

/* 榜单 */
.table-wrap {
  overflow-x: auto;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 12px;
}
.ranking-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.ranking-table th {
  padding: 12px 14px;
  text-align: left;
  font-weight: 600;
  color: var(--text-3);
  background: var(--panel-2);
  border-bottom: 1px solid var(--border);
  white-space: nowrap;
}
.ranking-table td {
  padding: 11px 14px;
  border-bottom: 1px solid var(--border);
  color: var(--text-2);
  white-space: nowrap;
}
.ranking-table tbody tr:hover { background: rgba(79, 124, 255, 0.06); }
.ranking-table tbody tr:last-child td { border-bottom: none; }
.col-rank { width: 56px; }
.rank-badge {
  display: inline-block;
  width: 24px;
  height: 24px;
  line-height: 24px;
  text-align: center;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 700;
  background: var(--panel-2);
  color: var(--text-2);
}
.rank-1 { background: var(--up); color: #fff; }
.rank-2 { background: #f0883e; color: #fff; }
.rank-3 { background: #d9a428; color: #fff; }
.code-cell { color: var(--accent); font-weight: 500; }
.name-cell { font-weight: 500; color: var(--text); }
.industry-cell { color: var(--text-3); }

.empty-state {
  padding: 48px 20px;
  text-align: center;
  color: var(--text-3);
  font-size: 14px;
}

.page-foot {
  margin-top: 12px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
  color: var(--text-3);
  font-size: 12px;
  text-align: center;
}

@media (max-width: 768px) {
  .rank-change { width: 70px; }
  .rank-net { width: 80px; }
}
</style>
