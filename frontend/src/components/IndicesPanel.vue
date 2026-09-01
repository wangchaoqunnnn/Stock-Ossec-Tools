<script setup>
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { fetchIndices } from '../api'
import { trendClass, signed, pct } from '../utils/format'

const markets = [
  { key: 'cn', label: 'A股' },
  { key: 'hk', label: '港股' },
  { key: 'us', label: '美股' },
]
const active = ref('cn')
const items = ref([])
const loading = ref(false)
const source = ref('')
const sourceLabel = { eastmoney: '东方财富', tencent: '腾讯行情' }

async function load(market) {
  loading.value = true
  try {
    const data = await fetchIndices(market)
    items.value = data.items || []
    source.value = data.source || ''
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

onMounted(() => load('cn'))
</script>

<template>
  <section class="terminal-card">
    <div class="terminal-card-head">
      <div class="terminal-card-title">主要指数</div>
      <div class="head-right">
        <a-tag v-if="source" size="small" color="blue">{{ sourceLabel[source] || source }}</a-tag>
        <a-radio-group :value="active" size="small" button-style="solid" @change="(e) => switchMarket(e.target.value)">
          <a-radio-button v-for="m in markets" :key="m.key" :value="m.key">{{ m.label }}</a-radio-button>
        </a-radio-group>
      </div>
    </div>

    <div class="index-body">
      <a-spin :spinning="loading">
        <div v-if="items.length" class="index-grid">
          <div v-for="item in items" :key="item.secid" class="index-card">
            <div class="index-name">{{ item.name }}</div>
            <div class="index-now num" :class="trendClass(item.change_pct)">{{ item.now !== null && item.now !== undefined ? item.now.toFixed(2) : '--' }}</div>
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
.head-right {
  display: flex;
  align-items: center;
  gap: 10px;
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
</style>
