<script setup>
import { ref, computed } from 'vue'

// 顶部标签
const topTabs = [
  { key: 'fundflow', label: '资金流向' },
  { key: 'sentiment', label: '市场情绪' },
  { key: 'hotlist', label: '东财热榜' },
  { key: 'news7x24', label: '7x24' },
  { key: 'meeting', label: '财经会议' },
  { key: 'ranking', label: '榜单' },
]
const activeTopTab = ref('fundflow')

// 资金流向子标签
const fundSubTabs = [
  { key: 'industry', label: '行业' },
  { key: 'concept', label: '概念' },
  { key: 'stock', label: '个股' },
]
const activeFundSubTab = ref('industry')

// 时间范围
const timeRange = ref('today')

// ========== 模拟数据 ==========

// 统计卡片
const stats = ref({
  up: 0,
  flat: 0,
  down: 0,
  median: 0,
  up3: 0,
  down3: 0,
  mainNet: 0,
  mainNetYoy: 0,
  amount: 0,
  amountYoy: 0,
})

// 行业列表
const industries = ref([])

// 从API获取市场涨跌分布数据
async function fetchMarketBreadth() {
  try {
    const res = await fetch('/api/rankings/market-breadth')
    const data = await res.json()
    if (data.code === 0 && data.data) {
      const d = data.data
      stats.value.up = d.up || 0
      stats.value.flat = d.flat || 0
      stats.value.down = d.down || 0
      // 计算中位数和分档数据
      const dist = d.dist || {}
      let total = 0
      let sum = 0
      let up3 = 0
      let down3 = 0
      for (const [k, v] of Object.entries(dist)) {
        const kk = parseInt(k)
        total += v
        sum += kk * v
        if (kk >= 3) up3 += v
        if (kk <= -3) down3 += v
      }
      stats.value.median = total > 0 ? parseFloat((sum / total).toFixed(2)) : 0
      stats.value.up3 = up3
      stats.value.down3 = down3
    }
  } catch (e) {
    console.error('获取市场涨跌分布失败:', e)
  }
}

// 从API获取行业资金流数据
async function fetchIndustryFlow() {
  try {
    const res = await fetch('/api/rankings/industry-flow?limit=30')
    const data = await res.json()
    if (data.code === 0 && data.data && data.data.length > 0) {
      const colors = ['#ef4444', '#f97316', '#f59e0b', '#eab308', '#84cc16', '#22c55e', '#14b8a6', '#06b6d4', '#0ea5e9', '#3b82f6', '#6366f1', '#8b5cf6', '#a855f7', '#d946ef', '#ec4899', '#f43f5e']
      industries.value = data.data.map((item, idx) => ({
        name: item.name,
        net: parseFloat((item.net_inflow / 100000000).toFixed(2)), // 转换为亿元
        change: item.pct,
        count: 0,
        color: colors[idx % colors.length],
      }))
      // 计算主力净流入总和
      const totalNet = industries.value.reduce((sum, item) => sum + item.net, 0)
      stats.value.mainNet = parseFloat(totalNet.toFixed(2))
      // 更新选中的行业
      selectedIndustryNames.value = industries.value.slice(0, 10).map(i => i.name)
      // 更新趋势数据
      updateTrendData()
    } else {
      // API没有返回数据，使用静态模拟数据
      useMockIndustryData()
    }
  } catch (e) {
    console.error('获取行业资金流失败:', e)
    // API请求失败，使用静态模拟数据
    useMockIndustryData()
  }
}

// 使用静态模拟行业数据
function useMockIndustryData() {
  const mockData = [
    { name: '军工装备', net: 60.8, change: 1.2, color: '#ef4444' },
    { name: '电网设备', net: 39.3, change: 0.8, color: '#f97316' },
    { name: '汽车零部件', net: 30.9, change: 0.5, color: '#f59e0b' },
    { name: '建筑材料', net: 21.7, change: 0.3, color: '#eab308' },
    { name: '消费电子', net: 17.7, change: 0.2, color: '#84cc16' },
    { name: '通用设备', net: 17.6, change: 0.1, color: '#22c55e' },
    { name: '计算机设备', net: 16.8, change: 0.1, color: '#14b8a6' },
    { name: '军工电子', net: 8.8, change: -0.1, color: '#06b6d4' },
    { name: '医疗服务', net: 8.1, change: -0.2, color: '#0ea5e9' },
    { name: '银行', net: 8.0, change: -0.3, color: '#3b82f6' },
    { name: '元件', net: -24.7, change: -0.5, color: '#6366f1' },
    { name: '煤炭开采加工', net: -26.9, change: -0.6, color: '#8b5cf6' },
    { name: '种植业与林业', net: -27.2, change: -0.7, color: '#a855f7' },
    { name: '工业金属', net: -29.8, change: -0.8, color: '#d946ef' },
    { name: '电池', net: -30.0, change: -0.9, color: '#ec4899' },
    { name: '软件开发', net: -32.0, change: -1.0, color: '#f43f5e' },
  ]
  industries.value = mockData
  const totalNet = mockData.reduce((sum, item) => sum + item.net, 0)
  stats.value.mainNet = parseFloat(totalNet.toFixed(2))
  selectedIndustryNames.value = mockData.slice(0, 10).map(i => i.name)
  updateTrendData()
}

// 更新趋势数据
function updateTrendData() {
  trendData.value = industries.value.slice(0, 10).map(ind => ({
    name: ind.name,
    color: ind.color,
    net: ind.net,
    selected: true,
    points: genTrendData(ind.net, Math.abs(ind.net) * 0.08 + 2),
  }))
}

// 悬停提示相关
const hoverIndex = ref(-1)
const hoverData = ref([])
const hoverTime = ref('')
const hoverTooltipX = ref(0)
const hoverTooltipY = ref(0)

function handleChartMouseMove(event, type) {
  const svg = event.currentTarget
  const rect = svg.getBoundingClientRect()
  const x = event.clientX - rect.left
  const ratio = x / rect.width
  const index = Math.round(ratio * 48)
  if (index < 0 || index > 48) {
    hoverIndex.value = -1
    return
  }
  hoverIndex.value = index
  // 使用视口坐标，提示框跟随鼠标移动
  hoverTooltipX.value = event.clientX
  hoverTooltipY.value = event.clientY
  
  // 计算时间
  const totalMinutes = 240 // 4小时交易时间
  const minutes = Math.round((index / 48) * totalMinutes)
  const hour = 9 + Math.floor(minutes / 60)
  const minute = minutes % 60
  hoverTime.value = `${hour}:${minute.toString().padStart(2, '0')}`
  
  // 获取悬停数据
  const data = type === 'industry' ? selectedTrendData.value : selectedConceptTrendData.value
  hoverData.value = data.map(trend => ({
    name: trend.name,
    color: trend.color,
    value: trend.points[index] || 0,
  })).sort((a, b) => b.value - a.value)
}

// 页面加载时获取数据
fetchMarketBreadth()
fetchIndustryFlow()
fetchConceptFlow()
fetchStockFlow()

// 选中的行业（用数组代替Set）
const selectedIndustryNames = ref([])

function toggleIndustry(name) {
  const idx = selectedIndustryNames.value.indexOf(name)
  if (idx >= 0) {
    selectedIndustryNames.value.splice(idx, 1)
  } else {
    selectedIndustryNames.value.push(name)
  }
}

function selectAll() {
  selectedIndustryNames.value = industries.value.map(i => i.name)
}

function selectNone() {
  selectedIndustryNames.value = []
}

// 生成趋势数据
function genTrendData(baseNet, volatility) {
  const points = []
  let val = 0
  const steps = 48
  for (let i = 0; i <= steps; i++) {
    val += (Math.random() - 0.48) * volatility
    if (i === steps) val = baseNet
    points.push(val)
  }
  return points
}

// 趋势数据（预计算，避免在模板中调用）
const trendData = ref([])

// 选中的趋势数据
const selectedTrendData = computed(() => {
  return trendData.value.filter(t => selectedIndustryNames.value.includes(t.name))
})

// ========== 概念板块数据 ==========

// 概念统计
const conceptStats = ref({
  up: 0,
  flat: 0,
  down: 0,
  median: 0,
  up3: 0,
  down3: 0,
  mainNet: 0,
  mainNetYoy: 0,
  amount: 0,
  amountYoy: 0,
})

// 概念列表
const concepts = ref([])

// 从API获取概念资金流数据
async function fetchConceptFlow() {
  try {
    const res = await fetch('/api/rankings/concept-flow?limit=30')
    const data = await res.json()
    if (data.code === 0 && data.data && data.data.length > 0) {
      const colors = ['#ef4444', '#f97316', '#f59e0b', '#eab308', '#84cc16', '#22c55e', '#14b8a6', '#06b6d4', '#0ea5e9', '#3b82f6', '#6366f1', '#8b5cf6', '#a855f7', '#d946ef', '#ec4899', '#f43f5e']
      concepts.value = data.data.map((item, idx) => ({
        name: item.name,
        net: parseFloat((item.net_inflow / 100000000).toFixed(2)), // 转换为亿元
        color: colors[idx % colors.length],
      }))
      // 计算主力净流入总和
      const totalNet = concepts.value.reduce((sum, item) => sum + item.net, 0)
      conceptStats.value.mainNet = parseFloat(totalNet.toFixed(2))
      // 更新趋势数据
      updateConceptTrendData()
    } else {
      // API没有返回数据，使用静态模拟数据
      useMockConceptData()
    }
  } catch (e) {
    console.error('获取概念资金流失败:', e)
    // API请求失败，使用静态模拟数据
    useMockConceptData()
  }
}

// 使用静态模拟概念数据
function useMockConceptData() {
  const mockData = [
    { name: '军工', net: 94.4, color: '#ef4444' },
    { name: '军民融合', net: 61.0, color: '#f97316' },
    { name: '液冷服务器', net: 51.6, color: '#f59e0b' },
    { name: '无人机', net: 32.7, color: '#eab308' },
    { name: '并购重组概念', net: 27.8, color: '#84cc16' },
    { name: '大飞机', net: 27.7, color: '#22c55e' },
    { name: '汽车热管理', net: 24.9, color: '#14b8a6' },
    { name: '特高压', net: 24.7, color: '#06b6d4' },
    { name: '航天航空', net: 22.8, color: '#0ea5e9' },
    { name: '铜缆高速连接', net: 22.3, color: '#3b82f6' },
    { name: '贬值受益', net: -66.5, color: '#6366f1' },
    { name: '通信技术', net: -69.0, color: '#8b5cf6' },
    { name: 'CPO概念', net: -73.0, color: '#a855f7' },
    { name: 'AI应用', net: -78.9, color: '#d946ef' },
    { name: '互联网金融', net: -81.9, color: '#ec4899' },
    { name: '5G概念', net: -84.8, color: '#f43f5e' },
  ]
  concepts.value = mockData
  const totalNet = mockData.reduce((sum, item) => sum + item.net, 0)
  conceptStats.value.mainNet = parseFloat(totalNet.toFixed(2))
  updateConceptTrendData()
}

// 更新概念趋势数据
function updateConceptTrendData() {
  conceptTrendData.value = concepts.value.map(c => ({
    name: c.name,
    color: c.color,
    net: c.net,
    selected: true,
    points: genTrendData(c.net, Math.abs(c.net) * 0.08 + 2),
  }))
}

// 概念趋势数据
const conceptTrendData = ref([])

// 选中的概念趋势数据
const selectedConceptTrendData = computed(() => {
  return conceptTrendData.value.filter(t => t.selected)
})

// 概念图表范围
const conceptChartMin = computed(() => {
  let min = 0
  selectedConceptTrendData.value.forEach(t => {
    t.points.forEach(p => { if (p < min) min = p })
  })
  return Math.min(min, -100)
})
const conceptChartMax = computed(() => {
  let max = 0
  selectedConceptTrendData.value.forEach(t => {
    t.points.forEach(p => { if (p > max) max = p })
  })
  return Math.max(max, 100)
})

// 全选/全不选概念
function selectAllConcepts() {
  conceptTrendData.value.forEach(t => t.selected = true)
}
function selectNoneConcepts() {
  conceptTrendData.value.forEach(t => t.selected = false)
}

// 构建SVG路径
function buildConceptPath(points, width, height, min, max) {
  const range = max - min || 1
  const stepX = width / (points.length - 1)
  let d = ''
  points.forEach((p, i) => {
    const x = i * stepX
    const y = height - ((p - min) / range) * height
    d += (i === 0 ? 'M' : 'L') + x.toFixed(1) + ',' + y.toFixed(1) + ' '
  })
  return d
}

// 时间标签
const timeLabels = ['09:46', '10:10', '10:34', '10:58', '11:22', '13:00', '13:24', '13:48', '14:12', '14:36', '14:52']

// 生成SVG路径
function buildPath(points, width, height, minVal, maxVal) {
  if (!points || !points.length) return ''
  const stepX = width / (points.length - 1)
  const range = maxVal - minVal || 1
  return points.map((v, i) => {
    const x = i * stepX
    const y = height - ((v - minVal) / range) * height
    return (i === 0 ? 'M' : 'L') + x.toFixed(1) + ',' + y.toFixed(1)
  }).join(' ')
}

const chartMin = -90
const chartMax = 90

// ========== 个股资金流向 ==========
const stocks = ref([])

async function fetchStockFlow() {
  try {
    const res = await fetch('/api/rankings/stock-flow?limit=30')
    const data = await res.json()
    if (data.code === 0 && data.data && data.data.length > 0) {
      stocks.value = data.data.map((item) => ({
        code: item.code,
        name: item.name,
        net: parseFloat((item.net_inflow / 100000000).toFixed(2)), // 转换为亿元
        change: item.pct,
      }))
    }
  } catch (e) {
    console.error('获取个股资金流失败:', e)
  }
}

// ========== 涨停复盘 ==========
const limitUpStocks = ref([
  { name: '新赛股份', code: '600540', price: 6.73, change: 9.97, turnover: 37.50, volumeRatio: 9.29, main: '<1万', floatMv: '39亿', boards: 5, sector: '种植业与林业', reason: '农业政策利好' },
  { name: '竞业达', code: '003005', price: 20.00, change: 10.01, turnover: 3.27, volumeRatio: 0.50, main: '5781.81万', floatMv: '27亿', boards: 4, sector: 'IT服务', reason: '信创概念' },
  { name: '国芳集团', code: '601086', price: 11.10, change: 10.01, turnover: 0.87, volumeRatio: 0.33, main: '6478.70万', floatMv: '74亿', boards: 4, sector: '零售', reason: '消费复苏' },
  { name: '欢瑞世纪', code: '000892', price: 5.20, change: 9.94, turnover: 3.06, volumeRatio: 0.53, main: '9787.34万', floatMv: '37亿', boards: 3, sector: '影视院线', reason: '影视传媒' },
  { name: '集泰股份', code: '002909', price: 7.28, change: 9.97, turnover: 6.94, volumeRatio: 1.15, main: '8756.09万', floatMv: '28亿', boards: 3, sector: '化学制品', reason: '化工涨价' },
  { name: '大晟文化', code: '600892', price: 5.35, change: 10.08, turnover: 2.01, volumeRatio: 0.33, main: '3369.74万', floatMv: '30亿', boards: 3, sector: '游戏', reason: '游戏概念' },
  { name: '龙版传媒', code: '605577', price: 12.85, change: 10.02, turnover: 6.00, volumeRatio: 2.36, main: '7963.83万', floatMv: '57亿', boards: 3, sector: '文化传媒', reason: '传媒教育' },
  { name: '英力特', code: '000635', price: 7.94, change: 9.97, turnover: 2.81, volumeRatio: 4.19, main: '1089.40万', floatMv: '29亿', boards: 2, sector: '化学原料', reason: '化工板块' },
  { name: '恒宝股份', code: '002104', price: 13.51, change: 10.02, turnover: 22.99, volumeRatio: 2.20, main: '4.43亿', floatMv: '82亿', boards: 2, sector: '通信设备', reason: '数字货币' },
  { name: '香溢融通', code: '600830', price: 10.15, change: 9.97, turnover: 8.37, volumeRatio: 5.23, main: '9486.25万', floatMv: '46亿', boards: 2, sector: '多元金融', reason: '金融改革' },
  { name: '内蒙一机', code: '600967', price: 13.41, change: 10.01, turnover: 3.82, volumeRatio: 2.49, main: '3.85亿', floatMv: '228亿', boards: 2, sector: '军工装备', reason: '军工订单' },
  { name: '九牧王', code: '601566', price: 10.36, change: 9.98, turnover: 8.50, volumeRatio: 6.43, main: '1.52亿', floatMv: '60亿', boards: 2, sector: '服装家纺', reason: '消费升级' },
  { name: '小方制药', code: '603207', price: 27.94, change: 10.00, turnover: 24.16, volumeRatio: 4.45, main: '9046.56万', floatMv: '15亿', boards: 2, sector: '化学制药', reason: '医药创新' },
])

// ========== 连板高度分析图 ==========
const boardHeightData = ref([
  { date: '8/27', lianban: 16, shouban: 61, ban2: 8, ban3: 5, ban4: 1, ban5: 1, ban6: 1, ban7: 0, ban8: 0, ban9: 0 },
  { date: '8/28', lianban: 14, shouban: 55, ban2: 7, ban3: 4, ban4: 2, ban5: 1, ban6: 0, ban7: 0, ban8: 0, ban9: 0 },
  { date: '8/29', lianban: 18, shouban: 72, ban2: 9, ban3: 6, ban4: 2, ban5: 1, ban6: 0, ban7: 0, ban8: 0, ban9: 0 },
  { date: '8/30', lianban: 12, shouban: 48, ban2: 6, ban3: 3, ban4: 2, ban5: 1, ban6: 0, ban7: 0, ban8: 0, ban9: 0 },
  { date: '9/1', lianban: 15, shouban: 61, ban2: 8, ban3: 5, ban4: 1, ban5: 1, ban6: 1, ban7: 0, ban8: 0, ban9: 0 },
])

const boardHeightSeries = [
  { key: 'lianban', label: '连板数', color: '#ef4444', dashed: false },
  { key: 'shouban', label: '首板', color: '#3b82f6', dashed: true },
  { key: 'ban2', label: '2板', color: '#22c55e', dashed: true },
  { key: 'ban3', label: '3板', color: '#eab308', dashed: true },
  { key: 'ban4', label: '4板', color: '#f97316', dashed: true },
  { key: 'ban5', label: '5板', color: '#06b6d4', dashed: true },
  { key: 'ban6', label: '6板', color: '#14b8a6', dashed: true },
  { key: 'ban7', label: '7板', color: '#f97316', dashed: true },
  { key: 'ban8', label: '8板', color: '#8b5cf6', dashed: true },
  { key: 'ban9', label: '9板', color: '#ec4899', dashed: true },
]

// 连板高度分析图选择状态
const selectedBoardHeightKeys = ref(boardHeightSeries.map(s => s.key))
const selectedBoardHeightSeries = computed(() => {
  return boardHeightSeries.filter(s => selectedBoardHeightKeys.value.includes(s.key))
})

function selectAllBoardHeight() {
  selectedBoardHeightKeys.value = boardHeightSeries.map(s => s.key)
}

function selectNoneBoardHeight() {
  selectedBoardHeightKeys.value = []
}

function toggleBoardHeightSeries(key) {
  const idx = selectedBoardHeightKeys.value.indexOf(key)
  if (idx >= 0) {
    selectedBoardHeightKeys.value.splice(idx, 1)
  } else {
    selectedBoardHeightKeys.value.push(key)
  }
}

// 获取菱形点坐标
function getDiamondPoints(cx, cy, r) {
  return `${cx},${cy-r} ${cx+r},${cy} ${cx},${cy+r} ${cx-r},${cy}`
}

// ========== 涨停时刻表 ==========
const limitUpStats = ref({
  currentSealed: 51,
  everSealed: 76,
  dynamicBreakRate: 32.9,
  cumulativeBreakRate: 67.1,
  resealRate: 62.7,
  maxBoard: 5,
})

const boardFilters = [
  { key: 'all', label: '全部' },
  { key: '1', label: '1板 封36/曾61' },
  { key: '2', label: '2板 封8/曾8' },
  { key: '3', label: '3板 封4/曾4' },
  { key: '4', label: '4板 封2/曾2' },
  { key: '5', label: '5板 封1/曾1' },
]
const activeBoardFilter = ref('all')

const statusFilters = [
  { key: 'all', label: '全部' },
  { key: 'sealed', label: '已封板' },
  { key: 'broken', label: '已炸板' },
  { key: 'resealed', label: '已回封' },
]
const activeStatusFilter = ref('all')

const limitUpSchedule = ref([
  { name: '京粮控股', code: '000505', boards: 1, status: '已炸板', price: 7.09, change: -8.40, turnover: 18.53, volumeRatio: 1.53, main: '<1万', floatMv: '47亿', sealTime: '09:25:09', breakTime: '09:30:16', resealTime: '09:30:05', currentSeal: '--', maxSeal: '8394.35万', breakReseal: '1次/0次' },
  { name: '英力特', code: '000635', boards: 2, status: '已封板', price: 7.94, change: 9.97, turnover: 2.81, volumeRatio: 4.19, main: '1089.40万', floatMv: '29亿', sealTime: '09:25:09', breakTime: '--', resealTime: '--', currentSeal: '9329.50万', maxSeal: '1.20亿', breakReseal: '0次/0次' },
  { name: '欢瑞世纪', code: '000892', boards: 3, status: '已封板', price: 5.20, change: 9.94, turnover: 3.06, volumeRatio: 0.53, main: '9787.34万', floatMv: '37亿', sealTime: '09:25:09', breakTime: '--', resealTime: '--', currentSeal: '3.95亿', maxSeal: '7.98亿', breakReseal: '0次/0次' },
  { name: '华昌化工', code: '002274', boards: 1, status: '已回封', price: 7.12, change: 10.05, turnover: 9.90, volumeRatio: 0.00, main: '9898.40万', floatMv: '67亿', sealTime: '09:25:09', breakTime: '09:39:47', resealTime: '15:39:51', currentSeal: '8206.58万', maxSeal: '2.56亿', breakReseal: '2次/2次' },
  { name: '金正大', code: '002470', boards: 1, status: '已炸板', price: 2.17, change: -6.47, turnover: 12.39, volumeRatio: 2.23, main: '<1万', floatMv: '71亿', sealTime: '09:25:09', breakTime: '09:25:20', resealTime: '09:25:09', currentSeal: '--', maxSeal: '1979.21万', breakReseal: '1次/0次' },
  { name: '山东墨龙', code: '002490', boards: 1, status: '已炸板', price: 8.69, change: 3.95, turnover: 23.33, volumeRatio: 2.39, main: '1332.83万', floatMv: '47亿', sealTime: '09:25:09', breakTime: '09:31:47', resealTime: '09:31:36', currentSeal: '--', maxSeal: '4.48亿', breakReseal: '1次/0次' },
  { name: '福建金森', code: '002679', boards: 1, status: '已炸板', price: 12.24, change: -5.19, turnover: 19.56, volumeRatio: 7.22, main: '<1万', floatMv: '29亿', sealTime: '09:25:09', breakTime: '09:32:10', resealTime: '09:31:58', currentSeal: '--', maxSeal: '3.78亿', breakReseal: '1次/0次' },
  { name: '百洋股份', code: '002696', boards: 1, status: '已炸板', price: 6.68, change: -8.24, turnover: 16.69, volumeRatio: 2.95, main: '<1万', floatMv: '22亿', sealTime: '09:25:09', breakTime: '09:25:20', resealTime: '09:25:09', currentSeal: '--', maxSeal: '2061.85万', breakReseal: '1次/0次' },
  { name: '集泰股份', code: '002909', boards: 3, status: '已封板', price: 7.28, change: 9.97, turnover: 6.94, volumeRatio: 1.15, main: '8756.09万', floatMv: '28亿', sealTime: '09:25:09', breakTime: '--', resealTime: '--', currentSeal: '7441.69万', maxSeal: '2.07亿', breakReseal: '0次/0次' },
  { name: '竞业达', code: '003005', boards: 4, status: '已封板', price: 20.00, change: 10.01, turnover: 3.27, volumeRatio: 0.50, main: '5781.81万', floatMv: '27亿', sealTime: '09:25:09', breakTime: '--', resealTime: '--', currentSeal: '1.81亿', maxSeal: '2.95亿', breakReseal: '0次/0次' },
  { name: '郑州煤电', code: '600121', boards: 1, status: '已炸板', price: 5.30, change: -1.85, turnover: 27.82, volumeRatio: 2.60, main: '<1万', floatMv: '65亿', sealTime: '09:25:09', breakTime: '09:35:48', resealTime: '09:35:37', currentSeal: '--', maxSeal: '4.91亿', breakReseal: '1次/0次' },
  { name: '新赛股份', code: '600540', boards: 5, status: '已回封', price: 6.73, change: 9.97, turnover: 37.50, volumeRatio: 9.29, main: '<1万', floatMv: '39亿', sealTime: '09:25:09', breakTime: '14:56:35', resealTime: '15:39:51', currentSeal: '9.68万', maxSeal: '1.57亿', breakReseal: '7次/7次' },
  { name: '云煤能源', code: '600792', boards: 1, status: '已炸板', price: 4.30, change: -2.71, turnover: 12.05, volumeRatio: 4.41, main: '<1万', floatMv: '48亿', sealTime: '09:25:09', breakTime: '09:37:19', resealTime: '09:37:07', currentSeal: '--', maxSeal: '3.50亿', breakReseal: '2次/1次' },
  { name: '茂业商业', code: '600828', boards: 2, status: '已回封', price: 4.81, change: 10.07, turnover: 2.66, volumeRatio: 3.20, main: '6425.93万', floatMv: '83亿', sealTime: '09:25:09', breakTime: '09:43:01', resealTime: '15:39:51', currentSeal: '6394.22万', maxSeal: '1.48亿', breakReseal: '1次/1次' },
  { name: '大晟文化', code: '600892', boards: 3, status: '已封板', price: 5.35, change: 10.08, turnover: 2.01, volumeRatio: 0.33, main: '3369.74万', floatMv: '30亿', sealTime: '09:25:09', breakTime: '--', resealTime: '--', currentSeal: '1.34亿', maxSeal: '2.77亿', breakReseal: '0次/0次' },
])

// 分页
const currentPage = ref(1)
const pageSize = ref(15)
const totalPages = computed(() => Math.ceil(limitUpSchedule.value.length / pageSize.value))
const pagedSchedule = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return limitUpSchedule.value.slice(start, start + pageSize.value)
})

function prevPage() {
  if (currentPage.value > 1) currentPage.value--
}
function nextPage() {
  if (currentPage.value < totalPages.value) currentPage.value++
}
function goToPage(p) {
  currentPage.value = p
}

// 状态颜色
function statusClass(status) {
  if (status === '已封板') return 'up'
  if (status === '已炸板') return 'down'
  return 'flat'
}

// ========== 市场情绪页面 ==========

// 分指数恐贪指数
const sentimentIndices = ref([
  { name: '全市场', value: 60.3, color: '#f97316' },
  { name: '中证500', value: 45.7, color: '#a3a33d' },
  { name: '科创50', value: 28.8, color: '#22c55e' },
  { name: '创业板指', value: 31.1, color: '#22c55e' },
  { name: '上证指数', value: 58.5, color: '#a16207' },
])

// 当前选中的指数
const selectedSentimentIndex = ref('全市场')

// 子标签
const sentimentSubTabs = [
  { key: 'overview', label: '概览' },
  { key: 'daily', label: '日线' },
]
const activeSentimentSubTab = ref('overview')

// 恐贪指数状态
function getSentimentStatus(value) {
  if (value < 20) return { label: '极度恐惧', color: '#22c55e' }
  if (value < 40) return { label: '恐惧', color: '#84cc16' }
  if (value < 60) return { label: '中立', color: '#eab308' }
  if (value < 80) return { label: '贪婪', color: '#f97316' }
  return { label: '极度贪婪', color: '#ef4444' }
}

const currentSentiment = computed(() => {
  const idx = sentimentIndices.value.find(i => i.name === selectedSentimentIndex.value)
  return idx || sentimentIndices.value[0]
})

const currentStatus = computed(() => getSentimentStatus(currentSentiment.value.value))

// 七个维度指标
const sentimentDimensions = ref([
  { name: '市场动量', value: 50.1, color: '#eab308' },
  { name: '股价强度', value: 45.9, color: '#eab308' },
  { name: '市场宽度', value: 23.8, color: '#22c55e' },
  { name: '看跌期权', value: 83.6, color: '#ef4444' },
  { name: '波动率', value: 94.8, color: '#ef4444' },
  { name: '避险需求', value: 61.6, color: '#f97316' },
  { name: '杠杆', value: 62.9, color: '#f97316' },
])

// 市场统计
const marketStats = ref({
  up: 1189,
  flat: 134,
  down: 3798,
  limitUp: 51,
  limitDown: 10,
  total: 5121,
})

// 两融余额
const marginTradingRange = ref('1y')
const marginTradingRanges = [
  { key: '60d', label: '近60日' },
  { key: '1y', label: '近1年' },
  { key: 'all', label: '全部' },
]

const marginTradingStats = ref({
  total: 26665,
  totalChange: 17.7,
  financing: 26369,
  financingRatio: 2.61,
  netBuy: 14.2,
  dataDate: '2026-09-01',
})

// 两融余额趋势数据
const marginTradingTrend = ref([
  { date: '06-09', value: 28800 },
  { date: '06-16', value: 29200 },
  { date: '06-24', value: 30100 },
  { date: '07-01', value: 30300 },
  { date: '07-08', value: 29800 },
  { date: '07-15', value: 29200 },
  { date: '07-22', value: 27200 },
  { date: '07-29', value: 26800 },
  { date: '08-05', value: 26000 },
  { date: '08-12', value: 26400 },
  { date: '08-19', value: 26700 },
  { date: '08-26', value: 26500 },
  { date: '09-01', value: 26665 },
])

// 生成两融余额SVG路径
function buildMarginPath(points, width, height, minVal, maxVal) {
  if (!points || !points.length) return ''
  const stepX = width / (points.length - 1)
  const range = maxVal - minVal || 1
  return points.map((p, i) => {
    const x = i * stepX
    const y = height - ((p.value - minVal) / range) * height
    return (i === 0 ? 'M' : 'L') + x.toFixed(1) + ',' + y.toFixed(1)
  }).join(' ')
}

function buildMarginAreaPath(points, width, height, minVal, maxVal) {
  const linePath = buildMarginPath(points, width, height, minVal, maxVal)
  if (!linePath) return ''
  const lastX = width
  const lastY = height
  return linePath + ` L${lastX},${lastY} L0,${lastY} Z`
}

// ========== 东财热榜页面 ==========

// 热榜子标签
const hotlistSubTabs = [
  { key: 'popular', label: '人气榜', tag: '热' },
  { key: 'soaring', label: '飙升榜', tag: '升' },
]
const activeHotlistSubTab = ref('popular')

// 市场选择
const marketTabs = [
  { key: 'a', label: 'A股' },
  { key: 'hk', label: '港股' },
  { key: 'us', label: '美股' },
]
const activeMarket = ref('a')

// 人气榜数据
const popularList = ref([
  { rank: 1, change: 127, changeType: 'up', code: '688836', name: '宇树科技-W', price: 546.02, changePct: -4.39, newFans: 15.52, oldFans: 84.48, hasTag: true },
  { rank: 2, change: 1132, changeType: 'up', code: '603618', name: '杭电股份', price: 37.22, changePct: 9.99, newFans: 19.97, oldFans: 80.03, hasTag: false },
  { rank: 3, change: 1157, changeType: 'up', code: '601606', name: '长城军工', price: 36.62, changePct: 10.00, newFans: 53.17, oldFans: 46.83, hasTag: false },
  { rank: 4, change: 129, changeType: 'up', code: '600967', name: '内蒙一机', price: 13.41, changePct: 10.01, newFans: 83.73, oldFans: 16.27, hasTag: false },
  { rank: 5, change: 1101, changeType: 'up', code: '600869', name: '远东股份', price: 19.5, changePct: 9.98, newFans: 45.92, oldFans: 54.08, hasTag: false },
  { rank: 6, change: 5, changeType: 'down', code: '600127', name: '金健米业', price: 12.4, changePct: -6.34, newFans: 36.76, oldFans: 63.24, hasTag: false },
  { rank: 7, change: 88, changeType: 'up', code: '002297', name: '博云新材', price: 20, changePct: 10.01, newFans: 57.58, oldFans: 42.42, hasTag: false },
  { rank: 8, change: 116, changeType: 'up', code: '002104', name: '恒宝股份', price: 13.51, changePct: 10.02, newFans: 50.23, oldFans: 49.77, hasTag: true },
  { rank: 9, change: 11, changeType: 'down', code: '300413', name: '芒果超媒', price: 20.52, changePct: 0.69, newFans: 94.29, oldFans: 5.71, hasTag: true },
  { rank: 10, change: 193, changeType: 'up', code: '002886', name: '沃特股份', price: 30.84, changePct: 9.99, newFans: 59.99, oldFans: 40.01, hasTag: false },
  { rank: 11, change: 133, changeType: 'up', code: '600487', name: '亨通光电', price: 66.9, changePct: -0.65, newFans: 10.85, oldFans: 89.15, hasTag: true },
  { rank: 12, change: 10, changeType: 'down', code: '000560', name: '我爱我家', price: 3.18, changePct: -0.31, newFans: 77.64, oldFans: 22.36, hasTag: false },
  { rank: 13, change: 16, changeType: 'down', code: '600103', name: '青山纸业', price: 3.93, changePct: -6.21, newFans: 35.52, oldFans: 64.48, hasTag: false },
  { rank: 14, change: 7, changeType: 'down', code: '600371', name: '万向德农', price: 14.42, changePct: 3.30, newFans: 57.69, oldFans: 42.31, hasTag: true },
  { rank: 15, change: 104, changeType: 'up', code: '600172', name: '黄河旋风', price: 14.75, changePct: 0.75, newFans: 23.20, oldFans: 76.80, hasTag: false },
])

// 飙升榜数据
const soaringList = ref([
  { rank: 134, change: 5277, changeType: 'up', code: '603701', name: '德宏股份', price: 21.23, changePct: 10.00, newFans: 88.27, oldFans: 11.73, hasTag: false },
  { rank: 150, change: 5149, changeType: 'up', code: '603665', name: '康隆达', price: 22.56, changePct: 10.00, newFans: 85.68, oldFans: 14.32, hasTag: false },
  { rank: 623, change: 4896, changeType: 'up', code: '688156', name: '路德科技', price: 22.21, changePct: 12.51, newFans: 88.07, oldFans: 11.93, hasTag: false },
  { rank: 445, change: 4878, changeType: 'up', code: '920222', name: '益坤电气', price: 28.77, changePct: 17.24, newFans: 64.16, oldFans: 35.84, hasTag: false },
  { rank: 266, change: 4873, changeType: 'up', code: '300950', name: '德固特', price: 19.28, changePct: 10.30, newFans: 86.58, oldFans: 13.42, hasTag: false },
  { rank: 118, change: 4861, changeType: 'up', code: '001278', name: '一彬科技', price: 18.22, changePct: 10.02, newFans: 90.06, oldFans: 9.94, hasTag: false },
])

// 当前热榜数据
const currentHotlist = computed(() => {
  return activeHotlistSubTab.value === 'popular' ? popularList.value : soaringList.value
})

// 分页
const hotlistCurrentPage = ref(1)
const hotlistPageSize = 20
const hotlistTotalPages = 5

function goToHotlistPage(p) {
  hotlistCurrentPage.value = p
}

// 排名颜色
function getRankColor(rank) {
  if (rank === 1) return '#f97316'
  if (rank === 2) return '#fb923c'
  if (rank === 3) return '#3b82f6'
  return '#475569'
}

// ========== 7x24页面 ==========

// 新闻列表
const newsList = ref([])

// 从API获取7x24新闻数据
async function fetchNews7x24() {
  try {
    const res = await fetch('/api/news/7x24?page=1&page_size=20')
    const data = await res.json()
    if (data.code === 0 && data.data) {
      newsList.value = data.data.map((item, idx) => ({
        id: idx + 1,
        title: item.title,
        source: item.source,
        time: item.time,
        content: item.content,
      }))
    }
  } catch (e) {
    console.error('获取7x24新闻失败:', e)
  }
}

// 页面加载时获取数据
fetchNews7x24()

// 分页
const newsCurrentPage = ref(1)
const newsTotalPages = 5

function goToNewsPage(p) {
  newsCurrentPage.value = p
}
function prevNewsPage() {
  if (newsCurrentPage.value > 1) newsCurrentPage.value--
}
function nextNewsPage() {
  if (newsCurrentPage.value < newsTotalPages) newsCurrentPage.value++
}

// ========== 财经会议页面 ==========

// 会议统计
const meetingStats = ref({
  total: 36,
  thisMonth: 32,
})

// 筛选条件
const meetingTimeFilter = ref('全部时间')
const meetingTypeFilter = ref('全部类型')
const meetingCityFilter = ref('全部城市')

// 会议列表
const meetingList = ref([
  {
    id: 1,
    title: '习近平将出席2026年上海合作组织峰会并对吉尔吉斯斯坦、埃及进行国事访问',
    type: '其他会议',
    city: '比什凯克',
    content: '8月30日至9月3日,国家主席习近平将出席在比什凯克举行的2026年上海合作组织峰会,并应吉尔吉斯斯坦总统扎帕罗夫、埃及总统塞西邀请对两国进行国事访问。',
    startTime: '2026-08-30 00:00:00',
    endTime: '2026-09-03 00:00:00',
  },
  {
    id: 2,
    title: '第十四届半导体设备材料及核心部件展(CSEAC-2026)',
    type: '行业会议',
    city: '无锡市',
    content: '第十四届半导体设备材料及核心部件展(CSEAC2026)是半导体设备材料及核心部件领域的展览会,于2026年8月31日至9月2日在无锡太湖国际博览中心举办。展览规划超7万平方米,集结1300余家国内外企业,覆盖晶圆制造设备、封测设备、核心部件及材料等领域,海外展商占比达16%。同期举办20余场论坛,包括核心论坛"2026半导体设备年会"及6场专题',
    startTime: '2026-08-31 00:00:00',
    endTime: '2026-09-02 00:00:00',
  },
  {
    id: 3,
    title: '2026第二届上海AI应用生态大会',
    type: '行业会议',
    city: '上海市',
    content: '为贯彻落实国家人工智能产业高质量发展的相关部署,聚焦AI技术规模化应用与实体经济深度融合,2026第二届上海AI应用生态大会定于9月21日至22日在上海龙之梦万丽酒店举办。大会由上海现代服务业联合会主办,立足长三角、辐射全国,整合技术交流、成果展示、供需对接与资本赋能等功能模块,致力于搭建一个能够切实推动产业合作的AI应用生态平台。',
    startTime: '2026-09-21 00:00:00',
    endTime: '2026-09-22 00:00:00',
  },
  {
    id: 4,
    title: 'ADEX2026第六届阿塞拜疆(巴库)国际防务展',
    type: '行业会议',
    city: '广州市',
    content: '',
    startTime: '2026-09-22 00:00:00',
    endTime: '2026-09-24 00:00:00',
  },
  {
    id: 5,
    title: '第48届世界技能大赛',
    type: '行业会议',
    city: '上海市',
    content: '第48届世界技能大赛是由世界技能组织主办的国际职业技能赛事,于2026年9月22日至27日在中国上海举办。该赛事被誉为"世界技能奥林匹克",每两年举办一届,中国上海于2022年9月经世界技能组织全体成员大会投票获得主办权。赛事预计使用国家会展中心12个馆作为主要场馆,总面积约36万平方米,划分为综合赛事、配套服务和国际会议中心3个区域。',
    startTime: '2026-09-22 00:00:00',
    endTime: '2026-09-27 00:00:00',
  },
  {
    id: 6,
    title: '2026骁龙峰会',
    type: '高峰论坛',
    city: '',
    content: '高通正式官宣2026骁龙峰会举办日程,线下活动将于夏威夷茂宜岛当地时间9月22日至24日举行,对应北京时间9月23日至25日。本届峰会最大核心看点,是高通首款2nm移动旗舰芯片骁龙8 Elite Gen6系列,该芯片将成为安卓行业首款规模化商用2nm手机处理器,下半年安卓高端旗舰市场格局将迎来重大更新。',
    startTime: '2026-09-23 00:00:00',
    endTime: '2026-09-25 00:00:00',
  },
])

// ========== 榜单页面 ==========

// 子标签：行业/个股
const rankingSubTabs = [
  { key: 'industry', label: '行业' },
  { key: 'stock', label: '个股' },
]
const activeRankingSubTab = ref('industry')

// 行业排序类型
const industrySortTypes = [
  { key: 'change', label: '涨跌幅' },
  { key: 'amount', label: '成交额' },
  { key: 'netflow', label: '净流入' },
  { key: 'volume', label: '成交量' },
]
const activeIndustrySort = ref('change')

// 个股排序类型
const stockSortTypes = [
  { key: 'gainers', label: '涨幅' },
  { key: 'losers', label: '跌幅' },
  { key: 'upSpeed', label: '涨速' },
  { key: 'downSpeed', label: '跌速' },
  { key: 'amount', label: '成交' },
  { key: 'netflow', label: '净流入' },
  { key: '10dChange', label: '10日涨幅' },
  { key: '10dDeviation', label: '10日偏离' },
  { key: 'darkInflow', label: '暗盘流入' },
  { key: 'darkOutflow', label: '暗盘流出' },
  { key: 'brightInDarkOut', label: '明流暗出' },
  { key: 'priceDownDarkIn', label: '价跌暗入' },
]
const activeStockSort = ref('gainers')

// 筛选展开状态
const showFilter = ref(true)

// 日期选择器
const showDatePicker = ref(false)
const selectedDate = ref('')
const currentMonth = ref(new Date())

// 生成日历数据
function getCalendarDays(year, month) {
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)
  const startDay = firstDay.getDay()
  const daysInMonth = lastDay.getDate()
  const days = []
  
  // 上个月的日期
  const prevMonthLastDay = new Date(year, month, 0).getDate()
  for (let i = startDay - 1; i >= 0; i--) {
    days.push({ day: prevMonthLastDay - i, isCurrentMonth: false, date: new Date(year, month - 1, prevMonthLastDay - i) })
  }
  
  // 当月的日期
  for (let i = 1; i <= daysInMonth; i++) {
    days.push({ day: i, isCurrentMonth: true, date: new Date(year, month, i) })
  }
  
  // 下个月的日期
  const remainingDays = 42 - days.length
  for (let i = 1; i <= remainingDays; i++) {
    days.push({ day: i, isCurrentMonth: false, date: new Date(year, month + 1, i) })
  }
  
  return days
}

const calendarDays = computed(() => {
  const year = currentMonth.value.getFullYear()
  const month = currentMonth.value.getMonth()
  return getCalendarDays(year, month)
})

const monthTitle = computed(() => {
  const year = currentMonth.value.getFullYear()
  const month = currentMonth.value.getMonth() + 1
  return `${year}年${month}月`
})

function isFutureDate(date) {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return date > today
}

function isSelectedDate(date) {
  if (!selectedDate.value) return false
  const dateStr = formatDate(date)
  return dateStr === selectedDate.value
}

function formatDate(date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function selectDate(day) {
  if (isFutureDate(day.date)) return
  selectedDate.value = formatDate(day.date)
  showDatePicker.value = false
}

function clearDate() {
  selectedDate.value = ''
}

function prevMonth() {
  currentMonth.value = new Date(currentMonth.value.getFullYear(), currentMonth.value.getMonth() - 1, 1)
}

function nextMonth() {
  currentMonth.value = new Date(currentMonth.value.getFullYear(), currentMonth.value.getMonth() + 1, 1)
}

// 行业板块数据
const industryRankingList = ref([
  { rank: 1, name: '地面兵装II', change: 5.89, amount: 1416.30, netflow: 12.81, volume: 0, count: 12, floatMv: '1416.30亿' },
  { rank: 2, name: '旅游及酒店', change: 3.56, amount: 57.00, netflow: 0, volume: 0, count: 2, floatMv: '0' },
  { rank: 3, name: '电机', change: 1.28, amount: 107.00, netflow: 0, volume: 0, count: 3, floatMv: '0' },
  { rank: 4, name: 'IT服务', change: 1.22, amount: 291.00, netflow: 0, volume: 0, count: 5, floatMv: '0' },
  { rank: 5, name: '厨卫电器', change: 1.15, amount: 477.10, netflow: 0, volume: 0, count: 9, floatMv: '0' },
  { rank: 6, name: '半导体', change: -1.50, amount: 1783.27, netflow: 0, volume: 0, count: 179, floatMv: '7.95万亿' },
  { rank: 7, name: '通信设备', change: -0.59, amount: 1270.50, netflow: 0, volume: 0, count: 87, floatMv: '3.60万亿' },
  { rank: 8, name: '元件', change: -1.45, amount: 782.34, netflow: 0, volume: 0, count: 62, floatMv: '2.69万亿' },
  { rank: 9, name: '通用设备', change: -0.35, amount: 590.03, netflow: 0, volume: 0, count: 220, floatMv: '1.61万亿' },
  { rank: 10, name: '消费电子', change: 0.32, amount: 551.55, netflow: 8.64, volume: 0, count: 90, floatMv: '3.12万亿' },
])

// 个股数据
const stockRankingList = ref([
  { rank: 1, name: '*ST清越', code: '688496', change: -2.15, price: 0.91, floatMv: '2.20亿', amount: 0, netflow: 0 },
  { rank: 2, name: 'ST如意', code: '002193', change: -0.92, price: 5.38, floatMv: '14.10亿', amount: 0, netflow: 0 },
  { rank: 3, name: 'ST云城', code: '600239', change: -0.69, price: 1.43, floatMv: '23.00亿', amount: 0, netflow: 0 },
  { rank: 4, name: 'ST中装', code: '002822', change: -0.96, price: 3.00, floatMv: '33.00亿', amount: 0, netflow: 0 },
  { rank: 5, name: '宇树科技-W', code: '688836', change: -4.39, price: 546.02, floatMv: '0', amount: 0, netflow: 0 },
  { rank: 6, name: '杭电股份', code: '603618', change: 9.99, price: 37.22, floatMv: '0', amount: 0, netflow: 0 },
  { rank: 7, name: '长城军工', code: '601606', change: 10.00, price: 36.62, floatMv: '0', amount: 0, netflow: 0 },
  { rank: 8, name: '内蒙一机', code: '600967', change: 10.01, price: 13.41, floatMv: '0', amount: 0, netflow: 0 },
  { rank: 9, name: '远东股份', code: '600869', change: 9.98, price: 19.5, floatMv: '0', amount: 0, netflow: 0 },
  { rank: 10, name: '金健米业', code: '600127', change: -6.34, price: 12.4, floatMv: '0', amount: 0, netflow: 0 },
])

// 刷新
const lastUpdate = ref('2026-09-02')
function refresh() {
  lastUpdate.value = new Date().toLocaleDateString('zh-CN')
}
</script>

<template>
  <div class="rankings-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="title-en">MARKET DATA TERMINAL</div>
      <h1 class="title-cn">行情中枢</h1>
      <p class="title-desc">追踪指数、行业、热榜、资讯与资金趋势。</p>
    </div>

    <!-- 顶部标签导航 -->
    <div class="top-tabs">
      <button
        v-for="tab in topTabs"
        :key="tab.key"
        class="top-tab-btn"
        :class="{ active: activeTopTab === tab.key }"
        @click="activeTopTab = tab.key"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- 资金流向内容 -->
    <div v-if="activeTopTab === 'fundflow'" class="fundflow-view">
      <!-- 子标签 -->
      <div class="sub-tabs">
        <button
          v-for="tab in fundSubTabs"
          :key="tab.key"
          class="sub-tab-btn"
          :class="{ active: activeFundSubTab === tab.key }"
          @click="activeFundSubTab = tab.key"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- 行业内容 -->
      <div v-if="activeFundSubTab === 'industry'">
      <!-- 统计信息栏 -->
      <div class="info-bar">
        <div class="info-left">
          <span class="info-count">共 {{ industries.length }} 个板块</span>
          <span class="info-time">更新于 {{ lastUpdate }}</span>
        </div>
        <div class="info-right">
          <select v-model="timeRange" class="time-select">
            <option value="today">今天</option>
            <option value="yesterday">昨天</option>
            <option value="week">本周</option>
          </select>
          <button class="refresh-btn" @click="refresh">
            <span class="refresh-icon">↻</span> 刷新
          </button>
        </div>
      </div>

      <!-- 三个统计卡片 -->
      <div class="stats-grid">
        <div class="stats-card">
          <div class="stats-label">涨跌分布</div>
          <div class="stats-value">
            <span class="up">{{ stats.up }}</span>
            <span class="dim">:</span>
            <span class="flat">{{ stats.flat }}</span>
            <span class="dim">:</span>
            <span class="down">{{ stats.down }}</span>
          </div>
          <div class="stats-sub">
            中位 <span :class="stats.median >= 0 ? 'up' : 'down'">{{ stats.median }}%</span>
            <span class="dim"> | </span>
            ≥3% <span class="up">{{ stats.up3 }}</span>
            <span class="dim"> | </span>
            ≤-3% <span class="down">{{ stats.down3 }}</span>
          </div>
        </div>
        <div class="stats-card">
          <div class="stats-label">主力净流入</div>
          <div class="stats-value" :class="stats.mainNet >= 0 ? 'up' : 'down'">
            {{ stats.mainNet >= 0 ? '+' : '' }}{{ stats.mainNet }}亿
          </div>
          <div class="stats-sub">
            同比昨日 <span :class="stats.mainNetYoy >= 0 ? 'up' : 'down'">{{ stats.mainNetYoy >= 0 ? '+' : '' }}{{ stats.mainNetYoy }}亿</span>
          </div>
        </div>
        <div class="stats-card">
          <div class="stats-label">成交额</div>
          <div class="stats-value">{{ stats.amount }}亿</div>
          <div class="stats-sub">
            同比昨日 <span :class="stats.amountYoy >= 0 ? 'up' : 'down'">{{ stats.amountYoy >= 0 ? '+' : '' }}{{ stats.amountYoy }}亿</span>
          </div>
        </div>
      </div>

      <!-- 净流入折线图 -->
      <div class="chart-panel">
        <div class="chart-header">
          <span class="chart-title">净流入（亿元）</span>
          <div class="chart-actions">
            <button class="action-btn" @click="selectAll">全选</button>
            <button class="action-btn action-btn-secondary" @click="selectNone">全不选</button>
          </div>
        </div>
        <div class="chart-body">
          <div class="chart-container" @mouseleave="hoverIndex = -1">
            <!-- Y轴标签 -->
            <div class="y-axis-labels">
              <span>{{ chartMax }}</span>
              <span>{{ Math.round(chartMax * 0.67) }}</span>
              <span>{{ Math.round(chartMax * 0.33) }}</span>
              <span>0</span>
              <span>{{ Math.round(chartMin * 0.33) }}</span>
              <span>{{ Math.round(chartMin * 0.67) }}</span>
              <span>{{ chartMin }}</span>
            </div>
            <svg viewBox="0 0 1000 350" class="trend-chart" preserveAspectRatio="none" @mousemove="handleChartMouseMove($event, 'industry')">
              <!-- 网格线 -->
              <g stroke="rgba(255,255,255,0.08)" stroke-width="1">
                <line x1="0" y1="0" x2="1000" y2="0" />
                <line x1="0" y1="58.3" x2="1000" y2="58.3" />
                <line x1="0" y1="116.7" x2="1000" y2="116.7" />
                <line x1="0" y1="175" x2="1000" y2="175" />
                <line x1="0" y1="233.3" x2="1000" y2="233.3" />
                <line x1="0" y1="291.7" x2="1000" y2="291.7" />
                <line x1="0" y1="350" x2="1000" y2="350" />
              </g>
              <!-- 0轴 -->
              <line x1="0" y1="175" x2="1000" y2="175" stroke="rgba(255,255,255,0.2)" stroke-width="1" stroke-dasharray="4,2" />
              <!-- 悬停线 -->
              <line v-if="hoverIndex >= 0" :x1="hoverIndex * (1000 / 48)" :x2="hoverIndex * (1000 / 48)" y1="0" y2="350" stroke="rgba(255,255,255,0.3)" stroke-width="1" stroke-dasharray="4,2" />
              <!-- 折线 -->
              <path
                v-for="trend in selectedTrendData"
                :key="trend.name"
                :d="buildPath(trend.points, 1000, 350, chartMin, chartMax)"
                fill="none"
                :stroke="trend.color"
                stroke-width="1.5"
                opacity="0.9"
              />
            </svg>
            <!-- 右侧图例 -->
            <div class="right-legend">
              <div
                v-for="trend in selectedTrendData"
                :key="trend.name"
                class="right-legend-item"
              >
                <span class="legend-dot" :style="{ background: trend.color }"></span>
                <span class="legend-name">{{ trend.name }}</span>
                <span class="legend-value" :class="trend.net >= 0 ? 'up' : 'down'">{{ trend.net >= 0 ? '+' : '' }}{{ trend.net }}亿</span>
              </div>
            </div>
          </div>
          <!-- X轴标签 -->
          <div class="x-axis-labels">
            <span>09:30</span>
            <span>10:00</span>
            <span>10:30</span>
            <span>11:00</span>
            <span>11:30</span>
            <span>13:00</span>
            <span>13:30</span>
            <span>14:00</span>
            <span>14:30</span>
            <span>15:00</span>
          </div>
          <!-- 悬停提示 -->
          <div v-if="hoverIndex >= 0 && hoverData.length > 0" class="hover-tooltip" :style="{ left: hoverTooltipX + 'px', top: hoverTooltipY + 'px' }">
            <div class="hover-time">{{ hoverTime }}</div>
            <div class="hover-list">
              <div v-for="item in hoverData" :key="item.name" class="hover-item">
                <span class="hover-dot" :style="{ background: item.color }"></span>
                <span class="hover-name">{{ item.name }}</span>
                <span class="hover-value" :class="item.value >= 0 ? 'up' : 'down'">{{ item.value >= 0 ? '+' : '' }}{{ item.value.toFixed(2) }}亿</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 板块资金排名 -->
      <div class="ranking-panel">
        <div class="panel-title">板块资金排名</div>
        <div class="ranking-list">
          <div
            v-for="(ind, idx) in industries"
            :key="ind.name"
            class="ranking-item"
          >
            <span class="rank-num" :class="idx < 3 ? 'top' : ''">{{ idx + 1 }}</span>
            <span class="rank-name">{{ ind.name }}</span>
            <span class="rank-change" :class="ind.change >= 0 ? 'up' : 'down'">{{ ind.change >= 0 ? '+' : '' }}{{ ind.change }}%</span>
            <span class="rank-net" :class="ind.net >= 0 ? 'up' : 'down'">{{ ind.net >= 0 ? '+' : '' }}{{ ind.net }}亿</span>
            <span class="rank-count" v-if="ind.count > 0">{{ ind.count }}</span>
            <span class="rank-arrow">›</span>
          </div>
        </div>
      </div>

      <!-- 涨停复盘 -->
      <div class="limitup-panel">
        <div class="panel-header">
          <div class="panel-title-en">BOARD REVIEW</div>
          <div class="panel-title-cn">涨停复盘</div>
          <button class="refresh-btn-small" @click="refresh">↻</button>
        </div>
        <div class="limitup-table-wrap">
          <div class="limitup-header">
            <span class="limitup-title">【市场连板股】 {{ limitUpStocks.length }}只 流通市值848亿</span>
          </div>
          <div class="table-scroll">
            <table class="limitup-table">
              <thead>
                <tr>
                  <th>股票</th>
                  <th>现价</th>
                  <th>涨跌幅</th>
                  <th>换手</th>
                  <th>量比</th>
                  <th>主力</th>
                  <th>流通市值</th>
                  <th>连板数</th>
                  <th>板块</th>
                  <th>原因</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="stock in limitUpStocks" :key="stock.code">
                  <td>
                    <div class="stock-name">{{ stock.name }}</div>
                    <div class="stock-code num">{{ stock.code }}</div>
                  </td>
                  <td class="num">{{ stock.price }}</td>
                  <td class="num up">+{{ stock.change }}%</td>
                  <td class="num">{{ stock.turnover }}%</td>
                  <td class="num">{{ stock.volumeRatio }}</td>
                  <td class="num up">{{ stock.main }}</td>
                  <td class="num">{{ stock.floatMv }}</td>
                  <td class="num up">{{ stock.boards }}</td>
                  <td>{{ stock.sector }}</td>
                  <td class="reason">{{ stock.reason }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- 连板高度分析图 -->
      <div class="board-height-panel">
        <div class="panel-header">
          <div class="panel-title">连板高度分析图</div>
          <div class="panel-actions">
            <button class="action-btn" @click="selectAllBoardHeight">全选</button>
            <button class="action-btn action-btn-secondary" @click="selectNoneBoardHeight">全不选</button>
          </div>
        </div>
        <div class="board-height-chart">
          <div class="chart-container">
            <!-- Y轴标签 -->
            <div class="y-axis-labels">
              <span>150</span>
              <span>120</span>
              <span>90</span>
              <span>60</span>
              <span>30</span>
              <span>0</span>
            </div>
            <svg viewBox="0 0 1000 300" class="height-chart" preserveAspectRatio="none">
              <!-- 网格线 -->
              <g stroke="rgba(255,255,255,0.08)" stroke-width="1">
                <line x1="0" y1="30" x2="1000" y2="30" />
                <line x1="0" y1="84" x2="1000" y2="84" />
                <line x1="0" y1="138" x2="1000" y2="138" />
                <line x1="0" y1="192" x2="1000" y2="192" />
                <line x1="0" y1="246" x2="1000" y2="246" />
                <line x1="0" y1="300" x2="1000" y2="300" />
              </g>
              <!-- 折线 -->
              <path
                v-for="series in selectedBoardHeightSeries"
                :key="series.key"
                :d="buildPath(boardHeightData.map(d => d[series.key]), 1000, 270, 0, 150)"
                fill="none"
                :stroke="series.color"
                stroke-width="2"
                transform="translate(0, 30)"
              />
              <!-- 数据点标记 -->
              <g v-for="series in selectedBoardHeightSeries" :key="'dots-' + series.key">
                <circle
                  v-for="(d, idx) in boardHeightData"
                  :key="'dot-' + series.key + '-' + idx"
                  :cx="(idx / (boardHeightData.length - 1)) * 1000"
                  :cy="30 + 270 - (d[series.key] / 150) * 270"
                  :r="series.key === 'lianban' ? 4 : 3"
                  :fill="series.color"
                  :stroke="series.key === 'lianban' ? '#ef4444' : 'none'"
                  stroke-width="1"
                />
                <!-- 连板数用菱形标记 -->
                <polygon
                  v-if="series.key === 'lianban'"
                  v-for="(d, idx) in boardHeightData"
                  :key="'diamond-' + idx"
                  :points="getDiamondPoints((idx / (boardHeightData.length - 1)) * 1000, 30 + 270 - (d[series.key] / 150) * 270, 5)"
                  fill="#ef4444"
                />
              </g>
            </svg>
          </div>
          <!-- X轴标签 -->
          <div class="height-x-labels">
            <span v-for="d in boardHeightData" :key="d.date">{{ d.date }}</span>
          </div>
          <!-- 图例 -->
          <div class="height-legend">
            <span
              v-for="series in boardHeightSeries"
              :key="series.key"
              class="height-legend-item"
              :class="{ selected: selectedBoardHeightKeys.includes(series.key) }"
              @click="toggleBoardHeightSeries(series.key)"
            >
              <span class="height-legend-dot" :style="{ background: series.color }"></span>
              {{ series.label }}
            </span>
          </div>
        </div>
      </div>

      <!-- 涨停时刻表 -->
      <div class="schedule-panel">
        <div class="panel-header">
          <div class="panel-title-en">LIMIT UP</div>
          <div class="panel-title-cn">涨停时刻表</div>
          <div class="panel-actions">
            <button class="toggle-btn">--</button>
            <button class="refresh-btn-small" @click="refresh">↻</button>
          </div>
        </div>

        <!-- 统计卡片 -->
        <div class="schedule-stats">
          <div class="schedule-stat-card">
            <div class="stat-value up">{{ limitUpStats.currentSealed }}</div>
            <div class="stat-label">当前封板</div>
          </div>
          <div class="schedule-stat-card">
            <div class="stat-value">{{ limitUpStats.everSealed }}</div>
            <div class="stat-label">曾封板</div>
          </div>
          <div class="schedule-stat-card">
            <div class="stat-value">{{ limitUpStats.dynamicBreakRate }}%</div>
            <div class="stat-label">动态炸板率</div>
          </div>
          <div class="schedule-stat-card">
            <div class="stat-value">{{ limitUpStats.cumulativeBreakRate }}%</div>
            <div class="stat-label">累计炸板率</div>
          </div>
          <div class="schedule-stat-card">
            <div class="stat-value">{{ limitUpStats.resealRate }}%</div>
            <div class="stat-label">回封率</div>
          </div>
          <div class="schedule-stat-card">
            <div class="stat-value up">{{ limitUpStats.maxBoard }}板</div>
            <div class="stat-label">最高板</div>
          </div>
        </div>

        <!-- 板数筛选 -->
        <div class="filter-row">
          <button
            v-for="f in boardFilters"
            :key="f.key"
            class="filter-btn"
            :class="{ active: activeBoardFilter === f.key }"
            @click="activeBoardFilter = f.key"
          >
            {{ f.label }}
          </button>
        </div>

        <!-- 状态筛选 -->
        <div class="filter-row">
          <button
            v-for="f in statusFilters"
            :key="f.key"
            class="filter-btn"
            :class="{ active: activeStatusFilter === f.key }"
            @click="activeStatusFilter = f.key"
          >
            {{ f.label }}
          </button>
        </div>

        <!-- 详细表格 -->
        <div class="schedule-table-wrap">
          <div class="table-scroll">
            <table class="schedule-table">
              <thead>
                <tr>
                  <th>股票</th>
                  <th>板数</th>
                  <th>状态</th>
                  <th>现价</th>
                  <th>涨跌幅</th>
                  <th>换手</th>
                  <th>量比</th>
                  <th>主力</th>
                  <th>流通市值</th>
                  <th>封板</th>
                  <th>炸板</th>
                  <th>回封</th>
                  <th>当前封单</th>
                  <th>最大封单</th>
                  <th>炸板/回封</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="stock in pagedSchedule" :key="stock.code">
                  <td>
                    <div class="stock-name">{{ stock.name }}</div>
                    <div class="stock-code num">{{ stock.code }}</div>
                  </td>
                  <td class="num up">{{ stock.boards }}</td>
                  <td :class="statusClass(stock.status)">{{ stock.status }}</td>
                  <td class="num">{{ stock.price }}</td>
                  <td class="num" :class="stock.change >= 0 ? 'up' : 'down'">{{ stock.change >= 0 ? '+' : '' }}{{ stock.change }}%</td>
                  <td class="num">{{ stock.turnover }}%</td>
                  <td class="num">{{ stock.volumeRatio }}</td>
                  <td class="num" :class="stock.main.startsWith('<') ? 'down' : 'up'">{{ stock.main }}</td>
                  <td class="num">{{ stock.floatMv }}</td>
                  <td class="num">{{ stock.sealTime }}</td>
                  <td class="num">{{ stock.breakTime }}</td>
                  <td class="num">{{ stock.resealTime }}</td>
                  <td class="num">{{ stock.currentSeal }}</td>
                  <td class="num">{{ stock.maxSeal }}</td>
                  <td class="num">{{ stock.breakReseal }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- 分页 -->
        <div class="pagination">
          <span class="page-info">每页
            <select v-model="pageSize" class="page-size-select">
              <option :value="15">15</option>
              <option :value="30">30</option>
              <option :value="50">50</option>
            </select>
            条
          </span>
          <span class="page-total">共 {{ limitUpSchedule.length }} 条</span>
          <div class="page-buttons">
            <button class="page-btn" :disabled="currentPage === 1" @click="prevPage">上一页</button>
            <button
              v-for="p in totalPages"
              :key="p"
              class="page-btn"
              :class="{ active: currentPage === p }"
              @click="goToPage(p)"
            >{{ p }}</button>
            <button class="page-btn" :disabled="currentPage === totalPages" @click="nextPage">下一页</button>
          </div>
        </div>
      </div>
      </div>

      <!-- 概念内容 -->
      <div v-else-if="activeFundSubTab === 'concept'" class="concept-view">
        <!-- 统计信息栏 -->
        <div class="info-bar">
          <div class="info-left">
            <span class="info-count">共 {{ concepts.length }} 个板块</span>
            <span class="info-time">更新于 {{ lastUpdate }}</span>
          </div>
          <div class="info-right">
            <button class="date-today-btn" @click="showDatePicker = true">
              今天 <span class="date-arrow">▼</span>
            </button>
            <button class="refresh-btn" @click="refresh">
              <span class="refresh-icon">↻</span> 刷新
            </button>
          </div>
        </div>

        <!-- 三个统计卡片 -->
        <div class="stats-grid">
          <div class="stats-card">
            <div class="stats-label">涨跌分布</div>
            <div class="stats-value">
              <span class="up">{{ conceptStats.up }}</span>
              <span class="dim">:</span>
              <span class="flat">{{ conceptStats.flat }}</span>
              <span class="dim">:</span>
              <span class="down">{{ conceptStats.down }}</span>
            </div>
            <div class="stats-sub">
              中位 <span :class="conceptStats.median >= 0 ? 'up' : 'down'">{{ conceptStats.median }}%</span>
              <span class="dim"> | </span>
              ≥3% <span class="up">{{ conceptStats.up3 }}</span>
              <span class="dim"> | </span>
              ≤-3% <span class="down">{{ conceptStats.down3 }}</span>
            </div>
          </div>
          <div class="stats-card">
            <div class="stats-label">主力净流入</div>
            <div class="stats-value" :class="conceptStats.mainNet >= 0 ? 'up' : 'down'">
              {{ conceptStats.mainNet >= 0 ? '+' : '' }}{{ conceptStats.mainNet }}亿
            </div>
            <div class="stats-sub">
              同比昨日 <span :class="conceptStats.mainNetYoy >= 0 ? 'up' : 'down'">{{ conceptStats.mainNetYoy >= 0 ? '+' : '' }}{{ conceptStats.mainNetYoy }}亿</span>
            </div>
          </div>
          <div class="stats-card">
            <div class="stats-label">成交额</div>
            <div class="stats-value">{{ conceptStats.amount }}亿</div>
            <div class="stats-sub">
              同比昨日 <span :class="conceptStats.amountYoy >= 0 ? 'up' : 'down'">{{ conceptStats.amountYoy >= 0 ? '+' : '' }}{{ conceptStats.amountYoy }}亿</span>
            </div>
          </div>
        </div>

        <!-- 净流入折线图 -->
        <div class="chart-panel">
          <div class="chart-header">
            <span class="chart-title">净流入 (亿元)</span>
            <div class="chart-actions">
              <button class="action-btn" @click="selectAllConcepts">全选</button>
              <button class="action-btn action-btn-secondary" @click="selectNoneConcepts">全不选</button>
            </div>
          </div>
          <div class="chart-body">
            <svg viewBox="0 0 1000 350" class="trend-chart" preserveAspectRatio="none">
              <!-- 网格线 -->
              <g stroke="rgba(255,255,255,0.08)" stroke-width="1">
                <line x1="0" y1="0" x2="1000" y2="0" />
                <line x1="0" y1="87.5" x2="1000" y2="87.5" />
                <line x1="0" y1="175" x2="1000" y2="175" />
                <line x1="0" y1="262.5" x2="1000" y2="262.5" />
                <line x1="0" y1="350" x2="1000" y2="350" />
              </g>
              <!-- 0轴 -->
              <line x1="0" y1="175" x2="1000" y2="175" stroke="rgba(255,255,255,0.2)" stroke-width="1" stroke-dasharray="4,2" />
              <!-- 折线 -->
              <path
                v-for="trend in selectedConceptTrendData"
                :key="trend.name"
                :d="buildConceptPath(trend.points, 1000, 350, conceptChartMin, conceptChartMax)"
                fill="none"
                :stroke="trend.color"
                stroke-width="1.5"
                opacity="0.9"
              />
            </svg>
            <!-- 图例 -->
            <div class="chart-legend">
              <div
                v-for="c in conceptTrendData"
                :key="c.name"
                class="legend-item"
                :class="{ selected: c.selected }"
                @click="c.selected = !c.selected"
              >
                <span class="legend-dot" :style="{ background: c.color }"></span>
                <span class="legend-name">{{ c.name }}</span>
                <span class="legend-value" :class="c.net >= 0 ? 'up' : 'down'">{{ c.net >= 0 ? '+' : '' }}{{ c.net }}亿</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 个股内容 -->
      <div v-else-if="activeFundSubTab === 'stock'" class="stock-view">
        <div class="info-bar">
          <div class="info-left">
            <span class="info-count">共 {{ stocks.length }} 只个股</span>
            <span class="info-time">更新于 {{ lastUpdate }}</span>
          </div>
          <div class="info-right">
            <button class="refresh-btn" @click="refresh">
              <span class="refresh-icon">↻</span> 刷新
            </button>
          </div>
        </div>

        <div class="ranking-panel">
          <div class="panel-title">个股主力净流入排名</div>
          <div class="ranking-list">
            <div v-for="(s, idx) in stocks" :key="s.code || s.name" class="ranking-item">
              <span class="rank-num" :class="idx < 3 ? 'top' : ''">{{ idx + 1 }}</span>
              <span class="rank-name">{{ s.name }} <span style="color:#64748b;font-size:11px;" class="num">{{ s.code }}</span></span>
              <span class="rank-change" :class="s.change >= 0 ? 'up' : 'down'">{{ s.change >= 0 ? '+' : '' }}{{ s.change }}%</span>
              <span class="rank-net" :class="s.net >= 0 ? 'up' : 'down'">{{ s.net >= 0 ? '+' : '' }}{{ s.net }}亿</span>
              <span class="rank-arrow">›</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 市场情绪内容 -->
    <div v-else-if="activeTopTab === 'sentiment'" class="sentiment-view">
      <!-- 信息栏 -->
      <div class="info-bar">
        <div class="info-left">
          <span class="info-count">数据日 2026-09-02 · 更新 2026-09-02 16:05:04</span>
        </div>
        <div class="info-right">
          <button class="refresh-btn" @click="refresh">
            <span class="refresh-icon">↻</span> 刷新
          </button>
        </div>
      </div>

      <!-- 分指数对比 -->
      <div class="sentiment-panel">
        <div class="panel-header">
          <div class="panel-title">分指数对比</div>
          <div class="panel-hint">点柱切换下方指数</div>
        </div>
        <div class="index-compare-chart">
          <div
            v-for="idx in sentimentIndices"
            :key="idx.name"
            class="index-compare-row"
            @click="selectedSentimentIndex = idx.name"
          >
            <span class="index-compare-label">{{ idx.name }}</span>
            <div class="index-compare-bar-wrap">
              <div
                class="index-compare-bar"
                :style="{ width: idx.value + '%', background: idx.color }"
              ></div>
              <!-- 刻度线 -->
              <div class="index-tick" style="left: 25%">
                <span class="tick-label">恐惧</span>
              </div>
              <div class="index-tick" style="left: 50%">
                <span class="tick-label">中立</span>
              </div>
              <div class="index-tick" style="left: 75%">
                <span class="tick-label">贪婪</span>
              </div>
            </div>
            <span class="index-compare-value" :style="{ color: idx.color }">{{ idx.value }}</span>
          </div>
          <div class="index-compare-x-axis">
            <span>0</span>
            <span>20</span>
            <span>40</span>
            <span>60</span>
            <span>80</span>
            <span>100</span>
          </div>
        </div>
      </div>

      <!-- 指数选择按钮 -->
      <div class="index-selector">
        <button
          v-for="idx in sentimentIndices"
          :key="idx.name"
          class="index-select-btn"
          :class="{ active: selectedSentimentIndex === idx.name }"
          @click="selectedSentimentIndex = idx.name"
        >
          <span class="index-select-name">{{ idx.name }}</span>
          <span class="index-select-value" :style="{ color: idx.color }">{{ idx.value }}</span>
        </button>
      </div>

      <!-- 子标签 -->
      <div class="sentiment-sub-tabs">
        <button
          v-for="tab in sentimentSubTabs"
          :key="tab.key"
          class="sentiment-sub-tab-btn"
          :class="{ active: activeSentimentSubTab === tab.key }"
          @click="activeSentimentSubTab = tab.key"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- 概览内容 -->
      <div v-if="activeSentimentSubTab === 'overview'" class="sentiment-overview">
        <!-- 恐贪指数仪表盘 -->
        <div class="gauge-panel">
          <div class="gauge-container">
            <svg viewBox="0 0 200 120" class="gauge-svg">
              <!-- 背景弧 -->
              <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="#334155" stroke-width="16" stroke-linecap="round" />
              <!-- 刻度分区 -->
              <path d="M 20 100 A 80 80 0 0 1 52 48" fill="none" stroke="#22c55e" stroke-width="16" stroke-linecap="round" opacity="0.6" />
              <path d="M 52 48 A 80 80 0 0 1 100 20" fill="none" stroke="#84cc16" stroke-width="16" opacity="0.6" />
              <path d="M 100 20 A 80 80 0 0 1 148 48" fill="none" stroke="#eab308" stroke-width="16" opacity="0.6" />
              <path d="M 148 48 A 80 80 0 0 1 180 100" fill="none" stroke="#f97316" stroke-width="16" stroke-linecap="round" opacity="0.6" />
              <!-- 当前值指针弧 -->
              <path
                :d="`M 20 100 A 80 80 0 0 1 ${20 + 160 * (currentSentiment.value / 100)} ${100 - 80 * Math.sin((currentSentiment.value / 100) * Math.PI)}`"
                fill="none"
                :stroke="currentStatus.color"
                stroke-width="16"
                stroke-linecap="round"
              />
            </svg>
            <div class="gauge-center">
              <div class="gauge-value" :style="{ color: currentStatus.color }">{{ currentSentiment.value }}</div>
              <div class="gauge-status" :style="{ color: currentStatus.color }">{{ currentStatus.label }}</div>
            </div>
          </div>
          <div class="gauge-labels">
            <span class="gauge-label" style="color: #22c55e">极度恐惧</span>
            <span class="gauge-label" style="color: #84cc16">恐惧</span>
            <span class="gauge-label" style="color: #eab308">中立</span>
            <span class="gauge-label" style="color: #f97316">贪婪</span>
            <span class="gauge-label" style="color: #ef4444">极度贪婪</span>
          </div>
          <div class="gauge-hint">点分数或指标名可看说明</div>
        </div>

        <!-- 七个维度指标 -->
        <div class="dimensions-panel">
          <div
            v-for="dim in sentimentDimensions"
            :key="dim.name"
            class="dimension-row"
          >
            <div class="dimension-header">
              <span class="dimension-name">{{ dim.name }}</span>
              <span class="dimension-info" title="指标说明">ⓘ</span>
              <span class="dimension-value" :style="{ color: dim.color }">{{ dim.value }}</span>
            </div>
            <div class="dimension-bar-wrap">
              <div
                class="dimension-bar"
                :style="{ width: dim.value + '%', background: dim.color }"
              ></div>
            </div>
          </div>
        </div>

        <!-- 市场统计 -->
        <div class="market-stats-bar">
          <span>涨 <span class="up">{{ marketStats.up }}</span></span>
          <span>平 <span class="flat">{{ marketStats.flat }}</span></span>
          <span>跌 <span class="down">{{ marketStats.down }}</span></span>
          <span>涨停 <span class="up">{{ marketStats.limitUp }}</span></span>
          <span>跌停 <span class="down">{{ marketStats.limitDown }}</span></span>
          <span>样本 <span class="flat">{{ marketStats.total }}</span></span>
        </div>
      </div>

      <!-- 日线内容（占位） -->
      <div v-else class="sentiment-daily">
        <div class="placeholder-text">日线数据功能开发中</div>
      </div>

      <!-- 两融余额 -->
      <div class="margin-panel">
        <div class="panel-header">
          <div class="panel-title">两融余额</div>
          <div class="margin-range-selector">
            <button
              v-for="r in marginTradingRanges"
              :key="r.key"
              class="range-btn"
              :class="{ active: marginTradingRange === r.key }"
              @click="marginTradingRange = r.key"
            >
              {{ r.label }}
            </button>
          </div>
        </div>

        <!-- 三个统计卡片 -->
        <div class="margin-stats-grid">
          <div class="margin-stat-card">
            <div class="margin-stat-label">两融余额</div>
            <div class="margin-stat-value">{{ marginTradingStats.total }}亿</div>
            <div class="margin-stat-sub">日变 <span class="up">+{{ marginTradingStats.totalChange }}亿</span></div>
          </div>
          <div class="margin-stat-card">
            <div class="margin-stat-label">融资余额</div>
            <div class="margin-stat-value">{{ marginTradingStats.financing }}亿</div>
            <div class="margin-stat-sub">占流通 {{ marginTradingStats.financingRatio }}%</div>
          </div>
          <div class="margin-stat-card">
            <div class="margin-stat-label">融资净买入</div>
            <div class="margin-stat-value up">{{ marginTradingStats.netBuy }}亿</div>
            <div class="margin-stat-sub">数据日 {{ marginTradingStats.dataDate }}</div>
          </div>
        </div>

        <!-- 两融余额趋势图 -->
        <div class="margin-chart-container">
          <div class="margin-chart-unit">亿元</div>
          <svg viewBox="0 0 800 250" class="margin-chart" preserveAspectRatio="none">
            <!-- 网格线 -->
            <g stroke="rgba(255,255,255,0.08)" stroke-width="1">
              <line x1="0" y1="30" x2="800" y2="30" />
              <line x1="0" y1="80" x2="800" y2="80" />
              <line x1="0" y1="130" x2="800" y2="130" />
              <line x1="0" y1="180" x2="800" y2="180" />
              <line x1="0" y1="230" x2="800" y2="230" />
            </g>
            <!-- 面积 -->
            <path
              :d="buildMarginAreaPath(marginTradingTrend, 800, 230, 25000, 31000)"
              fill="url(#marginGradient)"
              opacity="0.3"
            />
            <!-- 渐变定义 -->
            <defs>
              <linearGradient id="marginGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" style="stop-color:#3b82f6;stop-opacity:0.6" />
                <stop offset="100%" style="stop-color:#3b82f6;stop-opacity:0.05" />
              </linearGradient>
            </defs>
            <!-- 折线 -->
            <path
              :d="buildMarginPath(marginTradingTrend, 800, 230, 25000, 31000)"
              fill="none"
              stroke="#3b82f6"
              stroke-width="2"
            />
          </svg>
          <!-- Y轴标签 -->
          <div class="margin-y-labels">
            <span>31,000</span>
            <span>30,000</span>
            <span>29,000</span>
            <span>28,000</span>
            <span>27,000</span>
            <span>26,000</span>
          </div>
          <!-- X轴标签 -->
          <div class="margin-x-labels">
            <span v-for="(p, idx) in marginTradingTrend" :key="idx" v-show="idx % 2 === 0">{{ p.date }}</span>
          </div>
        </div>
        <div class="margin-chart-desc">全市场两融汇总；可选近60日 / 近1年 / 全部。</div>
      </div>

      <!-- 底部说明 -->
      <div class="sentiment-footer">
        自算指标（ossec_ashare_v1），非官方恐贪指数；仅供参考。
      </div>
    </div>

    <!-- 东财热榜内容 -->
    <div v-else-if="activeTopTab === 'hotlist'" class="hotlist-view">
      <!-- 子标签 -->
      <div class="hotlist-sub-tabs">
        <button
          v-for="tab in hotlistSubTabs"
          :key="tab.key"
          class="hotlist-sub-tab-btn"
          :class="{ active: activeHotlistSubTab === tab.key }"
          @click="activeHotlistSubTab = tab.key"
        >
          <span class="hotlist-tag">{{ tab.tag }}</span>
          {{ tab.label }}
        </button>
        <div class="hotlist-info">
          <span class="hotlist-update">更新: 2026-09-02 19:48</span>
          <button class="refresh-btn-small" @click="refresh">↻</button>
        </div>
      </div>

      <!-- 市场选择 -->
      <div class="market-selector">
        <button
          v-for="m in marketTabs"
          :key="m.key"
          class="market-btn"
          :class="{ active: activeMarket === m.key }"
          @click="activeMarket = m.key"
        >
          {{ m.label }}
        </button>
      </div>

      <!-- 热榜表格 -->
      <div class="hotlist-table-wrap">
        <table class="hotlist-table">
          <thead>
            <tr>
              <th style="width: 80px">排名</th>
              <th style="width: 80px">变动</th>
              <th>代码 / 名称</th>
              <th style="width: 100px">现价</th>
              <th style="width: 120px">涨跌幅</th>
              <th>新粉 / 铁粉</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in currentHotlist" :key="item.code">
              <td>
                <span class="rank-badge" :style="{ background: getRankColor(item.rank) }">{{ item.rank }}</span>
              </td>
              <td>
                <span class="change-num" :class="item.changeType === 'up' ? 'up' : 'down'">
                  {{ item.changeType === 'up' ? '↑' : '↓' }}{{ item.change }}
                </span>
              </td>
              <td>
                <div class="stock-code">{{ item.code }}</div>
                <div class="stock-name-row">
                  <span class="stock-name">{{ item.name }}</span>
                  <span v-if="item.hasTag" class="stock-hash-tag">#</span>
                </div>
              </td>
              <td class="num" :class="item.changePct >= 0 ? 'up' : 'down'">{{ item.price }}</td>
              <td>
                <span class="change-pct-badge" :class="item.changePct >= 0 ? 'up' : 'down'">
                  {{ item.changePct >= 0 ? '+' : '' }}{{ item.changePct }}%
                </span>
              </td>
              <td>
                <div class="fans-row">
                  <span class="fans-label new">新粉 {{ item.newFans }}%</span>
                  <span class="fans-label old">铁粉 {{ item.oldFans }}%</span>
                </div>
                <div class="fans-bar-wrap">
                  <div class="fans-bar new" :style="{ width: item.newFans + '%' }"></div>
                  <div class="fans-bar old" :style="{ width: item.oldFans + '%' }"></div>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 分页 -->
      <div class="hotlist-pagination">
        <button
          v-for="p in hotlistTotalPages"
          :key="p"
          class="hotlist-page-btn"
          :class="{ active: hotlistCurrentPage === p }"
          @click="goToHotlistPage(p)"
        >
          第{{ p }}页
        </button>
      </div>
    </div>

    <!-- 7x24页面内容 -->
    <div v-else-if="activeTopTab === 'news7x24'" class="news7x24-view">
      <!-- 页面标题 -->
      <div class="news-header">
        <h2 class="news-title">7x24小时财经新闻</h2>
        <button class="news-refresh-btn" @click="refresh">刷新</button>
      </div>

      <!-- 新闻列表 -->
      <div class="news-list">
        <div
          v-for="news in newsList"
          :key="news.id"
          class="news-item"
        >
          <h3 class="news-item-title">{{ news.title }}</h3>
          <div class="news-item-meta">
            <span class="news-source">{{ news.source }}</span>
            <span class="news-time">{{ news.time }}</span>
          </div>
          <p class="news-item-content">{{ news.content }}</p>
        </div>
      </div>

      <!-- 分页 -->
      <div class="news-pagination">
        <button class="news-page-btn" :disabled="newsCurrentPage === 1" @click="prevNewsPage">上一页</button>
        <button
          v-for="p in newsTotalPages"
          :key="p"
          class="news-page-btn"
          :class="{ active: newsCurrentPage === p }"
          @click="goToNewsPage(p)"
        >{{ p }}</button>
        <button class="news-page-btn" :disabled="newsCurrentPage === newsTotalPages" @click="nextNewsPage">下一页</button>
      </div>
    </div>

    <!-- 财经会议页面内容 -->
    <div v-else-if="activeTopTab === 'meeting'" class="meeting-view">
      <!-- 页面标题 -->
      <div class="meeting-header">
        <h2 class="meeting-title">财经会议</h2>
      </div>

      <!-- 统计卡片 -->
      <div class="meeting-stats-grid">
        <div class="meeting-stat-card">
          <div class="meeting-stat-value">{{ meetingStats.total }}</div>
          <div class="meeting-stat-label">总会议数</div>
        </div>
        <div class="meeting-stat-card">
          <div class="meeting-stat-value">{{ meetingStats.thisMonth }}</div>
          <div class="meeting-stat-label">本月会议</div>
        </div>
      </div>

      <!-- 筛选按钮 -->
      <div class="meeting-filters">
        <button class="filter-tag-btn">时间: {{ meetingTimeFilter }}</button>
        <button class="filter-tag-btn">类型: {{ meetingTypeFilter }}</button>
        <button class="filter-tag-btn">城市: {{ meetingCityFilter }}</button>
        <button class="meeting-refresh-btn" @click="refresh">刷新</button>
      </div>

      <!-- 会议列表 -->
      <div class="meeting-list">
        <div
          v-for="meeting in meetingList"
          :key="meeting.id"
          class="meeting-item"
        >
          <h3 class="meeting-item-title">{{ meeting.title }}</h3>
          <div class="meeting-item-tags">
            <span class="meeting-tag">[{{ meeting.type }}]</span>
            <span v-if="meeting.city" class="meeting-tag">[{{ meeting.city }}]</span>
          </div>
          <p v-if="meeting.content" class="meeting-item-content">{{ meeting.content }}</p>
          <div class="meeting-item-time">{{ meeting.startTime }} - {{ meeting.endTime }}</div>
        </div>
      </div>
    </div>

    <!-- 榜单页面内容 -->
    <div v-else-if="activeTopTab === 'ranking'" class="ranking-view">
      <!-- 子标签：行业/个股 -->
      <div class="ranking-sub-tabs">
        <button
          v-for="tab in rankingSubTabs"
          :key="tab.key"
          class="ranking-sub-tab-btn"
          :class="{ active: activeRankingSubTab === tab.key }"
          @click="activeRankingSubTab = tab.key"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- 行业板块排行 -->
      <div v-if="activeRankingSubTab === 'industry'" class="industry-ranking">
        <div class="ranking-header">
          <span class="ranking-title">行业板块排行</span>
          <button class="ranking-refresh-btn" @click="refresh">
            <span class="refresh-icon">↻</span> 刷新
          </button>
        </div>

        <!-- 排序类型 -->
        <div class="sort-type-tabs">
          <button
            v-for="type in industrySortTypes"
            :key="type.key"
            class="sort-type-btn"
            :class="{ active: activeIndustrySort === type.key }"
            @click="activeIndustrySort = type.key"
          >
            {{ type.label }}
          </button>
        </div>

        <!-- 行业列表 -->
        <div class="industry-list">
          <div
            v-for="item in industryRankingList"
            :key="item.name"
            class="industry-item"
          >
            <span class="industry-rank" :class="item.rank <= 5 ? 'top' : ''">{{ item.rank }}</span>
            <div class="industry-info">
              <div class="industry-name-row">
                <span class="industry-name">{{ item.name }}</span>
                <span class="industry-change" :class="item.change >= 0 ? 'up' : 'down'">{{ item.change >= 0 ? '+' : '' }}{{ item.change }}%</span>
              </div>
            </div>
            <div class="industry-right">
              <div class="industry-amount" :class="item.change >= 0 ? 'up' : 'down'">{{ item.amount }}亿</div>
              <div class="industry-meta">{{ item.count }}只 · 流通 {{ item.floatMv }}</div>
            </div>
            <span class="industry-arrow">›</span>
          </div>
        </div>
      </div>

      <!-- 个股排行 -->
      <div v-else class="stock-ranking">
        <div class="ranking-header">
          <div class="ranking-header-left">
            <span class="ranking-title">个股排行</span>
            <span v-if="selectedDate" class="ranking-date-subtitle">{{ selectedDate }} 收盘</span>
          </div>
          <div class="ranking-header-right">
            <!-- 日期选择器 -->
            <div class="date-picker-wrapper">
              <button v-if="!selectedDate" class="date-today-btn" @click="showDatePicker = true">
                今天 <span class="date-arrow">▼</span>
              </button>
              <template v-else>
                <span class="selected-date-tag">
                  {{ selectedDate }}
                  <span class="date-close-btn" @click="clearDate">×</span>
                </span>
                <button class="date-calendar-btn" @click="showDatePicker = true">
                  <span class="calendar-icon">📅</span>
                </button>
              </template>
            </div>
            <button class="ranking-refresh-btn" @click="refresh">
              <span class="refresh-icon">↻</span> 刷新
            </button>
          </div>
        </div>

        <!-- 排序类型 -->
        <div class="sort-type-tabs sort-type-tabs-scroll">
          <button
            v-for="type in stockSortTypes"
            :key="type.key"
            class="sort-type-btn"
            :class="{ active: activeStockSort === type.key }"
            @click="activeStockSort = type.key"
          >
            {{ type.label }}
          </button>
        </div>

        <!-- 筛选区域 -->
        <div class="filter-panel">
          <div class="filter-header" @click="showFilter = !showFilter">
            <span class="filter-title">▽ 筛选</span>
            <span class="filter-toggle">{{ showFilter ? '▲' : '▼' }}</span>
          </div>
          <div v-if="showFilter" class="filter-content">
            <!-- 涨跌幅筛选 -->
            <div class="filter-group">
              <div class="filter-label">涨跌幅</div>
              <div class="filter-input-row">
                <input type="text" placeholder="最小" class="filter-input" />
                <span class="filter-sep">~</span>
                <input type="text" placeholder="最大" class="filter-input" />
                <span class="filter-unit">%</span>
              </div>
              <div class="filter-quick-btns">
                <button class="quick-btn active">>0%</button>
                <button class="quick-btn">>3%</button>
                <button class="quick-btn">>5%</button>
                <button class="quick-btn active"><0%</button>
                <button class="quick-btn"><-3%</button>
                <button class="quick-btn"><-5%</button>
              </div>
            </div>

            <!-- 价格筛选 -->
            <div class="filter-group">
              <div class="filter-label">价格</div>
              <div class="filter-input-row">
                <input type="text" placeholder="最小" class="filter-input" />
                <span class="filter-sep">~</span>
                <input type="text" placeholder="最大" class="filter-input" />
                <span class="filter-unit">元</span>
              </div>
              <div class="filter-quick-btns">
                <button class="quick-btn"><10</button>
                <button class="quick-btn"><20</button>
                <button class="quick-btn"><50</button>
                <button class="quick-btn">>50</button>
                <button class="quick-btn">>100</button>
              </div>
            </div>

            <!-- 流通市值筛选 -->
            <div class="filter-group">
              <div class="filter-label">流通市值</div>
              <div class="filter-input-row">
                <input type="text" placeholder="最小" class="filter-input" />
                <span class="filter-sep">~</span>
                <input type="text" placeholder="最大" class="filter-input" />
                <span class="filter-unit">亿</span>
              </div>
              <div class="filter-quick-btns">
                <button class="quick-btn"><30亿</button>
                <button class="quick-btn"><50亿</button>
                <button class="quick-btn"><100亿</button>
                <button class="quick-btn">>100亿</button>
                <button class="quick-btn">>300亿</button>
              </div>
            </div>
          </div>
        </div>

        <!-- 个股列表 -->
        <div class="stock-list">
          <div
            v-for="item in stockRankingList"
            :key="item.code"
            class="stock-item"
          >
            <span class="stock-rank" :class="item.rank <= 3 ? 'top' : ''">{{ item.rank }}</span>
            <div class="stock-info">
              <div class="stock-name-row">
                <span class="stock-name">{{ item.name }}({{ item.code }})</span>
                <span class="stock-change" :class="item.change >= 0 ? 'up' : 'down'">{{ item.change >= 0 ? '+' : '' }}{{ item.change }}%</span>
              </div>
            </div>
            <div class="stock-right">
              <div class="stock-price" :class="item.change >= 0 ? 'up' : 'down'">现价 {{ item.price }}</div>
              <div class="stock-meta">流通 {{ item.floatMv }}</div>
            </div>
            <span class="stock-arrow">›</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 日期选择器弹窗 -->
    <div v-if="showDatePicker" class="date-picker-modal" @click.self="showDatePicker = false">
      <div class="date-picker-content">
        <div class="date-picker-header">
          <span class="date-picker-title">日期选择</span>
          <button class="date-picker-close" @click="showDatePicker = false">×</button>
        </div>
        <div class="date-picker-calendar">
          <div class="calendar-nav">
            <button class="calendar-nav-btn" @click="prevMonth">‹</button>
            <span class="calendar-month-title">{{ monthTitle }}</span>
            <button class="calendar-nav-btn" @click="nextMonth">›</button>
          </div>
          <div class="calendar-weekdays">
            <span class="weekday">日</span>
            <span class="weekday">一</span>
            <span class="weekday">二</span>
            <span class="weekday">三</span>
            <span class="weekday">四</span>
            <span class="weekday">五</span>
            <span class="weekday">六</span>
          </div>
          <div class="calendar-days">
            <div
              v-for="(day, index) in calendarDays"
              :key="index"
              class="calendar-day"
              :class="{
                'other-month': !day.isCurrentMonth,
                'future': isFutureDate(day.date),
                'selected': isSelectedDate(day.date),
              }"
              @click="selectDate(day)"
            >
              {{ day.day }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 其他标签占位 -->
    <div v-else class="placeholder-view">
      <div class="placeholder-text">{{ topTabs.find(t => t.key === activeTopTab)?.label }} 功能开发中</div>
    </div>
  </div>
</template>

<style scoped>
.rankings-page {
  padding: 20px;
  min-height: 100vh;
  background: #0a0e1a;
}

/* 页面标题 */
.page-header {
  background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 50%, #1e40af 100%);
  border-radius: 16px;
  padding: 24px 28px;
  margin-bottom: 16px;
}
.title-en {
  font-size: 12px;
  color: rgba(255,255,255,0.7);
  letter-spacing: 2px;
  margin-bottom: 4px;
}
.title-cn {
  font-size: 28px;
  font-weight: 700;
  color: #fff;
  margin: 0 0 4px 0;
}
.title-desc {
  font-size: 14px;
  color: rgba(255,255,255,0.8);
  margin: 0;
}

/* 顶部标签 */
.top-tabs {
  display: flex;
  gap: 4px;
  background: #1e293b;
  border-radius: 12px;
  padding: 6px;
  margin-bottom: 16px;
}
.top-tab-btn {
  flex: 1;
  padding: 12px 16px;
  background: none;
  border: none;
  border-radius: 8px;
  color: #94a3b8;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}
.top-tab-btn:hover {
  color: #cbd5e1;
}
.top-tab-btn.active {
  background: #334155;
  color: #fff;
  font-weight: 600;
}

/* 子标签 */
.sub-tabs {
  display: flex;
  gap: 0;
  background: #141824;
  border-radius: 8px 8px 0 0;
  overflow: hidden;
}
.sub-tab-btn {
  padding: 12px 32px;
  background: none;
  border: none;
  color: #64748b;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border-bottom: 2px solid transparent;
}
.sub-tab-btn.active {
  color: #fff;
  border-bottom-color: #3b82f6;
  background: rgba(59,130,246,0.08);
}

/* 信息栏 */
.info-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
  background: #1e293b;
  border: 1px solid #334155;
  border-top: none;
}
.info-left {
  display: flex;
  gap: 16px;
  align-items: center;
}
.info-count {
  font-size: 14px;
  color: #94a3b8;
}
.info-time {
  font-size: 13px;
  color: #64748b;
}
.info-right {
  display: flex;
  gap: 10px;
  align-items: center;
}
.time-select {
  padding: 6px 12px;
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 6px;
  color: #3b82f6;
  font-size: 13px;
  cursor: pointer;
}
.refresh-btn {
  padding: 6px 14px;
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 6px;
  color: #f1f5f9;
  font-size: 13px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
}
.refresh-btn:hover {
  border-color: #3b82f6;
}

/* 统计卡片 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin: 16px 0;
}
.stats-card {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 10px;
  padding: 16px 18px;
}
.stats-label {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 8px;
}
.stats-value {
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 6px;
}
.stats-sub {
  font-size: 12px;
  color: #64748b;
}
.dim {
  color: #475569;
}

/* 图表面板 */
.chart-panel {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
}
.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.chart-title {
  font-size: 14px;
  font-weight: 600;
  color: #f1f5f9;
}
.chart-actions {
  display: flex;
  gap: 8px;
}
.action-btn {
  padding: 4px 12px;
  background: #3b82f6;
  border: none;
  border-radius: 6px;
  color: #fff;
  font-size: 12px;
  cursor: pointer;
}
.action-btn-secondary {
  background: #0f172a;
  border: 1px solid #334155;
  color: #94a3b8;
}
.chart-body {
  position: relative;
  padding: 16px;
}

.chart-container {
  display: flex;
  align-items: stretch;
  gap: 8px;
}

.y-axis-labels {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 0 4px;
  font-size: 11px;
  color: #64748b;
  min-width: 32px;
}

.x-axis-labels {
  display: flex;
  justify-content: space-between;
  padding: 8px 40px 0 40px;
  font-size: 11px;
  color: #64748b;
}

.right-legend {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 140px;
  max-height: 280px;
  overflow-y: auto;
  padding-left: 8px;
}

.right-legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  white-space: nowrap;
}

.right-legend-item .legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.right-legend-item .legend-name {
  color: #94a3b8;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
}

.right-legend-item .legend-value {
  font-weight: 600;
}

.hover-tooltip {
  position: fixed;
  background: rgba(15, 23, 42, 0.95);
  border: 1px solid #334155;
  border-radius: 8px;
  padding: 12px;
  z-index: 1000;
  min-width: 200px;
  max-height: 400px;
  overflow-y: auto;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  pointer-events: none;
  transform: translate(14px, 14px);
}

.hover-time {
  font-size: 14px;
  font-weight: 600;
  color: #f1f5f9;
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid #334155;
}

.hover-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.hover-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.hover-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.hover-name {
  color: #94a3b8;
  flex: 1;
}

.hover-value {
  font-weight: 600;
}
.trend-chart {
  width: 100%;
  height: 280px;
  display: block;
}
.chart-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #334155;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  background: #0f172a;
  border-radius: 4px;
  cursor: pointer;
  opacity: 0.5;
  transition: opacity 0.2s;
}
.legend-item.selected {
  opacity: 1;
}
.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.legend-name {
  font-size: 11px;
  color: #94a3b8;
}
.legend-value {
  font-size: 11px;
  font-weight: 600;
}

/* 板块资金排名 */
.ranking-panel {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
}
.panel-title {
  font-size: 16px;
  font-weight: 600;
  color: #f1f5f9;
  margin-bottom: 14px;
}
.ranking-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.ranking-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  background: #0f172a;
  border-radius: 8px;
  transition: background 0.2s;
}
.ranking-item:hover {
  background: #1e293b;
}
.rank-num {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #334155;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 600;
  color: #94a3b8;
}
.rank-num.top {
  background: #ef4444;
  color: #fff;
}
.rank-name {
  flex: 1;
  font-size: 14px;
  color: #f1f5f9;
}
.rank-change {
  font-size: 13px;
  font-weight: 500;
  width: 70px;
}
.rank-net {
  font-size: 14px;
  font-weight: 600;
  width: 90px;
  text-align: right;
}
.rank-count {
  background: #ef4444;
  color: #fff;
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  min-width: 20px;
  text-align: center;
}
.rank-arrow {
  color: #64748b;
  font-size: 18px;
}

/* 涨停复盘 */
.limitup-panel {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
}
.panel-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
}
.panel-title-en {
  font-size: 11px;
  color: #64748b;
  letter-spacing: 1px;
}
.panel-title-cn {
  font-size: 18px;
  font-weight: 700;
  color: #f1f5f9;
  flex: 1;
}
.refresh-btn-small {
  width: 32px;
  height: 32px;
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 50%;
  color: #3b82f6;
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}
.limitup-table-wrap {
  background: #0f172a;
  border-radius: 8px;
  overflow: hidden;
}
.limitup-header {
  padding: 10px 14px;
  background: linear-gradient(90deg, rgba(239,68,68,0.15), transparent);
  border-bottom: 1px solid #334155;
}
.limitup-title {
  font-size: 14px;
  font-weight: 600;
  color: #ef4444;
}
.table-scroll {
  overflow-x: auto;
}
.limitup-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  min-width: 900px;
}
.limitup-table th {
  background: #1e293b;
  color: #94a3b8;
  font-weight: 600;
  padding: 10px 12px;
  text-align: left;
  border-bottom: 1px solid #334155;
  white-space: nowrap;
}
.limitup-table td {
  padding: 10px 12px;
  border-bottom: 1px solid rgba(255,255,255,0.04);
  color: #cbd5e1;
}
.limitup-table tbody tr:hover {
  background: rgba(59,130,246,0.04);
}
.stock-name {
  font-weight: 600;
  color: #f1f5f9;
}
.stock-code {
  font-size: 11px;
  color: #64748b;
  margin-top: 2px;
}
.reason {
  font-size: 12px;
  color: #94a3b8;
}

/* 连板高度分析图 */
.board-height-panel {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
}

.board-height-panel .panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.board-height-panel .panel-title {
  font-size: 16px;
  font-weight: 600;
  color: #f1f5f9;
}

.board-height-panel .panel-actions {
  display: flex;
  gap: 8px;
}

.board-height-chart {
  position: relative;
}

.board-height-chart .chart-container {
  display: flex;
  align-items: stretch;
  gap: 8px;
}

.board-height-chart .y-axis-labels {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 30px 4px 0;
  font-size: 11px;
  color: #64748b;
  min-width: 32px;
}

.height-chart {
  width: 100%;
  height: 280px;
  display: block;
  flex: 1;
}

.height-x-labels {
  display: flex;
  justify-content: space-around;
  padding: 6px 0 0 40px;
  font-size: 11px;
  color: #64748b;
}

.height-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #334155;
}

.height-legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #94a3b8;
  cursor: pointer;
  opacity: 0.5;
  transition: opacity 0.2s;
}

.height-legend-item.selected {
  opacity: 1;
}

.height-legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

/* 涨停时刻表 */
.schedule-panel {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 12px;
  padding: 16px;
}
.panel-actions {
  display: flex;
  gap: 8px;
}
.toggle-btn {
  width: 32px;
  height: 32px;
  background: #3b82f6;
  border: none;
  border-radius: 6px;
  color: #fff;
  font-size: 14px;
  cursor: pointer;
}
.schedule-stats {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 10px;
  margin-bottom: 14px;
}
.schedule-stat-card {
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 8px;
  padding: 14px;
  text-align: center;
}
.stat-value {
  font-size: 22px;
  font-weight: 700;
  color: #f1f5f9;
  margin-bottom: 4px;
}
.stat-label {
  font-size: 12px;
  color: #64748b;
}
.filter-row {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}
.filter-btn {
  padding: 6px 14px;
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 16px;
  color: #94a3b8;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}
.filter-btn:hover {
  border-color: #475569;
  color: #cbd5e1;
}
.filter-btn.active {
  background: #3b82f6;
  border-color: #3b82f6;
  color: #fff;
}
.schedule-table-wrap {
  background: #0f172a;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 14px;
}
.schedule-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
  min-width: 1400px;
}
.schedule-table th {
  background: #1e293b;
  color: #94a3b8;
  font-weight: 600;
  padding: 10px 8px;
  text-align: left;
  border-bottom: 1px solid #334155;
  white-space: nowrap;
  position: sticky;
  top: 0;
}
.schedule-table td {
  padding: 10px 8px;
  border-bottom: 1px solid rgba(255,255,255,0.04);
  color: #cbd5e1;
  white-space: nowrap;
}
.schedule-table tbody tr:hover {
  background: rgba(59,130,246,0.04);
}
.pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 10px;
}
.page-info {
  font-size: 13px;
  color: #64748b;
  display: flex;
  align-items: center;
  gap: 6px;
}
.page-size-select {
  padding: 4px 8px;
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 4px;
  color: #f1f5f9;
  font-size: 13px;
}
.page-total {
  font-size: 13px;
  color: #64748b;
}
.page-buttons {
  display: flex;
  gap: 4px;
}
.page-btn {
  min-width: 36px;
  height: 32px;
  padding: 0 10px;
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 4px;
  color: #94a3b8;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}
.page-btn:hover:not(:disabled) {
  border-color: #3b82f6;
  color: #3b82f6;
}
.page-btn.active {
  background: #3b82f6;
  border-color: #3b82f6;
  color: #fff;
}
.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 涨跌颜色 */
.up { color: #ef4444; }
.down { color: #22c55e; }
.flat { color: #94a3b8; }
.num { font-family: 'SF Mono', 'Monaco', 'Consolas', monospace; }

/* 市场情绪页面 */
.sentiment-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.sentiment-panel {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 12px;
  padding: 16px;
}

.panel-hint {
  font-size: 12px;
  color: #64748b;
}

/* 分指数对比 */
.index-compare-chart {
  margin-top: 16px;
}
.index-compare-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: background 0.2s;
}
.index-compare-row:hover {
  background: rgba(59,130,246,0.08);
}
.index-compare-label {
  width: 70px;
  font-size: 14px;
  color: #f1f5f9;
  text-align: right;
}
.index-compare-bar-wrap {
  flex: 1;
  height: 20px;
  background: #0f172a;
  border-radius: 4px;
  position: relative;
  overflow: visible;
}
.index-compare-bar {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s;
}
.index-tick {
  position: absolute;
  top: -4px;
  height: 28px;
  border-left: 1px dashed rgba(255,255,255,0.2);
}
.tick-label {
  position: absolute;
  top: -18px;
  left: -20px;
  font-size: 10px;
  color: #64748b;
  white-space: nowrap;
}
.index-compare-value {
  width: 50px;
  font-size: 14px;
  font-weight: 600;
}
.index-compare-x-axis {
  display: flex;
  justify-content: space-between;
  padding-left: 82px;
  padding-right: 62px;
  font-size: 11px;
  color: #64748b;
  margin-top: 8px;
}

/* 指数选择按钮 */
.index-selector {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
.index-select-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 10px 16px;
  background: #1e293b;
  border: 2px solid #334155;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  min-width: 80px;
}
.index-select-btn:hover {
  border-color: #475569;
}
.index-select-btn.active {
  border-color: #3b82f6;
  background: rgba(59,130,246,0.1);
}
.index-select-name {
  font-size: 13px;
  color: #f1f5f9;
}
.index-select-value {
  font-size: 18px;
  font-weight: 700;
}

/* 子标签 */
.sentiment-sub-tabs {
  display: flex;
  gap: 0;
  background: #141824;
  border-radius: 10px;
  padding: 4px;
}
.sentiment-sub-tab-btn {
  flex: 1;
  padding: 12px 24px;
  background: none;
  border: none;
  border-radius: 8px;
  color: #64748b;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}
.sentiment-sub-tab-btn.active {
  background: #0f172a;
  color: #fff;
  font-weight: 600;
}

/* 概览内容 */
.sentiment-overview {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 恐贪指数仪表盘 */
.gauge-panel {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 12px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.gauge-container {
  position: relative;
  width: 280px;
  height: 170px;
}
.gauge-svg {
  width: 100%;
  height: 100%;
}
.gauge-center {
  position: absolute;
  bottom: 10px;
  left: 50%;
  transform: translateX(-50%);
  text-align: center;
}
.gauge-value {
  font-size: 42px;
  font-weight: 700;
  line-height: 1;
}
.gauge-status {
  font-size: 16px;
  font-weight: 600;
  margin-top: 4px;
}
.gauge-labels {
  display: flex;
  justify-content: space-between;
  width: 100%;
  max-width: 400px;
  margin-top: 12px;
}
.gauge-label {
  font-size: 12px;
  font-weight: 500;
}
.gauge-hint {
  font-size: 12px;
  color: #64748b;
  margin-top: 8px;
}

/* 七个维度指标 */
.dimensions-panel {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.dimension-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.dimension-header {
  display: flex;
  align-items: center;
  gap: 8px;
}
.dimension-name {
  font-size: 14px;
  font-weight: 600;
  color: #f1f5f9;
}
.dimension-info {
  font-size: 12px;
  color: #64748b;
  cursor: help;
}
.dimension-value {
  margin-left: auto;
  font-size: 15px;
  font-weight: 700;
}
.dimension-bar-wrap {
  height: 10px;
  background: #0f172a;
  border-radius: 5px;
  overflow: hidden;
}
.dimension-bar {
  height: 100%;
  border-radius: 5px;
  transition: width 0.3s;
}

/* 市场统计 */
.market-stats-bar {
  display: flex;
  gap: 20px;
  padding: 12px 16px;
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 10px;
  font-size: 13px;
  color: #94a3b8;
  flex-wrap: wrap;
}

/* 两融余额 */
.margin-panel {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 12px;
  padding: 16px;
}
.margin-range-selector {
  display: flex;
  gap: 6px;
}
.range-btn {
  padding: 6px 14px;
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 16px;
  color: #94a3b8;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}
.range-btn:hover {
  border-color: #475569;
  color: #cbd5e1;
}
.range-btn.active {
  background: #3b82f6;
  border-color: #3b82f6;
  color: #fff;
}
.margin-stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin: 16px 0;
}
.margin-stat-card {
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 8px;
  padding: 14px;
}
.margin-stat-label {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 6px;
}
.margin-stat-value {
  font-size: 22px;
  font-weight: 700;
  color: #f1f5f9;
  margin-bottom: 4px;
}
.margin-stat-sub {
  font-size: 12px;
  color: #64748b;
}
.margin-chart-container {
  position: relative;
  margin-top: 16px;
}
.margin-chart-unit {
  font-size: 11px;
  color: #64748b;
  margin-bottom: 4px;
  padding-left: 50px;
}
.margin-chart {
  width: 100%;
  height: 220px;
  display: block;
  padding-left: 50px;
}
.margin-y-labels {
  position: absolute;
  left: 0;
  top: 24px;
  height: 220px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  font-size: 11px;
  color: #64748b;
  padding: 0 4px;
}
.margin-x-labels {
  display: flex;
  justify-content: space-around;
  padding-left: 50px;
  font-size: 11px;
  color: #64748b;
  margin-top: 6px;
}
.margin-chart-desc {
  font-size: 12px;
  color: #64748b;
  margin-top: 12px;
}

/* 底部说明 */
.sentiment-footer {
  font-size: 12px;
  color: #64748b;
  padding: 8px 0;
}

.sentiment-daily {
  padding: 60px 0;
  text-align: center;
}

/* 东财热榜页面 */
.hotlist-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.hotlist-sub-tabs {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 12px;
  padding: 12px 16px;
}
.hotlist-sub-tab-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: #0f172a;
  border: 2px solid #334155;
  border-radius: 24px;
  color: #94a3b8;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}
.hotlist-sub-tab-btn:hover {
  border-color: #475569;
  color: #cbd5e1;
}
.hotlist-sub-tab-btn.active {
  border-color: #f97316;
  color: #fff;
  background: rgba(249,115,22,0.1);
}
.hotlist-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: #f97316;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 700;
  color: #fff;
}
.hotlist-info {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 12px;
}
.hotlist-update {
  font-size: 13px;
  color: #94a3b8;
}

/* 市场选择 */
.market-selector {
  display: flex;
  gap: 10px;
}
.market-btn {
  padding: 8px 20px;
  background: #0f172a;
  border: 2px solid #334155;
  border-radius: 20px;
  color: #94a3b8;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}
.market-btn:hover {
  border-color: #475569;
  color: #cbd5e1;
}
.market-btn.active {
  border-color: #3b82f6;
  color: #fff;
  background: rgba(59,130,246,0.1);
}

/* 热榜表格 */
.hotlist-table-wrap {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 12px;
  overflow: hidden;
}
.hotlist-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}
.hotlist-table th {
  background: #334155;
  color: #cbd5e1;
  font-weight: 600;
  padding: 14px 16px;
  text-align: left;
  border-bottom: 1px solid #475569;
}
.hotlist-table td {
  padding: 14px 16px;
  border-bottom: 1px solid rgba(255,255,255,0.04);
  color: #cbd5e1;
  vertical-align: middle;
}
.hotlist-table tbody tr:hover {
  background: rgba(59,130,246,0.04);
}
.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  font-size: 14px;
  font-weight: 700;
  color: #fff;
}
.change-num {
  font-size: 14px;
  font-weight: 600;
}
.stock-code {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 2px;
}
.stock-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.stock-name {
  font-size: 15px;
  font-weight: 600;
  color: #3b82f6;
}
.stock-hash-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: rgba(249,115,22,0.2);
  border: 1px solid #f97316;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 700;
  color: #f97316;
}
.change-pct-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 13px;
  font-weight: 600;
}
.change-pct-badge.up {
  background: rgba(239,68,68,0.15);
  color: #ef4444;
}
.change-pct-badge.down {
  background: rgba(34,197,94,0.15);
  color: #22c55e;
}
.fans-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
}
.fans-label {
  font-size: 12px;
  font-weight: 600;
}
.fans-label.new {
  color: #f97316;
}
.fans-label.old {
  color: #3b82f6;
}
.fans-bar-wrap {
  display: flex;
  height: 8px;
  background: #0f172a;
  border-radius: 4px;
  overflow: hidden;
}
.fans-bar {
  height: 100%;
}
.fans-bar.new {
  background: #f97316;
}
.fans-bar.old {
  background: #3b82f6;
}

/* 分页 */
.hotlist-pagination {
  display: flex;
  gap: 10px;
  padding: 0 4px;
}
.hotlist-page-btn {
  padding: 10px 20px;
  background: #0f172a;
  border: 2px solid #334155;
  border-radius: 20px;
  color: #94a3b8;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}
.hotlist-page-btn:hover {
  border-color: #475569;
  color: #cbd5e1;
}
.hotlist-page-btn.active {
  border-color: #3b82f6;
  color: #fff;
  background: rgba(59,130,246,0.1);
}

/* 7x24页面 */
.news7x24-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.news-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 12px;
  padding: 16px 20px;
}
.news-title {
  font-size: 20px;
  font-weight: 700;
  color: #f1f5f9;
  margin: 0;
}
.news-refresh-btn {
  padding: 8px 20px;
  background: #3b82f6;
  border: none;
  border-radius: 20px;
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}
.news-refresh-btn:hover {
  background: #2563eb;
}

/* 新闻列表 */
.news-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.news-item {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 12px;
  padding: 20px;
  transition: all 0.2s;
}
.news-item:hover {
  border-color: #475569;
  background: #263449;
}
.news-item-title {
  font-size: 18px;
  font-weight: 700;
  color: #f1f5f9;
  margin: 0 0 10px 0;
  line-height: 1.4;
}
.news-item-meta {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}
.news-source {
  font-size: 13px;
  color: #64748b;
}
.news-time {
  font-size: 13px;
  color: #64748b;
}
.news-item-content {
  font-size: 14px;
  color: #94a3b8;
  line-height: 1.7;
  margin: 0;
}

/* 分页 */
.news-pagination {
  display: flex;
  justify-content: center;
  gap: 8px;
  padding: 16px 0;
}
.news-page-btn {
  min-width: 44px;
  height: 40px;
  padding: 0 16px;
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 6px;
  color: #94a3b8;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}
.news-page-btn:hover:not(:disabled) {
  border-color: #3b82f6;
  color: #3b82f6;
}
.news-page-btn.active {
  background: #3b82f6;
  border-color: #3b82f6;
  color: #fff;
}
.news-page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 财经会议页面 */
.meeting-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.meeting-header {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 12px;
  padding: 16px 20px;
}
.meeting-title {
  font-size: 20px;
  font-weight: 700;
  color: #f1f5f9;
  margin: 0;
}

/* 统计卡片 */
.meeting-stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}
.meeting-stat-card {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 12px;
  padding: 20px;
}
.meeting-stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #f1f5f9;
  margin-bottom: 6px;
}
.meeting-stat-label {
  font-size: 14px;
  color: #94a3b8;
}

/* 筛选按钮 */
.meeting-filters {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.filter-tag-btn {
  padding: 8px 16px;
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 20px;
  color: #f1f5f9;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}
.filter-tag-btn:hover {
  border-color: #475569;
}
.meeting-refresh-btn {
  padding: 8px 20px;
  background: #3b82f6;
  border: none;
  border-radius: 20px;
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}
.meeting-refresh-btn:hover {
  background: #2563eb;
}

/* 会议列表 */
.meeting-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.meeting-item {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 12px;
  padding: 20px;
  transition: all 0.2s;
}
.meeting-item:hover {
  border-color: #475569;
  background: #263449;
}
.meeting-item-title {
  font-size: 18px;
  font-weight: 700;
  color: #f1f5f9;
  margin: 0 0 12px 0;
  line-height: 1.4;
}
.meeting-item-tags {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}
.meeting-tag {
  padding: 4px 12px;
  background: rgba(59,130,246,0.15);
  border: 1px solid rgba(59,130,246,0.3);
  border-radius: 16px;
  font-size: 13px;
  color: #3b82f6;
  font-weight: 500;
}
.meeting-item-content {
  font-size: 14px;
  color: #94a3b8;
  line-height: 1.7;
  margin: 0 0 12px 0;
}
.meeting-item-time {
  font-size: 13px;
  color: #64748b;
}

/* 榜单页面 */
.ranking-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 子标签 */
.ranking-sub-tabs {
  display: flex;
  gap: 0;
  background: #141824;
  border-radius: 10px;
  overflow: hidden;
}
.ranking-sub-tab-btn {
  flex: 1;
  padding: 14px 24px;
  background: none;
  border: none;
  color: #64748b;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border-bottom: 2px solid transparent;
}
.ranking-sub-tab-btn.active {
  color: #fff;
  border-bottom-color: #3b82f6;
  background: rgba(59,130,246,0.08);
}

/* 排行头部 */
.ranking-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 12px 12px 0 0;
  border-bottom: none;
}
.ranking-title {
  font-size: 16px;
  font-weight: 600;
  color: #f1f5f9;
}
.ranking-refresh-btn {
  padding: 8px 16px;
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 8px;
  color: #f1f5f9;
  font-size: 13px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
}
.ranking-refresh-btn:hover {
  border-color: #3b82f6;
}

/* 排序类型 */
.sort-type-tabs {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
  background: #1e293b;
  border: 1px solid #334155;
  border-top: none;
  flex-wrap: wrap;
}
.sort-type-tabs-scroll {
  flex-wrap: nowrap;
  overflow-x: auto;
}
.sort-type-btn {
  padding: 8px 16px;
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 20px;
  color: #94a3b8;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}
.sort-type-btn:hover {
  border-color: #475569;
  color: #cbd5e1;
}
.sort-type-btn.active {
  background: #3b82f6;
  border-color: #3b82f6;
  color: #fff;
}

/* 行业列表 */
.industry-list {
  background: #1e293b;
  border: 1px solid #334155;
  border-top: none;
  border-radius: 0 0 12px 12px;
  padding: 8px;
}
.industry-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  background: #0f172a;
  border-radius: 10px;
  margin-bottom: 8px;
  transition: all 0.2s;
}
.industry-item:last-child {
  margin-bottom: 0;
}
.industry-item:hover {
  background: #1e293b;
}
.industry-rank {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #334155;
  border-radius: 50%;
  font-size: 14px;
  font-weight: 700;
  color: #94a3b8;
  flex-shrink: 0;
}
.industry-rank.top {
  background: #ef4444;
  color: #fff;
}
.industry-info {
  flex: 1;
}
.industry-name-row {
  display: flex;
  align-items: center;
  gap: 12px;
}
.industry-name {
  font-size: 16px;
  font-weight: 600;
  color: #f1f5f9;
}
.industry-change {
  font-size: 14px;
  font-weight: 600;
}
.industry-right {
  text-align: right;
  flex-shrink: 0;
}
.industry-amount {
  font-size: 18px;
  font-weight: 700;
}
.industry-meta {
  font-size: 12px;
  color: #64748b;
  margin-top: 2px;
}
.industry-arrow {
  color: #64748b;
  font-size: 20px;
  flex-shrink: 0;
}

/* 筛选面板 */
.filter-panel {
  background: #1e293b;
  border: 1px solid #334155;
  border-top: none;
}
.filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 20px;
  cursor: pointer;
}
.filter-title {
  font-size: 14px;
  font-weight: 600;
  color: #f1f5f9;
}
.filter-toggle {
  font-size: 12px;
  color: #64748b;
}
.filter-content {
  padding: 0 20px 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.filter-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.filter-label {
  font-size: 14px;
  font-weight: 600;
  color: #f1f5f9;
}
.filter-input-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.filter-input {
  flex: 1;
  padding: 10px 14px;
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 8px;
  color: #f1f5f9;
  font-size: 14px;
}
.filter-input::placeholder {
  color: #475569;
}
.filter-sep {
  color: #64748b;
  font-size: 14px;
}
.filter-unit {
  color: #64748b;
  font-size: 14px;
  width: 20px;
}
.filter-quick-btns {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.quick-btn {
  padding: 6px 14px;
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 16px;
  color: #94a3b8;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}
.quick-btn:hover {
  border-color: #475569;
  color: #cbd5e1;
}
.quick-btn.active {
  background: #3b82f6;
  border-color: #3b82f6;
  color: #fff;
}

/* 个股列表 */
.stock-list {
  background: #1e293b;
  border: 1px solid #334155;
  border-top: none;
  border-radius: 0 0 12px 12px;
  padding: 8px;
}
.stock-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  background: #0f172a;
  border-radius: 10px;
  margin-bottom: 8px;
  transition: all 0.2s;
}
.stock-item:last-child {
  margin-bottom: 0;
}
.stock-item:hover {
  background: #1e293b;
}
.stock-rank {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #334155;
  border-radius: 50%;
  font-size: 14px;
  font-weight: 700;
  color: #94a3b8;
  flex-shrink: 0;
}
.stock-rank.top {
  background: #ef4444;
  color: #fff;
}
.stock-info {
  flex: 1;
}
.stock-name-row {
  display: flex;
  align-items: center;
  gap: 12px;
}
.stock-name {
  font-size: 16px;
  font-weight: 600;
  color: #f1f5f9;
}
.stock-change {
  font-size: 14px;
  font-weight: 600;
}
.stock-right {
  text-align: right;
  flex-shrink: 0;
}
.stock-price {
  font-size: 14px;
  font-weight: 600;
}
.stock-meta {
  font-size: 12px;
  color: #64748b;
  margin-top: 2px;
}
.stock-arrow {
  color: #64748b;
  font-size: 20px;
  flex-shrink: 0;
}

/* 日期选择器 */
.ranking-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.ranking-date-subtitle {
  font-size: 14px;
  color: #94a3b8;
  font-weight: 400;
}
.ranking-header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.date-picker-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
}
.date-today-btn {
  padding: 8px 16px;
  background: rgba(59,130,246,0.1);
  border: 1px solid #3b82f6;
  border-radius: 20px;
  color: #3b82f6;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
}
.date-today-btn:hover {
  background: rgba(59,130,246,0.2);
}
.date-arrow {
  font-size: 10px;
}
.selected-date-tag {
  padding: 6px 12px;
  background: rgba(59,130,246,0.1);
  border: 1px solid #3b82f6;
  border-radius: 20px;
  color: #3b82f6;
  font-size: 14px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
}
.date-close-btn {
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
  opacity: 0.7;
  transition: opacity 0.2s;
}
.date-close-btn:hover {
  opacity: 1;
}
.date-calendar-btn {
  width: 36px;
  height: 36px;
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}
.date-calendar-btn:hover {
  border-color: #3b82f6;
}
.calendar-icon {
  font-size: 16px;
}

/* 日期选择器弹窗 */
.date-picker-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.6);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 100px;
  z-index: 1000;
}
.date-picker-content {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 12px;
  width: 500px;
  max-width: 90vw;
  overflow: hidden;
}
.date-picker-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #334155;
}
.date-picker-title {
  font-size: 16px;
  font-weight: 600;
  color: #f1f5f9;
}
.date-picker-close {
  background: none;
  border: none;
  color: #94a3b8;
  font-size: 24px;
  cursor: pointer;
  line-height: 1;
  transition: color 0.2s;
}
.date-picker-close:hover {
  color: #f1f5f9;
}
.date-picker-calendar {
  padding: 16px 20px 20px;
}
.calendar-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.calendar-nav-btn {
  width: 32px;
  height: 32px;
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 6px;
  color: #94a3b8;
  font-size: 18px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}
.calendar-nav-btn:hover {
  border-color: #3b82f6;
  color: #3b82f6;
}
.calendar-month-title {
  font-size: 16px;
  font-weight: 600;
  color: #f1f5f9;
}
.calendar-weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
  margin-bottom: 8px;
}
.weekday {
  text-align: center;
  font-size: 13px;
  font-weight: 500;
  color: #64748b;
  padding: 8px 0;
}
.calendar-days {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
}
.calendar-day {
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  color: #f1f5f9;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}
.calendar-day:hover:not(.future):not(.other-month) {
  background: rgba(59,130,246,0.2);
}
.calendar-day.other-month {
  color: #475569;
}
.calendar-day.future {
  color: #475569;
  cursor: not-allowed;
}
.calendar-day.selected {
  background: #3b82f6;
  color: #fff;
  font-weight: 600;
}

/* 占位 */
.placeholder-view {
  padding: 80px 0;
  text-align: center;
}
.placeholder-text {
  font-size: 16px;
  color: #64748b;
}

/* 响应式 */
@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
  .schedule-stats {
    grid-template-columns: repeat(3, 1fr);
  }
  .top-tabs {
    flex-wrap: wrap;
  }
  .top-tab-btn {
    flex: none;
    padding: 10px 12px;
    font-size: 13px;
  }
}
</style>
