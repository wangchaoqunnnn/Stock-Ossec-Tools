<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { message } from 'ant-design-vue'
import { fetchIndices } from '../api'
import { trendClass, signed, pct } from '../utils/format'

const markets = [
  { key: 'cn', label: 'A股' },
  { key: 'asia', label: '亚太' },
  { key: 'us', label: '美股' },
  { key: 'futures', label: '期货' },
]
const active = ref('cn')
const items = ref([])
const loading = ref(false)
const source = ref('')
const sourceLabel = { eastmoney: '东方财富', tencent: '腾讯行情' }
const autoRefresh = ref(true)
const lastUpdate = ref('')
const countdown = ref(60)
let refreshTimer = null
let countdownTimer = null

async function load(market) {
  loading.value = true
  try {
    const data = await fetchIndices(market)
    items.value = data.items || []
    source.value = data.source || ''
    lastUpdate.value = new Date().toLocaleTimeString('zh-CN', { hour12: false })
    countdown.value = 60
  } catch (e) {
    items.value = []
    message.error(`指数加载失败：${e.message}`)
  } finally {
    loading.value = false
  }
}

function switchMarket(key) {
  active.value = key
  load(key)
}

function toggleAutoRefresh(checked) {
  // v-model:checked 已更新 autoRefresh，这里只负责启停定时器
  // （不要再翻转 autoRefresh，否则与 v-model 双重取反导致开关无效）
  if (checked) {
    countdown.value = 60
    startTimers()
  } else {
    stopTimers()
  }
}

function manualRefresh() {
  load(active.value)
}

function startTimers() {
  stopTimers()
  countdownTimer = setInterval(() => {
    countdown.value = Math.max(0, countdown.value - 1)
    if (countdown.value <= 0 && autoRefresh.value) {
      load(active.value)
    }
  }, 1000)
}

function stopTimers() {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
}

onMounted(() => {
  load('cn')
  if (autoRefresh.value) startTimers()
})

onUnmounted(() => {
  stopTimers()
})
</script>

<template>
  <section class="terminal-card">
    <div class="terminal-card-head">
      <div>
        <div class="terminal-card-title">主要指数</div>
        <div class="card-sub" v-if="lastUpdate">更新于 {{ lastUpdate }}</div>
      </div>
      <div class="head-right">
        <a-tag v-if="source" size="small" color="blue">{{ sourceLabel[source] || source }}</a-tag>
        <a-radio-group :value="active" size="small" button-style="solid" @change="(e) => switchMarket(e.target.value)">
          <a-radio-button v-for="m in markets" :key="m.key" :value="m.key">{{ m.label }}</a-radio-button>
        </a-radio-group>
        <a-switch
          v-model:checked="autoRefresh"
          size="small"
          checked-children="60s"
          un-checked-children="关闭"
          @change="toggleAutoRefresh"
        />
        <a-button size="small" :loading="loading" @click="manualRefresh">
          <template #icon>
            <span :class="{ 'spin-icon': loading }">↻</span>
          </template>
        </a-button>
      </div>
    </div>

    <div class="index-body">
      <a-spin :spinning="loading">
        <div v-if="items.length" class="index-grid">
          <div v-for="item in items" :key="item.secid" class="index-card">
            <div class="index-name">{{ item.name }}</div>
            <div class="index-now num" :class="trendClass(item.change_pct)">
              {{ item.now !== null && item.now !== undefined ? item.now.toFixed(2) : '--' }}
            </div>
            <div class="index-chg num" :class="trendClass(item.change_pct)">
              {{ signed(item.change) }} / {{ pct(item.change_pct) }}
            </div>
          </div>
        </div>
        <div v-else class="index-empty">暂无指数数据</div>
      </a-spin>
    </div>
  </section>
</template>

<style scoped>
.card-sub {
  font-size: 12px;
  color: var(--text-3);
  margin-top: 2px;
}
.head-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.index-body {
  padding: 16px 18px 18px;
}
.index-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
}
.index-card {
  background: var(--panel-2);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 14px 16px;
  transition: border-color 0.2s;
}
.index-card:hover {
  border-color: var(--accent);
}
.index-name {
  color: var(--text-2);
  font-size: 13px;
}
.index-now {
  font-size: 26px;
  font-weight: 700;
  margin: 6px 0 4px;
}
.index-chg {
  font-size: 13px;
}
.index-empty {
  padding: 32px 0;
  text-align: center;
  color: var(--text-3);
}
.spin-icon {
  display: inline-block;
  animation: spin 1s linear infinite;
}
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
