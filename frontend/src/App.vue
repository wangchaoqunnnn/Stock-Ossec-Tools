<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { message } from 'ant-design-vue'
import Home from './views/Home.vue'
import Portfolio from './views/Portfolio.vue'
import Tools from './views/Tools.vue'
import Utility from './views/Utility.vue'
import Rankings from './views/Rankings.vue'
import Community from './views/Community.vue'

const now = ref('')
const currentView = ref('rankings')
let timer = null

const views = {
  home: Home,
  portfolio: Portfolio,
  tools: Tools,
  utility: Utility,
  rankings: Rankings,
  community: Community,
}

const navItems = [
  { key: 'home', label: '首页', icon: '⌂' },
  { key: 'portfolio', label: '组合', icon: '◈' },
  { key: 'tools', label: '工具', icon: '⚙' },
  { key: 'rankings', label: '行情', icon: '📈' },
  { key: 'community', label: '复盘', icon: '▤' },
]

const pageTitles = {
  home: '首页',
  portfolio: '投资组合',
  tools: '个股查询',
  utility: '量化工具',
  rankings: '行情中枢',
  community: '复盘',
}

function tick() {
  now.value = new Date().toLocaleString('zh-CN', { hour12: false })
}

function switchView(key) {
  currentView.value = key
  window.scrollTo(0, 0)
}

function navigateTo(key) {
  currentView.value = key
  window.scrollTo(0, 0)
}

function showNotify() {
  message.info('暂无新通知')
}

function showSettings() {
  message.info('设置功能正在建设中')
}

// 提供给子组件的导航方法
defineExpose({ navigateTo })

onMounted(() => {
  tick()
  timer = setInterval(tick, 1000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<template>
  <div class="app-layout">
    <!-- 顶部导航栏 -->
    <header class="top-nav">
      <div class="nav-left">
        <div class="logo" @click="switchView('home')">
          <span class="logo-icon">📊</span>
          <span class="logo-text">量化终端</span>
        </div>
      </div>
      <div class="nav-center">
        <span class="page-header-title">{{ pageTitles[currentView] }}</span>
      </div>
      <div class="nav-right">
        <span class="nav-time num">{{ now }}</span>
        <button class="nav-btn" title="通知" @click="showNotify">
          <span class="nav-icon">🔔</span>
        </button>
        <button class="nav-btn" title="设置" @click="showSettings">
          <span class="nav-icon">⚙</span>
        </button>
        <div class="user-avatar" title="用户">
          <span>👤</span>
        </div>
      </div>
    </header>

    <!-- 主内容区 -->
    <main class="main-content">
      <div class="content-inner">
        <component :is="views[currentView]" @navigate="navigateTo" />
      </div>
    </main>

    <!-- 底部导航栏 -->
    <nav class="bottom-nav">
      <button
        v-for="item in navItems"
        :key="item.key"
        class="bottom-nav-item"
        :class="{ active: currentView === item.key }"
        @click="switchView(item.key)"
      >
        <span class="bottom-nav-icon">{{ item.icon }}</span>
        <span class="bottom-nav-label">{{ item.label }}</span>
      </button>
    </nav>
  </div>
</template>

<style scoped>
.app-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg);
}

/* 顶部导航 */
.top-nav {
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 52px;
  background: rgba(18, 18, 28, 0.92);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border);
}
.nav-left {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 180px;
}
.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}
.logo-icon {
  font-size: 20px;
}
.logo-text {
  font-size: 16px;
  font-weight: 700;
  background: linear-gradient(135deg, #4f7cff, #7c5cff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.nav-center {
  flex: 1;
  text-align: center;
}
.page-header-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
}
.nav-right {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 180px;
  justify-content: flex-end;
}
.nav-time {
  font-size: 12px;
  color: var(--text-3);
  margin-right: 8px;
}
.nav-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 6px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}
.nav-btn:hover {
  background: var(--panel-2);
}
.nav-icon {
  font-size: 16px;
}
.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--panel-2);
  border: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 16px;
}

/* 主内容 */
.main-content {
  flex: 1;
  padding-bottom: 70px;
}
.content-inner {
  max-width: 1280px;
  margin: 0 auto;
  padding: 24px 20px 32px;
}

/* 底部导航 */
.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: space-around;
  height: 60px;
  background: rgba(18, 18, 28, 0.95);
  backdrop-filter: blur(12px);
  border-top: 1px solid var(--border);
  padding: 0 12px;
}
.bottom-nav-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  background: none;
  border: none;
  cursor: pointer;
  padding: 6px 0;
  border-radius: 8px;
  transition: all 0.2s;
  color: var(--text-3);
}
.bottom-nav-item:hover {
  color: var(--text-2);
  background: var(--panel-2);
}
.bottom-nav-item.active {
  color: var(--accent);
}
.bottom-nav-icon {
  font-size: 18px;
}
.bottom-nav-label {
  font-size: 11px;
  font-weight: 500;
}

@media (max-width: 768px) {
  .top-nav {
    padding: 0 12px;
  }
  .nav-time {
    display: none;
  }
  .content-inner {
    padding: 16px 12px 24px;
  }
  .nav-left,
  .nav-right {
    min-width: auto;
  }
}
</style>
