<template>
  <div class="queue-page">
    <section class="page-head">
      <div>
        <div class="eyebrow">待办队列</div>
        <h2 class="page-title">待办队列</h2>
        <p class="page-meta">从当前待办直接进入商品详情，处理后继续下一个对象。</p>
      </div>
      <el-space wrap>
        <RouterLink to="/admin/products">
          <el-button plain>全部商品</el-button>
        </RouterLink>
        <el-button :loading="loading" @click="loadQueue">刷新队列</el-button>
      </el-space>
    </section>

    <LoadingState v-if="loading && !tasks.length" :rows="5" />
    <ErrorState v-else-if="error && !tasks.length" :description="error" @retry="loadQueue" />
    <EmptyState v-else-if="!tasks.length" description="当前没有待处理任务。" />
    <div v-else class="panel queue-card">
      <el-table :data="tasks" row-key="id">
        <el-table-column prop="id" label="任务 ID" width="88" />
        <el-table-column prop="task_type" label="类型" width="150" />
        <el-table-column label="对象" min-width="280">
          <template #default="{ row }">
            <div class="queue-object">
              <strong>{{ row.payload?.title || `商品 #${row.entity_id}` }}</strong>
              <span>{{ row.entity_type }} / {{ row.entity_id }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <AuditStatusBadge :status="row.status" />
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="160">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button type="primary" plain size="small" @click="openTask(row)">进入处理</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import AuditStatusBadge from '../../components/admin/AuditStatusBadge.vue'
import EmptyState from '../../components/admin/EmptyState.vue'
import ErrorState from '../../components/admin/ErrorState.vue'
import LoadingState from '../../components/admin/LoadingState.vue'
import { adminApi } from '../../api/admin'

const router = useRouter()
const loading = ref(false)
const error = ref('')
const tasks = ref([])

async function loadQueue() {
  loading.value = true
  error.value = ''
  try {
    tasks.value = (await adminApi.auditTasks()).filter((item) => item.entity_type === 'PRODUCT' && item.status === 'PENDING')
  } catch (loadError) {
    error.value = loadError.message
  } finally {
    loading.value = false
  }
}

function openTask(task) {
  router.push({ path: `/admin/products/${task.entity_id}`, query: { from: 'audits', taskId: task.id } })
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

onMounted(loadQueue)
</script>

<style scoped>
.queue-page {
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

.queue-card {
  padding: 18px;
}

.queue-object {
  display: grid;
  gap: 4px;
}

.queue-object span {
  color: var(--muted);
  font-size: 0.82rem;
}
</style>
