<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { message } from 'ant-design-vue'
import { fetchStockRank } from '../api'
import { num, pct, mv, trendClass } from '../utils/format'

const activeTab = ref('watch')
const tabs = [
  { key: 'watch', label: '今日关注' },
  { key: 'stockpicker', label: '选股器' },
  { key: 'anomaly', label: '异动寻龙' },
]

// 今日关注：展示实时涨幅榜（真实交易数据）
const watchKeyword = ref('')
const watchList = ref([])
const loading = ref(false)
const lastUpdate = ref('')
let timer = null

async function loadWatchList() {
  loading.value = true
  try {
    const data = await fetchStockRank('gainers', 20)
    watchList.value = data || []
    lastUpdate.value = new Date().toLocaleTimeString('zh-CN', { hour12: false })
  } catch (e) {
    watchList.value = []
  } finally {
    loading.value = false
  }
}

const filteredWatch = computed(() => {
  const kw = (watchKeyword.value || '').trim().toLowerCase()
  if (!kw) return watchList.value
  return watchList.value.filter(
    (it) => String(it.code).toLowerCase().includes(kw) || (it.name || '').toLowerCase().includes(kw)
  )
})

function refresh() {
  loadWatchList()
}

onMounted(() => {
  loadWatchList()
  timer = setInterval(loadWatchList, 15000)
})
onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<template>
  <div class="utility-page">
    <!-- 页面头部 -->
    <header class="page-head">
      <div>
        <div class="brand-tag">QUANT TERMINAL</div>
        <h1 class="page-title">量化工具</h1>
        <div class="page-sub">今日关注（实时涨幅榜）· 选股器 · 异动寻龙
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
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- 今日关注（真实涨幅榜） -->
    <div v-if="activeTab === 'watch'" class="tab-content">
      <div class="toolbar">
        <div class="search-group">
          <input v-model="watchKeyword" class="search-input" placeholder="按代码/名称筛选" />
          <button class="btn-outline" @click="refresh">刷新</button>
        </div>
        <div class="toolbar-note">今日涨幅榜（沪深京 A 股，实时）</div>
      </div>

      <a-spin :spinning="loading">
        <div v-if="filteredWatch.length" class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>排名</th>
                <th>代码</th>
                <th>名称</th>
                <th>现价</th>
                <th>涨跌幅</th>
                <th>换手率</th>
                <th>成交额</th>
                <th>行业</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, idx) in filteredWatch" :key="item.code">
                <td class="num">{{ idx + 1 }}</td>
                <td class="code-cell">{{ item.code }}</td>
                <td class="name-cell">{{ item.name }}</td>
                <td class="num">{{ num(item.price, 2) }}</td>
                <td class="num" :class="trendClass(item.pct)">{{ pct(item.pct) }}</td>
                <td class="num">{{ pct(item.turnover) }}</td>
                <td class="num">{{ mv(item.amount) }}</td>
                <td class="text-muted">{{ item.industry || '--' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="empty-state">暂无榜单数据，请稍后刷新</div>
      </a-spin>
    </div>

    <!-- 选股器（需专用数据源） -->
    <div v-if="activeTab === 'stockpicker'" class="tab-content">
      <div class="placeholder-panel">
        <div class="placeholder-title">选股器</div>
        <div class="placeholder-desc">选股器依赖量化信号数据源（买卖信号、机构活跃度、主力资金等），需接入专用数据源后提供真实选股结果。</div>
      </div>
    </div>

    <!-- 异动寻龙（需专用数据源） -->
    <div v-if="activeTab === 'anomaly'" class="tab-content">
      <div class="placeholder-panel">
        <div class="placeholder-title">异动寻龙</div>
        <div class="placeholder-desc">异动（暗盘资金、明盘资金、异动次数等）需接入专用数据源后提供真实异动排行。</div>
      </div>
    </div>

    <footer class="page-foot">
      今日关注为实时涨幅榜数据；选股器、异动寻龙需接入专用数据源 · 仅供学习参考，不构成投资建议
    </footer>
  </div>
</template>

<style scoped>
.utility-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.brand-tag {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 2px;
  color: #8b5cf6;
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
.tab-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 12px 16px;
}
.search-group {
  display: flex;
  gap: 8px;
}
.search-input {
  width: 200px;
  padding: 8px 12px;
  background: var(--panel-2);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text);
  font-size: 13px;
  outline: none;
}
.search-input:focus { border-color: var(--accent); }
.toolbar-note {
  font-size: 12px;
  color: var(--text-3);
}
.btn-outline {
  padding: 8px 16px;
  background: var(--panel-2);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text-2);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-outline:hover { border-color: var(--accent); color: var(--accent); }
.table-wrap {
  overflow-x: auto;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 12px;
}
.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.data-table th {
  padding: 12px 14px;
  text-align: left;
  font-weight: 600;
  color: var(--text-3);
  background: var(--panel-2);
  border-bottom: 1px solid var(--border);
  white-space: nowrap;
}
.data-table td {
  padding: 11px 14px;
  border-bottom: 1px solid var(--border);
  color: var(--text-2);
  white-space: nowrap;
}
.data-table tbody tr:hover { background: rgba(79, 124, 255, 0.06); }
.data-table tbody tr:last-child td { border-bottom: none; }
.code-cell { color: var(--accent); font-weight: 500; }
.name-cell { font-weight: 500; color: var(--text); }
.text-muted { color: var(--text-3); }
.empty-state {
  padding: 48px 20px;
  text-align: center;
  color: var(--text-3);
  font-size: 14px;
}
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
