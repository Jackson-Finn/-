<template>
  <div class="detail-page" :key="productId">
    <section class="detail-head">
      <BackButton :to="backTarget" />
      <el-space wrap>
        <RouterLink to="/admin/audits">
          <el-button plain>待办队列</el-button>
        </RouterLink>
        <RouterLink to="/admin/operations">
          <el-button plain>操作记录</el-button>
        </RouterLink>
      </el-space>
    </section>

    <LoadingState v-if="loading && !product.id" :rows="6" />
    <ErrorState v-else-if="error && !product.id" :description="error" @retry="loadDetail" />
    <template v-else-if="product.id">
      <ProductDetailHeader :product="product" />

      <div class="detail-layout">
        <main class="content-column">
          <ProductMediaGallery
            :images="product.images || []"
            :active-image="activeImage"
            :title="product.title"
            @select="activeImage = $event"
          />

          <section class="panel body-card">
            <div class="section-header">
              <div>
                <div class="eyebrow">Description</div>
                <h3 class="section-title">商品说明</h3>
              </div>
            </div>
            <div class="description-block">{{ product.description || '暂无描述' }}</div>
          </section>

          <section class="panel body-card">
            <div class="section-header">
              <div>
                <div class="eyebrow">Audit Context</div>
                <h3 class="section-title">审核记录</h3>
              </div>
            </div>

            <div class="timeline-list">
              <div v-for="task in context.tasks" :key="task.id" class="timeline-item">
                <div class="timeline-title">
                  <strong>{{ task.task_type }}</strong>
                  <AuditStatusBadge :status="task.status" />
                </div>
                <p>{{ task.payload?.note || task.payload?.title || task.payload?.reason || '暂无附加说明' }}</p>
                <span>{{ formatDateTime(task.created_at) }}</span>
              </div>
              <EmptyState v-if="!context.tasks.length" title="TASKS" description="暂无审核任务记录。" />
            </div>
          </section>

          <section class="panel body-card">
            <div class="section-header">
              <div>
                <div class="eyebrow">Action Log</div>
                <h3 class="section-title">操作日志</h3>
              </div>
            </div>

            <el-timeline v-if="context.operations.length">
              <el-timeline-item
                v-for="item in context.operations"
                :key="item.id"
                :timestamp="formatDateTime(item.created_at)"
              >
                <strong>{{ item.action }}</strong>
                <div class="muted">操作人：{{ item.actor_id ?? '系统' }}</div>
                <div class="muted">{{ formatDetails(item.details) }}</div>
              </el-timeline-item>
            </el-timeline>
            <EmptyState v-else title="LOGS" description="还没有关联操作记录。" />
          </section>
        </main>

        <aside class="side-column">
          <ActionToolbar
            :disabled="submitting"
            :loading-action="loadingAction"
            :audit-status="product.audit_status"
            :product-status="product.product_status"
            @approve="openDecision('approve')"
            @request-changes="openDecision('request_changes')"
            @reject="openDecision('reject')"
            @off-shelf="openDecision('off_shelf')"
          />

          <ProductMetaPanel title="Meta" headline="基础信息" :items="metaItems" />

          <ProductMetaPanel title="Governance" headline="治理信息" :items="governanceItems">
            <div v-if="context.reports.length" class="report-list">
              <div v-for="report in context.reports" :key="report.id" class="report-item">
                <div class="report-row">
                  <strong>举报 #{{ report.id }}</strong>
                  <AuditStatusBadge :status="report.status" />
                </div>
                <p>{{ report.reason }}</p>
              </div>
            </div>
            <div v-else class="inline-empty">暂无关联举报。</div>
          </ProductMetaPanel>
        </aside>
      </div>
    </template>

    <ConfirmDialog
      v-model="decisionDialog.visible"
      :title="decisionDialog.title"
      :description="decisionDialog.description"
      :note="decisionDialog.note"
      :loading="submitting"
      placeholder="补充处理说明"
      @confirm="submitDecision"
    />
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'

import ActionToolbar from '../../components/admin/ActionToolbar.vue'
import AuditStatusBadge from '../../components/admin/AuditStatusBadge.vue'
import BackButton from '../../components/admin/BackButton.vue'
import ConfirmDialog from '../../components/admin/ConfirmDialog.vue'
import EmptyState from '../../components/admin/EmptyState.vue'
import ErrorState from '../../components/admin/ErrorState.vue'
import LoadingState from '../../components/admin/LoadingState.vue'
import ProductDetailHeader from '../../components/admin/ProductDetailHeader.vue'
import ProductMediaGallery from '../../components/admin/ProductMediaGallery.vue'
import ProductMetaPanel from '../../components/admin/ProductMetaPanel.vue'
import { adminApi } from '../../api/admin'

const route = useRoute()

const loading = ref(false)
const error = ref('')
const product = ref({})
const context = ref({ tasks: [], reports: [], operations: [] })
const activeImage = ref('')
const submitting = ref(false)
const loadingAction = ref('')

const decisionDialog = ref({
  visible: false,
  action: '',
  title: '',
  description: '',
  note: ''
})

const productId = computed(() => route.params.productId)
const backTarget = computed(() => (route.query.from === 'audits' ? '/admin/audits' : '/admin/products'))

const metaItems = computed(() => [
  { label: '商品 ID', value: product.value.id },
  { label: '卖家', value: product.value.seller_name || '--' },
  { label: '分类', value: product.value.category_name || '--' },
  { label: '库存', value: product.value.stock },
  { label: '发布时间', value: formatDateTime(product.value.created_at) }
])

const governanceItems = computed(() => [
  { label: '审核状态', value: statusText(product.value.audit_status) },
  { label: '商品状态', value: statusText(product.value.product_status) },
  { label: '关联任务', value: context.value.tasks.length },
  { label: '关联举报', value: context.value.reports.length }
])

watch(
  productId,
  async () => {
    product.value = {}
    context.value = { tasks: [], reports: [], operations: [] }
    activeImage.value = ''
    await loadDetail()
  },
  { immediate: true }
)

async function loadDetail() {
  loading.value = true
  error.value = ''
  try {
    const data = await adminApi.productDetail(productId.value)
    product.value = data.product
    context.value = {
      tasks: data.tasks || [],
      reports: data.reports || [],
      operations: data.operations || []
    }
    activeImage.value = data.product.images?.[0] || ''
  } catch (loadError) {
    error.value = loadError.message
  } finally {
    loading.value = false
  }
}

function openDecision(action) {
  const mapping = {
    approve: {
      title: '确认通过商品',
      description: '通过后商品会进入可售状态。',
      note: '信息完整，允许上架'
    },
    request_changes: {
      title: '确认打回修改',
      description: '商品会进入待修改状态，卖家补充后可重新提交审核。',
      note: '请补充商品说明、成色或配图后重新提交'
    },
    reject: {
      title: '确认驳回商品',
      description: '驳回后商品会进入拦截状态。',
      note: '信息不完整，需修改后重新提交'
    },
    off_shelf: {
      title: '确认下架商品',
      description: '下架后商品会从可售列表移除。',
      note: '管理员手动下架'
    }
  }
  decisionDialog.value = {
    visible: true,
    action,
    ...mapping[action]
  }
}

async function submitDecision(note) {
  submitting.value = true
  loadingAction.value = decisionDialog.value.action
  try {
    if (decisionDialog.value.action === 'off_shelf') {
      await adminApi.offShelfProduct(product.value.id, { note })
      ElMessage.success('商品已下架')
    } else {
      await adminApi.auditProduct(product.value.id, {
        decision:
          decisionDialog.value.action === 'approve'
            ? 'APPROVE'
            : decisionDialog.value.action === 'request_changes'
              ? 'REQUEST_CHANGES'
              : 'REJECT',
        note
      })
      ElMessage.success(
        decisionDialog.value.action === 'approve'
          ? '审核已通过'
          : decisionDialog.value.action === 'request_changes'
            ? '已打回修改'
            : '商品已驳回'
      )
    }
    decisionDialog.value.visible = false
    await loadDetail()
  } catch (submitError) {
    ElMessage.error(submitError.message)
  } finally {
    submitting.value = false
    loadingAction.value = ''
  }
}

function formatDateTime(value) {
  if (!value) return '--'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function statusText(value) {
  const mapping = {
    PENDING: '待审',
    APPROVED: '已通过',
    REJECTED: '已驳回',
    CHANGES_REQUESTED: '待修改',
    ACTIVE: '在售',
    NEEDS_REVISION: '待修改',
    BLOCKED: '已拦截',
    OFF_SHELF: '已下架'
  }
  return mapping[value] || value || '--'
}

function formatDetails(details) {
  if (!details || typeof details !== 'object') return '--'
  return Object.entries(details)
    .map(([key, value]) => `${key}: ${value}`)
    .join(' · ')
}
</script>

<style scoped>
.detail-page {
  display: grid;
  gap: 16px;
}

.detail-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.detail-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) 360px;
  gap: 16px;
  align-items: start;
}

.content-column,
.side-column {
  display: grid;
  gap: 16px;
}

.body-card {
  padding: 18px;
}

.description-block {
  line-height: 1.75;
  color: var(--text);
}

.timeline-list {
  display: grid;
  gap: 12px;
}

.timeline-item {
  padding: 14px;
  border-radius: 16px;
  border: 1px solid var(--line);
  background: #fbfdff;
}

.timeline-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

.timeline-item p,
.report-item p {
  margin: 0;
  color: var(--muted);
  line-height: 1.6;
}

.timeline-item span {
  display: inline-block;
  margin-top: 8px;
  color: var(--muted);
  font-size: 0.8rem;
}

.report-list {
  display: grid;
  gap: 10px;
  margin-top: 12px;
}

.report-item {
  padding-top: 12px;
  border-top: 1px solid var(--line);
}

.report-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 8px;
}

.inline-empty {
  color: var(--muted);
  font-size: 0.88rem;
}

@media (max-width: 1100px) {
  .detail-layout {
    grid-template-columns: 1fr;
  }
}
</style>
