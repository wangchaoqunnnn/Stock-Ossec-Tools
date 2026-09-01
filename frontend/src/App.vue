<script setup>
import { ref, onMounted } from 'vue'
import Tools from './views/Tools.vue'

const now = ref('')
const tick = () => {
  now.value = new Date().toLocaleString('zh-CN', { hour12: false })
}
onMounted(() => {
  tick()
  setInterval(tick, 1000)
})
</script>

<template>
  <div class="page-tools">
    <header class="page-head">
      <div>
        <h1 class="page-title">股票数据查询工具</h1>
        <div class="page-sub">个股查询 · 主要指数 —— 免登录 · 免费 · 纯只读展示</div>
      </div>
      <div class="num page-sub">{{ now }}</div>
    </header>
    <Tools />
    <footer class="page-foot">
      数据来源于公开行情接口，仅供学习参考，不构成投资建议 · 行情可能存在延迟或误差
    </footer>
  </div>
</template>

<style scoped>
.page-foot {
  margin-top: 32px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
  color: var(--text-3);
  font-size: 12px;
  text-align: center;
}
</style>
