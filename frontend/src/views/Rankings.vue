<script setup>
import { ref } from 'vue'
import { fetchMarketBreadth, fetchIndustryFlow, fetchStockRank } from '../api'
import { useAutoRefresh } from '../composables/useAutoRefresh'
import { num, pct, mv, trendClass } from '../utils/format'

const tabs = [
  { key: 'sentiment', label: '市场情绪' },
  { key: 'fundflow', label: '资金流向' },
  { key: 'ranking', label: '榜单' },
]
const rankKinds = [
  { key: 'gainers', label: '涨幅榜' },
  { key: 'losers', label: '跌幅榜' },
  { key: 'amount', label: '成交额榜' },
  { key: 'turnover', label: '换手率榜' },
]

const activeTab = ref('sentiment')
const rankKind = ref('gainers')

const breadth = ref(null)
const industryFlow = ref([])
const rankList = ref([])
const loading = ref(false)
const lastUpdate = ref('')
const loadError = ref('')

// 防止并发请求竞态
let seq = 0

async function loadSentiment() {
  const id = ++seq
  try {
    const data = await fetchMarketBreadth()
    if (id !== seq) return
    breadth.value = data
    loadError.value = ''
  } catch (e) {
    if (id !== seq) return
    breadth.value = null
    loadError.value = e.message || '加载失败'
  }
}

async function loadFundFlow() {
  const id = ++seq
  try {
    const data = await fetchIndustryFlow(20)
    if (id !== seq) return
    industryFlow.value = data || []
    loadError.value = ''
  } catch (e) {
    if (id !== seq) return
    industryFlow.value = []
    loadError.value = e.message || '加载失败'
  }
}

async function loadRanking() {
  const id = ++seq
  try {
    const data = await fetchStockRank(rankKind.value, 20)
    if (id !== seq) return
    rankList.value = data || []
    loadError.value = ''
  } catch (e) {
    if (id !== seq) return
    rankList.value = []
    loadError.value = e.message || '加载失败'
  }
}

async function loadActive() {
  loading.value = true
  try {
    if (activeTab.value === 'sentiment') await loadSentiment()
    else if (activeTab.value === 'fundflow') await loadFundFlow()
    else await loadRanking()
    lastUpdate.value = new Date().toLocaleTimeString('zh-CN', { hour12: false })
  } finally {
    loading.value = false
  }
}

function switchTab(key) {
  activeTab.value = key
  loadActive()
}

function switchRank(kind) {
  rankKind.value = kind
  loadRanking()
}

// 每 15 秒自动刷新；页面切回立即刷新
useAutoRefresh(loadActive, 15000)

// 涨跌分布柱状图数据（按档位升序）
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

// 涨跌占比
function upRatio() {
  if (!breadth.value || !breadth.value.total) return 0
  return Math.round((breadth.value.up / breadth.value.total) * 100)
}

// 行业资金流向最大绝对值（用于柱状比例）
function maxInflow() {
  const arr = industryFlow.value || []
  return Math.max(1, ...arr.map((i) => Math.abs(i.net_inflow || 0)))
}
</script>

<template>
  <div class="rankings-page">
    <!-- 页面头部 -->
    <header class="page-head">
      <div>
        <div class="brand-tag">MARKET DATA TERMINAL</div>
        <h1 class="page-title">行情中枢</h1>
        <div class="page-sub">市场情绪 · 行业资金流向 · 涨跌榜 —— 数据实时刷新
          <span v-if="lastUpdate" class="update-time">更新于 {{ lastUpdate }}</span>
        </div>
      </div>
    </header>

    <!-- 标签导航 -->
    <div class="tab-nav">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="tab-btn"
        :class="{ active: activeTab === tab.key }"
        @click="switchTab(tab.key)"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- 市场情绪 -->
    <div v-if="activeTab === 'sentiment'" class="sentiment-view">
      <a-spin :spinning="loading">
        <template v-if="breadth">
          <!-- 涨跌家数总览 -->
          <div class="overview-grid">
            <div class="overview-card">
              <div class="overview-label">上涨家数</div>
              <div class="overview-value num up">{{ breadth.up }}</div>
              <div class="overview-sub">占比 {{ upRatio() }}%</div>
            </div>
            <div class="overview-card">
              <div class="overview-label">平盘家数</div>
              <div class="overview-value num flat">{{ breadth.flat }}</div>
              <div class="overview-sub">横盘整理</div>
            </div>
            <div class="overview-card">
              <div class="overview-label">下跌家数</div>
              <div class="overview-value num down">{{ breadth.down }}</div>
              <div class="overview-sub">占比 {{ 100 - upRatio() - Math.round(breadth.flat / breadth.total * 100) }}%</div>
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

          <!-- 涨跌分布 -->
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
        <div v-else class="empty-state">{{ loadError ? '数据加载失败，请稍后自动重试' : '暂无市场情绪数据，请稍后刷新' }}</div>
      </a-spin>
    </div>

    <!-- 资金流向 -->
    <div v-if="activeTab === 'fundflow'" class="fundflow-view">
      <a-spin :spinning="loading">
        <div v-if="industryFlow.length" class="flow-list">
          <div v-for="(item, idx) in industryFlow" :key="item.code || item.name" class="flow-item">
            <div class="flow-rank num">{{ idx + 1 }}</div>
            <div class="flow-name">
              {{ item.name }}
              <span class="flow-pct num" :class="trendClass(item.pct)">{{ pct(item.pct) }}</span>
            </div>
            <div class="flow-bar-wrap">
              <div
                class="flow-bar"
                :class="{ positive: item.net_inflow >= 0, negative: item.net_inflow < 0 }"
                :style="{ width: `${Math.min(Math.abs(item.net_inflow || 0) / maxInflow() * 100, 100)}%` }"
              ></div>
            </div>
            <div class="flow-value num" :class="trendClass(item.net_inflow)">
              {{ item.net_inflow > 0 ? '+' : '' }}{{ mv(item.net_inflow) }}
            </div>
            <div class="flow-ratio num">{{ item.net_ratio !== null && item.net_ratio !== undefined ? item.net_ratio.toFixed(2) + '%' : '--' }}</div>
          </div>
        </div>
        <div v-else class="empty-state">{{ loadError ? '数据加载失败，请稍后自动重试' : '暂无行业资金流向数据，请稍后刷新' }}</div>
      </a-spin>
    </div>

    <!-- 榜单 -->
    <div v-if="activeTab === 'ranking'" class="ranking-view">
      <div class="ranking-tabs">
        <button
          v-for="k in rankKinds"
          :key="k.key"
          class="ranking-tab"
          :class="{ active: rankKind === k.key }"
          @click="switchRank(k.key)"
        >
          {{ k.label }}
        </button>
      </div>

      <a-spin :spinning="loading">
        <div v-if="rankList.length" class="table-wrap">
          <table class="ranking-table">
            <thead>
              <tr>
                <th class="col-rank">排名</th>
                <th>代码</th>
                <th>名称</th>
                <th class="num">最新价</th>
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
        <div v-else class="empty-state">{{ loadError ? '数据加载失败，请稍后自动重试' : '暂无榜单数据，请稍后刷新' }}</div>
      </a-spin>
    </div>

    <footer class="page-foot">
      数据来源于公开行情接口，仅供学习参考，不构成投资建议 · 行情可能存在延迟或误差
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
.update-time {
  color: var(--text-3);
  margin-left: 8px;
}

/* 标签 */
.tab-nav {
  display: flex;
  gap: 0;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 12px;
  overflow: hidden;
}
.tab-btn {
  flex: 1;
  padding: 14px 20px;
  background: none;
  border: none;
  color: var(--text-3);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border-bottom: 2px solid transparent;
}
.tab-btn:hover { color: var(--text-2); }
.tab-btn.active {
  color: var(--accent);
  border-bottom-color: var(--accent);
  font-weight: 600;
  background: rgba(79, 124, 255, 0.06);
}

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
.overview-label {
  font-size: 12px;
  color: var(--text-3);
  margin-bottom: 8px;
}
.overview-value {
  font-size: 26px;
  font-weight: 700;
  margin-bottom: 4px;
}
.overview-value .dim { color: var(--text-3); font-size: 16px; }
.overview-sub {
  font-size: 12px;
  color: var(--text-3);
}
.dist-panel {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 16px 18px;
}
.panel-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 14px;
}
.dist-bars {
  display: flex;
  flex-direction: column;
  gap: 6px;
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
.dist-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s;
}
.dist-fill.up { background: var(--up); }
.dist-fill.down { background: var(--down); }
.dist-fill.flat { background: #6f6f8a; }
.dist-value {
  width: 40px;
  font-size: 12px;
  color: var(--text-2);
  flex-shrink: 0;
}
.panel-note {
  margin-top: 12px;
  font-size: 11px;
  color: var(--text-3);
}

/* 资金流向 */
.flow-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.flow-item {
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 10px 14px;
}
.flow-rank {
  width: 24px;
  color: var(--text-3);
  flex-shrink: 0;
}
.flow-name {
  width: 150px;
  font-size: 13px;
  color: var(--text);
  font-weight: 500;
  flex-shrink: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.flow-pct { margin-left: 6px; font-size: 12px; }
.flow-bar-wrap {
  flex: 1;
  height: 10px;
  background: var(--panel-2);
  border-radius: 5px;
  overflow: hidden;
}
.flow-bar { height: 100%; border-radius: 5px; transition: width 0.3s; }
.flow-bar.positive { background: var(--up); }
.flow-bar.negative { background: var(--down); }
.flow-value {
  width: 90px;
  text-align: right;
  font-size: 13px;
  font-weight: 600;
  flex-shrink: 0;
}
.flow-ratio {
  width: 60px;
  text-align: right;
  font-size: 12px;
  color: var(--text-3);
  flex-shrink: 0;
}

/* 榜单 */
.ranking-tabs {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.ranking-tab {
  padding: 8px 18px;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text-3);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}
.ranking-tab:hover { color: var(--text-2); border-color: var(--accent); }
.ranking-tab.active {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
  font-weight: 600;
}
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
  .flow-name { width: 100px; }
  .flow-value { width: 70px; }
  .flow-ratio { display: none; }
}
</style>
