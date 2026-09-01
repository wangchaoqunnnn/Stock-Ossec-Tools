<script setup>
import { ref } from 'vue'

const emit = defineEmits(['navigate'])

const activeTab = ref('watch')
const tabs = [
  { key: 'watch', label: '今日关注' },
  { key: 'stockpicker', label: '选股器' },
  { key: 'anomaly', label: '异动寻龙' },
]

// 今日关注 - 搜索和日期
const watchKeyword = ref('')
const watchDate = ref('2026-09-01')

// 今日关注 - 表格数据（模拟8条）
const watchList = [
  { date: '2026-09-01', code: '共***(6***)', industry: '通信设备', recChange: 18.54, recChangePct: -3.40, price: 17.91, pricePct: -3.71, speed: -0.11, darkFund: '--', volumeRatio: 0.84, turnover: 14.08, marketCap: '141亿' },
  { date: '2026-09-01', code: '风***(6***)', industry: '数字媒体', recChange: 12.02, recChangePct: -0.67, price: 11.94, pricePct: -0.51, speed: -0.08, darkFund: '--', volumeRatio: 1.49, turnover: 18.3, marketCap: '71.02亿' },
  { date: '2026-09-01', code: '奋***(0***)', industry: '消费电子', recChange: 5.09, recChangePct: 1.57, price: 5.17, pricePct: 2.38, speed: -0.19, darkFund: '--', volumeRatio: 1.6, turnover: 6.52, marketCap: '81.27亿' },
  { date: '2026-09-01', code: '达***(0***)', industry: 'IT服务Ⅱ', recChange: 3.39, recChangePct: 3.24, price: 3.50, pricePct: 4.48, speed: 0.00, darkFund: '--', volumeRatio: 1.76, turnover: 15.42, marketCap: '71.27亿' },
  { date: '2026-09-01', code: '华***(0***)', industry: '炼化及贸易', recChange: 5.80, recChangePct: 3.62, price: 6.01, pricePct: 3.98, speed: -0.33, darkFund: '--', volumeRatio: 1.44, turnover: 9.43, marketCap: '96.12亿' },
  { date: '2026-09-01', code: '易***(3***)', industry: '广告营销', recChange: 38.09, recChangePct: -3.47, price: 36.77, pricePct: -3.24, speed: 0.14, darkFund: '--', volumeRatio: 1.24, turnover: 18.97, marketCap: '184.54亿' },
  { date: '2026-09-01', code: '网***(3***)', industry: 'IT服务Ⅱ', recChange: 16.19, recChangePct: 1.24, price: 16.39, pricePct: 0.18, speed: 0.12, darkFund: '--', volumeRatio: 1.03, turnover: 9.06, marketCap: '387.86亿' },
  { date: '2026-09-01', code: '蓝***(3***)', industry: '广告营销', recChange: 14.21, recChangePct: -1.27, price: 14.03, pricePct: -0.50, speed: 0.14, darkFund: '--', volumeRatio: 1.33, turnover: 12.75, marketCap: '487.95亿' },
]

// 选股器 - 左侧分类
const pickerCategories = [
  { key: 'decision', label: '决策指标', active: true },
  { key: 'fundamental', label: '基本面', active: false },
  { key: 'technical', label: '技术面', active: false },
  { key: 'scope', label: '股票范围', active: false },
]
const activeCategory = ref('decision')

// 选股器 - 决策指标子标签
const decisionTags = [
  '买卖信号', '机构活跃度', '主力资金', '主力雷达', '牛熊线',
  '竞价雷达', '高频参与度', '经典K线组合', '市场关注度', '市场活跃度', '模拟赛高手选股'
]
const selectedTags = ref([])

function toggleTag(tag) {
  const idx = selectedTags.value.indexOf(tag)
  if (idx > -1) {
    selectedTags.value.splice(idx, 1)
  } else {
    selectedTags.value.push(tag)
  }
}

function selectCategory(key) {
  activeCategory.value = key
}

// 选股结果（模拟数据）
const pickerResults = [
  { code: '300750', name: '宁德时代', price: 198.56, change: 5.23, volumeRatio: 3.2, turnover: 8.5, industry: '电池', signal: '放量突破' },
  { code: '002594', name: '比亚迪', price: 256.78, change: 4.15, volumeRatio: 2.8, turnover: 6.2, industry: '汽车', signal: '趋势加速' },
  { code: '688981', name: '中芯国际', price: 89.32, change: 6.78, volumeRatio: 4.5, turnover: 12.3, industry: '半导体', signal: '强势拉升' },
  { code: '002475', name: '立讯精密', price: 42.15, change: 3.56, volumeRatio: 2.3, turnover: 5.8, industry: '消费电子', signal: '底部启动' },
  { code: '300059', name: '东方财富', price: 15.67, change: 4.89, volumeRatio: 3.8, turnover: 9.2, industry: '证券', signal: '资金流入' },
  { code: '601012', name: '隆基绿能', price: 23.45, change: 3.12, volumeRatio: 2.1, turnover: 5.5, industry: '光伏', signal: '企稳反弹' },
  { code: '002415', name: '海康威视', price: 34.89, change: 3.78, volumeRatio: 2.5, turnover: 4.8, industry: '安防', signal: '放量上涨' },
  { code: '300124', name: '汇川技术', price: 62.34, change: 4.45, volumeRatio: 2.9, turnover: 6.7, industry: '工控', signal: '突破平台' },
]

// 异动寻龙 - 表格数据（模拟12条）
const anomalyList = [
  { name: '柿*****(3*****)', industry: '种植业与林业', price: 0.00, change: 20.03, speed: 0.00, volumeRatio: 1.01, darkFund: '5.33亿', darkFundColor: 'up', lightFund: '7.23亿', lightFundColor: 'up', signal: 'VIP', strongLine: 'VIP', anomalyCount: 8 },
  { name: '神*****(6*****)', industry: '化学制药', price: 0.00, change: 0.00, speed: 0.00, volumeRatio: 1.61, darkFund: '1.98亿', darkFundColor: 'up', lightFund: '8302.50万', lightFundColor: 'up', signal: 'VIP', strongLine: 'VIP', anomalyCount: 7 },
  { name: '透*****(3*****)', industry: '医疗器械', price: 0.00, change: 19.99, speed: 0.00, volumeRatio: 1.37, darkFund: '2.32亿', darkFundColor: 'up', lightFund: '1.41亿', lightFundColor: 'up', signal: 'VIP', strongLine: 'VIP', anomalyCount: 7 },
  { name: '药*****(0*****)', industry: '化学制药', price: 0.00, change: 0.53, speed: 0.36, volumeRatio: 3.01, darkFund: '-1265.20万', darkFundColor: 'down', lightFund: '-1.42亿', lightFundColor: 'down', signal: 'VIP', strongLine: 'VIP', anomalyCount: 6 },
  { name: '华*****(6*****)', industry: 'IT服务', price: 0.00, change: 9.97, speed: 0.00, volumeRatio: 3.74, darkFund: '1.73亿', darkFundColor: 'up', lightFund: '5.90亿', lightFundColor: 'up', signal: 'VIP', strongLine: 'VIP', anomalyCount: 6 },
  { name: '博*****(0*****)', industry: '影视院线', price: 0.00, change: 9.98, speed: 0.00, volumeRatio: 3.14, darkFund: '1.87亿', darkFundColor: 'up', lightFund: '1.82亿', lightFundColor: 'up', signal: 'VIP', strongLine: 'VIP', anomalyCount: 6 },
  { name: '常*****(0*****)', industry: 'IT服务', price: 0.00, change: 9.98, speed: 0.00, volumeRatio: 5.24, darkFund: '1.86亿', darkFundColor: 'up', lightFund: '4.65亿', lightFundColor: 'up', signal: 'VIP', strongLine: 'VIP', anomalyCount: 6 },
  { name: '江*****(3*****)', industry: '化学原料', price: 0.00, change: 20.00, speed: 0.00, volumeRatio: 1.13, darkFund: '2.31亿', darkFundColor: 'up', lightFund: '1.57亿', lightFundColor: 'up', signal: 'VIP', strongLine: 'VIP', anomalyCount: 6 },
  { name: '郑*****(6*****)', industry: '煤炭开采加工', price: 0.00, change: 9.98, speed: 0.00, volumeRatio: 2.22, darkFund: '3.63亿', darkFundColor: 'up', lightFund: '1.35亿', lightFundColor: 'up', signal: 'VIP', strongLine: 'VIP', anomalyCount: 5 },
  { name: '誉*****(0*****)', industry: '化学制药', price: 0.00, change: -0.46, speed: -0.23, volumeRatio: 0.85, darkFund: '4.10亿', darkFundColor: 'up', lightFund: '6283.40万', lightFundColor: 'up', signal: 'VIP', strongLine: 'VIP', anomalyCount: 5 },
  { name: '青*****(6*****)', industry: '造纸', price: 0.00, change: 9.97, speed: 0.00, volumeRatio: 2.01, darkFund: '5.84亿', darkFundColor: 'up', lightFund: '4.39亿', lightFundColor: 'up', signal: 'VIP', strongLine: 'VIP', anomalyCount: 5 },
  { name: '山*****(0*****)', industry: '汽车零部件', price: 0.00, change: 10.01, speed: 0.00, volumeRatio: 2.56, darkFund: '3.21亿', darkFundColor: 'up', lightFund: '2.18亿', lightFundColor: 'up', signal: 'VIP', strongLine: 'VIP', anomalyCount: 5 },
]

function formatChange(v) {
  return v > 0 ? `+${v.toFixed(2)}%` : `${v.toFixed(2)}%`
}
</script>

<template>
  <div class="utility-page">
    <!-- 页面头部 -->
    <header class="page-head">
      <div>
        <div class="brand-tag">QUANT TERMINAL</div>
        <h1 class="page-title">量化工具</h1>
        <div class="page-sub">管理今日关注、选股器、异常监控与策略数据</div>
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

    <!-- 今日关注 -->
    <div v-if="activeTab === 'watch'" class="tab-content">
      <div class="toolbar">
        <div class="search-group">
          <input v-model="watchKeyword" class="search-input" placeholder="搜股票名/代码" />
          <button class="btn-primary">搜索</button>
        </div>
        <div class="date-group">
          <span class="date-label">日期</span>
          <input type="date" v-model="watchDate" class="date-input" />
        </div>
        <div class="action-group">
          <button class="btn-outline">刷新</button>
          <button class="btn-outline">留列</button>
        </div>
      </div>

      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>关注日期</th>
              <th>代码</th>
              <th>行业</th>
              <th>推荐后涨幅</th>
              <th>现价</th>
              <th>涨速</th>
              <th>暗盘资金</th>
              <th>量比</th>
              <th>换手</th>
              <th>流通市值</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, idx) in watchList" :key="idx">
              <td class="text-muted">{{ item.date }}</td>
              <td class="code-cell">{{ item.code }}</td>
              <td>{{ item.industry }}</td>
              <td>
                <div class="num" :class="item.recChangePct >= 0 ? 'up' : 'down'">{{ item.recChange.toFixed(2) }}</div>
                <div class="num small" :class="item.recChangePct >= 0 ? 'up' : 'down'">{{ item.recChangePct >= 0 ? '+' : '' }}{{ item.recChangePct.toFixed(2) }}%</div>
              </td>
              <td>
                <div class="num" :class="item.pricePct >= 0 ? 'up' : 'down'">{{ item.price.toFixed(2) }}</div>
                <div class="num small" :class="item.pricePct >= 0 ? 'up' : 'down'">{{ item.pricePct >= 0 ? '+' : '' }}{{ item.pricePct.toFixed(2) }}%</div>
              </td>
              <td class="num" :class="item.speed >= 0 ? 'up' : 'down'">{{ item.speed >= 0 ? '+' : '' }}{{ item.speed.toFixed(2) }}%</td>
              <td class="text-muted">{{ item.darkFund }}</td>
              <td class="num">{{ item.volumeRatio.toFixed(2) }}</td>
              <td class="num">{{ item.turnover.toFixed(2) }}%</td>
              <td class="num">{{ item.marketCap }}</td>
              <td><button class="btn-detail">详情</button></td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="table-footer">共 {{ watchList.length }} 条</div>
    </div>

    <!-- 选股器 -->
    <div v-if="activeTab === 'stockpicker'" class="tab-content">
      <!-- 条件选择区 -->
      <div class="picker-panel">
        <div class="picker-sidebar">
          <button
            v-for="cat in pickerCategories"
            :key="cat.key"
            class="cat-btn"
            :class="{ active: activeCategory === cat.key }"
            @click="selectCategory(cat.key)"
          >
            {{ cat.label }}
          </button>
        </div>
        <div class="picker-tags">
          <template v-if="activeCategory === 'decision'">
            <button
              v-for="tag in decisionTags"
              :key="tag"
              class="tag-btn"
              :class="{ selected: selectedTags.includes(tag) }"
              @click="toggleTag(tag)"
            >
              {{ tag }}
            </button>
          </template>
          <template v-else>
            <div class="empty-tags">该分类条件开发中</div>
          </template>
        </div>
      </div>
      <div class="collapse-btn">^ 收起条件</div>

      <!-- 已选条件 -->
      <div class="selected-panel">
        <div class="panel-header">
          <span class="panel-title">已选条件</span>
          <button class="link-btn">修改</button>
        </div>
        <div class="selected-content" v-if="selectedTags.length === 0">
          请选择筛选条件
        </div>
        <div class="selected-tags" v-else>
          <span v-for="tag in selectedTags" :key="tag" class="selected-tag">{{ tag }}</span>
        </div>
      </div>

      <div class="selected-count">
        <span>已选 <span class="num">{{ selectedTags.length }}</span> 项</span>
        <button class="btn-primary small" :disabled="selectedTags.length === 0">确定</button>
      </div>

      <!-- 选股结果 -->
      <div class="result-panel">
        <div class="panel-header">
          <span class="panel-title">选股结果</span>
          <div class="result-actions">
            <span class="date-label">日期</span>
            <input type="date" value="2026-09-01" class="date-input small" />
            <button class="btn-outline small">刷新</button>
            <button class="btn-outline small">导出</button>
          </div>
        </div>
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>代码</th>
                <th>名称</th>
                <th>现价</th>
                <th>涨跌幅</th>
                <th>量比</th>
                <th>换手率</th>
                <th>行业</th>
                <th>信号</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, idx) in pickerResults" :key="idx">
                <td class="code-cell">{{ item.code }}</td>
                <td class="name-cell">{{ item.name }}</td>
                <td class="num">{{ item.price.toFixed(2) }}</td>
                <td class="num" :class="item.change >= 0 ? 'up' : 'down'">{{ formatChange(item.change) }}</td>
                <td class="num">{{ item.volumeRatio.toFixed(1) }}</td>
                <td class="num">{{ item.turnover.toFixed(1) }}%</td>
                <td>{{ item.industry }}</td>
                <td><span class="signal-tag">{{ item.signal }}</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 异动寻龙 -->
    <div v-if="activeTab === 'anomaly'" class="tab-content">
      <div class="anomaly-header">
        <span class="count-text">共 73 只</span>
        <button class="btn-outline">导出全部</button>
      </div>

      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>名称(代码)</th>
              <th>行业</th>
              <th>现价</th>
              <th>涨跌幅</th>
              <th>涨速</th>
              <th>量比</th>
              <th>暗盘资金</th>
              <th>明盘资金</th>
              <th>买卖信号</th>
              <th>强弱线</th>
              <th>异动次数</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, idx) in anomalyList" :key="idx">
              <td class="code-cell">{{ item.name }}</td>
              <td>{{ item.industry }}</td>
              <td class="num">{{ item.price.toFixed(2) }}</td>
              <td class="num" :class="item.change >= 0 ? 'up' : 'down'">{{ formatChange(item.change) }}</td>
              <td class="num" :class="item.speed >= 0 ? 'up' : 'down'">{{ item.speed >= 0 ? '+' : '' }}{{ item.speed.toFixed(2) }}%</td>
              <td class="num">{{ item.volumeRatio.toFixed(2) }}</td>
              <td class="num" :class="item.darkFundColor">{{ item.darkFund }}</td>
              <td class="num" :class="item.lightFundColor">{{ item.lightFund }}</td>
              <td><span class="vip-tag">{{ item.signal }}</span></td>
              <td><span class="vip-tag">{{ item.strongLine }}</span></td>
              <td class="num">{{ item.anomalyCount }}</td>
              <td><button class="btn-detail">详情</button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <footer class="page-foot">
      选股器与异动数据为演示数据，仅供参考，不构成投资建议
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
}
.page-sub {
  color: var(--text-3);
  font-size: 13px;
}

/* 标签导航 */
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
.tab-btn:hover {
  color: var(--text-2);
}
.tab-btn.active {
  color: var(--accent);
  border-bottom-color: var(--accent);
  font-weight: 600;
}

.tab-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 工具栏 */
.toolbar {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 14px 18px;
}
.search-group {
  display: flex;
  gap: 8px;
}
.search-input {
  width: 180px;
  padding: 8px 12px;
  background: var(--panel-2);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text);
  font-size: 13px;
  outline: none;
}
.search-input:focus {
  border-color: var(--accent);
}
.date-group {
  display: flex;
  align-items: center;
  gap: 8px;
}
.date-label {
  font-size: 13px;
  color: var(--text-3);
}
.date-input {
  padding: 8px 12px;
  background: var(--panel-2);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text);
  font-size: 13px;
  outline: none;
}
.date-input.small {
  padding: 6px 10px;
  font-size: 12px;
}
.action-group {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

/* 按钮 */
.btn-primary {
  padding: 8px 18px;
  background: var(--accent);
  border: none;
  border-radius: 8px;
  color: #fff;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.2s;
}
.btn-primary:hover {
  opacity: 0.9;
}
.btn-primary.small {
  padding: 6px 14px;
  font-size: 12px;
}
.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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
.btn-outline:hover {
  border-color: var(--accent);
  color: var(--accent);
}
.btn-outline.small {
  padding: 6px 12px;
  font-size: 12px;
}
.btn-detail {
  padding: 4px 12px;
  background: var(--panel-2);
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--text-2);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-detail:hover {
  border-color: var(--accent);
  color: var(--accent);
}
.link-btn {
  background: none;
  border: none;
  color: var(--accent);
  font-size: 13px;
  cursor: pointer;
}
.link-btn:hover {
  text-decoration: underline;
}

/* 表格 */
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
  padding: 12px 14px;
  border-bottom: 1px solid var(--border);
  color: var(--text-2);
  white-space: nowrap;
}
.data-table tbody tr:hover {
  background: var(--panel-2);
}
.data-table tbody tr:last-child td {
  border-bottom: none;
}
.code-cell {
  color: var(--accent);
  font-weight: 500;
}
.name-cell {
  font-weight: 500;
  color: var(--text);
}
.num {
  font-variant-numeric: tabular-nums;
  font-weight: 500;
}
.num.small {
  font-size: 11px;
  font-weight: 400;
}
.up {
  color: var(--up, #ef4444);
}
.down {
  color: var(--down, #22c55e);
}
.text-muted {
  color: var(--text-3);
}
.table-footer {
  font-size: 12px;
  color: var(--text-3);
  padding: 8px 4px;
}

/* 选股器 */
.picker-panel {
  display: flex;
  gap: 0;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 12px;
  overflow: hidden;
}
.picker-sidebar {
  width: 100px;
  flex-shrink: 0;
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
}
.cat-btn {
  padding: 16px 12px;
  background: none;
  border: none;
  color: var(--text-3);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
  border-left: 3px solid transparent;
}
.cat-btn:hover {
  color: var(--text-2);
  background: var(--panel-2);
}
.cat-btn.active {
  color: var(--text);
  background: var(--panel-2);
  border-left-color: var(--accent);
  font-weight: 600;
}
.picker-tags {
  flex: 1;
  padding: 16px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-content: flex-start;
}
.tag-btn {
  padding: 8px 16px;
  background: var(--panel-2);
  border: 1px solid var(--border);
  border-radius: 20px;
  color: var(--text-2);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}
.tag-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
}
.tag-btn.selected {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}
.empty-tags {
  color: var(--text-3);
  font-size: 13px;
  padding: 20px;
}
.collapse-btn {
  text-align: center;
  color: var(--text-3);
  font-size: 13px;
  padding: 8px;
  cursor: pointer;
}
.collapse-btn:hover {
  color: var(--text-2);
}

.selected-panel, .result-panel {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 16px 18px;
}
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.panel-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
}
.result-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.selected-content {
  color: var(--text-3);
  font-size: 13px;
  padding: 8px 0;
}
.selected-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.selected-tag {
  padding: 4px 12px;
  background: rgba(139, 92, 246, 0.15);
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: 16px;
  color: #8b5cf6;
  font-size: 12px;
}
.selected-count {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 4px;
  font-size: 13px;
  color: var(--text-3);
}
.signal-tag {
  padding: 3px 10px;
  background: rgba(59, 130, 246, 0.15);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 6px;
  color: #3b82f6;
  font-size: 12px;
}

/* 异动寻龙 */
.anomaly-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 4px;
}
.count-text {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
}
.vip-tag {
  padding: 3px 10px;
  background: rgba(245, 158, 11, 0.15);
  border: 1px solid rgba(245, 158, 11, 0.3);
  border-radius: 6px;
  color: #f59e0b;
  font-size: 12px;
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
