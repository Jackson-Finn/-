<template>
  <div class="my-products-page">
    <header class="panel page-header">
      <div>
        <div class="eyebrow">Seller Workspace</div>
        <h2>我的商品</h2>
        <p>统一查看审核状态、继续编辑，并处理打回修改的商品。</p>
      </div>
      <div class="header-actions">
        <RouterLink to="/publish">
          <el-button type="primary">新建商品</el-button>
        </RouterLink>
        <el-button plain :loading="loading" @click="loadProducts">刷新</el-button>
      </div>
    </header>

    <section class="metrics-grid">
      <article class="panel metric-card">
        <span class="metric-label">全部商品</span>
        <strong>{{ products.length }}</strong>
      </article>
      <article class="panel metric-card">
        <span class="metric-label">待审</span>
        <strong>{{ summary.pending }}</strong>
      </article>
      <article class="panel metric-card">
        <span class="metric-label">待修改</span>
        <strong>{{ summary.revision }}</strong>
      </article>
      <article class="panel metric-card">
        <span class="metric-label">已上架</span>
        <strong>{{ summary.active }}</strong>
      </article>
    </section>

    <DataStateCard
      :state="pageState"
      title="商品列表加载失败"
      :error-description="error"
      empty-title="还没有发布商品"
      empty-description="先创建第一件商品，之后就可以在这里统一跟进审核与修改。"
      @retry="loadProducts"
    >
      <section class="panel workspace-panel">
        <div class="toolbar">
          <el-input
            v-model="keyword"
            clearable
            placeholder="搜索标题或描述"
            class="toolbar-search"
          />
          <el-select v-model="statusFilter" class="toolbar-select">
            <el-option label="全部状态" value="ALL" />
            <el-option label="待审" value="PENDING" />
            <el-option label="待修改" value="CHANGES_REQUESTED" />
            <el-option label="已通过" value="APPROVED" />
            <el-option label="已驳回" value="REJECTED" />
            <el-option label="已下架" value="OFF_SHELF" />
          </el-select>
          <el-select v-model="sortBy" class="toolbar-select">
            <el-option label="最近更新" value="updated" />
            <el-option label="最新创建" value="created" />
            <el-option label="价格从低到高" value="price_asc" />
            <el-option label="价格从高到低" value="price_desc" />
          </el-select>
        </div>

        <el-table :data="filteredProducts" class="product-table" empty-text="暂无匹配商品">
          <el-table-column label="商品" min-width="300">
            <template #default="{ row }">
              <div class="product-cell">
                <img v-if="row.cover_image" :src="row.cover_image" :alt="row.title" class="product-thumb">
                <div v-else class="product-thumb placeholder">{{ (row.title || 'P').slice(0, 1) }}</div>
                <div class="product-copy">
                  <strong>{{ row.title }}</strong>
                  <p>{{ row.description || '暂无描述' }}</p>
                  <div class="product-meta">
                    <span>¥ {{ Number(row.price || 0).toFixed(2) }}</span>
                    <span>库存 {{ row.stock }}</span>
                    <span v-if="row.category_name">{{ row.category_name }}</span>
                  </div>
                </div>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="审核状态" width="140">
            <template #default="{ row }">
              <el-tag :type="statusTagType(row.audit_status)" effect="plain">
                {{ auditStatusLabel(row.audit_status) }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column label="商品状态" width="140">
            <template #default="{ row }">
              <el-tag effect="plain">{{ productStatusLabel(row.product_status) }}</el-tag>
            </template>
          </el-table-column>

          <el-table-column label="更新时间" width="140">
            <template #default="{ row }">
              {{ formatTime(row.updated_at || row.created_at) }}
            </template>
          </el-table-column>

          <el-table-column label="操作" min-width="320" fixed="right">
            <template #default="{ row }">
              <div class="table-actions">
                <el-button link type="primary" @click="viewDetail(row.id)">查看详情</el-button>
                <el-button link @click="editProduct(row.id)">继续编辑</el-button>
                <el-button
                  v-if="row.audit_status === 'CHANGES_REQUESTED'"
                  link
                  type="warning"
                  @click="resubmitFromEditor(row.id)"
                >
                  修改后重提
                </el-button>
                <el-button
                  link
                  :disabled="row.product_status !== 'ACTIVE'"
                  :loading="isActionLoading(row.id, 'off-shelf')"
                  @click="offShelf(row)"
                >
                  下架
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </section>
    </DataStateCard>

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
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import ConfirmDialog from '../../components/common/ConfirmDialog.vue'
import DataStateCard from '../../components/DataStateCard.vue'
import { productApi } from '../../api/products'

const router = useRouter()

const products = ref([])
const loading = ref(false)
const error = ref('')
const keyword = ref('')
const statusFilter = ref('ALL')
const sortBy = ref('updated')
const activeActionKey = ref('')

const confirmDialog = ref({
  visible: false,
  title: '确认下架',
  description: '',
  loading: false,
  onConfirm: null
})

const pageState = computed(() => {
  if (loading.value && !products.value.length) return 'loading'
  if (error.value && !products.value.length) return 'error'
  if (!filteredProducts.value.length && !products.value.length) return 'empty'
  return 'ready'
})

const summary = computed(() => ({
  pending: products.value.filter((item) => item.audit_status === 'PENDING').length,
  revision: products.value.filter((item) => item.audit_status === 'CHANGES_REQUESTED').length,
  active: products.value.filter((item) => item.product_status === 'ACTIVE').length
}))

const filteredProducts = computed(() => {
  const normalized = keyword.value.trim().toLowerCase()
  const next = products.value.filter((item) => {
    const matchesKeyword = !normalized
      || item.title?.toLowerCase().includes(normalized)
      || item.description?.toLowerCase().includes(normalized)
    const matchesStatus = statusFilter.value === 'ALL'
      || item.audit_status === statusFilter.value
      || item.product_status === statusFilter.value
    return matchesKeyword && matchesStatus
  })

  const sorting = {
    updated: (a, b) => new Date(b.updated_at || b.created_at) - new Date(a.updated_at || a.created_at),
    created: (a, b) => new Date(b.created_at) - new Date(a.created_at),
    price_asc: (a, b) => Number(a.price || 0) - Number(b.price || 0),
    price_desc: (a, b) => Number(b.price || 0) - Number(a.price || 0)
  }

  return [...next].sort(sorting[sortBy.value] || sorting.updated)
})

loadProducts()

async function loadProducts() {
  loading.value = true
  error.value = ''
  try {
    products.value = await productApi.mine()
  } catch (requestError) {
    error.value = requestError.message
  } finally {
    loading.value = false
  }
}

function viewDetail(productId) {
  router.push(`/products/${productId}`)
}

function editProduct(productId) {
  router.push({ path: '/publish', query: { productId } })
}

function resubmitFromEditor(productId) {
  router.push({ path: '/publish', query: { productId, mode: 'resubmit' } })
}

async function offShelf(product) {
  confirmDialog.value = {
    visible: true,
    title: '确认下架',
    description: `确定要下架"${product.title}"吗？`,
    loading: false,
    onConfirm: async () => {
      const actionKey = `${product.id}:off-shelf`
      activeActionKey.value = actionKey
      confirmDialog.value.loading = true
      try {
        const updated = await productApi.offShelf(product.id)
        products.value = products.value.map((item) => (item.id === product.id ? updated : item))
        confirmDialog.value.visible = false
        ElMessage.success('商品已下架')
      } catch (requestError) {
        ElMessage.error(requestError.message)
      } finally {
        if (activeActionKey.value === actionKey) {
          activeActionKey.value = ''
        }
        confirmDialog.value.loading = false
      }
    }
  }
}

function isActionLoading(productId, action) {
  return activeActionKey.value === `${productId}:${action}`
}

function auditStatusLabel(status) {
  const mapping = {
    PENDING: '待审',
    APPROVED: '已通过',
    REJECTED: '已驳回',
    CHANGES_REQUESTED: '待修改'
  }
  return mapping[status] || status
}

function productStatusLabel(status) {
  const mapping = {
    DRAFT: '草稿',
    ACTIVE: '在售',
    BLOCKED: '已拦截',
    OFF_SHELF: '已下架',
    NEEDS_REVISION: '待修改'
  }
  return mapping[status] || status
}

function statusTagType(status) {
  if (status === 'APPROVED') return 'success'
  if (status === 'PENDING') return 'warning'
  if (status === 'CHANGES_REQUESTED') return 'info'
  if (status === 'REJECTED') return 'danger'
  return ''
}

function formatTime(value) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.my-products-page {
  display: grid;
  gap: 18px;
}

.page-header,
.workspace-panel {
  padding: 20px 22px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.page-header h2 {
  margin: 0 0 6px;
  font-size: 1.4rem;
  font-weight: 700;
  letter-spacing: -0.03em;
}

.page-header p {
  margin: 0;
  color: var(--muted);
  font-size: 0.92rem;
}

.header-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.metric-card {
  padding: 18px;
  display: grid;
  gap: 8px;
}

.metric-label {
  color: var(--muted);
  font-size: 0.8rem;
  font-weight: 600;
}

.metric-card strong {
  font-size: 1.8rem;
  line-height: 1;
  letter-spacing: -0.04em;
}

.workspace-panel {
  display: grid;
  gap: 16px;
}

.toolbar {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 160px 160px;
  gap: 12px;
}

.toolbar-search,
.toolbar-select {
  width: 100%;
}

.product-table :deep(.el-table__cell) {
  vertical-align: top;
}

.product-cell {
  display: flex;
  gap: 14px;
}

.product-thumb {
  width: 72px;
  height: 72px;
  border-radius: 14px;
  object-fit: cover;
  flex-shrink: 0;
  background: #eef3fb;
}

.product-thumb.placeholder {
  display: grid;
  place-items: center;
  color: var(--muted);
  font-weight: 700;
}

.product-copy {
  min-width: 0;
  display: grid;
  gap: 6px;
}

.product-copy strong {
  font-size: 0.95rem;
  line-height: 1.45;
}

.product-copy p {
  margin: 0;
  color: var(--muted);
  line-height: 1.55;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.product-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  color: var(--muted);
  font-size: 0.78rem;
}

.table-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
}

@media (max-width: 960px) {
  .page-header {
    flex-direction: column;
  }

  .metrics-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .toolbar {
    grid-template-columns: 1fr;
  }
}
</style>
