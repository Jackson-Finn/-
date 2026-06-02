<template>
  <div class="product-detail-page">
    <DataStateCard
      :state="pageState"
      title="商品详情加载失败"
      description="暂时无法获取当前商品信息。"
      :error-description="pageError"
      empty-title="商品不存在"
      empty-description="这个商品可能已下架，或当前链接已经失效。"
      @retry="loadProduct"
    >
      <div class="detail-shell">
        <header class="detail-topbar">
          <button type="button" class="back-button" @click="goBack">
            <span>返回列表</span>
          </button>
        </header>

        <section class="hero-grid">
          <div class="hero-media">
            <ProductGallery
              :images="galleryImages"
              :title="product.title"
              :category="product.category_name"
              :current-index="currentImageIndex"
              @update:current-index="currentImageIndex = $event"
            />
          </div>

          <aside class="hero-side">
            <div class="panel hero-copy-panel">
              <ProductHeader
                :product="product"
                :status="statusMeta"
                :category="product.category_name || '闲置商品'"
                :product-code="productCode"
                :subtitle="statusMeta.summary"
                :published-at="publishedAt"
              />
            </div>

            <ProductActions
              ref="productActionsRef"
              :price="product.price"
              :status-label="statusMeta.label"
              :status-tone="statusMeta.tone"
              :loading="actionLoading"
              :can-order="canOrder"
              :report-reason="reportReason"
              :is-favorite="isFavorite"
              :action-status-text="actionStatus"
              :action-status-tone="actionStatusTone"
              @update:report-reason="reportReason = $event"
              @order="createOrder"
              @session="openSession"
              @favorite="toggleFavorite"
              @report="reportProduct"
              @focus-report="focusReportForm"
              @share="shareProduct"
            />

            <div class="seller-section">
              <SellerCard v-if="sellerProfile" :seller="sellerProfile" />
              <el-button v-if="sellerProfile" plain class="seller-entry" @click="viewSellerProfile">查看卖家主页</el-button>
            </div>
          </aside>
        </section>

        <section class="content-stack">
          <div class="content-panel panel">
            <ProductDescription
              :description="product.description || '卖家暂未补充更多描述。'"
              :sections="descriptionSections"
            />
          </div>

          <div class="content-panel panel">
            <ProductFacts :items="factItems" />
          </div>

          <div class="content-panel panel ai-insight-panel">
            <div class="section-header">
              <div>
                <strong class="section-title">AI 购买助手</strong>
                <p class="section-meta">围绕价格、风险和沟通问题，给你一个更像交易助手的判断入口。</p>
              </div>
              <el-button plain :loading="purchaseInsightsLoading" @click="loadPurchaseInsights(productId)">刷新建议</el-button>
            </div>
            <div class="ai-summary-card">
              <strong>{{ purchaseInsights.summary || '正在整理这件商品的购买建议。' }}</strong>
              <el-tag size="small" effect="plain">
                {{ purchaseInsights.source_mode === 'provider' ? '模型建议' : '规则建议' }}
              </el-tag>
            </div>
            <div class="ai-grid">
              <article class="ai-card">
                <span>价格判断</span>
                <strong>{{ purchaseInsights.pricing_view || '等待分析' }}</strong>
              </article>
              <article class="ai-card">
                <span>风险等级</span>
                <strong>{{ purchaseInsights.risk_level || '待分析' }}</strong>
              </article>
            </div>
            <div class="ai-list-grid">
              <div class="ai-list-block">
                <strong>建议先确认</strong>
                <ul>
                  <li v-for="item in purchaseInsights.next_questions || []" :key="item">{{ item }}</li>
                </ul>
              </div>
              <div class="ai-list-block">
                <strong>验货清单</strong>
                <ul>
                  <li v-for="item in purchaseInsights.checklist || []" :key="item">{{ item }}</li>
                </ul>
              </div>
            </div>
          </div>

          <DataStateCard
            class="content-panel panel"
            :state="reviewState"
            title="商品评价"
            description="这里只展示买家对商品本身的公开评价。"
            empty-title="还没有商品评价"
            empty-description="完成交易后的商品评价会沉淀在这里。"
            error-title="商品评价加载失败"
            :error-description="reviewError"
            @retry="loadReviews"
          >
            <div class="review-panel">
              <div class="review-head">
                <strong>商品评价</strong>
                <span>{{ reviews.length }} 条反馈</span>
              </div>
              <article v-for="review in reviews" :key="review.id" class="review-item">
                <div class="review-meta">
                  <strong>{{ review.reviewer_name || '买家' }}</strong>
                  <span>{{ formatDateTime(review.created_at) }}</span>
                </div>
                <div class="review-rating">评分 {{ review.rating }}/5</div>
                <p>{{ review.content }}</p>
              </article>
            </div>
          </DataStateCard>
        </section>

        <section class="recommendation-stack">
          <div class="content-panel panel">
            <RelatedProducts
              eyebrow="Seller Collection"
              title="卖家在售"
              description="如果你还想横向比较，可以继续看看这个卖家当前在售的其他商品。"
              :items="sellerProducts"
              :state="sellerProductsState"
              :emphasize="true"
              empty-title="卖家当前暂无更多在售商品"
              empty-description="目前公开可见的在售商品只有这一件。"
              error-title="卖家商品加载失败"
              :error-description="sellerProductsError"
              @retry="loadSellerProducts"
            />
          </div>

          <div class="content-panel panel">
            <RelatedProducts
              eyebrow="Related Picks"
              title="相关推荐"
              description="如果你还在对比，可以继续往下看同场景下更接近的候选商品。"
              :items="related"
              :state="relatedState"
              empty-title="暂时没有相关推荐"
              empty-description="系统还没整理出更接近的候选商品。"
              error-title="相关推荐加载失败"
              :error-description="relatedError"
              @retry="loadRelated"
            />
          </div>
        </section>
      </div>
    </DataStateCard>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import DataStateCard from '../../components/DataStateCard.vue'
import ProductActions from '../../components/marketplace/ProductActions.vue'
import ProductDescription from '../../components/marketplace/ProductDescription.vue'
import ProductFacts from '../../components/marketplace/ProductFacts.vue'
import ProductGallery from '../../components/marketplace/ProductGallery.vue'
import ProductHeader from '../../components/marketplace/ProductHeader.vue'
import RelatedProducts from '../../components/marketplace/RelatedProducts.vue'
import SellerCard from '../../components/marketplace/SellerCard.vue'
import { interactionApi } from '../../api/interaction'
import { productApi } from '../../api/products'
import request from '../../api/request'
import { tradeApi } from '../../api/trade'
import { userApi } from '../../api/users'
import {
  buildProductCode,
  formatDateTime,
  getStatusMeta,
  normalizeDelivery,
  normalizeDetailSections,
  normalizeRiskFlags,
  normalizeSpecs,
  productGalleryImages
} from '../../utils/marketplace'
import { useUserStore } from '../../stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const productId = computed(() => Number(route.params.id))
const product = ref({})
const sellerProfile = ref(null)
const sellerProducts = ref([])
const related = ref([])
const reviews = ref([])
const favoriteIds = ref([])
const currentImageIndex = ref(0)
const reportReason = ref('图文描述、价格或卖家沟通内容存在异常，请平台协助复核。')
const reviewsLoading = ref(false)
const relatedLoading = ref(false)
const sellerProductsLoading = ref(false)
const sellerProductsError = ref('')
const reviewError = ref('')
const relatedError = ref('')
const pageError = ref('')
const pageLoading = ref(false)
const actionStatus = ref('')
const actionStatusTone = ref('muted')
const productActionsRef = ref(null)
const actionLoading = ref({
  order: false,
  favorite: false,
  session: false,
  report: false,
  share: false
})
const purchaseInsights = ref({})
const purchaseInsightsLoading = ref(false)
let loadSequence = 0

const statusMeta = computed(() => getStatusMeta(product.value))
const productCode = computed(() => buildProductCode(product.value))
const publishedAt = computed(() => formatDateTime(product.value.created_at))
const galleryImages = computed(() => productGalleryImages(product.value))
const descriptionSections = computed(() => normalizeDetailSections(product.value))
const specItems = computed(() => normalizeSpecs(product.value))
const deliveryItems = computed(() => normalizeDelivery(product.value))
const riskFlags = computed(() => normalizeRiskFlags(product.value))
const trustSnapshot = computed(() => product.value.trust_snapshot || {
  audit_label: '',
  audit_note: '',
  support_label: '',
  support_note: '',
  report_entry: '',
  dispute_entry: ''
})
const isFavorite = computed(() => favoriteIds.value.includes(productId.value))
const canOrder = computed(() => {
  const approved = product.value.audit_status === 'APPROVED'
  const active = product.value.product_status === 'ACTIVE'
  const notMine = !userStore.profile || userStore.profile.id !== product.value.seller_id
  return approved && active && notMine
})

const factItems = computed(() => [
  ...specItems.value.map((item) => ({ label: item.label, value: item.value })),
  ...deliveryItems.value.map((item) => ({
    label: item.label,
    value: item.value,
    note: item.note,
    tone: 'muted'
  })),
  {
    label: '平台审核',
    value: trustSnapshot.value.audit_label,
    note: trustSnapshot.value.audit_note,
    tone: 'muted'
  },
  {
    label: '平台协助',
    value: trustSnapshot.value.support_label,
    note: trustSnapshot.value.support_note,
    tone: 'muted'
  },
  ...riskFlags.value.map((item) => ({
    label: item.title,
    value: riskLabel(item.level),
    note: item.detail
  }))
])

const pageState = computed(() => {
  if (pageLoading.value && !product.value?.id) return 'loading'
  if (!product.value?.id && pageError.value) return 'error'
  if (!product.value?.id) return 'empty'
  return 'ready'
})

const reviewState = computed(() => {
  if (reviewsLoading.value && !reviews.value.length) return 'loading'
  if (reviewError.value) return 'error'
  if (!reviews.value.length) return 'empty'
  return 'ready'
})

const relatedState = computed(() => {
  if (relatedLoading.value && !related.value.length) return 'loading'
  if (relatedError.value) return 'error'
  if (!related.value.length) return 'empty'
  return 'ready'
})

const sellerProductsState = computed(() => {
  if (sellerProductsLoading.value && !sellerProducts.value.length) return 'loading'
  if (sellerProductsError.value) return 'error'
  if (!sellerProducts.value.length) return 'empty'
  return 'ready'
})

function riskLabel(level) {
  const mapping = {
    high: '高风险提醒',
    medium: '重点关注',
    low: '常规提醒'
  }
  return mapping[(level || '').toLowerCase()] || '平台提示'
}

function resetPageState() {
  product.value = {}
  sellerProfile.value = null
  sellerProducts.value = []
  related.value = []
  reviews.value = []
  favoriteIds.value = []
  currentImageIndex.value = 0
  reportReason.value = '图文描述、价格或卖家沟通内容存在异常，请平台协助复核。'
  reviewError.value = ''
  relatedError.value = ''
  pageError.value = ''
  sellerProductsError.value = ''
  actionStatus.value = ''
  actionStatusTone.value = 'muted'
  purchaseInsights.value = {}
  purchaseInsightsLoading.value = false
  reviewsLoading.value = false
  relatedLoading.value = false
  sellerProductsLoading.value = false
  actionLoading.value = {
    order: false,
    favorite: false,
    session: false,
    report: false,
    share: false
  }
}

function setActionStatus(message = '', tone = 'muted') {
  actionStatus.value = message
  actionStatusTone.value = tone
}

async function loadProduct(targetId = productId.value) {
  const sequence = ++loadSequence
  pageLoading.value = true
  pageError.value = ''
  try {
    const detail = await productApi.detail(targetId)
    if (sequence !== loadSequence) return
    product.value = detail
    currentImageIndex.value = 0
    await Promise.all([
      loadPurchaseInsights(targetId, sequence),
      loadReviews(targetId, sequence),
      loadRelated(targetId, sequence),
      loadSellerProfile(detail.seller_id, sequence),
      loadFavoriteState(sequence),
      userStore.isAuthenticated ? tradeApi.captureHistory(targetId) : Promise.resolve()
    ])
  } catch (error) {
    if (sequence !== loadSequence) return
    pageError.value = error.message
  } finally {
    if (sequence === loadSequence) {
      pageLoading.value = false
    }
  }
}

async function loadSellerProfile(sellerId, sequence = loadSequence) {
  sellerProductsLoading.value = true
  sellerProductsError.value = ''
  try {
    const [profile, products] = await Promise.all([userApi.detail(sellerId), userApi.products(sellerId)])
    if (sequence !== loadSequence) return
    sellerProfile.value = profile
    sellerProducts.value = (products || []).filter((item) => item.id !== productId.value)
  } catch (error) {
    if (sequence !== loadSequence) return
    sellerProductsError.value = error.message
    sellerProfile.value = null
    sellerProducts.value = []
  } finally {
    if (sequence === loadSequence) {
      sellerProductsLoading.value = false
    }
  }
}

async function loadSellerProducts() {
  if (!product.value.seller_id) return
  await loadSellerProfile(product.value.seller_id)
}

async function loadReviews(targetId = productId.value, sequence = loadSequence) {
  reviewsLoading.value = true
  reviewError.value = ''
  try {
    const nextReviews = await tradeApi.listReviews(targetId)
    if (sequence !== loadSequence) return
    reviews.value = nextReviews
  } catch (error) {
    if (sequence !== loadSequence) return
    reviewError.value = error.message
    reviews.value = []
  } finally {
    if (sequence === loadSequence) {
      reviewsLoading.value = false
    }
  }
}

async function loadRelated(targetId = productId.value, sequence = loadSequence) {
  relatedLoading.value = true
  relatedError.value = ''
  try {
    const recommendation = await tradeApi.recommendRelated(targetId)
    if (sequence !== loadSequence) return
    related.value = recommendation.items || []
  } catch (error) {
    if (sequence !== loadSequence) return
    relatedError.value = error.message
    related.value = []
  } finally {
    if (sequence === loadSequence) {
      relatedLoading.value = false
    }
  }
}

async function loadFavoriteState(sequence = loadSequence) {
  if (!userStore.isAuthenticated) {
    favoriteIds.value = []
    return
  }
  try {
    const items = await tradeApi.listFavorites()
    if (sequence !== loadSequence) return
    favoriteIds.value = items.map((item) => item.product_id)
  } catch {
    if (sequence !== loadSequence) return
    favoriteIds.value = []
  }
}

async function loadPurchaseInsights(targetId = productId.value, sequence = loadSequence) {
  purchaseInsightsLoading.value = true
  try {
    const result = await productApi.aiPurchaseInsights({ product_id: targetId })
    if (sequence !== loadSequence) return
    purchaseInsights.value = result
  } catch {
    if (sequence !== loadSequence) return
    purchaseInsights.value = {}
  } finally {
    if (sequence === loadSequence) {
      purchaseInsightsLoading.value = false
    }
  }
}

async function openSession() {
  if (!userStore.isAuthenticated) {
    setActionStatus('请先登录后再联系卖家', 'warning')
    ElMessage.warning('请先登录后再联系卖家')
    return
  }
  if (!product.value.seller_id) {
    setActionStatus('卖家信息暂不可用', 'warning')
    ElMessage.warning('卖家信息暂不可用')
    return
  }
  if (actionLoading.value.session) return
  setActionStatus('正在为你打开真实会话窗口...', 'info')
  actionLoading.value.session = true
  try {
    const session = await interactionApi.createSession({
      product_id: productId.value,
      seller_id: product.value.seller_id
    })
    setActionStatus('已打开会话，正在进入消息中心', 'success')
    ElMessage.success('已打开会话，正在进入消息中心')
    router.push({
      name: 'messages',
      query: { sessionId: session.id, productId: productId.value }
    })
  } catch (error) {
    setActionStatus(error.message, 'danger')
    ElMessage.error(error.message)
  } finally {
    actionLoading.value.session = false
  }
}

async function createOrder() {
  if (!userStore.isAuthenticated) {
    setActionStatus('请先登录后再下单', 'warning')
    ElMessage.warning('请先登录后再下单')
    return
  }
  if (!canOrder.value) {
    setActionStatus('当前状态下暂不支持直接下单，请先联系卖家确认', 'warning')
    ElMessage.warning('当前状态下暂不支持直接下单，请先联系卖家确认')
    return
  }
  if (actionLoading.value.order) return
  setActionStatus('正在创建订单...', 'info')
  actionLoading.value.order = true
  try {
    await tradeApi.createOrder({ product_id: productId.value, quantity: 1 })
    setActionStatus('订单已创建，请继续确认交易细节', 'success')
    ElMessage.success('订单已创建，请继续确认交易细节')
    await loadProduct(productId.value)
  } catch (error) {
    setActionStatus(error.message, 'danger')
    ElMessage.error(error.message)
  } finally {
    actionLoading.value.order = false
  }
}

async function toggleFavorite() {
  if (!userStore.isAuthenticated) {
    setActionStatus('请先登录后再收藏', 'warning')
    ElMessage.warning('请先登录后再收藏')
    return
  }
  if (actionLoading.value.favorite) return
  setActionStatus(isFavorite.value ? '正在取消收藏...' : '正在加入收藏...', 'info')
  actionLoading.value.favorite = true
  try {
    if (isFavorite.value) {
      await tradeApi.removeFavorite(productId.value)
      favoriteIds.value = favoriteIds.value.filter((id) => id !== productId.value)
      setActionStatus('已取消收藏', 'success')
      ElMessage.success('已取消收藏')
    } else {
      await tradeApi.addFavorite(productId.value)
      favoriteIds.value = [...favoriteIds.value, productId.value]
      setActionStatus('已加入收藏', 'success')
      ElMessage.success('已加入收藏')
    }
  } catch (error) {
    setActionStatus(error.message, 'danger')
    ElMessage.error(error.message)
  } finally {
    actionLoading.value.favorite = false
  }
}

function focusReportForm() {
  productActionsRef.value?.focusReportInput?.()
  setActionStatus('请补充异常说明后点击“提交举报”', 'info')
}

async function reportProduct() {
  if (!userStore.isAuthenticated) {
    setActionStatus('请先登录后再举报', 'warning')
    ElMessage.warning('请先登录后再举报')
    return
  }
  if (!reportReason.value.trim()) {
    setActionStatus('请先补充异常说明再提交举报', 'warning')
    ElMessage.warning('请先补充异常说明再提交举报')
    return
  }
  if (actionLoading.value.report) return
  setActionStatus('正在提交举报...', 'info')
  actionLoading.value.report = true
  try {
    await request.post('/reports', {
      target_type: 'PRODUCT',
      target_id: productId.value,
      reason: reportReason.value
    })
    setActionStatus('举报已提交，平台会结合商品审核与聊天记录复核', 'success')
    ElMessage.success('举报已提交，平台会结合商品审核与聊天记录复核')
  } catch (error) {
    setActionStatus(error.message, 'danger')
    ElMessage.error(error.message)
  } finally {
    actionLoading.value.report = false
  }
}

function viewSellerProfile() {
  if (!product.value.seller_id) {
    setActionStatus('卖家信息暂不可用', 'warning')
    ElMessage.warning('卖家信息暂不可用')
    return
  }
  router.push(`/sellers/${product.value.seller_id}`)
}

async function copyShareLink(url) {
  if (!window.isSecureContext || !navigator.clipboard?.writeText) {
    return false
  }
  await navigator.clipboard.writeText(url)
  return true
}

async function shareProduct() {
  if (actionLoading.value.share) return
  const url = window.location.href
  const shareText = product.value.title ? `看看这件闲置：${product.value.title}` : '看看这件闲置商品'
  setActionStatus('正在准备分享内容...', 'info')
  actionLoading.value.share = true
  try {
    if (typeof navigator.share === 'function') {
      await navigator.share({
        title: product.value.title || '商品详情',
        text: shareText,
        url
      })
      setActionStatus('系统分享面板已打开', 'success')
      ElMessage.success('已打开系统分享面板')
      return
    }
    if (await copyShareLink(url)) {
      setActionStatus('商品链接已复制，可以直接发给朋友', 'success')
      ElMessage.success('商品链接已复制')
      return
    }
    window.prompt('复制并分享这个链接', url)
    setActionStatus('当前环境不支持系统分享，已提供链接供手动复制', 'warning')
    ElMessage.warning('当前环境不支持系统分享，已提供链接供手动复制')
  } catch (error) {
    if (error?.name === 'AbortError') {
      setActionStatus('你已取消本次分享', 'muted')
      return
    }
    try {
      if (await copyShareLink(url)) {
        setActionStatus('系统分享失败，已改为复制商品链接', 'warning')
        ElMessage.success('分享面板不可用，商品链接已复制')
        return
      }
    } catch {
      // Ignore clipboard fallback errors and continue to the prompt fallback.
    }
    window.prompt('复制并分享这个链接', url)
    setActionStatus('当前环境暂不支持自动分享，请手动复制链接', 'warning')
    ElMessage.warning('当前环境暂不支持自动分享，请手动复制链接')
  } finally {
    actionLoading.value.share = false
  }
}

function goBack() {
  if (window.history.length > 1) {
    router.back()
    return
  }
  router.push('/')
}

watch(
  productId,
  async (nextId) => {
    if (!nextId) return
    resetPageState()
    await loadProduct(nextId)
  },
  { immediate: true }
)
</script>

<style scoped>
.product-detail-page {
  display: grid;
}

.detail-shell {
  display: grid;
  gap: 20px;
  max-width: 1360px;
  margin: 0 auto;
}

.detail-topbar {
  display: flex;
  justify-content: flex-start;
}

.back-button {
  min-height: 42px;
  padding: 0 16px;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: var(--surface);
  color: var(--text);
  font-weight: 800;
  cursor: pointer;
}

.hero-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(360px, 0.82fr);
  gap: 20px;
  align-items: start;
}

.hero-side,
.content-stack,
.recommendation-stack {
  display: grid;
  gap: 18px;
}

.hero-side {
  position: sticky;
  top: 24px;
}

.hero-copy-panel,
.content-panel {
  padding: 20px;
}

.seller-section {
  display: grid;
  gap: 12px;
}

.seller-entry {
  width: 100%;
}

.ai-insight-panel {
  display: grid;
  gap: 16px;
}

.ai-summary-card {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
  align-items: start;
  padding: 16px 18px;
  border-radius: 12px;
  background: var(--surface-soft);
  border: 1px solid var(--line);
}

.ai-summary-card strong {
  line-height: 1.7;
}

.ai-grid,
.ai-list-grid {
  display: grid;
  gap: 14px;
}

.ai-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.ai-card,
.ai-list-block {
  padding: 16px 18px;
  border-radius: 12px;
  background: var(--surface-soft);
  border: 1px solid var(--line);
}

.ai-card {
  display: grid;
  gap: 8px;
}

.ai-card span {
  color: var(--muted);
  font-size: 0.8rem;
  font-weight: 800;
}

.ai-list-block strong {
  display: block;
  margin-bottom: 10px;
}

.ai-list-block ul {
  margin: 0;
  padding-left: 18px;
  color: var(--muted-strong);
}

.ai-list-block li + li {
  margin-top: 8px;
}

.review-panel {
  display: grid;
  gap: 12px;
}

.review-head,
.review-meta {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.review-head span,
.review-meta span {
  color: var(--muted);
  font-size: 0.82rem;
  font-weight: 800;
}

.review-item {
  padding: 16px 0;
  border-top: 1px solid rgba(73, 57, 41, 0.08);
}

.review-item:first-of-type {
  border-top: 0;
  padding-top: 0;
}

.review-rating {
  margin-top: 6px;
  color: var(--trust);
  font-size: 0.84rem;
  font-weight: 800;
}

.review-item p {
  margin: 10px 0 0;
  line-height: 1.8;
}

@media (max-width: 1180px) {
  .hero-grid {
    grid-template-columns: 1fr;
  }

  .hero-side {
    position: static;
  }

  .ai-grid,
  .ai-list-grid {
    grid-template-columns: 1fr;
  }
}
</style>
