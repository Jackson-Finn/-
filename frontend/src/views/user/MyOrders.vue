<template>
  <div class="grid grid-2">
    <DataStateCard
      :state="orderState"
      title="我的订单"
      description="确认收货、查看进度和补评价都收进同一个履约中心。"
      empty-title="还没有订单"
      empty-description="去首页挑一件商品，下单后会在这里继续推进交易。"
      error-title="订单加载失败"
      :error-description="error"
      @retry="loadOrders"
    >
      <section class="panel order-panel">
        <div class="section-header">
          <div>
            <h2 class="section-title">履约中心</h2>
            <p class="section-meta">每笔订单只展示当前阶段最需要处理的动作，减少不必要的按钮干扰。</p>
          </div>
          <el-space wrap>
            <el-tag effect="plain">{{ orders.length }} 笔订单</el-tag>
            <el-button type="primary" plain @click="loadOrders">刷新</el-button>
          </el-space>
        </div>

        <div class="order-summary">
          <article v-for="item in statusSummary" :key="item.label" class="summary-card">
            <strong>{{ item.count }}</strong>
            <span>{{ item.label }}</span>
          </article>
        </div>

        <section v-for="group in groupedOrders" :key="group.key" class="order-group">
          <div class="group-head">
            <div>
              <strong>{{ group.label }}</strong>
              <p>{{ group.description }}</p>
            </div>
            <el-tag effect="plain">{{ group.items.length }}</el-tag>
          </div>

          <article v-for="row in group.items" :key="row.id" class="order-card">
            <div class="order-card-head">
              <div>
                <RouterLink :to="`/products/${row.product_id}`" class="order-title">
                  {{ row.product_summary?.title || `商品 #${row.product_id}` }}
                </RouterLink>
                <p class="order-meta">卖家：{{ row.product_summary?.seller_name || `卖家 #${row.seller_id}` }} · 金额 ¥{{ Number(row.total_amount || 0).toFixed(2) }}</p>
              </div>
              <el-tag effect="plain">{{ row.status }}</el-tag>
            </div>

            <div v-if="row.next_actions?.length" class="action-list">
              <span v-for="item in row.next_actions" :key="item" class="action-pill">{{ item }}</span>
            </div>

            <div class="order-actions">
              <el-button v-if="row.can_confirm" size="small" @click="confirmOrder(row.id)">确认收货</el-button>
              <el-button v-if="row.is_buyer && row.status === 'CREATED'" size="small" @click="cancelOrder(row.id)">取消订单</el-button>
              <el-button
                v-if="row.is_buyer"
                size="small"
                type="primary"
                plain
                :disabled="!row.can_review_product && !row.can_review_seller"
                @click="openReview(row)"
              >
                {{ row.product_review || row.seller_review ? '查看 / 修改评价' : '评价' }}
              </el-button>
            </div>
          </article>
        </section>
      </section>
    </DataStateCard>

    <section class="panel review-panel">
      <div class="section-header">
        <div>
          <h2 class="section-title">订单评价</h2>
          <p class="section-meta">评价始终从订单出发，但商品评价和卖家评价分开管理、分开展示。</p>
        </div>
      </div>

      <el-form :model="reviewForm" label-position="top">
        <el-form-item label="订单 ID">
          <el-input v-model="reviewForm.order_id" disabled />
        </el-form-item>
        <el-form-item label="商品评价">
          <div class="review-block">
            <div class="review-head">
              <el-rate v-model="reviewForm.product_rating" :disabled="!reviewForm.can_review_product" />
              <el-tag v-if="reviewForm.product_review_id" type="success" effect="plain">已提交，可修改</el-tag>
            </div>
            <el-input
              v-model="reviewForm.product_content"
              type="textarea"
              :rows="3"
              :disabled="!reviewForm.can_review_product"
              placeholder="评价商品本身的成色、描述一致性和实物情况"
            />
            <p v-if="!reviewForm.can_review_product" class="review-tip">当前订单无法再编辑商品评价。</p>
          </div>
        </el-form-item>
        <el-form-item label="卖家评价">
          <div class="review-block">
            <div class="review-head">
              <el-rate v-model="reviewForm.seller_rating" :disabled="!reviewForm.can_review_seller" />
              <el-tag v-if="reviewForm.seller_review_id" type="success" effect="plain">已提交，可修改</el-tag>
            </div>
            <el-input
              v-model="reviewForm.seller_content"
              type="textarea"
              :rows="3"
              :disabled="!reviewForm.can_review_seller"
              placeholder="评价卖家的沟通效率、发货体验和配合程度"
            />
            <p v-if="!reviewForm.can_review_seller" class="review-tip">当前订单无法再编辑卖家评价。</p>
          </div>
        </el-form-item>
        <el-button type="primary" :disabled="!canSubmitReview" @click="submitReview">{{ submitLabel }}</el-button>
      </el-form>
    </section>

    <ConfirmDialog
      v-model="confirmDialog.visible"
      :title="confirmDialog.title"
      :description="confirmDialog.description"
      :loading="confirmDialog.loading"
      @confirm="confirmDialog.onConfirm"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { ElMessage } from 'element-plus'

import ConfirmDialog from '../../components/common/ConfirmDialog.vue'
import DataStateCard from '../../components/DataStateCard.vue'
import { tradeApi } from '../../api/trade'

const orders = ref([])
const loading = ref(false)
const error = ref('')
const reviewForm = reactive({
  order_id: '',
  product_rating: 5,
  product_content: '',
  product_review_id: null,
  seller_rating: 5,
  seller_content: '',
  seller_review_id: null,
  can_review_product: false,
  can_review_seller: false
})

const confirmDialog = ref({
  visible: false,
  title: '',
  description: '',
  loading: false,
  onConfirm: null
})

async function loadOrders() {
  loading.value = true
  error.value = ''
  try {
    orders.value = await tradeApi.listOrders()
  } catch (err) {
    error.value = err.message
    orders.value = []
  } finally {
    loading.value = false
  }
}

async function confirmOrder(id) {
  confirmDialog.value = {
    visible: true,
    title: '确认收货',
    description: '确认收货会将订单标记为完成，是否继续？',
    loading: false,
    onConfirm: async () => {
      confirmDialog.value.loading = true
      try {
        await tradeApi.confirmOrder(id)
        confirmDialog.value.visible = false
        ElMessage.success('订单已确认完成')
        await loadOrders()
      } catch (err) {
        ElMessage.error(err.message)
      } finally {
        confirmDialog.value.loading = false
      }
    }
  }
}

async function cancelOrder(id) {
  confirmDialog.value = {
    visible: true,
    title: '取消订单',
    description: '取消订单后将终止交易流程，确定继续吗？',
    loading: false,
    onConfirm: async () => {
      confirmDialog.value.loading = true
      try {
        await tradeApi.cancelOrder(id)
        confirmDialog.value.visible = false
        ElMessage.success('订单已取消')
        await loadOrders()
      } catch (err) {
        ElMessage.error(err.message)
      } finally {
        confirmDialog.value.loading = false
      }
    }
  }
}

function openReview(row) {
  reviewForm.order_id = row.id
  reviewForm.can_review_product = row.can_review_product
  reviewForm.can_review_seller = row.can_review_seller
  reviewForm.product_rating = row.product_review?.rating ?? 5
  reviewForm.product_content = row.product_review?.content ?? ''
  reviewForm.product_review_id = row.product_review?.id ?? null
  reviewForm.seller_rating = row.seller_review?.rating ?? 5
  reviewForm.seller_content = row.seller_review?.content ?? ''
  reviewForm.seller_review_id = row.seller_review?.id ?? null
}

async function submitReview() {
  try {
    await tradeApi.createReview({
      order_id: Number(reviewForm.order_id),
      product_review: reviewForm.can_review_product && reviewForm.product_content.trim()
        ? { rating: reviewForm.product_rating, content: reviewForm.product_content.trim() }
        : null,
      seller_review: reviewForm.can_review_seller && reviewForm.seller_content.trim()
        ? { rating: reviewForm.seller_rating, content: reviewForm.seller_content.trim() }
        : null
    })
    ElMessage.success('评价已保存')
    await loadOrders()
    const latest = orders.value.find((item) => item.id === Number(reviewForm.order_id))
    if (latest) {
      openReview(latest)
    }
  } catch (err) {
    ElMessage.error(err.message)
  }
}

onMounted(loadOrders)

const groupedOrders = computed(() => {
  const groups = [
    { key: 'created', label: '进行中', description: '建议继续确认验货、交付方式和收货动作。', match: (row) => row.status === 'CREATED' },
    { key: 'completed', label: '已完成', description: '可以回看聊天、订单和评价记录。', match: (row) => row.status === 'COMPLETED' },
    { key: 'cancelled', label: '已取消', description: '交易已终止，保留记录便于后续核对。', match: (row) => row.status === 'CANCELLED' }
  ]
  return groups
    .map((group) => ({ ...group, items: orders.value.filter(group.match) }))
    .filter((group) => group.items.length)
})

const statusSummary = computed(() => [
  { label: '进行中', count: orders.value.filter((item) => item.status === 'CREATED').length },
  { label: '已完成', count: orders.value.filter((item) => item.status === 'COMPLETED').length },
  { label: '已取消', count: orders.value.filter((item) => item.status === 'CANCELLED').length }
])

const orderState = computed(() => {
  if (loading.value) return 'loading'
  if (error.value) return 'error'
  if (!orders.value.length) return 'empty'
  return 'ready'
})

const canSubmitReview = computed(() => {
  if (!reviewForm.order_id) return false
  const canProduct = reviewForm.can_review_product && Boolean(reviewForm.product_content.trim())
  const canSeller = reviewForm.can_review_seller && Boolean(reviewForm.seller_content.trim())
  return canProduct || canSeller
})

const submitLabel = computed(() => {
  if (reviewForm.product_review_id || reviewForm.seller_review_id) {
    return '保存评价'
  }
  return '提交评价'
})
</script>

<style scoped>
.order-panel,
.review-panel {
  padding: 22px;
}

.order-summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 18px;
}

.summary-card {
  display: grid;
  gap: 6px;
  padding: 16px 18px;
  border-radius: 20px;
  background: rgba(73, 57, 41, 0.04);
}

.summary-card strong {
  font-size: 1.9rem;
  line-height: 1;
  letter-spacing: -0.05em;
}

.order-group + .order-group {
  margin-top: 20px;
}

.group-head,
.order-card-head,
.review-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.group-head {
  margin-bottom: 12px;
}

.group-head p,
.order-meta,
.review-tip {
  margin: 6px 0 0;
  color: var(--muted);
  line-height: 1.7;
}

.order-card {
  display: grid;
  gap: 14px;
  padding: 18px;
  border-radius: 22px;
  border: 1px solid var(--line);
  background: rgba(255, 252, 247, 0.94);
}

.order-card + .order-card {
  margin-top: 12px;
}

.order-title {
  color: var(--brand);
  font-weight: 800;
}

.action-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.action-pill {
  padding: 7px 10px;
  border-radius: 999px;
  background: var(--brand-soft);
  color: var(--brand-strong);
  font-size: 0.78rem;
  font-weight: 700;
}

.order-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.review-block {
  display: grid;
  gap: 12px;
  width: 100%;
}

@media (max-width: 960px) {
  .order-summary {
    grid-template-columns: 1fr;
  }
}
</style>
