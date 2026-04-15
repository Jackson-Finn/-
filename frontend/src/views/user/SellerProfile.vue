<template>
  <div class="seller-page">
    <DataStateCard
      :state="pageState"
      title="卖家主页加载失败"
      description="无法获取卖家信息。"
      :error-description="pageError"
      empty-title="卖家不存在"
      empty-description="这个卖家主页可能已经不可访问。"
      @retry="loadSeller"
    >
      <div class="page-stack">
        <button type="button" class="back-button" @click="goBack">返回</button>

        <SellerProfileSummary v-if="seller" :seller="seller" />

        <section class="seller-layout">
          <div class="main-column">
            <RelatedProducts
              eyebrow="On Sale"
              title="当前在售商品"
              description="这里展示卖家当前公开可见的在售商品。"
              :items="products"
              :state="productsState"
              empty-title="卖家暂时没有在售商品"
              empty-description="可以稍后再来看看，或先与卖家沟通其他需求。"
              error-title="卖家商品加载失败"
              :error-description="productsError"
              @retry="loadSellerProducts"
            />

            <section class="panel review-panel">
              <div class="section-header compact">
                <div>
                  <div class="eyebrow">Seller Reviews</div>
                  <h2 class="section-title">卖家评价</h2>
                </div>
              </div>
              <el-empty v-if="!sellerReviews.length" description="暂时还没有卖家评价" />
              <article v-for="review in sellerReviews" :key="review.id" class="review-item">
                <div class="review-meta">
                  <strong>{{ review.reviewer_name || '买家' }}</strong>
                  <span>{{ formatDateTime(review.created_at) }}</span>
                </div>
                <div class="review-rating">评分 {{ review.rating }}/5</div>
                <p>{{ review.content }}</p>
              </article>
            </section>
          </div>

          <aside class="side-column">
            <div v-if="seller" class="panel info-card">
              <div class="section-header compact">
                <div>
                  <div class="eyebrow">Seller Notes</div>
                  <h2 class="section-title">卖家摘要</h2>
                </div>
              </div>
              <div class="info-list">
                <div class="info-item">
                  <span>注册时间</span>
                  <strong>{{ formatDateTime(seller.created_at) }}</strong>
                </div>
                <div class="info-item">
                  <span>所在城市</span>
                  <strong>{{ seller.city }}</strong>
                </div>
                <div class="info-item">
                  <span>常用交易方式</span>
                  <strong>{{ seller.preferred_deal_methods.join(' / ') }}</strong>
                </div>
                <div class="info-item">
                  <span>联系入口</span>
                  <strong>{{ primaryProduct ? '可从在售商品直接发起会话' : '当前暂无可联系商品' }}</strong>
                </div>
              </div>
              <div class="action-row">
                <el-button type="primary" :disabled="!primaryProduct" @click="openPrimaryProduct">
                  查看在售商品
                </el-button>
                <el-button plain :disabled="!primaryProduct" :loading="contactLoading" @click="contactSeller">
                  联系卖家
                </el-button>
              </div>
            </div>
          </aside>
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
import RelatedProducts from '../../components/marketplace/RelatedProducts.vue'
import SellerProfileSummary from '../../components/marketplace/SellerProfileSummary.vue'
import { interactionApi } from '../../api/interaction'
import { tradeApi } from '../../api/trade'
import { userApi } from '../../api/users'
import { formatDateTime } from '../../utils/marketplace'
import { useUserStore } from '../../stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const sellerId = computed(() => Number(route.params.sellerId))
const seller = ref(null)
const products = ref([])
const sellerReviews = ref([])
const pageLoading = ref(false)
const productsError = ref('')
const pageError = ref('')
const contactLoading = ref(false)
let loadSequence = 0

const pageState = computed(() => {
  if (pageLoading.value && !seller.value) return 'loading'
  if (pageError.value && !seller.value) return 'error'
  if (!seller.value) return 'empty'
  return 'ready'
})

const productsState = computed(() => {
  if (productsError.value) return 'error'
  if (!products.value.length) return 'empty'
  return 'ready'
})

const primaryProduct = computed(() => products.value[0] || null)

async function loadSeller(targetId = sellerId.value) {
  const sequence = ++loadSequence
  pageLoading.value = true
  pageError.value = ''
  productsError.value = ''
  try {
    const [profile, nextProducts, nextReviews] = await Promise.all([
      userApi.detail(targetId),
      userApi.products(targetId),
      tradeApi.listSellerReviews(targetId)
    ])
    if (sequence !== loadSequence) return
    seller.value = profile
    products.value = nextProducts
    sellerReviews.value = Array.isArray(nextReviews) ? nextReviews : []
  } catch (error) {
    if (sequence !== loadSequence) return
    pageError.value = error.message
    seller.value = null
    products.value = []
    sellerReviews.value = []
  } finally {
    if (sequence === loadSequence) {
      pageLoading.value = false
    }
  }
}

async function loadSellerProducts() {
  if (!sellerId.value) return
  try {
    productsError.value = ''
    products.value = await userApi.products(sellerId.value)
  } catch (error) {
    productsError.value = error.message
    products.value = []
  }
}

function openPrimaryProduct() {
  if (!primaryProduct.value) return
  router.push(`/products/${primaryProduct.value.id}`)
}

function contactSeller() {
  openConversation()
}

async function openConversation() {
  if (!primaryProduct.value) return
  if (!userStore.isAuthenticated) {
    ElMessage.warning('请先登录再联系卖家')
    router.push({ name: 'login', query: { redirect: route.fullPath } })
    return
  }
  contactLoading.value = true
  try {
    const session = await interactionApi.createSession({
      product_id: primaryProduct.value.id,
      seller_id: sellerId.value
    })
    ElMessage.success('已打开与卖家的会话')
    router.push({ name: 'messages', query: { sessionId: session.id, productId: primaryProduct.value.id } })
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    contactLoading.value = false
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
  sellerId,
  async (nextId) => {
    if (!nextId) return
    await loadSeller(nextId)
  },
  { immediate: true }
)
</script>

<style scoped>
.seller-page {
  display: grid;
}

.page-stack {
  display: grid;
  gap: 22px;
}

.back-button {
  width: fit-content;
  min-height: 42px;
  padding: 0 16px;
  border: 0;
  border-radius: 999px;
  background: rgba(73, 57, 41, 0.06);
  color: var(--text);
  font-weight: 800;
  cursor: pointer;
}

.review-panel {
  padding: 22px;
  display: grid;
  gap: 12px;
}

.review-item {
  padding: 16px 0;
  border-top: 1px solid rgba(73, 57, 41, 0.08);
}

.review-item:first-of-type {
  border-top: 0;
  padding-top: 0;
}

.review-meta {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.review-meta span {
  color: var(--muted);
  font-size: 0.8rem;
}

.review-rating {
  margin-top: 6px;
  color: var(--trust);
  font-size: 0.84rem;
  font-weight: 800;
}

.seller-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(320px, 0.8fr);
  gap: 20px;
  align-items: start;
}

.main-column,
.side-column {
  display: grid;
  gap: 18px;
}

.info-card {
  padding: 20px;
}

.compact {
  margin-bottom: 0;
}

.info-list {
  display: grid;
  gap: 12px;
}

.info-item {
  padding: 14px 16px;
  border-radius: 16px;
  background: #f8fbff;
  border: 1px solid var(--line);
  display: grid;
  gap: 6px;
}

.info-item span {
  color: var(--muted);
  font-size: 0.8rem;
  font-weight: 700;
}

.action-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-top: 18px;
}

@media (max-width: 960px) {
  .seller-layout {
    grid-template-columns: 1fr;
  }
}
</style>
