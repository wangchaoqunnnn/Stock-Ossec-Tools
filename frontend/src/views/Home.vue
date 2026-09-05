<script setup>
import { ref } from 'vue'
import { fetchIndices } from '../api'
import { useAutoRefresh } from '../composables/useAutoRefresh'

const emit = defineEmits(['navigate'])

// 首页指数速览：实时拉取 A 股主要指数，每 15 秒自动刷新
const SHOWN_INDICES = ['上证指数', '深证成指', '创业板指', '科创50']
const homeStats = ref(
  SHOWN_INDICES.map((name) => ({ name, value: '--', changeText: '--', up: true, loaded: false }))
)

async function loadHomeIndices() {
  try {
    const data = await fetchIndices('cn')
    const items = (data && data.items) || []
    const map = {}
    items.forEach((it) => { map[it.name] = it })
    homeStats.value = SHOWN_INDICES.map((name) => {
      const it = map[name]
      if (!it || it.now === null || it.now === undefined) {
        const prev = homeStats.value.find((s) => s.name === name)
        return prev || { name, value: '--', changeText: '--', up: true, loaded: false }
      }
      const pctVal = Number(it.change_pct) || 0
      return {
        name,
        value: Number(it.now).toFixed(2),
        changeText: `${pctVal > 0 ? '+' : ''}${pctVal.toFixed(2)}%`,
        up: pctVal >= 0,
        loaded: true,
      }
    })
  } catch (e) {
    // 加载失败保留上一次数据（避免闪断），后端不可用时显示占位
  }
}

useAutoRefresh(loadHomeIndices, 15000)

const modules = [
  {
    key: 'tools',
    icon: '🔍',
    title: '个股查询',
    desc: '股票代码/名称搜索，完整行情详情，关注清单管理',
    color: '#4f7cff',
  },
  {
    key: 'utility',
    icon: '⚡',
    title: '量化工具',
    desc: '今日关注、选股器、异动寻龙，策略数据一览',
    color: '#7c5cff',
  },
  {
    key: 'rankings',
    icon: '📊',
    title: '行情中枢',
    desc: '资金流向、市场情绪、涨幅榜单、行业板块动态',
    color: '#ff6b6b',
  },
  {
    key: 'portfolio',
    icon: '✩',
    title: '个股打分',
    desc: '六维智能打分（基础面/板块/技术面/短线情绪/买点），给出买卖建议',
    color: '#51cf66',
  },
  {
    key: 'community',
    icon: '📝',
    title: '复盘社区',
    desc: '精选复盘文章，每日盘前/午盘/收盘深度解读',
    color: '#ff922b',
  },
]
</script>

<template>
  <div class="home-page">
    <!-- 欢迎区 -->
    <section class="hero-section">
      <div class="hero-content">
        <div class="hero-tag">QUANT TERMINAL</div>
        <h1 class="hero-title">老王量化 · 自建终端</h1>
        <p class="hero-desc">免登录 · 免费 · 纯只读展示的股票行情查询与分析工具</p>
      </div>
      <div class="hero-stats">
        <div v-for="stat in homeStats" :key="stat.name" class="stat-item">
          <div class="stat-label">{{ stat.name }}</div>
          <div class="stat-value num">{{ stat.value }}</div>
          <div class="stat-change num" :class="stat.up ? 'up' : 'down'">{{ stat.changeText }}</div>
        </div>
      </div>
    </section>

    <!-- 功能模块入口 -->
    <section class="modules-section">
      <h2 class="section-title">功能模块</h2>
      <div class="modules-grid">
        <div
          v-for="mod in modules"
          :key="mod.key"
          class="module-card"
          :style="{ '--accent-color': mod.color }"
          @click="emit('navigate', mod.key)"
        >
          <div class="module-icon">{{ mod.icon }}</div>
          <div class="module-title">{{ mod.title }}</div>
          <div class="module-desc">{{ mod.desc }}</div>
          <div class="module-arrow">进入 →</div>
        </div>
      </div>
    </section>

    <!-- 免责声明 -->
    <footer class="page-foot">
      数据来源于公开行情接口，仅供学习参考，不构成投资建议 · 行情可能存在延迟或误差
    </footer>
  </div>
</template>

<style scoped>
.home-page {
  display: flex;
  flex-direction: column;
  gap: 28px;
}

/* 欢迎区 */
.hero-section {
  background: linear-gradient(135deg, rgba(79, 124, 255, 0.15), rgba(124, 92, 255, 0.1));
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 28px 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  flex-wrap: wrap;
}
.hero-tag {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 3px;
  color: var(--accent);
  margin-bottom: 8px;
}
.hero-title {
  font-size: 28px;
  font-weight: 700;
  margin: 0 0 8px;
  background: linear-gradient(135deg, #e6e6f0, #9a9ab4);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.hero-desc {
  color: var(--text-2);
  font-size: 14px;
  margin: 0;
}
.hero-stats {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}
.stat-item {
  text-align: center;
  min-width: 90px;
}
.stat-label {
  font-size: 12px;
  color: var(--text-3);
  margin-bottom: 4px;
}
.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: var(--text);
}
.stat-change {
  font-size: 13px;
  margin-top: 2px;
}

/* 功能模块 */
.section-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 16px;
  color: var(--text);
}
.modules-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
}
.module-card {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 22px 20px;
  cursor: pointer;
  transition: all 0.25s ease;
  position: relative;
  overflow: hidden;
}
.module-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--accent-color);
  opacity: 0;
  transition: opacity 0.25s;
}
.module-card:hover {
  transform: translateY(-4px);
  border-color: var(--accent-color);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}
.module-card:hover::before {
  opacity: 1;
}
.module-icon {
  font-size: 32px;
  margin-bottom: 12px;
}
.module-title {
  font-size: 17px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 6px;
}
.module-desc {
  font-size: 13px;
  color: var(--text-3);
  line-height: 1.6;
  margin-bottom: 14px;
}
.module-arrow {
  font-size: 13px;
  color: var(--accent-color);
  font-weight: 500;
}

.page-foot {
  margin-top: 12px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
  color: var(--text-3);
  font-size: 12px;
  text-align: center;
  line-height: 1.8;
}

@media (max-width: 768px) {
  .hero-section {
    padding: 20px;
  }
  .hero-title {
    font-size: 22px;
  }
  .hero-stats {
    gap: 16px;
  }
  .stat-item {
    min-width: 70px;
  }
  .stat-value {
    font-size: 16px;
  }
}
</style>
