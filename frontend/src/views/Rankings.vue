<script setup>
import { ref } from 'vue'

const emit = defineEmits(['navigate'])

const activeTab = ref('fundflow')
const tabs = [
  { key: 'fundflow', label: '资金流向' },
  { key: 'sentiment', label: '市场情绪' },
  { key: 'hotlist', label: '东财热榜' },
  { key: 'news', label: '7x24' },
  { key: 'calendar', label: '财经会议' },
  { key: 'ranking', label: '榜单' },
]

const subTab = ref('industry')

// 市场概览数据（模拟）
const marketOverview = {
  up: 3038,
  flat: 111,
  down: 1971,
  median: 0.48,
  up3: 516,
  down3: 544,
  mainInflow: -309.2,
  mainInflowChange: -252.4,
  turnover: 19104,
  turnoverChange: -1796,
}

// 行业资金流向（模拟）
const industryFlow = [
  { name: '银行', inflow: 94.3, change: 1.2 },
  { name: '电力', inflow: 62.3, change: 0.8 },
  { name: '证券', inflow: 56.6, change: 2.1 },
  { name: '文化传媒', inflow: 51.7, change: 3.5 },
  { name: '种植业与林业', inflow: 48.3, change: 4.2 },
  { name: '软件开发', inflow: 42.6, change: 1.5 },
  { name: '零售', inflow: 42.4, change: 0.9 },
  { name: '化学制药', inflow: 36.8, change: 1.8 },
  { name: 'IT服务', inflow: 28.9, change: 0.6 },
  { name: '汽车零部件', inflow: 28.8, change: 1.1 },
  { name: '光伏设备', inflow: -17.1, change: -2.3 },
  { name: '光学光电子', inflow: -19.5, change: -1.8 },
  { name: '自动化设备', inflow: -21.1, change: -1.2 },
  { name: '建筑材料', inflow: -25.3, change: -0.8 },
  { name: '消费电子', inflow: -33.8, change: -2.1 },
  { name: '电子化学品', inflow: -38.8, change: -1.5 },
  { name: '小金属', inflow: -41.3, change: -2.8 },
  { name: '电池', inflow: -44.9, change: -3.2 },
  { name: '元件', inflow: -125.1, change: -4.5 },
]

// 涨幅榜（模拟）
const topGainers = [
  { code: '300001', name: '特锐德', price: 28.56, change: 20.02, turnover: 15.2, amount: '12.3亿' },
  { code: '688001', name: '华兴源创', price: 45.32, change: 18.56, turnover: 12.8, amount: '8.7亿' },
  { code: '300002', name: '神州泰岳', price: 12.89, change: 15.34, turnover: 18.5, amount: '15.6亿' },
  { code: '002001', name: '新和成', price: 32.45, change: 12.78, turnover: 8.3, amount: '6.2亿' },
  { code: '600001', name: '邯郸钢铁', price: 5.67, change: 10.11, turnover: 6.5, amount: '3.4亿' },
  { code: '300003', name: '乐普医疗', price: 25.78, change: 9.85, turnover: 7.2, amount: '5.8亿' },
  { code: '002002', name: '鸿达兴业', price: 4.32, change: 9.65, turnover: 9.1, amount: '4.2亿' },
  { code: '688002', name: '睿创微纳', price: 68.90, change: 8.92, turnover: 5.6, amount: '7.1亿' },
]

// 跌幅榜（模拟）
const topLosers = [
  { code: '300004', name: '南风股份', price: 8.56, change: -12.34, turnover: 10.2, amount: '4.5亿' },
  { code: '688003', name: '天准科技', price: 35.67, change: -10.56, turnover: 8.5, amount: '5.2亿' },
  { code: '002003', name: '伟星股份', price: 15.23, change: -9.87, turnover: 6.3, amount: '3.8亿' },
  { code: '300005', name: '探路者', price: 7.89, change: -8.65, turnover: 12.1, amount: '6.7亿' },
  { code: '600002', name: '齐鲁石化', price: 6.45, change: -7.89, turnover: 4.5, amount: '2.1亿' },
  { code: '002004', name: '华邦健康', price: 5.67, change: -7.23, turnover: 5.8, amount: '2.9亿' },
  { code: '300006', name: '莱美药业', price: 6.78, change: -6.98, turnover: 7.5, amount: '3.6亿' },
  { code: '688004', name: '博汇科技', price: 42.34, change: -6.54, turnover: 4.2, amount: '2.8亿' },
]

// 7x24 资讯（模拟）
const newsList = [
  { time: '14:55', content: '北向资金今日净买入 28.5 亿元，连续 3 日加仓', type: '资金' },
  { time: '14:42', content: '央行开展 2000 亿元 7 天期逆回购操作，中标利率 1.8%', type: '政策' },
  { time: '14:30', content: '半导体板块午后拉升，中芯国际涨超 6%', type: '板块' },
  { time: '14:15', content: '国家发改委：加快推进新型基础设施建设', type: '政策' },
  { time: '13:58', content: '黄金期货突破 2600 美元/盎司，创历史新高', type: '商品' },
  { time: '13:45', content: '新能源汽车销量数据超预期，产业链个股集体走强', type: '行业' },
  { time: '11:30', content: '午评：三大指数涨跌互现，粮食种业板块领涨', type: '市场' },
  { time: '10:15', content: '证监会：进一步优化 IPO 审核流程，提高审核效率', type: '政策' },
  { time: '9:45', content: '开盘：沪指低开 0.2%，半导体板块回调', type: '市场' },
  { time: '9:30', content: '今日共有 3 只新股上市申购', type: '新股' },
]

// 财经会议（模拟）
const calendarList = [
  { date: '09-02', time: '10:00', title: '国家统计局发布 PMI 数据', importance: 'high' },
  { date: '09-03', time: '20:30', title: '美国非农就业数据公布', importance: 'high' },
  { date: '09-04', time: '14:00', title: '美联储公布经济状况褐皮书', importance: 'medium' },
  { date: '09-05', time: '09:30', title: '中国贸易数据公布', importance: 'medium' },
  { date: '09-06', time: '16:00', title: '欧元区 GDP 数据公布', importance: 'low' },
]

const rankingTab = ref('gainers')

function trendClass(v) {
  if (v > 0) return 'up'
  if (v < 0) return 'down'
  return 'flat'
}

function inflowColor(v) {
  return v >= 0 ? 'var(--up)' : 'var(--down)'
}

function getImportanceColor(level) {
  if (level === 'high') return 'error'
  if (level === 'medium') return 'warning'
  return 'default'
}

function getImportanceText(level) {
  if (level === 'high') return '重要'
  if (level === 'medium') return '关注'
  return '一般'
}
</script>

<template>
  <div class="rankings-page">
    <!-- 页面头部 -->
    <header class="page-head">
      <div>
        <div class="brand-tag">MARKET DATA TERMINAL</div>
        <h1 class="page-title">行情中枢</h1>
        <div class="page-sub">追踪指数、行业、热榜、资讯与资金趋势</div>
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

    <!-- 市场概览（所有标签共享） -->
    <div class="market-overview">
      <div class="overview-card">
        <div class="overview-label">涨跌分布</div>
        <div class="overview-main">
          <span class="up num">{{ marketOverview.up }}</span>
          <span class="sep">:</span>
          <span class="flat num">{{ marketOverview.flat }}</span>
          <span class="sep">:</span>
          <span class="down num">{{ marketOverview.down }}</span>
        </div>
        <div class="overview-sub">
          中位 <span class="up num">+{{ marketOverview.median }}%</span>
          · ≥3% <span class="num">{{ marketOverview.up3 }}</span>
          · ≤-3% <span class="num">{{ marketOverview.down3 }}</span>
        </div>
      </div>
      <div class="overview-card">
        <div class="overview-label">主力净流入</div>
        <div class="overview-main">
          <span class="num" :class="trendClass(marketOverview.mainInflow)">{{ marketOverview.mainInflow }}亿</span>
        </div>
        <div class="overview-sub">
          同比昨日 <span class="num down">{{ marketOverview.mainInflowChange }}亿</span>
        </div>
      </div>
      <div class="overview-card">
        <div class="overview-label">成交额</div>
        <div class="overview-main">
          <span class="num">{{ marketOverview.turnover }}亿</span>
        </div>
        <div class="overview-sub">
          同比昨日 <span class="num down">{{ marketOverview.turnoverChange }}亿</span>
        </div>
      </div>
    </div>

    <!-- 资金流向 -->
    <div v-if="activeTab === 'fundflow'" class="fundflow-view">
      <div class="sub-tabs">
        <button class="sub-tab" :class="{ active: subTab === 'industry' }" @click="subTab = 'industry'">行业</button>
        <button class="sub-tab" :class="{ active: subTab === 'concept' }" @click="subTab = 'concept'">概念</button>
      </div>

      <div class="flow-list">
        <div v-for="item in industryFlow" :key="item.name" class="flow-item">
          <div class="flow-name">{{ item.name }}</div>
          <div class="flow-bar-wrap">
            <div
              class="flow-bar"
              :class="{ positive: item.inflow >= 0, negative: item.inflow < 0 }"
              :style="{ width: `${Math.min(Math.abs(item.inflow) / 125 * 100, 100)}%` }"
            ></div>
          </div>
          <div class="flow-value num" :class="trendClass(item.inflow)">
            {{ item.inflow > 0 ? '+' : '' }}{{ item.inflow }}亿
          </div>
        </div>
      </div>
    </div>

    <!-- 市场情绪 -->
    <div v-if="activeTab === 'sentiment'" class="sentiment-view">
      <div class="sentiment-grid">
        <div class="sentiment-card">
          <div class="sentiment-label">涨停家数</div>
          <div class="sentiment-value num up">68</div>
          <div class="sentiment-sub">较昨日 +12</div>
        </div>
        <div class="sentiment-card">
          <div class="sentiment-label">跌停家数</div>
          <div class="sentiment-value num down">15</div>
          <div class="sentiment-sub">较昨日 -3</div>
        </div>
        <div class="sentiment-card">
          <div class="sentiment-label">连板高度</div>
          <div class="sentiment-value num">5板</div>
          <div class="sentiment-sub">最高连板个股</div>
        </div>
        <div class="sentiment-card">
          <div class="sentiment-label">炸板率</div>
          <div class="sentiment-value num warning">28.5%</div>
          <div class="sentiment-sub">较昨日 +5.2%</div>
        </div>
        <div class="sentiment-card">
          <div class="sentiment-label">赚钱效应</div>
          <div class="sentiment-value num up">偏强</div>
          <div class="sentiment-sub">上涨家数占比 60.5%</div>
        </div>
        <div class="sentiment-card">
          <div class="sentiment-label">北向资金</div>
          <div class="sentiment-value num up">+28.5亿</div>
          <div class="sentiment-sub">连续 3 日净流入</div>
        </div>
      </div>
    </div>

    <!-- 东财热榜 -->
    <div v-if="activeTab === 'hotlist'" class="hotlist-view">
      <div class="hotlist-table">
        <div class="hotlist-header">
          <span class="col-rank">排名</span>
          <span class="col-name">股票名称</span>
          <span class="col-code">代码</span>
          <span class="col-price num">最新价</span>
          <span class="col-change num">涨跌幅</span>
          <span class="col-heat num">热度</span>
        </div>
        <div v-for="(item, idx) in topGainers.slice(0, 6)" :key="item.code" class="hotlist-row">
          <span class="col-rank"><span class="rank-num" :class="`rank-${idx + 1}`">{{ idx + 1 }}</span></span>
          <span class="col-name">{{ item.name }}</span>
          <span class="col-code num">{{ item.code }}</span>
          <span class="col-price num">{{ item.price }}</span>
          <span class="col-change num up">+{{ item.change }}%</span>
          <span class="col-heat num">{{ (10000 - idx * 1200).toLocaleString() }}</span>
        </div>
      </div>
    </div>

    <!-- 7x24 资讯 -->
    <div v-if="activeTab === 'news'" class="news-view">
      <div class="news-timeline">
        <div v-for="(news, idx) in newsList" :key="idx" class="news-item">
          <div class="news-time num">{{ news.time }}</div>
          <div class="news-dot"></div>
          <div class="news-content">
            <a-tag size="small" class="news-tag">{{ news.type }}</a-tag>
            <span class="news-text">{{ news.content }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 财经会议 -->
    <div v-if="activeTab === 'calendar'" class="calendar-view">
      <div class="calendar-list">
        <div v-for="(item, idx) in calendarList" :key="idx" class="calendar-item">
          <div class="calendar-date">
            <div class="date-day num">{{ item.date }}</div>
            <div class="date-time num">{{ item.time }}</div>
          </div>
          <div class="calendar-content">
            <div class="calendar-title">{{ item.title }}</div>
            <a-tag :color="getImportanceColor(item.importance)" size="small">
              {{ getImportanceText(item.importance) }}
            </a-tag>
          </div>
        </div>
      </div>
    </div>

    <!-- 榜单 -->
    <div v-if="activeTab === 'ranking'" class="ranking-view">
      <div class="ranking-tabs">
        <button class="ranking-tab" :class="{ active: rankingTab === 'gainers' }" @click="rankingTab = 'gainers'">涨幅榜</button>
        <button class="ranking-tab" :class="{ active: rankingTab === 'losers' }" @click="rankingTab = 'losers'">跌幅榜</button>
      </div>

      <div class="table-wrap">
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
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, idx) in (rankingTab === 'gainers' ? topGainers : topLosers)" :key="item.code">
              <td class="col-rank"><span class="rank-badge" :class="`rank-${idx + 1}`">{{ idx + 1 }}</span></td>
              <td class="num code-cell">{{ item.code }}</td>
              <td class="name-cell">{{ item.name }}</td>
              <td class="num">{{ item.price }}</td>
              <td class="num" :class="trendClass(item.change)">{{ item.change > 0 ? '+' : '' }}{{ item.change }}%</td>
              <td class="num">{{ item.turnover }}%</td>
              <td class="num">{{ item.amount }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <footer class="page-foot">
      行情数据为演示数据，仅供参考 · 不构成投资建议
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
  color: #ff6b6b;
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
  overflow-x: auto;
}
.tab-btn {
  padding: 10px 18px;
  background: none;
  border: none;
  border-radius: 8px;
  color: var(--text-2);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}
.tab-btn:hover {
  color: var(--text);
  background: var(--panel-2);
}
.tab-btn.active {
  background: #ff6b6b;
  color: #fff;
}

/* 市场概览 */
.market-overview {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
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
.overview-main {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 6px;
}
.overview-main .sep {
  color: var(--text-3);
  margin: 0 4px;
  font-weight: 400;
}
.overview-sub {
  font-size: 12px;
  color: var(--text-3);
}

/* 子标签 */
.sub-tabs, .ranking-tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 12px;
}
.sub-tab, .ranking-tab {
  padding: 8px 20px;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text-2);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}
.sub-tab:hover, .ranking-tab:hover {
  border-color: var(--accent);
  color: var(--accent);
}
.sub-tab.active, .ranking-tab.active {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}

/* 资金流向 */
.flow-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 16px;
}
.flow-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 0;
}
.flow-name {
  width: 100px;
  font-size: 13px;
  font-weight: 500;
  flex-shrink: 0;
}
.flow-bar-wrap {
  flex: 1;
  height: 20px;
  background: var(--panel-2);
  border-radius: 4px;
  position: relative;
  overflow: hidden;
}
.flow-bar {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s;
}
.flow-bar.positive {
  background: linear-gradient(90deg, rgba(255, 77, 94, 0.6), var(--up));
  margin-left: auto;
}
.flow-bar.negative {
  background: linear-gradient(90deg, var(--down), rgba(0, 197, 142, 0.6));
}
.flow-value {
  width: 80px;
  text-align: right;
  font-size: 13px;
  font-weight: 600;
  flex-shrink: 0;
}

/* 市场情绪 */
.sentiment-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
}
.sentiment-card {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 18px;
  text-align: center;
}
.sentiment-label {
  font-size: 12px;
  color: var(--text-3);
  margin-bottom: 8px;
}
.sentiment-value {
  font-size: 26px;
  font-weight: 700;
  margin-bottom: 4px;
}
.sentiment-sub {
  font-size: 11px;
  color: var(--text-3);
}

/* 热榜 */
.hotlist-table {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 10px;
  overflow: hidden;
}
.hotlist-header, .hotlist-row {
  display: grid;
  grid-template-columns: 60px 1fr 100px 100px 100px 100px;
  padding: 12px 16px;
  align-items: center;
  gap: 8px;
}
.hotlist-header {
  background: var(--panel-2);
  font-weight: 600;
  font-size: 13px;
  color: var(--text-2);
  border-bottom: 1px solid var(--border);
}
.hotlist-row {
  border-bottom: 1px solid var(--border);
  font-size: 13px;
  transition: background 0.2s;
}
.hotlist-row:hover {
  background: rgba(255, 107, 107, 0.06);
}
.hotlist-row:last-child {
  border-bottom: none;
}
.rank-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 700;
  background: var(--panel-2);
  color: var(--text-2);
}
.rank-1 { background: #ffd700; color: #000; }
.rank-2 { background: #c0c0c0; color: #000; }
.rank-3 { background: #cd7f32; color: #fff; }

/* 7x24 资讯 */
.news-timeline {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 20px;
}
.news-item {
  display: flex;
  gap: 16px;
  padding: 12px 0;
  border-bottom: 1px solid var(--border);
  position: relative;
}
.news-item:last-child {
  border-bottom: none;
}
.news-time {
  width: 50px;
  flex-shrink: 0;
  font-size: 13px;
  font-weight: 600;
  color: var(--accent);
  padding-top: 2px;
}
.news-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent);
  margin-top: 6px;
  flex-shrink: 0;
}
.news-content {
  flex: 1;
  display: flex;
  align-items: flex-start;
  gap: 8px;
  flex-wrap: wrap;
}
.news-tag {
  flex-shrink: 0;
}
.news-text {
  font-size: 13px;
  color: var(--text);
  line-height: 1.6;
}

/* 财经会议 */
.calendar-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.calendar-item {
  display: flex;
  align-items: center;
  gap: 16px;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px 18px;
}
.calendar-date {
  text-align: center;
  min-width: 70px;
  padding-right: 16px;
  border-right: 1px solid var(--border);
}
.date-day {
  font-size: 16px;
  font-weight: 700;
  color: var(--text);
}
.date-time {
  font-size: 12px;
  color: var(--text-3);
  margin-top: 2px;
}
.calendar-content {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.calendar-title {
  font-size: 14px;
  font-weight: 500;
}

/* 榜单表格 */
.table-wrap {
  overflow-x: auto;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 10px;
}
.ranking-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.ranking-table th {
  background: var(--panel-2);
  padding: 12px 14px;
  text-align: left;
  font-weight: 600;
  color: var(--text-2);
  border-bottom: 1px solid var(--border);
  white-space: nowrap;
}
.ranking-table td {
  padding: 12px 14px;
  border-bottom: 1px solid var(--border);
  white-space: nowrap;
}
.ranking-table tbody tr:hover {
  background: rgba(255, 107, 107, 0.06);
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
.code-cell {
  color: var(--accent);
  font-weight: 500;
}
.name-cell {
  font-weight: 500;
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
