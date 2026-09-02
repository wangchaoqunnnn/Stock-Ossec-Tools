<script setup>
import { ref } from 'vue'
import { fetchStockRank } from '../api'
import { num, pct, mv, trendClass } from '../utils/format'

const emit = defineEmits(['navigate'])

const activeTab = ref('ranking')
const tabs = [
  { key: 'ranking', label: '自选组合' },
  { key: 'strategies', label: '策略分类' },
]

// 自选组合：以真实涨幅榜为持仓样例，展示实时行情（公开组合功能需接入数据源）
const holdings = ref([])
const loading = ref(false)

async function loadHoldings() {
  loading.value = true
  try {
    const data = await fetchStockRank('gainers', 10)
    holdings.value = data || []
  } catch (e) {
    holdings.value = []
  } finally {
    loading.value = false
  }
}

function init() {
  loadHoldings()
}
init()
</script>

<template>
  <div class="portfolio-page">
    <!-- 页面头部 -->
    <header class="page-head">
      <div>
        <div class="brand-tag">PORTFOLIO LAB</div>
        <h1 class="page-title">投资组合</h1>
        <div class="page-sub">自选组合以实时行情展示 · 公开组合排行与策略分类需接入数据源</div>
      </div>
    </header>

    <!-- 标签导航 -->
    <div class="tab-nav">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="tab-btn"
        :class="{ active: activeTab === tab.key }"
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- 自选组合 -->
    <div v-if="activeTab === 'ranking'" class="ranking-view">
      <a-spin :spinning="loading">
        <div v-if="holdings.length" class="table-wrap">
          <table class="portfolio-table">
            <thead>
              <tr>
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
              <tr v-for="item in holdings" :key="item.code">
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
        <div v-else class="placeholder-panel">暂无自选组合数据</div>
      </a-spin>
    </div>

    <!-- 策略分类（需数据源） -->
    <div v-if="activeTab === 'strategies'" class="strategies-view">
      <div class="placeholder-panel">
        <div class="placeholder-title">策略分类</div>
        <div class="placeholder-desc">公开组合的策略分布、收益统计需接入后端组合数据源后提供。</div>
      </div>
    </div>

    <footer class="page-foot">
      自选组合以实时行情展示；公开组合排行、策略统计需接入数据源 · 仅供学习参考，不构成投资建议
    </footer>
  </div>
</template>

<style scoped>
.portfolio-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.brand-tag {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 2px;
  color: #51cf66;
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
.ranking-view,
.strategies-view {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.table-wrap {
  overflow-x: auto;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 12px;
}
.portfolio-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.portfolio-table th {
  padding: 12px 14px;
  text-align: left;
  font-weight: 600;
  color: var(--text-3);
  background: var(--panel-2);
  border-bottom: 1px solid var(--border);
  white-space: nowrap;
}
.portfolio-table td {
  padding: 11px 14px;
  border-bottom: 1px solid var(--border);
  color: var(--text-2);
  white-space: nowrap;
}
.portfolio-table tbody tr:hover { background: rgba(79, 124, 255, 0.06); }
.portfolio-table tbody tr:last-child td { border-bottom: none; }
.code-cell { color: var(--accent); font-weight: 500; }
.name-cell { font-weight: 500; color: var(--text); }
.industry-cell { color: var(--text-3); }
.placeholder-panel {
  background: var(--panel);
  border: 1px dashed var(--border);
  border-radius: 12px;
  padding: 60px 24px;
  text-align: center;
}
.placeholder-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 10px;
}
.placeholder-desc {
  font-size: 13px;
  color: var(--text-3);
  line-height: 1.7;
}
.page-foot {
  margin-top: 12px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
  color: var(--text-3);
  font-size: 12px;
  text-align: center;
}
</style>
