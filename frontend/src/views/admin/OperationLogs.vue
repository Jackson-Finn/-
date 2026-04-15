<template>
  <div class="logs-page">
    <section class="page-head">
      <div>
        <div class="eyebrow">Operations</div>
        <h2 class="page-title">操作记录</h2>
        <p class="page-meta">关键动作在这里统一留痕，便于追溯和复核。</p>
      </div>
      <el-button :loading="loading" @click="loadOperations">刷新记录</el-button>
    </section>

    <LoadingState v-if="loading && !operations.length" :rows="5" />
    <ErrorState v-else-if="error && !operations.length" :description="error" @retry="loadOperations" />
    <EmptyState v-else-if="!operations.length" description="暂无操作记录。" />
    <div v-else class="panel logs-card">
      <el-table :data="operations" row-key="id">
        <el-table-column prop="action" label="动作" width="180" />
        <el-table-column label="操作者" width="100">
          <template #default="{ row }">{{ row.actor_id ?? '系统' }}</template>
        </el-table-column>
        <el-table-column label="详情">
          <template #default="{ row }">{{ formatDetails(row.details) }}</template>
        </el-table-column>
        <el-table-column label="时间" width="180">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'

import EmptyState from '../../components/admin/EmptyState.vue'
import ErrorState from '../../components/admin/ErrorState.vue'
import LoadingState from '../../components/admin/LoadingState.vue'
import { adminApi } from '../../api/admin'

const loading = ref(false)
const error = ref('')
const operations = ref([])

async function loadOperations() {
  loading.value = true
  error.value = ''
  try {
    operations.value = await adminApi.operations()
  } catch (loadError) {
    error.value = loadError.message
  } finally {
    loading.value = false
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

function formatDetails(details) {
  if (!details || typeof details !== 'object') return '--'
  return Object.entries(details)
    .map(([key, value]) => `${key}: ${value}`)
    .join(' · ')
}

onMounted(loadOperations)
</script>

<style scoped>
.logs-page {
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

.logs-card {
  padding: 18px;
}
</style>
