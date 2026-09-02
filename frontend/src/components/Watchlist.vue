<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { searchStocks, fetchBatchQuotes } from '../api'
import { trendClass, signed, pct, num, mv, volume } from '../utils/format'

const STORAGE_KEY = 'stock_watchlist_v1'
const COLUMNS_KEY = 'stock_watchlist_columns_v1'

// 关注清单原始数据（localStorage）
const watchlist = ref([])
// 行情数据 { code: quote }
const quotes = ref({})
// 搜索相关
const keyword = ref('')
const searchOptions = ref([])
const searching = ref(false)
// 批量选中
const selectedCodes = ref([])
// 排序
const sortField = ref('addedAt')
const sortOrder = ref('desc')
// 列配置
const allColumns = [
  { key: 'code', label: '代码', visible: true },
  { key: 'name', label: '名称', visible: true },
  { key: 'now_price', label: '现价', visible: true },
  { key: 'change_pct', label: '涨跌幅', visible: true },
  { key: 'speed', label: '涨速', visible: true },
  { key: 'amount', label: '成交额', visible: true },
  { key: 'signal', label: '信号', visible: true },
  { key: 'remark', label: '备注', visible: true },
  { key: 'action', label: '操作', visible: true },
]
const columnSettings = ref({})
const columnPopover = ref(false)
// 刷新
const loading = ref(false)
const lastUpdate = ref('')
let refreshTimer = null
let searchTimer = null
let searchSeq = 0

// 计算可见列
const visibleColumns = computed(() => allColumns.filter((c) => columnSettings.value[c.key] !== false))

// 合并行情后的列表
const mergedList = computed(() => {
  const list = watchlist.value.map((item) => {
    const q = quotes.value[item.code] || {}
    return {
      ...item,
      ...q,
      signal: computeSignal(q),
    }
  })
  // 排序
  const field = sortField.value
  const order = sortOrder.value === 'asc' ? 1 : -1
  list.sort((a, b) => {
    let va = a[field]
    let vb = b[field]
    if (field === 'addedAt') {
      va = new Date(va).getTime()
      vb = new Date(vb).getTime()
    }
    if (va === null || va === undefined || va === '') va = -Infinity
    if (vb === null || vb === undefined || vb === '') vb = -Infinity
    if (typeof va === 'string') va = va.toLowerCase()
    if (typeof vb === 'string') vb = vb.toLowerCase()
    if (va < vb) return -1 * order
    if (va > vb) return 1 * order
    return 0
  })
  return list
})

// 信号计算：按中国用户习惯分类（红=买入/强势、绿=卖出/弱势、灰=观望）
// 返回 { text, category }，category: 'buy' | 'sell' | 'hold'
function computeSignal(q) {
  if (!q || q.now_price === null || q.now_price === undefined) return { text: '--', category: 'hold' }
  const pctVal = q.change_pct || 0
  const speed = q.speed || 0
  const vr = q.volume_ratio || 0
  // 买入/强势信号
  if (pctVal >= 7 && vr >= 2) return { text: '买入', category: 'buy' } // 强势涨停
  if (pctVal >= 5 && speed >= 0.5) return { text: '买入', category: 'buy' } // 强势拉升
  if (pctVal >= 3) return { text: '买入', category: 'buy' } // 偏强
  if (speed >= 1) return { text: '买入', category: 'buy' } // 快速拉升
  // 卖出/弱势信号
  if (pctVal <= -7) return { text: '卖出', category: 'sell' } // 大跌
  if (pctVal <= -3) return { text: '卖出', category: 'sell' } // 偏弱
  if (speed <= -1) return { text: '卖出', category: 'sell' } // 快速下跌
  return { text: '观望', category: 'hold' }
}

// 加载本地存储
function loadStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) watchlist.value = JSON.parse(raw)
  } catch (e) {
    watchlist.value = []
  }
  try {
    const colRaw = localStorage.getItem(COLUMNS_KEY)
    if (colRaw) columnSettings.value = JSON.parse(colRaw)
  } catch (e) {
    columnSettings.value = {}
  }
}

function saveStorage() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(watchlist.value))
}

function saveColumns() {
  localStorage.setItem(COLUMNS_KEY, JSON.stringify(columnSettings.value))
}

watch(columnSettings, saveColumns, { deep: true })

// 刷新行情
async function refreshQuotes() {
  if (!watchlist.value.length) {
    quotes.value = {}
    lastUpdate.value = new Date().toLocaleTimeString('zh-CN', { hour12: false })
    return
  }
  loading.value = true
  try {
    const codes = watchlist.value.map((item) => item.code)
    const data = await fetchBatchQuotes(codes)
    const map = {}
    data.forEach((q) => {
      if (q && q.code) map[q.code] = q
    })
    quotes.value = map
    lastUpdate.value = new Date().toLocaleTimeString('zh-CN', { hour12: false })
  } catch (e) {
    message.error(`关注清单刷新失败：${e.message}`)
  } finally {
    loading.value = false
  }
}

// 搜索股票
async function doSearch(val) {
  const kw = (val || '').trim()
  if (!kw) {
    searchOptions.value = []
    return
  }
  searching.value = true
  const id = ++searchSeq
  try {
    const list = await searchStocks(kw)
    if (id !== searchSeq) return
    searchOptions.value = list
      .filter((s) => !watchlist.value.find((w) => w.code === s.code))
      .map((s) => ({ value: `${s.code} ${s.name}`, code: s.code, name: s.name, type: s.security_type || s.market_type }))
  } catch (e) {
    if (id !== searchSeq) return
    searchOptions.value = []
  } finally {
    if (id === searchSeq) searching.value = false
  }
}

function onSearch(val) {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => doSearch(val), 300)
}

function onSelect(value, option) {
  const code = (option && option.code) || String(value).split(' ')[0]
  addStock(code, option && option.name)
  keyword.value = ''
  searchOptions.value = []
}

// 添加股票
function addStock(code, name) {
  if (!code) return
  if (watchlist.value.find((w) => w.code === code)) {
    message.warning('该股票已在关注清单中')
    return
  }
  const item = {
    code,
    name: name || code,
    remark: '',
    addedAt: new Date().toISOString(),
  }
  watchlist.value.push(item)
  saveStorage()
  refreshQuotes()
  message.success(`已添加 ${name || code}`)
}

// 批量添加（逗号分隔代码）
const batchInput = ref('')
const batchModal = ref(false)
function openBatchModal() {
  batchInput.value = ''
  batchModal.value = true
}
function confirmBatchAdd() {
  const codes = batchInput.value
    .split(/[,，\s\n]+/)
    .map((c) => c.trim())
    .filter((c) => /^\d{6}$/.test(c))
  if (!codes.length) {
    message.warning('请输入有效的 6 位股票代码，多个用逗号或空格分隔')
    return
  }
  let added = 0
  codes.forEach((code) => {
    if (!watchlist.value.find((w) => w.code === code)) {
      watchlist.value.push({ code, name: code, remark: '', addedAt: new Date().toISOString() })
      added++
    }
  })
  saveStorage()
  refreshQuotes()
  batchModal.value = false
  message.success(`成功添加 ${added} 只股票`)
}

// 删除
function removeStock(code) {
  Modal.confirm({
    title: '确认删除',
    content: '确定要从关注清单中移除这只股票吗？',
    okText: '删除',
    okType: 'danger',
    cancelText: '取消',
    onOk: () => {
      watchlist.value = watchlist.value.filter((w) => w.code !== code)
      selectedCodes.value = selectedCodes.value.filter((c) => c !== code)
      saveStorage()
      message.success('已移除')
    },
  })
}

function batchRemove() {
  if (!selectedCodes.value.length) {
    message.warning('请先选择要删除的股票')
    return
  }
  Modal.confirm({
    title: '批量删除',
    content: `确定要移除选中的 ${selectedCodes.value.length} 只股票吗？`,
    okText: '删除',
    okType: 'danger',
    cancelText: '取消',
    onOk: () => {
      watchlist.value = watchlist.value.filter((w) => !selectedCodes.value.includes(w.code))
      selectedCodes.value = []
      saveStorage()
      message.success('已批量移除')
    },
  })
}

// 备注编辑
const editingCode = ref('')
const editingRemark = ref('')
function startEditRemark(item) {
  editingCode.value = item.code
  editingRemark.value = item.remark || ''
}
function saveRemark(item) {
  item.remark = editingRemark.value
  saveStorage()
  editingCode.value = ''
  message.success('备注已保存')
}
function cancelEditRemark() {
  editingCode.value = ''
}

// 全选/取消全选
const allSelected = computed(() => {
  if (!mergedList.value.length) return false
  return mergedList.value.every((item) => selectedCodes.value.includes(item.code))
})
function toggleSelectAll() {
  if (allSelected.value) {
    selectedCodes.value = []
  } else {
    selectedCodes.value = mergedList.value.map((item) => item.code)
  }
}

// 排序切换
function toggleSort(field) {
  if (sortField.value === field) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortField.value = field
    sortOrder.value = 'desc'
  }
}

function sortIcon(field) {
  if (sortField.value !== field) return ''
  return sortOrder.value === 'asc' ? '↑' : '↓'
}

// 格式化
function fmtSpeed(v) {
  if (v === null || v === undefined || Number.isNaN(v)) return '--'
  return `${v > 0 ? '+' : ''}${Number(v).toFixed(2)}%`
}

onMounted(() => {
  loadStorage()
  refreshQuotes()
  refreshTimer = setInterval(refreshQuotes, 30000)
  window.addEventListener('watchlist-changed', onWatchlistChanged)
  document.addEventListener('visibilitychange', onVisibilityChange)
})

function onWatchlistChanged() {
  loadStorage()
  refreshQuotes()
}

// 页面从后台切回时立即刷新行情
function onVisibilityChange() {
  if (document.visibilityState === 'visible') refreshQuotes()
}

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
  if (searchTimer) clearTimeout(searchTimer)
  window.removeEventListener('watchlist-changed', onWatchlistChanged)
  document.removeEventListener('visibilitychange', onVisibilityChange)
})
</script>

<template>
  <section class="terminal-card watchlist-card">
    <div class="terminal-card-head">
      <div>
        <div class="terminal-card-title">关注清单</div>
        <div class="card-sub">支持搜索、排序、列配置、备注编辑和批量操作 · 数据本地存储</div>
      </div>
      <div class="head-actions">
        <a-select
          v-model:value="keyword"
          :options="searchOptions"
          show-search
          :filter-option="false"
          :loading="searching"
          placeholder="搜索股票添加…"
          class="search-input"
          @search="onSearch"
          @select="onSelect"
        >
          <template #option="{ value: v, code, name, type }">
            <div class="opt-row">
              <span class="opt-name">{{ name }}</span>
              <span class="opt-code num">{{ code }}</span>
              <span class="opt-type">{{ type }}</span>
            </div>
          </template>
        </a-select>
        <a-button size="small" @click="openBatchModal">批量添加</a-button>
        <a-popover v-model:open="columnPopover" trigger="click" placement="bottomRight">
          <template #content>
            <div class="column-panel">
              <div class="column-panel-title">列配置</div>
              <div v-for="col in allColumns" :key="col.key" class="column-item">
                <a-checkbox v-model:checked="columnSettings[col.key]" :indeterminate="false">
                  {{ col.label }}
                </a-checkbox>
              </div>
            </div>
          </template>
          <a-button size="small">列配置</a-button>
        </a-popover>
        <span v-if="lastUpdate" class="update-time">更新于 {{ lastUpdate }}</span>
      </div>
    </div>

    <!-- 工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <a-button size="small" :disabled="!selectedCodes.length" @click="batchRemove">
          批量删除 ({{ selectedCodes.length }})
        </a-button>
        <span class="stock-count">共 {{ watchlist.length }} 只</span>
      </div>
      <div class="toolbar-right">
        <span class="sort-label">排序：</span>
        <a-select v-model:value="sortField" size="small" class="sort-select" @change="() => {}">
          <a-select-option value="addedAt">关注日期</a-select-option>
          <a-select-option value="code">代码</a-select-option>
          <a-select-option value="name">名称</a-select-option>
          <a-select-option value="now_price">现价</a-select-option>
          <a-select-option value="change_pct">涨跌幅</a-select-option>
          <a-select-option value="speed">涨速</a-select-option>
          <a-select-option value="amount">成交额</a-select-option>
        </a-select>
        <a-select v-model:value="sortOrder" size="small" class="sort-order">
          <a-select-option value="desc">降序</a-select-option>
          <a-select-option value="asc">升序</a-select-option>
        </a-select>
        <a-button size="small" :loading="loading" @click="refreshQuotes">刷新</a-button>
      </div>
    </div>

    <!-- 表格 -->
    <div class="table-wrap">
      <a-spin :spinning="loading">
        <table v-if="mergedList.length" class="watch-table">
          <thead>
            <tr>
              <th class="col-check">
                <a-checkbox :checked="allSelected" @change="toggleSelectAll" />
              </th>
              <th v-if="visibleColumns.find((c) => c.key === 'code')" class="sortable" @click="toggleSort('code')">
                代码 {{ sortIcon('code') }}
              </th>
              <th v-if="visibleColumns.find((c) => c.key === 'name')" class="sortable" @click="toggleSort('name')">
                名称 {{ sortIcon('name') }}
              </th>
              <th v-if="visibleColumns.find((c) => c.key === 'now_price')" class="sortable num" @click="toggleSort('now_price')">
                现价 {{ sortIcon('now_price') }}
              </th>
              <th v-if="visibleColumns.find((c) => c.key === 'change_pct')" class="sortable num" @click="toggleSort('change_pct')">
                涨跌幅 {{ sortIcon('change_pct') }}
              </th>
              <th v-if="visibleColumns.find((c) => c.key === 'speed')" class="sortable num" @click="toggleSort('speed')">
                涨速 {{ sortIcon('speed') }}
              </th>
              <th v-if="visibleColumns.find((c) => c.key === 'amount')" class="sortable num" @click="toggleSort('amount')">
                成交额 {{ sortIcon('amount') }}
              </th>
              <th v-if="visibleColumns.find((c) => c.key === 'signal')">信号</th>
              <th v-if="visibleColumns.find((c) => c.key === 'remark')">备注</th>
              <th v-if="visibleColumns.find((c) => c.key === 'action')" class="col-action">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in mergedList" :key="item.code" :class="{ selected: selectedCodes.includes(item.code) }">
              <td class="col-check">
                <a-checkbox :checked="selectedCodes.includes(item.code)" @change="(e) => {
                  if (e.target.checked) selectedCodes.push(item.code)
                  else selectedCodes = selectedCodes.filter((c) => c !== item.code)
                }" />
              </td>
              <td v-if="visibleColumns.find((c) => c.key === 'code')" class="num code-cell">{{ item.code }}</td>
              <td v-if="visibleColumns.find((c) => c.key === 'name')" class="name-cell">{{ item.name }}</td>
              <td v-if="visibleColumns.find((c) => c.key === 'now_price')" class="num" :class="trendClass(item.change_pct)">
                {{ num(item.now_price, 2) }}
              </td>
              <td v-if="visibleColumns.find((c) => c.key === 'change_pct')" class="num" :class="trendClass(item.change_pct)">
                {{ pct(item.change_pct) }}
              </td>
              <td v-if="visibleColumns.find((c) => c.key === 'speed')" class="num" :class="trendClass(item.speed)">
                {{ fmtSpeed(item.speed) }}
              </td>
              <td v-if="visibleColumns.find((c) => c.key === 'amount')" class="num">{{ mv(item.amount) }}</td>
              <td v-if="visibleColumns.find((c) => c.key === 'signal')">
                <span class="signal-badge" :class="`signal-${item.signal.category}`">{{ item.signal.text }}</span>
              </td>
              <td v-if="visibleColumns.find((c) => c.key === 'remark')" class="remark-cell">
                <template v-if="editingCode === item.code">
                  <a-input
                    v-model:value="editingRemark"
                    size="small"
                    placeholder="输入备注"
                    @press-enter="saveRemark(item)"
                    @blur="saveRemark(item)"
                  />
                </template>
                <span v-else class="remark-text" @click="startEditRemark(item)">
                  {{ item.remark || '点击添加备注' }}
                </span>
              </td>
              <td v-if="visibleColumns.find((c) => c.key === 'action')" class="col-action">
                <a-button type="link" size="small" danger @click="removeStock(item.code)">删除</a-button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty-state">
          <div class="empty-icon">☆</div>
          <div class="empty-text">暂无关注股票</div>
          <div class="empty-hint">在上方搜索框输入股票代码或名称添加，或点击"批量添加"一次导入多只</div>
        </div>
      </a-spin>
    </div>

    <!-- 批量添加弹窗 -->
    <a-modal v-model:open="batchModal" title="批量添加股票" ok-text="添加" cancel-text="取消" @ok="confirmBatchAdd">
      <p class="batch-hint">输入 6 位股票代码，多个代码用逗号、空格或换行分隔。</p>
      <a-textarea
        v-model:value="batchInput"
        :rows="5"
        placeholder="例如：600519, 000001, 300750"
      />
    </a-modal>
  </section>
</template>

<style scoped>
.watchlist-card {
  overflow: hidden;
}
.card-sub {
  font-size: 12px;
  color: var(--text-3);
  margin-top: 2px;
}
.head-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.search-input {
  width: 220px;
}
.update-time {
  font-size: 12px;
  color: var(--text-3);
}
.opt-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.opt-name {
  font-weight: 500;
}
.opt-code {
  color: var(--text-2);
  font-size: 12px;
}
.opt-type {
  font-size: 11px;
  color: var(--text-3);
  margin-left: auto;
}
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 18px;
  border-bottom: 1px solid var(--border);
  flex-wrap: wrap;
  gap: 8px;
}
.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
}
.stock-count {
  font-size: 12px;
  color: var(--text-3);
}
.sort-label {
  font-size: 12px;
  color: var(--text-3);
}
.sort-select {
  width: 110px;
}
.sort-order {
  width: 70px;
}
.table-wrap {
  padding: 0;
  overflow-x: auto;
}
.watch-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.watch-table thead th {
  background: var(--panel-2);
  padding: 10px 12px;
  text-align: left;
  font-weight: 600;
  color: var(--text-2);
  border-bottom: 1px solid var(--border);
  white-space: nowrap;
  user-select: none;
}
.watch-table thead th.sortable {
  cursor: pointer;
}
.watch-table thead th.sortable:hover {
  color: var(--accent);
}
.watch-table tbody td {
  padding: 10px 12px;
  border-bottom: 1px solid var(--border);
  white-space: nowrap;
}
.watch-table tbody tr:hover {
  background: rgba(79, 124, 255, 0.06);
}
.watch-table tbody tr.selected {
  background: rgba(79, 124, 255, 0.1);
}
.col-check {
  width: 40px;
  text-align: center;
}
.code-cell {
  color: var(--accent);
  font-weight: 500;
}
.name-cell {
  font-weight: 500;
}
.remark-cell {
  min-width: 120px;
}
.remark-text {
  color: var(--text-2);
  cursor: pointer;
  font-size: 12px;
}
.remark-text:hover {
  color: var(--accent);
}
.col-action {
  width: 70px;
  text-align: center;
}

/* 信号徽章：与网页配色一致的高对比颜色（红=买入 绿=卖出 灰=观望） */
.signal-badge {
  display: inline-block;
  padding: 1px 10px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 600;
  line-height: 18px;
  white-space: nowrap;
}
.signal-buy {
  color: #ff6b7a;
  background: rgba(255, 77, 94, 0.12);
  border: 1px solid rgba(255, 77, 94, 0.5);
}
.signal-sell {
  color: #00d9a4;
  background: rgba(0, 197, 142, 0.12);
  border: 1px solid rgba(0, 197, 142, 0.5);
}
.signal-hold {
  color: #c6c6da;
  background: rgba(154, 154, 180, 0.12);
  border: 1px solid rgba(154, 154, 180, 0.4);
}
.empty-state {
  padding: 48px 20px;
  text-align: center;
}
.empty-icon {
  font-size: 40px;
  color: var(--text-3);
  margin-bottom: 12px;
}
.empty-text {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-2);
  margin-bottom: 6px;
}
.empty-hint {
  font-size: 13px;
  color: var(--text-3);
}
.column-panel {
  min-width: 140px;
}
.column-panel-title {
  font-weight: 600;
  margin-bottom: 8px;
  font-size: 13px;
}
.column-item {
  padding: 4px 0;
}
.batch-hint {
  font-size: 13px;
  color: var(--text-2);
  margin-bottom: 10px;
}
</style>
