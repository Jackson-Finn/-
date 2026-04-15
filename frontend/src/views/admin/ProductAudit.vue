<template>
  <div class="page-grid">
    <section class="page-head">
      <div>
        <div class="eyebrow">Product Management</div>
        <h2 class="page-title">商品列表</h2>
        <p class="page-meta">先筛选，再查看详情，再做审核动作。</p>
      </div>
      <el-space wrap>
        <RouterLink to="/admin/audits">
          <el-button plain>查看待办队列</el-button>
        </RouterLink>
        <el-button :loading="loading" @click="loadProducts">刷新列表</el-button>
      </el-space>
    </section>

    <LoadingState v-if="loading && !products.length" :rows="6" />
    <ErrorState v-else-if="error && !products.length" :description="error" @retry="loadProducts" />
    <EmptyState v-else-if="!products.length" description="当前没有符合条件的商品。" />
    <ProductTable
      v-else
      :products="products"
      :filters="filters"
      :action-loading-id="actionLoadingId"
      @apply-filter="applyFilters"
      @reset-filter="resetFilters"
      @view="openDetail"
      @approve="openDecision('approve', $event)"
      @request-changes="openDecision('request_changes', $event)"
      @reject="openDecision('reject', $event)"
    />

    <ConfirmDialog
      v-model="decisionDialog.visible"
      :title="decisionTitle"
      :description="decisionDescription"
      :note="decisionDialog.note"
      :loading="decisionSubmitting"
      placeholder="补充审核备注"
      @confirm="submitDecision"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import ConfirmDialog from '../../components/admin/ConfirmDialog.vue'
import EmptyState from '../../components/admin/EmptyState.vue'
import ErrorState from '../../components/admin/ErrorState.vue'
import LoadingState from '../../components/admin/LoadingState.vue'
import ProductTable from '../../components/admin/ProductTable.vue'
import { adminApi } from '../../api/admin'

const router = useRouter()
const loading = ref(false)
const error = ref('')
const products = ref([])
const actionLoadingId = ref('')
const decisionSubmitting = ref(false)

const filters = reactive({
  keyword: '',
  audit_status: '',
  product_status: '',
  sort: 'newest'
})

const decisionDialog = reactive({
  visible: false,
  mode: 'approve',
  note: '',
  row: null
})

const decisionTitleMap = {
  approve: '确认通过商品',
  request_changes: '确认打回修改',
  reject: '确认驳回商品'
}

const decisionDescriptionMap = {
  approve: '通过后商品会进入可售状态。',
  request_changes: '商品会进入待修改状态，卖家补充后可重新提交审核。',
  reject: '驳回后商品会进入拦截状态，并记录审核备注。'
}

async function loadProducts() {
  loading.value = true
  error.value = ''
  try {
    products.value = await adminApi.products({
      keyword: filters.keyword || undefined,
      audit_status: filters.audit_status || undefined,
      product_status: filters.product_status || undefined,
      sort: filters.sort
    })
  } catch (loadError) {
    error.value = loadError.message
  } finally {
    loading.value = false
  }
}

function applyFilters(nextFilters) {
  filters.keyword = nextFilters.keyword || ''
  filters.audit_status = nextFilters.audit_status || ''
  filters.product_status = nextFilters.product_status || ''
  filters.sort = nextFilters.sort || 'newest'
  loadProducts()
}

function resetFilters() {
  filters.keyword = ''
  filters.audit_status = ''
  filters.product_status = ''
  filters.sort = 'newest'
  loadProducts()
}

function openDetail(row) {
  router.push({ path: `/admin/products/${row.id}`, query: { from: 'products' } })
}

function openDecision(mode, row) {
  decisionDialog.visible = true
  decisionDialog.mode = mode
  decisionDialog.row = row
  decisionDialog.note = mode === 'approve'
    ? '信息完整，允许上架'
    : mode === 'request_changes'
      ? '请补充商品说明、成色或配图后重新提交'
      : '信息不符合要求，请补充后重新提交'
}

async function submitDecision(note) {
  if (!decisionDialog.row) return
  const row = decisionDialog.row
  decisionSubmitting.value = true
  actionLoadingId.value = `${decisionDialog.mode}-${row.id}`
  try {
    await adminApi.auditProduct(row.id, {
      decision:
        decisionDialog.mode === 'approve'
          ? 'APPROVE'
          : decisionDialog.mode === 'request_changes'
            ? 'REQUEST_CHANGES'
            : 'REJECT',
      note
    })
    ElMessage.success(
      decisionDialog.mode === 'approve'
        ? '审核已通过'
        : decisionDialog.mode === 'request_changes'
          ? '已打回修改'
          : '商品已驳回'
    )
    decisionDialog.visible = false
    await loadProducts()
  } catch (submitError) {
    ElMessage.error(submitError.message)
  } finally {
    decisionSubmitting.value = false
    actionLoadingId.value = ''
  }
}

onMounted(loadProducts)

const decisionTitle = computed(() => decisionTitleMap[decisionDialog.mode] || '确认操作')
const decisionDescription = computed(() => decisionDescriptionMap[decisionDialog.mode] || '请确认本次审核动作。')
</script>

<style scoped>
.page-grid {
  display: grid;
  gap: 16px;
}

.page-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.page-title {
  margin: 0 0 4px;
  font-size: 1.3rem;
  font-weight: 700;
}

.page-meta {
  margin: 0;
  color: var(--muted);
  font-size: 0.9rem;
}
</style>
