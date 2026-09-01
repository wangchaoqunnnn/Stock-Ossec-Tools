<script setup>
import StockQuery from '../components/StockQuery.vue'
import IndicesPanel from '../components/IndicesPanel.vue'
import Watchlist from '../components/Watchlist.vue'

const emit = defineEmits(['navigate'])
</script>

<template>
  <div class="tools-page">
    <header class="page-head">
      <div>
        <div class="brand-tag">QUANT TERMINAL</div>
        <h1 class="page-title">个股查询与关注清单</h1>
        <div class="page-sub">输入代码或名称快速查询，支持关注、排序、列配置、备注与批量管理</div>
      </div>
      <a-button class="utility-entry" @click="emit('navigate', 'utility')">
        量化工具 →
      </a-button>
    </header>
    <div class="tools-shell">
      <StockQuery />
      <IndicesPanel />
      <Watchlist />
    </div>
    <footer class="page-foot">
      数据来源于公开行情接口，仅供学习参考，不构成投资建议 · 行情可能存在延迟或误差 · 关注清单数据保存在本地浏览器
    </footer>
  </div>
</template>

<style scoped>
.tools-page {
  display: flex;
  flex-direction: column;
  gap: 0;
}
.page-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
}
.brand-tag {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 2px;
  color: var(--accent);
  margin-bottom: 6px;
}
.page-title {
  font-size: 22px;
  font-weight: 700;
  margin: 0 0 6px;
  color: var(--text);
}
.page-sub {
  color: var(--text-3);
  font-size: 13px;
}
.utility-entry {
  margin-top: 8px;
}
.tools-shell {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.page-foot {
  margin-top: 32px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
  color: var(--text-3);
  font-size: 12px;
  text-align: center;
  line-height: 1.8;
}
</style>
