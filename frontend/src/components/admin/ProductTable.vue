<template>
  <div class="panel table-card">
    <div class="table-toolbar">
      <div class="toolbar-group grow">
        <el-input v-model="draftKeyword" clearable placeholder="搜索标题或描述" @keyup.enter="emitFilter" />
        <el-select v-model="draftAuditStatus" clearable placeholder="审核状态">
          <el-option v-for="item in auditOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-select v-model="draftProductStatus" clearable placeholder="商品状态">
          <el-option v-for="item in productOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-select v-model="draftSort" placeholder="排序">
          <el-option label="最新创建" value="newest" />
          <el-option label="最近更新" value="updated_desc" />
          <el-option label="价格升序" value="price_asc" />
          <el-option label="价格降序" value="price_desc" />
        </el-select>
      </div>
      <div class="toolbar-group">
        <el-button @click="emitFilter">应用筛选</el-button>
        <el-button plain @click="emitReset">重置</el-button>
      </div>
    </div>

    <el-table :data="products" row-key="id" @row-click="(row) => $emit('view', row)">
      <el-table-column prop="id" label="ID" width="84" />
      <el-table-column label="商品">
        <template #default="{ row }">
          <div class="product-cell">
            <strong>{{ row.title }}</strong>
            <span>{{ row.seller_name || '未知卖家' }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="价格" width="120">
        <template #default="{ row }">¥ {{ Number(row.price || 0).toFixed(2) }}</template>
      </el-table-column>
      <el-table-column label="审核状态" width="120">
        <template #default="{ row }">
          <AuditStatusBadge :status="row.audit_status" />
        </template>
      </el-table-column>
      <el-table-column label="商品状态" width="120">
        <template #default="{ row }">
          <AuditStatusBadge :status="row.product_status" />
        </template>
      </el-table-column>
      <el-table-column label="更新时间" width="120">
        <template #default="{ row }">{{ formatDate(row.updated_at || row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="250" fixed="right">
        <template #default="{ row }">
          <el-space>
            <el-button size="small" type="primary" plain @click.stop="$emit('view', row)">查看详情</el-button>
            <el-button
              size="small"
              :loading="actionLoadingId === `approve-${row.id}`"
              :disabled="row.audit_status === 'APPROVED'"
              @click.stop="$emit('approve', row)"
            >
              通过
            </el-button>
            <el-button
              size="small"
              plain
              :loading="actionLoadingId === `request_changes-${row.id}`"
              :disabled="row.audit_status === 'CHANGES_REQUESTED'"
              @click.stop="$emit('request-changes', row)"
            >
              打回修改
            </el-button>
            <el-button
              size="small"
              plain
              :loading="actionLoadingId === `reject-${row.id}`"
              :disabled="row.audit_status === 'REJECTED'"
              @click.stop="$emit('reject', row)"
            >
              驳回
            </el-button>
          </el-space>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

import AuditStatusBadge from './AuditStatusBadge.vue'

const props = defineProps({
  products: {
    type: Array,
    default: () => []
  },
  filters: {
    type: Object,
    default: () => ({})
  },
  actionLoadingId: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['apply-filter', 'reset-filter', 'view', 'approve', 'request-changes', 'reject'])

const auditOptions = [
  { label: '待审', value: 'PENDING' },
  { label: '已通过', value: 'APPROVED' },
  { label: '已驳回', value: 'REJECTED' },
  { label: '待修改', value: 'CHANGES_REQUESTED' }
]

const productOptions = [
  { label: '在售', value: 'ACTIVE' },
  { label: '草稿', value: 'DRAFT' },
  { label: '已拦截', value: 'BLOCKED' },
  { label: '已下架', value: 'OFF_SHELF' },
  { label: '待修改', value: 'NEEDS_REVISION' }
]

const draftKeyword = ref('')
const draftAuditStatus = ref('')
const draftProductStatus = ref('')
const draftSort = ref('newest')

watch(
  () => props.filters,
  (value) => {
    draftKeyword.value = value.keyword || ''
    draftAuditStatus.value = value.audit_status || ''
    draftProductStatus.value = value.product_status || ''
    draftSort.value = value.sort || 'newest'
  },
  { immediate: true, deep: true }
)

function emitFilter() {
  const payload = {
    keyword: draftKeyword.value.trim(),
    audit_status: draftAuditStatus.value || undefined,
    product_status: draftProductStatus.value || undefined,
    sort: draftSort.value || 'newest'
  }
  emit('apply-filter', payload)
}

function emitReset() {
  draftKeyword.value = ''
  draftAuditStatus.value = ''
  draftProductStatus.value = ''
  draftSort.value = 'newest'
  emit('reset-filter')
}

function formatDate(value) {
  if (!value) return '--'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
}
</script>

<style scoped>
.table-card {
  padding: 18px;
}

.table-toolbar {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.toolbar-group {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.grow {
  flex: 1;
}

.product-cell {
  display: grid;
  gap: 4px;
}

.product-cell strong {
  font-size: 0.92rem;
}

.product-cell span {
  color: var(--muted);
  font-size: 0.82rem;
}
</style>
