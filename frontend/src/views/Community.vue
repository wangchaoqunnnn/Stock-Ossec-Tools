<script setup>
import { ref } from 'vue'

const emit = defineEmits(['navigate'])

const activeTab = ref('all')
const tabs = [
  { key: 'all', label: '全部' },
  { key: 'opinion', label: '观点' },
  { key: 'long', label: '长文' },
]

const activeSubTab = ref('latest')
const subTabs = [
  { key: 'latest', label: '最新发帖' },
  { key: 'reply', label: '最新回复' },
  { key: 'essence', label: '精华' },
  { key: 'recommend', label: '推荐' },
]

const searchKeyword = ref('')
const expandedId = ref(null)

// 模拟复盘文章数据
const articles = [
  {
    id: 1,
    author: '机器人老王',
    avatar: '王',
    time: '7小时前',
    location: '上海',
    type: 'long',
    typeLabel: '长文',
    title: '「A股收盘复盘 09-01」· 缩量高低切，粮食传媒唱戏',
    summary: '一、全天大盘：指数分化，金融护盘，个股涨多跌少。今日三大指数收盘涨跌互现，权重与科技硬件拖累指数，低位小票反而活跃：上证指数收 3979.89 点，跌 0.16%；深证成指收 13872.38 点，跌 1.02%；创业板指收 3393.43 点，跌 1.32%。',
    content: `一、全天大盘：指数分化，金融护盘，个股涨多跌少

今日三大指数收盘涨跌互现，权重与科技硬件拖累指数，低位小票反而活跃：
- 上证指数收 3979.89 点，跌 0.16%
- 深证成指收 13872.38 点，跌 1.02%
- 创业板指收 3393.43 点，跌 1.32%

二、板块表现：粮食种业爆发，科技硬件回调

粮食种业在美豆期货创近三年新高刺激下全线爆发，半导体、PCB等科技硬件天量失血，资金高低切特征鲜明。

涨幅居前：
- 种植业与林业 +4.2%
- 文化传媒 +3.5%
- 银行 +1.2%
- 证券 +2.1%

跌幅居前：
- 半导体 -3.8%
- 元件 -4.5%
- 电池 -3.2%
- 光伏设备 -2.3%

三、资金面：主力净流出 309 亿，北向逆势净流入

主力资金净流出 309.2 亿，同比昨日多流出 252.4 亿。北向资金逆势净流入 28.5 亿，连续 3 日加仓。

四、后市展望：关注低位补涨机会

缩量行情下，资金高低切特征明显，建议关注低位滞涨板块的补涨机会，同时警惕高位科技股的回调风险。`,
    tags: ['每日复盘', '收盘复盘'],
    comments: 0,
    likes: 0,
    shares: 30,
    hasImage: true,
  },
  {
    id: 2,
    author: '机器人老王',
    avatar: '王',
    time: '10小时前',
    location: '上海',
    type: 'long',
    typeLabel: '长文',
    title: '「A股午盘复盘 09-01」· 种业粮食爆发，科技硬件回调',
    summary: '一句话看盘：指数分化、个股普涨——上证靠金融托底勉强翻红，科创50领跌；粮食种业在美豆期货创近三年新高刺激下全线爆发，半导体、PCB等科技硬件天量失血，资金高低切特征鲜明。',
    content: `一句话看盘：指数分化、个股普涨——上证靠金融托底勉强翻红，科创50领跌；粮食种业在美豆期货创近三年新高刺激下全线爆发，半导体、PCB等科技硬件天量失血，资金高低切特征鲜明。

一、上午大盘实录

截至午间收盘：
- 上证指数 3987.56 点，+0.04%
- 深证成指 13956.78 点，-0.42%
- 创业板指 3421.56 点，-0.51%
- 科创50 1678.32 点，-0.45%

二、板块异动

种业粮食板块集体爆发，农发种业、隆平高科涨停。半导体板块回调，中芯国际跌超 3%。

三、资金流向

上午主力资金净流出 180 亿，北向资金净流入 15 亿。`,
    tags: ['每日复盘', '午盘复盘'],
    comments: 0,
    likes: 0,
    shares: 21,
    hasImage: true,
  },
  {
    id: 3,
    author: '机器人老王',
    avatar: '王',
    time: '13小时前',
    location: '上海',
    type: 'long',
    typeLabel: '长文',
    title: '「A股盘前前瞻 09-01」· 外围温和消化，AI硬件催化密集',
    summary: '一、外围小结：美股小幅收跌，费半AI景气独红。隔夜美股（8月31日收盘）三大指数温和回落：道琼斯指数收 53185.90 点，跌 0.70%；标普500收 7686.14 点，跌 0.33%；纳斯达克收...',
    content: `一、外围小结：美股小幅收跌，费半AI景气独红

隔夜美股（8月31日收盘）三大指数温和回落：
- 道琼斯指数收 53185.90 点，跌 0.70%
- 标普500收 7686.14 点，跌 0.33%
- 纳斯达克收 18092.56 点，跌 0.28%

费城半导体指数逆势上涨 1.2%，AI 硬件景气度持续。

二、今日关注

1. 国家统计局 PMI 数据公布
2. 半导体板块能否企稳反弹
3. 粮食种业持续性观察

三、操作策略

建议控制仓位，关注低位补涨机会，避免追高。`,
    tags: ['每日复盘', '盘前前瞻'],
    comments: 0,
    likes: 0,
    shares: 15,
    hasImage: true,
  },
  {
    id: 4,
    author: '量化观察',
    avatar: '量',
    time: '15小时前',
    location: '北京',
    type: 'opinion',
    typeLabel: '观点',
    title: '9月投资策略：均衡配置，攻守兼备',
    summary: '进入9月，市场面临中报披露完毕后的业绩真空期，同时政策预期升温。建议采用均衡配置策略，一方面关注低估值蓝筹的防御属性，另一方面布局科技成长的弹性机会。',
    content: `进入9月，市场面临中报披露完毕后的业绩真空期，同时政策预期升温。

建议采用均衡配置策略：
1. 低估值蓝筹：银行、保险、公用事业，提供稳定分红
2. 科技成长：AI、半导体、新能源，关注业绩兑现
3. 消费复苏：食品饮料、医药，估值修复机会

仓位建议控制在 6-7 成，留有余地应对市场波动。`,
    tags: ['投资策略', '月度策略'],
    comments: 5,
    likes: 23,
    shares: 8,
    hasImage: false,
  },
  {
    id: 5,
    author: '市场雷达',
    avatar: '市',
    time: '1天前',
    location: '深圳',
    type: 'opinion',
    typeLabel: '观点',
    title: '北向资金连续3日净流入，释放什么信号？',
    summary: '北向资金今日净流入28.5亿，连续3日净流入，累计净流入超80亿。从流向来看，主要集中在银行、电力、食品饮料等低估值板块，显示外资对A股低位配置价值的认可。',
    content: `北向资金今日净流入 28.5 亿，连续 3 日净流入，累计净流入超 80 亿。

从流向来看：
- 银行 +12.3 亿
- 电力 +8.5 亿
- 食品饮料 +6.2 亿
- 半导体 -5.8 亿

外资主要集中在低估值板块，显示对 A 股低位配置价值的认可。

历史数据显示，北向资金连续净流入后，市场短期上涨概率较高。`,
    tags: ['资金流向', '北向资金'],
    comments: 12,
    likes: 45,
    shares: 18,
    hasImage: false,
  },
  {
    id: 6,
    author: '机器人老王',
    avatar: '王',
    time: '1天前',
    location: '上海',
    type: 'long',
    typeLabel: '长文',
    title: '「8月市场回顾」· 震荡磨底，结构分化',
    summary: '8月A股整体呈现震荡磨底态势，上证指数月跌1.2%，创业板指月跌3.5%。板块分化明显，煤炭、银行等低估值板块领涨，新能源、半导体等成长板块回调。9月关注政策窗口期的投资机会。',
    content: `8月A股整体呈现震荡磨底态势：
- 上证指数月跌 1.2%
- 深证成指月跌 2.8%
- 创业板指月跌 3.5%
- 科创50月跌 4.2%

板块分化明显：
涨幅居前：煤炭 +5.2%、银行 +3.8%、电力 +2.5%
跌幅居前：半导体 -8.5%、新能源 -6.2%、医药 -4.8%

9月展望：
关注政策窗口期，市场有望迎来反弹机会。建议均衡配置，把握结构性行情。`,
    tags: ['月度回顾', '市场总结'],
    comments: 8,
    likes: 56,
    shares: 32,
    hasImage: true,
  },
]

const filteredArticles = ref(articles)

function toggleExpand(id) {
  expandedId.value = expandedId.value === id ? null : id
}

function formatTime(time) {
  return time
}
</script>

<template>
  <div class="community-page">
    <!-- 页面头部 -->
    <header class="page-head">
      <div>
        <div class="brand-tag">REVIEW CENTER</div>
        <h1 class="page-title">复盘</h1>
        <div class="page-sub">精选市场复盘文章，每日盘前/午盘/收盘深度解读</div>
      </div>
    </header>

    <!-- 搜索框 -->
    <div class="search-bar">
      <a-input
        v-model:value="searchKeyword"
        placeholder="搜索内容"
        size="large"
        class="search-input"
      >
        <template #prefix>
          <span class="search-icon">🔍</span>
        </template>
      </a-input>
    </div>

    <!-- 标签导航 -->
    <div class="tab-row">
      <div class="main-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          class="main-tab"
          :class="{ active: activeTab === tab.key }"
          @click="activeTab = tab.key"
        >
          {{ tab.label }}
        </button>
      </div>
      <div class="sub-tabs">
        <button
          v-for="tab in subTabs"
          :key="tab.key"
          class="sub-tab"
          :class="{ active: activeSubTab === tab.key }"
          @click="activeSubTab = tab.key"
        >
          {{ tab.label }}
        </button>
      </div>
    </div>

    <!-- 文章列表 -->
    <div class="article-list">
      <article
        v-for="article in filteredArticles"
        :key="article.id"
        class="article-card"
        :class="{ expanded: expandedId === article.id }"
      >
        <div class="article-header">
          <div class="author-info">
            <div class="author-avatar">{{ article.avatar }}</div>
            <div class="author-meta">
              <div class="author-name">{{ article.author }}</div>
              <div class="author-time">
                {{ article.time }} · {{ article.location }}
              </div>
            </div>
          </div>
          <a-tag size="small" color="blue" class="type-tag">{{ article.typeLabel }}</a-tag>
        </div>

        <h3 class="article-title" @click="toggleExpand(article.id)">
          {{ article.title }}
        </h3>

        <div class="article-body">
          <div class="article-summary" v-if="expandedId !== article.id">
            {{ article.summary }}
          </div>
          <div class="article-content" v-else>
            <pre class="content-text">{{ article.content }}</pre>
          </div>
          <div v-if="article.hasImage && expandedId !== article.id" class="article-image-placeholder">
            <div class="image-box">
              <span class="image-icon">📊</span>
              <span class="image-text">配图</span>
            </div>
          </div>
        </div>

        <div class="article-footer">
          <div class="article-tags">
            <a-tag v-for="tag in article.tags" :key="tag" size="small" class="topic-tag">
              {{ tag }}
            </a-tag>
          </div>
          <div class="article-actions">
            <span class="action-item">
              <span class="action-icon">💬</span>
              <span class="action-count">{{ article.comments }}</span>
            </span>
            <span class="action-item">
              <span class="action-icon">👍</span>
              <span class="action-count">{{ article.likes }}</span>
            </span>
            <span class="action-item share-btn" @click="toggleExpand(article.id)">
              <span class="action-icon">{{ expandedId === article.id ? '收起' : '展开' }}</span>
            </span>
          </div>
        </div>
      </article>
    </div>

    <footer class="page-foot">
      复盘文章为精选演示内容，仅供参考 · 不构成投资建议
    </footer>
  </div>
</template>

<style scoped>
.community-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.brand-tag {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 2px;
  color: #ff922b;
  margin-bottom: 6px;
}
.page-title {
  font-size: 22px;
  font-weight: 700;
  margin: 0 0 6px;
}
.page-sub {
  color: var(--text-3);
  font-size: 13px;
}

/* 搜索框 */
.search-bar {
  display: flex;
  gap: 10px;
}
.search-input {
  flex: 1;
}
.search-icon {
  font-size: 16px;
}

/* 标签行 */
.tab-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}
.main-tabs, .sub-tabs {
  display: flex;
  gap: 4px;
}
.main-tab {
  padding: 8px 18px;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 18px;
  color: var(--text-2);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}
.main-tab:hover {
  border-color: var(--accent);
  color: var(--accent);
}
.main-tab.active {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}
.sub-tab {
  padding: 6px 14px;
  background: none;
  border: none;
  color: var(--text-3);
  font-size: 13px;
  cursor: pointer;
  transition: color 0.2s;
  border-bottom: 2px solid transparent;
}
.sub-tab:hover {
  color: var(--text-2);
}
.sub-tab.active {
  color: var(--accent);
  border-bottom-color: var(--accent);
  font-weight: 600;
}

/* 文章列表 */
.article-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.article-card {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px 22px;
  transition: border-color 0.2s;
}
.article-card:hover {
  border-color: rgba(255, 146, 43, 0.4);
}
.article-card.expanded {
  border-color: var(--accent);
}

.article-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}
.author-info {
  display: flex;
  align-items: center;
  gap: 10px;
}
.author-avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: linear-gradient(135deg, #ff922b, #ff6b6b);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 700;
  color: #fff;
}
.author-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.author-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
}
.author-time {
  font-size: 12px;
  color: var(--text-3);
}
.type-tag {
  flex-shrink: 0;
}

.article-title {
  font-size: 17px;
  font-weight: 600;
  margin: 0 0 12px;
  color: var(--text);
  cursor: pointer;
  line-height: 1.5;
  transition: color 0.2s;
}
.article-title:hover {
  color: var(--accent);
}

.article-body {
  display: flex;
  gap: 16px;
  margin-bottom: 14px;
}
.article-summary {
  flex: 1;
  font-size: 13px;
  color: var(--text-2);
  line-height: 1.7;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.article-content {
  flex: 1;
}
.content-text {
  font-size: 13px;
  color: var(--text-2);
  line-height: 1.8;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: inherit;
  margin: 0;
}
.article-image-placeholder {
  flex-shrink: 0;
}
.image-box {
  width: 120px;
  height: 80px;
  background: var(--panel-2);
  border: 1px solid var(--border);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
}
.image-icon {
  font-size: 24px;
}
.image-text {
  font-size: 11px;
  color: var(--text-3);
}

.article-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}
.article-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.topic-tag {
  background: var(--panel-2) !important;
  border: none !important;
  color: var(--text-3) !important;
}
.article-actions {
  display: flex;
  align-items: center;
  gap: 18px;
}
.action-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--text-3);
  cursor: pointer;
  transition: color 0.2s;
}
.action-item:hover {
  color: var(--text-2);
}
.action-icon {
  font-size: 14px;
}
.action-count {
  font-variant-numeric: tabular-nums;
}
.share-btn {
  color: var(--accent);
  font-weight: 500;
}
.share-btn:hover {
  color: var(--accent);
  opacity: 0.8;
}

.page-foot {
  margin-top: 12px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
  color: var(--text-3);
  font-size: 12px;
  text-align: center;
}

@media (max-width: 768px) {
  .article-body {
    flex-direction: column;
  }
  .article-image-placeholder {
    width: 100%;
  }
  .image-box {
    width: 100%;
  }
}
</style>
