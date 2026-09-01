<script setup>
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { searchStocks, fetchQuote } from '../api'
import { trendClass, signed, pct, num, mv, volume } from '../utils/format'

const keyword = ref('')
const options = ref([])
const searching = ref(false)
const quote = ref(null)
const quoteLoading = ref(false)
const sourceLabel = { eastmoney: '东方财富', tencent: '腾讯行情' }

let timer = null
let seq = 0

async function doSearch(val) {
  const kw = (val || '').trim()
  if (!kw) {
    options.value = []
    return
  }
  searching.value = true
  const id = ++seq
  try {
    const list = await searchStocks(kw)
    if (id !== seq) return
    options.value = list.map((s) => ({
      value: `${s.code} ${s.name}`,
      code: s.code,
      name: s.name,
      type: s.security_type || s.market_type,
    }))
  } catch (e) {
    if (id !== seq) return
    options.value = []
    message.error(e.message)
  } finally {
    if (id === seq) searching.value = false
  }
}

function onSearch(val) {
  clearTimeout(timer)
  timer = setTimeout(() => doSearch(val), 300)
}

async function onSelect(value, option) {
  // ant-design-vue: @select 第一参数为选中 value（字符串），第二参数为 option 记录
  const code = (option && option.code) || String(value).split(' ')[0]
  await loadQuote(code)
}

async function onPressEnter(rawText) {
  // show-search 模式下 v-model 只在选中时更新，需用输入框当前文本
  const kw = (rawText || '').trim()
  if (!kw) return
  // 纯数字视为代码直接查询
  if (/^\d{6}$/.test(kw)) {
    await loadQuote(kw)
    return
  }
  if (options.value.length) {
    await loadQuote(options.value[0].code)
  } else {
    await doSearch(kw)
    if (options.value.length) await loadQuote(options.value[0].code)
  }
}

function onInputKeyDown(e) {
  if (e && e.key === 'Enter') {
    e.preventDefault()
    onPressEnter(e.target && e.target.value)
  }
}

async function loadQuote(code) {
  const c = String(code || '').trim()
  if (!/^\d{6}$/.test(c)) {
    message.warning('请输入有效的 6 位股票代码')
    return
  }
  quoteLoading.value = true
  try {
    const data = await fetchQuote(c)
    quote.value = data
  } catch (e) {
    quote.value = null
    message.error(e.message)
  } finally {
    quoteLoading.value = false
  }
}

// 默认展示一只参考股票
onMounted(() => loadQuote('600519'))
</script>

<template>
  <section class="hero terminal-card">
    <div class="hero-head">
      <div class="terminal-card-title">股票查询</div>
      <div class="hero-tip">输入股票代码或名称关键词（如 600519 / 贵州茅台 / 茅台）</div>
    </div>

    <div class="hero-body">
      <a-select
        v-model:value="keyword"
        :options="options"
        show-search
        :filter-option="false"
        :loading="searching"
        placeholder="输入代码或名称搜索…"
        style="width: 100%"
        @search="onSearch"
        @select="onSelect"
        @input-key-down="onInputKeyDown"
      >
        <template #option="{ value: v, code, name, type }">
          <div class="opt-row">
            <span class="opt-name num">{{ name }}</span>
            <span class="opt-code num">{{ code }}</span>
            <span class="opt-type">{{ type }}</span>
          </div>
        </template>
      </a-select>

      <a-spin :spinning="quoteLoading">
        <div v-if="quote" class="quote-panel">
          <div class="quote-top">
            <div class="quote-name-row">
              <span class="quote-name">{{ quote.name }}</span>
              <span class="quote-code num">{{ quote.code }}</span>
              <a-tag
                v-if="quote.source"
                size="small"
                color="blue"
                class="quote-source"
              >{{ sourceLabel[quote.source] || quote.source }}</a-tag>
            </div>
            <div class="quote-price-row">
              <span class="quote-price num" :class="trendClass(quote.change_pct)">{{ num(quote.now_price, 2) }}</span>
              <span class="quote-change num" :class="trendClass(quote.change_pct)">
                {{ signed(quote.change) }} &nbsp; {{ pct(quote.change_pct) }}
              </span>
            </div>
          </div>

          <a-descriptions :column="4" size="small" bordered class="quote-desc">
            <a-descriptions-item label="今开"><span class="num">{{ num(quote.open) }}</span></a-descriptions-item>
            <a-descriptions-item label="最高"><span class="num up">{{ num(quote.high) }}</span></a-descriptions-item>
            <a-descriptions-item label="最低"><span class="num down">{{ num(quote.low) }}</span></a-descriptions-item>
            <a-descriptions-item label="昨收"><span class="num">{{ num(quote.prev_close) }}</span></a-descriptions-item>
            <a-descriptions-item label="成交量"><span class="num">{{ volume(quote.volume) }}</span></a-descriptions-item>
            <a-descriptions-item label="成交额"><span class="num">{{ mv(quote.amount) }}</span></a-descriptions-item>
            <a-descriptions-item label="换手率"><span class="num">{{ pct(quote.turnover) }}</span></a-descriptions-item>
            <a-descriptions-item label="量比"><span class="num">{{ num(quote.volume_ratio, 2) }}</span></a-descriptions-item>
            <a-descriptions-item label="市盈率(TTM)"><span class="num">{{ num(quote.pe, 2) }}</span></a-descriptions-item>
            <a-descriptions-item label="市净率"><span class="num">{{ num(quote.pb, 2) }}</span></a-descriptions-item>
            <a-descriptions-item label="振幅"><span class="num">{{ pct(quote.amplitude) }}</span></a-descriptions-item>
            <a-descriptions-item label="更新时间"><span class="num">{{ quote.time || '--' }}</span></a-descriptions-item>
            <a-descriptions-item label="总市值"><span class="num">{{ mv(quote.total_mv) }}</span></a-descriptions-item>
            <a-descriptions-item label="流通市值"><span class="num">{{ mv(quote.float_mv) }}</span></a-descriptions-item>
          </a-descriptions>
        </div>
        <div v-else class="quote-empty">输入代码或名称后回车，即可查看个股行情详情</div>
      </a-spin>
    </div>
  </section>
</template>

<style scoped>
.hero-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid var(--border);
  flex-wrap: wrap;
  gap: 6px;
}
.hero-tip {
  color: var(--text-3);
  font-size: 12px;
}
.hero-body {
  padding: 18px;
}
.opt-row {
  display: flex;
  align-items: center;
  gap: 12px;
}
.opt-name {
  font-weight: 600;
}
.opt-code {
  color: var(--text-2);
}
.opt-type {
  margin-left: auto;
  color: var(--text-3);
  font-size: 12px;
}
.quote-panel {
  margin-top: 16px;
}
.quote-top {
  margin-bottom: 12px;
}
.quote-name-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.quote-name {
  font-size: 20px;
  font-weight: 700;
}
.quote-code {
  color: var(--text-2);
  font-size: 14px;
}
.quote-source {
  margin-left: 4px;
}
.quote-price-row {
  display: flex;
  align-items: baseline;
  gap: 16px;
  margin-top: 6px;
}
.quote-price {
  font-size: 34px;
  font-weight: 700;
  line-height: 1.1;
}
.quote-change {
  font-size: 16px;
}
.quote-empty {
  margin-top: 16px;
  padding: 36px 0;
  text-align: center;
  color: var(--text-3);
  border: 1px dashed var(--border);
  border-radius: var(--radius);
}
:deep(.quote-desc .ant-descriptions-item-label) {
  color: var(--text-2);
  background: var(--panel-2);
  width: 110px;
}
:deep(.quote-desc .ant-descriptions-item-content) {
  background: var(--panel);
}
@media (max-width: 900px) {
  :deep(.quote-desc .ant-descriptions-item) {
    min-width: 50%;
  }
}
</style>
