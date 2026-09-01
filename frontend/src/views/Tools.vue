<script setup>
import StockQuery from '../components/StockQuery.vue'
import IndicesPanel from '../components/IndicesPanel.vue'
</script>

<template>
  <div class="tools-shell">
    <StockQuery />
    <IndicesPanel />
  </div>
</template>

<style scoped>
.tools-shell {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
</style>
