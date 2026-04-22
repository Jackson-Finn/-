<template>
  <div class="home-page">
    <section class="panel search-hero">
      <div class="hero-copy">
        <div class="eyebrow">Discover</div>
        <h2 class="hero-title">发现宝贝，聊好价格，轻松交易。</h2>
        <p class="section-meta">从搜索到下单，完整交易路径一目了然，随时了解商品动态。</p>
      </div>

      <div class="hero-panel">
        <div class="search-bar">
          <el-autocomplete
            v-model="keyword"
            :fetch-suggestions="querySuggestions"
            clearable
            placeholder="搜索商品、场景或预算，例如：九成新 switch 800 以内"
            @select="submitSearch"
            @keyup.enter="submitSearch"
          />
          <el-button type="primary" @click="submitSearch">搜索</el-button>
        </div>
        <p class="search-brief">在商品大厅里逛逛，或直接搜索缩小范围。</p>
        <div class="hero-links">
          <RouterLink class="hero-link" to="/messages">去看消息</RouterLink>
          <RouterLink class="hero-link" to="/orders">处理订单</RouterLink>
          <RouterLink class="hero-link" to="/profile">进入我的</RouterLink>
        </div>
      </div>
    </section>

    <el-alert
      v-if="pageError"
      :title="pageError"
      type="warning"
      show-icon
      :closable="false"
    />

    <DataStateCard
      :state="catalogState"
      title="商品大厅加载失败"
      description="暂时无法获取商品大厅内容。"
      empty-title="商品大厅还没有内容"
      empty-description="当前还没有公开可浏览的商品，稍后再来看看。"
      :error-description="catalogError"
      @retry="loadCatalog"
    >
      <section class="panel section-panel">
        <div class="section-header">
          <div>
            <div class="eyebrow">Marketplace</div>
            <h3 class="section-title">商品大厅</h3>
            <p class="section-meta">公开在售的好物，看看有没有你想要的。</p>
          </div>
          <RouterLink to="/search">
            <el-button plain>进入搜索页</el-button>
          </RouterLink>
        </div>

        <div class="catalog-grid">
          <ProductCard v-for="item in hallProducts" :key="item.id" :product="item" />
        </div>
      </section>
    </DataStateCard>

    <DataStateCard
      :state="recommendationState"
      title="推荐流"
      description="先看最值得展开比较的商品，再决定是否联系卖家。"
      empty-title="还没有推荐内容"
      empty-description="系统还在整理你的交易信号，稍后刷新即可。"
      error-title="推荐加载失败"
      :error-description="recommendationError"
      @retry="loadRecommendations"
    >
      <section class="panel section-panel">
        <div class="section-header">
          <div>
            <div class="eyebrow">Recommendations</div>
            <h3 class="section-title">推荐流</h3>
            <p class="section-meta">根据你的偏好精选，帮你更快找到心仪好物。</p>
          </div>
          <el-button plain @click="loadRecommendations">刷新推荐</el-button>
        </div>

        <article v-if="featuredRecommendation" class="featured-card">
          <div class="featured-copy">
            <span class="featured-badge">Top Pick</span>
            <h3>{{ featuredRecommendation.title }}</h3>
            <p class="section-meta">{{ featuredRecommendation.reason || '系统根据浏览、收藏和订单信号整理出这条推荐。' }}</p>
            <div class="featured-meta">
              <span class="meta-pill">¥ {{ Number(featuredRecommendation.price || 0).toFixed(2) }}</span>
              <span v-if="featuredRecommendation.category_name" class="meta-pill">{{ featuredRecommendation.category_name }}</span>
              <span v-if="featuredRecommendation.seller_name" class="meta-pill">{{ featuredRecommendation.seller_name }}</span>
            </div>
            <RouterLink :to="`/products/${featuredRecommendation.product_id}`">
              <el-button type="primary">查看详情</el-button>
            </RouterLink>
          </div>
          <img
            v-if="featuredRecommendation.cover_image"
            :src="featuredRecommendation.cover_image"
            :alt="featuredRecommendation.title"
            class="featured-cover"
          >
        </article>

        <div class="catalog-grid">
          <ProductCard
            v-for="item in recommendationCards"
            :key="item.product_id"
            :product="{ ...item, id: item.product_id }"
          >
            <span class="pill">{{ item.reason }}</span>
          </ProductCard>
        </div>
      </section>
    </DataStateCard>

    <section class="panel section-panel">
      <div class="section-header">
        <div>
          <div class="eyebrow">Signals</div>
          <h3 class="section-title">最近交易信号</h3>
          <p class="section-meta">消息、订单、收藏和浏览记录统一汇总，随时把握交易进度。</p>
        </div>
      </div>

      <div class="signal-grid">
        <RouterLink to="/messages" class="signal-card">
          <strong>{{ workspace.unread_messages }}</strong>
          <span>未读消息</span>
          <p>随时查看正在沟通中的商品消息。</p>
        </RouterLink>
        <RouterLink to="/orders" class="signal-card">
          <strong>{{ workspace.active_orders }}</strong>
          <span>进行中订单</span>
          <p>查看进行中订单的进度和详情。</p>
        </RouterLink>
        <RouterLink to="/favorites" class="signal-card">
          <strong>{{ workspace.favorites }}</strong>
          <span>收藏夹</span>
          <p>从收藏夹快速回到候选商品，继续比较。</p>
        </RouterLink>
        <RouterLink to="/history" class="signal-card">
          <strong>{{ workspace.recent_history }}</strong>
          <span>最近浏览</span>
          <p>快速回到最近浏览过的商品。</p>
        </RouterLink>
      </div>

      <div class="signal-detail-grid">
        <section class="signal-panel">
          <div class="mini-head">
            <strong>最近浏览</strong>
            <RouterLink to="/history">查看全部</RouterLink>
          </div>
          <RouterLink
            v-for="item in history.slice(0, 3)"
            :key="item.id"
            class="mini-link"
            :to="`/products/${item.product_summary?.id || item.product_id}`"
          >
            <span>{{ item.product_summary?.title || `商品 #${item.product_id}` }}</span>
            <small>{{ item.product_summary?.seller_name || '卖家' }}</small>
          </RouterLink>
          <el-empty v-if="!history.length" description="还没有最近浏览记录" />
        </section>

        <section class="signal-panel">
          <div class="mini-head">
            <strong>通知与状态</strong>
            <RouterLink to="/profile">进入我的</RouterLink>
          </div>
          <div class="status-row">
            <span>消息同步</span>
            <el-tag :type="wsStatusType" effect="plain">{{ wsStatusLabel }}</el-tag>
          </div>
          <div class="status-row">
            <span>未读通知</span>
            <strong>{{ workspace.unread_notifications }}</strong>
          </div>
          <div class="status-row">
            <span>当前状态</span>
            <strong>{{ presenceLabel }}</strong>
          </div>
        </section>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import DataStateCard from '../../components/DataStateCard.vue'
import ProductCard from '../../components/ProductCard.vue'
import { interactionApi } from '../../api/interaction'
import { productApi } from '../../api/products'
import { tradeApi } from '../../api/trade'
import { useUiStore } from '../../stores/ui'
import { useUserStore } from '../../stores/user'

const router = useRouter()
const uiStore = useUiStore()
const userStore = useUserStore()

const keyword = ref('')
const workspace = ref({
  unread_messages: 0,
  unread_notifications: 0,
  favorites: 0,
  recent_history: 0,
  active_orders: 0
})
const hallProducts = ref([])
const recommendations = ref([])
const history = ref([])
const catalogLoading = ref(false)
const catalogError = ref('')
const recommendationLoading = ref(false)
const recommendationError = ref('')
const pageError = ref('')

async function loadRecommendations() {
  recommendationLoading.value = true
  recommendationError.value = ''
  try {
    const data = await tradeApi.recommendHome()
    recommendations.value = data.items || []
  } catch (error) {
    recommendationError.value = error.message
    recommendations.value = []
    throw error
  } finally {
    recommendationLoading.value = false
  }
}

async function loadCatalog() {
  catalogLoading.value = true
  catalogError.value = ''
  try {
    const data = await productApi.list()
    hallProducts.value = (data || []).slice(0, 6)
  } catch (error) {
    catalogError.value = error.message
    hallProducts.value = []
    throw error
  } finally {
    catalogLoading.value = false
  }
}

async function loadWorkspace() {
  if (!userStore.isAuthenticated) {
    workspace.value = {
      unread_messages: 0,
      unread_notifications: 0,
      favorites: 0,
      recent_history: 0,
      active_orders: 0
    }
    history.value = []
    return
  }

  const [sessionsResult, notificationsResult, favoritesResult, recentHistoryResult, ordersResult] = await Promise.allSettled([
    interactionApi.listSessions(),
    interactionApi.listNotifications(),
    tradeApi.listFavorites(),
    tradeApi.recentHistory(),
    tradeApi.listOrders()
  ])

  const sessions = sessionsResult.status === 'fulfilled' ? sessionsResult.value : []
  const notifications = notificationsResult.status === 'fulfilled' ? notificationsResult.value : []
  const favorites = favoritesResult.status === 'fulfilled' ? favoritesResult.value : []
  const recentHistory = recentHistoryResult.status === 'fulfilled' ? recentHistoryResult.value : []
  const orders = ordersResult.status === 'fulfilled' ? ordersResult.value : []

  workspace.value = {
    unread_messages: sessions.reduce((total, item) => total + Number(item.unread_count || 0), 0),
    unread_notifications: notifications.filter((item) => !item.read).length,
    favorites: favorites.length,
    recent_history: recentHistory.length,
    active_orders: orders.filter((item) => !['COMPLETED', 'CANCELLED'].includes(item.status)).length
  }
  history.value = recentHistory
}

async function loadPage() {
  pageError.value = ''
  const results = await Promise.allSettled([loadCatalog(), loadRecommendations(), loadWorkspace()])
  const failed = results.filter((item) => item.status === 'rejected').map((item) => item.reason?.message).filter(Boolean)
  pageError.value = failed.join('；')
}

async function querySuggestions(queryString, cb) {
  try {
    const data = await productApi.suggest(queryString ? { keyword: queryString } : {})
    cb((data.suggestions || []).map((value) => ({ value })))
  } catch {
    cb([])
  }
}

function submitSearch() {
  const raw = keyword.value.trim()
  if (!raw) {
    router.push({ name: 'search' })
    return
  }
  router.push({ name: 'search', query: { keyword: raw } })
}

onMounted(loadPage)

const catalogState = computed(() => {
  if (catalogLoading.value) return 'loading'
  if (catalogError.value) return 'error'
  if (!hallProducts.value.length) return 'empty'
  return 'ready'
})

const recommendationState = computed(() => {
  if (recommendationLoading.value) return 'loading'
  if (recommendationError.value) return 'error'
  if (!recommendations.value.length) return 'empty'
  return 'ready'
})

const featuredRecommendation = computed(() => recommendations.value[0] || null)
const recommendationCards = computed(() => recommendations.value.slice(featuredRecommendation.value ? 1 : 0))

const wsStatusLabel = computed(() => {
  const mapping = {
    OPEN: '实时同步',
    CONNECTING: '连接中',
    CLOSED: '未实时连接',
    ERROR: '同步异常',
    IDLE: '空闲'
  }
  return mapping[uiStore.wsStatus] || uiStore.wsStatus
})

const wsStatusType = computed(() => {
  if (uiStore.wsStatus === 'OPEN') return 'success'
  if (uiStore.wsStatus === 'CONNECTING') return 'warning'
  if (uiStore.wsStatus === 'ERROR') return 'danger'
  return 'info'
})

const presenceLabel = computed(() => {
  const mapping = {
    ONLINE: '在线',
    INVISIBLE: '隐身',
    OFFLINE: '离线'
  }
  return mapping[userStore.profile?.presence_status] || '离线'
})
</script>

<style scoped>
.home-page {
  display: grid;
  gap: 20px;
}

.search-hero,
.section-panel {
  padding: 24px;
}

.search-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(340px, 0.95fr);
  gap: 24px;
  align-items: stretch;
}

.hero-copy {
  display: grid;
  gap: 14px;
}

.hero-title {
  margin: 0;
  font-size: clamp(2rem, 4vw, 3rem);
  line-height: 1.05;
  letter-spacing: -0.05em;
}

.hero-panel {
  display: grid;
  gap: 14px;
  padding: 20px;
  border-radius: 24px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(248, 242, 234, 0.92));
  border: 1px solid var(--line);
}

.search-bar {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
}

.search-brief {
  margin: 0;
  color: var(--muted);
  line-height: 1.7;
}

.hero-links {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.hero-link {
  padding: 10px 14px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid var(--line);
  color: var(--text);
  font-weight: 700;
}

.featured-card {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) 280px;
  gap: 18px;
  padding: 18px;
  border-radius: 24px;
  border: 1px solid var(--line);
  background: linear-gradient(180deg, rgba(249, 251, 255, 0.98), rgba(255, 255, 255, 0.94));
  margin-bottom: 18px;
}

.featured-copy {
  display: grid;
  align-content: start;
  gap: 12px;
}

.featured-copy h3 {
  margin: 0;
  font-size: 1.45rem;
  line-height: 1.2;
}

.featured-badge,
.meta-pill {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 800;
}

.featured-badge {
  width: fit-content;
  background: var(--brand-soft);
  color: var(--brand-strong);
}

.featured-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.meta-pill {
  background: rgba(73, 57, 41, 0.06);
  color: var(--muted-strong);
}

.featured-cover {
  width: 100%;
  height: 100%;
  min-height: 240px;
  object-fit: cover;
  border-radius: 18px;
}

.catalog-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.signal-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 18px;
}

.signal-card {
  display: grid;
  gap: 6px;
  padding: 18px;
  border-radius: 22px;
  border: 1px solid var(--line);
  background: rgba(255, 252, 247, 0.96);
}

.signal-card strong {
  font-size: 1.8rem;
  line-height: 1;
  letter-spacing: -0.05em;
}

.signal-card span {
  font-weight: 800;
}

.signal-card p {
  margin: 0;
  color: var(--muted);
  line-height: 1.7;
}

.signal-detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.signal-panel {
  padding: 18px;
  border-radius: 22px;
  background: rgba(73, 57, 41, 0.04);
  display: grid;
  gap: 12px;
}

.mini-head,
.status-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.mini-link {
  display: grid;
  gap: 4px;
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.86);
}

.mini-link small {
  color: var(--muted);
}

@media (max-width: 1180px) {
  .search-hero,
  .featured-card,
  .signal-detail-grid {
    grid-template-columns: 1fr;
  }

  .signal-grid,
  .catalog-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .search-bar,
  .signal-grid,
  .catalog-grid {
    grid-template-columns: 1fr;
  }
}
</style>
