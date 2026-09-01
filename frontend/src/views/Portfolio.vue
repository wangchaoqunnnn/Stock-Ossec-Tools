<script setup>
import { ref } from 'vue'

const emit = defineEmits(['navigate'])

const activeTab = ref('radar')
const tabs = [
  { key: 'radar', label: '组合雷达' },
  { key: 'ranking', label: '收益排行榜' },
  { key: 'strategies', label: '策略分类' },
]

const filters = [
  { key: 'all', label: '全部' },
  { key: 'trend', label: '趋势跟踪' },
  { key: 'value', label: '价值投资' },
  { key: 'quant', label: '量化对冲' },
  { key: 'growth', label: '成长股' },
  { key: 'dividend', label: '红利策略' },
]
const activeFilter = ref('all')

// 模拟公开组合数据
const portfolios = [
  { rank: 1, name: '稳健增值一号', strategy: '价值投资', return: 156.8, today: 2.3, maxDrawdown: -12.5, created: '2024-03-15', followers: 2847, winRate: 68 },
  { rank: 2, name: '科技成长精选', strategy: '成长股', return: 142.3, today: -1.5, maxDrawdown: -28.4, created: '2024-01-20', followers: 3156, winRate: 55 },
  { rank: 3, name: '量化对冲Alpha', strategy: '量化对冲', return: 89.6, today: 0.8, maxDrawdown: -8.2, created: '2023-11-08', followers: 1892, winRate: 72 },
  { rank: 4, name: '红利低波组合', strategy: '红利策略', return: 67.4, today: 1.2, maxDrawdown: -6.8, created: '2023-08-12', followers: 4521, winRate: 75 },
  { rank: 5, name: '趋势跟踪一号', strategy: '趋势跟踪', return: 124.7, today: 3.1, maxDrawdown: -18.9, created: '2024-05-03', followers: 2103, winRate: 58 },
  { rank: 6, name: '消费医药精选', strategy: '价值投资', return: 45.2, today: -0.6, maxDrawdown: -22.3, created: '2024-02-18', followers: 1567, winRate: 52 },
  { rank: 7, name: '新能源产业组合', strategy: '成长股', return: 98.9, today: 4.2, maxDrawdown: -32.1, created: '2024-04-25', followers: 3289, winRate: 50 },
  { rank: 8, name: '小盘股轮动', strategy: '量化对冲', return: 176.5, today: -2.1, maxDrawdown: -15.6, created: '2023-09-30', followers: 2756, winRate: 64 },
  { rank: 9, name: '蓝筹核心资产', strategy: '价值投资', return: 38.7, today: 0.5, maxDrawdown: -10.2, created: '2023-06-15', followers: 5234, winRate: 69 },
  { rank: 10, name: '周期行业轮动', strategy: '趋势跟踪', return: 112.3, today: 1.8, maxDrawdown: -20.5, created: '2024-01-08', followers: 1876, winRate: 56 },
]

const strategyStats = [
  { name: '价值投资', count: 128, avgReturn: 45.2, color: '#4f7cff' },
  { name: '成长股', count: 96, avgReturn: 68.7, color: '#7c5cff' },
  { name: '量化对冲', count: 64, avgReturn: 52.3, color: '#51cf66' },
  { name: '趋势跟踪', count: 82, avgReturn: 71.5, color: '#ff922b' },
  { name: '红利策略', count: 45, avgReturn: 38.9, color: '#ff6b6b' },
]

function trendClass(v) {
  if (v > 0) return 'up'
  if (v < 0) return 'down'
  return 'flat'
}

function signed(v, digits = 1) {
  if (v === null || v === undefined) return '--'
  const s = Number(v).toFixed(digits)
  return v > 0 ? `+${s}` : s
}
</script>

<template>
  <div class="portfolio-page">
    <!-- 页面头部 -->
    <header class="page-head">
      <div>
        <div class="brand-tag">PORTFOLIO LAB</div>
        <h1 class="page-title">投资组合</h1>
        <div class="page-sub">跟踪公开组合收益、持仓状态和策略表现</div>
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

    <!-- 组合雷达视图 -->
    <div v-if="activeTab === 'radar'" class="radar-view">
      <div class="radar-summary">
        <div class="summary-card">
          <div class="summary-label">公开组合总数</div>
          <div class="summary-value num">415</div>
        </div>
        <div class="summary-card">
          <div class="summary-label">本月正收益占比</div>
          <div class="summary-value num up">62.4%</div>
        </div>
        <div class="summary-card">
          <div class="summary-label">平均最大回撤</div>
          <div class="summary-value num down">-16.8%</div>
        </div>
        <div class="summary-card">
          <div class="summary-label">最高累计收益</div>
          <div class="summary-value num up">+176.5%</div>
        </div>
      </div>

      <h3 class="sub-title">策略分布</h3>
      <div class="strategy-list">
        <div v-for="s in strategyStats" :key="s.name" class="strategy-item">
          <div class="strategy-info">
            <span class="strategy-dot" :style="{ background: s.color }"></span>
            <span class="strategy-name">{{ s.name }}</span>
            <span class="strategy-count">{{ s.count }} 个组合</span>
          </div>
          <div class="strategy-bar-wrap">
            <div class="strategy-bar" :style="{ width: `${(s.avgReturn / 80) * 100}%`, background: s.color }"></div>
          </div>
          <div class="strategy-return num up">平均 +{{ s.avgReturn }}%</div>
        </div>
      </div>
    </div>

    <!-- 收益排行榜视图 -->
    <div v-if="activeTab === 'ranking'" class="ranking-view">
      <!-- 筛选 -->
      <div class="filter-bar">
        <span class="filter-label">策略类型：</span>
        <button
          v-for="f in filters"
          :key="f.key"
          class="filter-btn"
          :class="{ active: activeFilter === f.key }"
          @click="activeFilter = f.key"
        >
          {{ f.label }}
        </button>
      </div>

      <!-- 排行榜表格 -->
      <div class="table-wrap">
        <table class="portfolio-table">
          <thead>
            <tr>
              <th class="col-rank">排名</th>
              <th>组合名称</th>
              <th>策略类型</th>
              <th class="num">累计收益</th>
              <th class="num">今日收益</th>
              <th class="num">最大回撤</th>
              <th class="num">胜率</th>
              <th>创建时间</th>
              <th class="num">关注数</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in portfolios" :key="p.rank">
              <td class="col-rank">
                <span class="rank-badge" :class="`rank-${p.rank}`">{{ p.rank }}</span>
              </td>
              <td class="portfolio-name">{{ p.name }}</td>
              <td><a-tag size="small">{{ p.strategy }}</a-tag></td>
              <td class="num" :class="trendClass(p.return)">{{ signed(p.return) }}%</td>
              <td class="num" :class="trendClass(p.today)">{{ signed(p.today) }}%</td>
              <td class="num down">{{ p.maxDrawdown }}%</td>
              <td class="num">{{ p.winRate }}%</td>
              <td class="time-cell">{{ p.created }}</td>
              <td class="num">{{ p.followers.toLocaleString() }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 策略分类视图 -->
    <div v-if="activeTab === 'strategies'" class="strategies-view">
      <div class="strategy-cards">
        <div v-for="s in strategyStats" :key="s.name" class="strategy-card" :style="{ '--card-color': s.color }">
          <div class="card-header">
            <span class="card-dot"></span>
            <span class="card-name">{{ s.name }}</span>
          </div>
          <div class="card-stats">
            <div class="card-stat">
              <div class="stat-label">组合数量</div>
              <div class="stat-value num">{{ s.count }}</div>
            </div>
            <div class="card-stat">
              <div class="stat-label">平均收益</div>
              <div class="stat-value num up">+{{ s.avgReturn }}%</div>
            </div>
          </div>
          <a-button size="small" class="card-btn" @click="activeTab = 'ranking'">查看组合</a-button>
        </div>
      </div>
    </div>

    <footer class="page-foot">
      组合数据为公开演示数据，仅供参考 · 不构成投资建议
    </footer>
  </div>
</template>

<style scoped>
.portfolio-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
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
}
.page-sub {
  color: var(--text-3);
  font-size: 13px;
}

/* 标签导航 */
.tab-nav {
  display: flex;
  gap: 4px;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 4px;
}
.tab-btn {
  flex: 1;
  padding: 10px 16px;
  background: none;
  border: none;
  border-radius: 8px;
  color: var(--text-2);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}
.tab-btn:hover {
  color: var(--text);
  background: var(--panel-2);
}
.tab-btn.active {
  background: var(--accent);
  color: #fff;
}

/* 组合雷达 */
.radar-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}
.summary-card {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 18px 20px;
}
.summary-label {
  font-size: 12px;
  color: var(--text-3);
  margin-bottom: 8px;
}
.summary-value {
  font-size: 26px;
  font-weight: 700;
}
.sub-title {
  font-size: 16px;
  font-weight: 600;
  margin: 8px 0 12px;
}
.strategy-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.strategy-item {
  display: flex;
  align-items: center;
  gap: 16px;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px 16px;
}
.strategy-info {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 180px;
}
.strategy-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}
.strategy-name {
  font-weight: 500;
  font-size: 14px;
}
.strategy-count {
  font-size: 12px;
  color: var(--text-3);
}
.strategy-bar-wrap {
  flex: 1;
  height: 8px;
  background: var(--panel-2);
  border-radius: 4px;
  overflow: hidden;
}
.strategy-bar {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s;
}
.strategy-return {
  min-width: 80px;
  text-align: right;
  font-weight: 600;
}

/* 排行榜 */
.filter-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}
.filter-label {
  font-size: 13px;
  color: var(--text-3);
}
.filter-btn {
  padding: 6px 14px;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 16px;
  color: var(--text-2);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}
.filter-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
}
.filter-btn.active {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}
.table-wrap {
  overflow-x: auto;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 10px;
}
.portfolio-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.portfolio-table th {
  background: var(--panel-2);
  padding: 12px 14px;
  text-align: left;
  font-weight: 600;
  color: var(--text-2);
  border-bottom: 1px solid var(--border);
  white-space: nowrap;
}
.portfolio-table td {
  padding: 12px 14px;
  border-bottom: 1px solid var(--border);
  white-space: nowrap;
}
.portfolio-table tbody tr:hover {
  background: rgba(79, 124, 255, 0.06);
}
.col-rank {
  width: 60px;
  text-align: center;
}
.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 700;
  background: var(--panel-2);
  color: var(--text-2);
}
.rank-1 { background: linear-gradient(135deg, #ffd700, #ffaa00); color: #000; }
.rank-2 { background: linear-gradient(135deg, #c0c0c0, #a0a0a0); color: #000; }
.rank-3 { background: linear-gradient(135deg, #cd7f32, #b87333); color: #fff; }
.portfolio-name {
  font-weight: 500;
  color: var(--text);
}
.time-cell {
  color: var(--text-3);
  font-size: 12px;
}

/* 策略分类 */
.strategy-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}
.strategy-card {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
  border-top: 3px solid var(--card-color);
}
.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}
.card-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--card-color);
}
.card-name {
  font-size: 16px;
  font-weight: 600;
}
.card-stats {
  display: flex;
  gap: 24px;
  margin-bottom: 16px;
}
.card-stat .stat-label {
  font-size: 12px;
  color: var(--text-3);
  margin-bottom: 4px;
}
.card-stat .stat-value {
  font-size: 20px;
  font-weight: 700;
}
.card-btn {
  width: 100%;
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
