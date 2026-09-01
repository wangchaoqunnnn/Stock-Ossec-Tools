<script setup>
import { ref, reactive, onMounted, h } from 'vue'
import { message } from 'ant-design-vue'
import { fetchWatchList } from '../api'
import { trendClass, signed, pct, num, mv } from '../utils/format'

const sourceLabel = { eastmoney: '东方财富', tencent: '腾讯行情' }

const state = reactive({
  items: [],
  total: 0,
  loading: false,
  source: '',
  sortField: 'change_pct',
  sortOrder: 'desc',
  page: 1,
  pageSize: 15,
})

const sortableSet = new Set(['code', 'now_price', 'change_pct', 'speed', 'turnover', 'volume_ratio', 'pe', 'pb', 'total_mv', 'float_mv'])

const columns = [
  { title: '代码', dataIndex: 'code', key: 'code', width: 90, sorter: true, customRender: ({ text }) => hNum(text) },
  { title: '名称', dataIndex: 'name', key: 'name', width: 110, fixed: 'left' },
  { title: '现价', dataIndex: 'now_price', key: 'now_price', width: 90, align: 'right', sorter: true, customRender: ({ record }) => hPrice(record) },
  { title: '涨跌幅', dataIndex: 'change_pct', key: 'change_pct', width: 100, align: 'right', sorter: true, customRender: ({ text }) => hPct(text) },
  { title: '涨速', dataIndex: 'speed', key: 'speed', width: 90, align: 'right', sorter: true, customRender: ({ text }) => hPct(text) },
  { title: '今开', dataIndex: 'open', key: 'open', width: 90, align: 'right', customRender: ({ text }) => hNum(text) },
  { title: '最高', dataIndex: 'high', key: 'high', width: 90, align: 'right', customRender: ({ text }) => hNum(text, 'up') },
  { title: '最低', dataIndex: 'low', key: 'low', width: 90, align: 'right', customRender: ({ text }) => hNum(text, 'down') },
  { title: '昨收', dataIndex: 'prev_close', key: 'prev_close', width: 90, align: 'right', customRender: ({ text }) => hNum(text) },
  { title: '换手率', dataIndex: 'turnover', key: 'turnover', width: 90, align: 'right', sorter: true, customRender: ({ text }) => hPct(text) },
  { title: '量比', dataIndex: 'volume_ratio', key: 'volume_ratio', width: 80, align: 'right', sorter: true, customRender: ({ text }) => hNum(text, '', 2) },
  { title: '市盈率', dataIndex: 'pe', key: 'pe', width: 90, align: 'right', sorter: true, customRender: ({ text }) => hNum(text, '', 2) },
  { title: '市净率', dataIndex: 'pb', key: 'pb', width: 90, align: 'right', sorter: true, customRender: ({ text }) => hNum(text, '', 2) },
  { title: '总市值', dataIndex: 'total_mv', key: 'total_mv', width: 100, align: 'right', sorter: true, customRender: ({ text }) => hMv(text) },
  { title: '流通市值', dataIndex: 'float_mv', key: 'float_mv', width: 100, align: 'right', sorter: true, customRender: ({ text }) => hMv(text) },
  { title: '行业', dataIndex: 'industry', key: 'industry', width: 110 },
]

function hNum(v, cls = '', digits = 2) {
  return h('span', { class: `num ${cls || trendClass(v)}` }, num(v, digits))
}
function hPct(v) {
  return h('span', { class: `num ${trendClass(v)}` }, pct(v))
}
function hMv(v) {
  return h('span', { class: 'num' }, mv(v))
}
function hPrice(record) {
  return h('span', { class: `num ${trendClass(record.change_pct)}` }, num(record.now_price))
}

async function load() {
  state.loading = true
  try {
    const data = await fetchWatchList({
      sort: state.sortField,
      order: state.sortOrder,
      page: state.page,
      pageSize: state.pageSize,
    })
    state.items = data.items || []
    state.total = data.total || 0
    state.source = data.source || ''
  } catch (e) {
    state.items = []
    message.error(`关注清单加载失败：${e.message}`)
  } finally {
    state.loading = false
  }
}

function onChange(pagination, _filters, sorter) {
  if (sorter && sorter.field) {
    const key = String(sorter.field)
    if (sortableSet.has(key)) {
      const order = sorter.order === 'ascend' ? 'asc' : sorter.order === 'descend' ? 'desc' : ''
      if (order) {
        state.sortField = key
        state.sortOrder = order
      }
    }
  }
  state.page = pagination.current || 1
  state.pageSize = pagination.pageSize || 15
  load()
}

function onTableChange(pagination, filters, sorter) {
  // a-table 的 change 回调统一入口
  onChange(pagination, filters, sorter)
}

onMounted(load)
</script>

<template>
  <section class="terminal-card">
    <div class="terminal-card-head">
      <div class="terminal-card-title">关注清单</div>
      <div class="watch-actions">
        <a-tag v-if="state.source" size="small" color="blue">{{ sourceLabel[state.source] || state.source }}</a-tag>
        <a-tag size="small">共 {{ state.total }} 只</a-tag>
      </div>
    </div>

    <div class="watch-body">
      <a-table
        :columns="columns"
        :data-source="state.items"
        :loading="state.loading"
        :pagination="{
          current: state.page,
          pageSize: state.pageSize,
          total: state.total,
          showSizeChanger: true,
          pageSizeOptions: ['10', '15', '20', '50'],
          showTotal: (t) => `共 ${t} 条`,
        }"
        size="small"
        :scroll="{ x: 1500 }"
        row-key="code"
        @change="onTableChange"
      />
    </div>
  </section>
</template>

<style scoped>
.watch-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.watch-body {
  padding: 8px 8px 12px;
}
:deep(.ant-table) {
  background: transparent;
}
:deep(.ant-table-thead > tr > th) {
  background: var(--panel-2) !important;
  color: var(--text-2) !important;
  border-bottom: 1px solid var(--border) !important;
  white-space: nowrap;
}
:deep(.ant-table-tbody > tr > td) {
  background: var(--panel) !important;
  border-bottom: 1px solid var(--border) !important;
  white-space: nowrap;
}
:deep(.ant-table-tbody > tr:hover > td) {
  background: var(--panel-2) !important;
}
:deep(.ant-table-cell-fix-left),
:deep(.ant-table-cell-fix-right) {
  background: var(--panel) !important;
}
</style>
