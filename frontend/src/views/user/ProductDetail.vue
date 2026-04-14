<template>
  <div class="grid grid-2">
    <DataStateCard
      :state="pageState"
      title="商品详情加载失败"
      :error-description="pageError"
      empty-title="商品不存在"
      empty-description="这个商品可能已被下架或被管理员隐藏。"
      @retry="loadProduct"
    >
      <section class="panel hero-card">
      <div class="section-header">
        <div>
          <div class="pill">商品详情</div>
          <h2 class="section-title">{{ product.title || `商品 ${route.params.id}` }}</h2>
          <p class="section-meta">{{ product.description || '暂无描述' }}</p>
        </div>
        <span class="pill">¥ {{ Number(product.price || 0).toFixed(2) }}</span>
      </div>
      <el-space wrap>
        <el-button type="primary" @click="createOrder">立即下单</el-button>
        <el-button @click="toggleFavorite">收藏</el-button>
        <el-button @click="openSession">发起会话</el-button>
        <el-button @click="reportProduct">举报</el-button>
      </el-space>
      <el-input
        v-model="reportReason"
        style="margin-top: 14px;"
        type="textarea"
        :rows="3"
        placeholder="填写举报原因，便于管理员处理"
      />
      <el-divider />
      <div class="grid">
        <div>
          <h3 class="section-title">相关推荐</h3>
          <DataStateCard
            :state="relatedState"
            title="暂无相关推荐"
            description="系统会基于浏览、收藏和类目行为补充相似商品。"
            empty-title="暂无相关推荐"
            empty-description="当前商品还没有足够的行为素材，稍后再看。"
            error-title="相关推荐加载失败"
            :error-description="relatedError"
            @retry="loadRelated"
          >
            <div class="grid">
              <ProductCard v-for="item in related" :key="item.product_id" :product="{ ...item, id: item.product_id }">
                <div class="pill">{{ item.reason }}</div>
              </ProductCard>
            </div>
          </DataStateCard>
        </div>
      </div>
      </section>
    </DataStateCard>

    <section class="grid">
      <ChatPanel
        :current-user-id="userStore.profile?.id"
        :sessions="sessions"
        :messages="messages"
        :active-session-id="activeSessionId"
        :ws-status="uiStore.wsStatus"
        :loading="sessionsLoading"
        :error="sessionsError"
        :sending="messageSending"
        @refresh="loadSessions"
        @select-session="selectSession"
        @send-message="sendMessage"
      />

      <div class="panel" style="padding: 22px;">
        <div class="section-header">
          <div>
            <h3 class="section-title">AI 会话摘要</h3>
            <p class="section-meta">对当前聊天内容做快速提炼，便于演示智能能力</p>
          </div>
          <el-button :disabled="!activeSessionId || summaryLoading" @click="summarizeChat">
            {{ summaryLoading ? '生成中' : '生成摘要' }}
          </el-button>
        </div>
        <el-empty v-if="!chatSummary" description="选中会话后可生成摘要" />
        <div v-else class="summary-card">{{ chatSummary }}</div>
      </div>

      <DataStateCard
        :state="reviewState"
        title="暂无评价"
        description="交易完成后可在订单页追加评价。"
        empty-title="暂无评价"
        empty-description="等待买家完成交易后，评价会在这里逐步沉淀。"
        error-title="评价加载失败"
        :error-description="reviewError"
        @retry="loadReviews"
      >
        <div class="panel" style="padding: 22px;">
          <div class="section-header">
            <div>
              <h3 class="section-title">评价</h3>
              <p class="section-meta">交易完成后可在订单页追加评价</p>
            </div>
            <el-tag effect="plain">{{ reviews.length }} 条评价</el-tag>
          </div>
          <el-timeline>
            <el-timeline-item v-for="review in reviews" :key="review.id" :timestamp="`评分 ${review.rating}`">
              {{ review.content }}
            </el-timeline-item>
          </el-timeline>
        </div>
      </DataStateCard>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'

import DataStateCard from '../../components/DataStateCard.vue'
import ChatPanel from '../../components/ChatPanel.vue'
import ProductCard from '../../components/ProductCard.vue'
import { productApi } from '../../api/products'
import { tradeApi } from '../../api/trade'
import { interactionApi } from '../../api/interaction'
import request from '../../api/request'
import { useUserStore } from '../../stores/user'
import { useUiStore } from '../../stores/ui'

const route = useRoute()
const userStore = useUserStore()
const uiStore = useUiStore()

const product = ref({})
const related = ref([])
const reviews = ref([])
const sessions = ref([])
const messages = ref([])
const activeSessionId = ref(null)
const reportReason = ref('商品信息与描述存在偏差，请管理员复核')
const sessionsLoading = ref(false)
const sessionsError = ref('')
const messageSending = ref(false)
const summaryLoading = ref(false)
const chatSummary = ref('')
const reviewError = ref('')
const relatedError = ref('')
const pageError = ref('')

async function loadProduct() {
  pageError.value = ''
  try {
    product.value = await productApi.detail(route.params.id)
    await Promise.all([loadReviews(), loadRelated()])

    if (userStore.isAuthenticated) {
      await tradeApi.captureHistory(route.params.id)
    }
  } catch (error) {
    pageError.value = error.message
    throw error
  }
}

async function loadReviews() {
  reviewError.value = ''
  try {
    reviews.value = await tradeApi.listReviews(route.params.id)
  } catch (error) {
    reviewError.value = error.message
    reviews.value = []
    throw error
  }
}

async function loadRelated() {
  relatedError.value = ''
  try {
    const recommendation = await tradeApi.recommendRelated(route.params.id)
    related.value = recommendation.items || []
  } catch (error) {
    relatedError.value = error.message
    related.value = []
    throw error
  }
}

async function loadSessions() {
  if (!userStore.isAuthenticated) {
    return
  }
  sessionsLoading.value = true
  sessionsError.value = ''
  try {
    sessions.value = await interactionApi.listSessions()
    if (!activeSessionId.value && sessions.value.length) {
      await selectSession(sessions.value[0].id)
    }
  } catch (error) {
    sessionsError.value = error.message
  } finally {
    sessionsLoading.value = false
  }
}

async function selectSession(sessionId) {
  activeSessionId.value = sessionId
  messages.value = await interactionApi.listMessages(sessionId)
  chatSummary.value = ''
}

async function openSession() {
  if (!userStore.isAuthenticated) {
    ElMessage.warning('请先登录')
    return
  }
  try {
    const session = await interactionApi.createSession({
      product_id: Number(route.params.id),
      seller_id: product.value.seller_id
    })
    await loadSessions()
    await selectSession(session.id)
    ElMessage.success('会话已创建')
  } catch (error) {
    ElMessage.error(error.message)
  }
}

async function sendMessage(content) {
  if (!content || !activeSessionId.value) {
    return
  }
  messageSending.value = true
  try {
    await interactionApi.sendMessage(activeSessionId.value, { content })
    await selectSession(activeSessionId.value)
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    messageSending.value = false
  }
}

async function createOrder() {
  if (!userStore.isAuthenticated) {
    ElMessage.warning('请先登录')
    return
  }
  try {
    await tradeApi.createOrder({ product_id: Number(route.params.id), quantity: 1 })
    ElMessage.success('订单已创建')
  } catch (error) {
    ElMessage.error(error.message)
  }
}

async function toggleFavorite() {
  if (!userStore.isAuthenticated) {
    ElMessage.warning('请先登录')
    return
  }
  try {
    await tradeApi.addFavorite(Number(route.params.id))
    ElMessage.success('已加入收藏')
  } catch (error) {
    ElMessage.error(error.message)
  }
}

async function reportProduct() {
  if (!userStore.isAuthenticated) {
    ElMessage.warning('请先登录')
    return
  }
  try {
    await request.post('/reports', {
      target_type: 'PRODUCT',
      target_id: Number(route.params.id),
      reason: reportReason.value
    })
    ElMessage.success('举报已提交')
  } catch (error) {
    ElMessage.error(error.message)
  }
}

async function summarizeChat() {
  if (!activeSessionId.value) {
    return
  }
  summaryLoading.value = true
  try {
    const result = await productApi.chatSummary({ session_id: activeSessionId.value })
    chatSummary.value = result.summary
    ElMessage.success('会话摘要已生成')
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    summaryLoading.value = false
  }
}

onMounted(async () => {
  await loadProduct()
  await loadSessions()
})

watch(
  () => uiStore.receivedEvents[0],
  async (event) => {
    if (!event || !activeSessionId.value) {
      return
    }
    if (event.event === 'chat.message.created' && event.payload?.session_id === activeSessionId.value) {
      await selectSession(activeSessionId.value)
    }
  }
)

const pageState = computed(() => {
  if (!product.value?.id && pageError.value) return 'error'
  if (!product.value?.id) return 'loading'
  return 'ready'
})

const reviewState = computed(() => {
  if (reviewError.value) return 'error'
  if (!reviews.value.length) return 'empty'
  return 'ready'
})

const relatedState = computed(() => {
  if (relatedError.value) return 'error'
  if (!related.value.length) return 'empty'
  return 'ready'
})
</script>

<style scoped>
.summary-card {
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(36, 92, 90, 0.08);
  line-height: 1.6;
}
</style>
