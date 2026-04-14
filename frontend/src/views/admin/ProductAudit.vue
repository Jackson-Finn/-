<template>
  <div class="panel" style="padding: 22px;">
    <div class="section-header">
      <div>
        <h2 class="section-title">商品审核</h2>
        <p class="section-meta">统一审核队列中的商品任务</p>
      </div>
      <el-button @click="loadPending">刷新</el-button>
    </div>

    <el-table :data="products">
      <el-table-column prop="id" label="商品 ID" width="100" />
      <el-table-column prop="title" label="标题" />
      <el-table-column prop="audit_status" label="审核状态" width="120" />
      <el-table-column label="操作" width="240">
        <template #default="{ row }">
          <el-space>
            <el-button type="primary" size="small" @click="audit(row.id, true)">通过</el-button>
            <el-button type="danger" plain size="small" @click="audit(row.id, false)">驳回</el-button>
          </el-space>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { adminApi } from '../../api/admin'

const products = ref([])

async function loadPending() {
  products.value = await adminApi.pendingProducts()
}

async function audit(id, approved) {
  await adminApi.auditProduct(id, { approved, note: approved ? '审核通过' : '信息不符合要求' })
  ElMessage.success('审核完成')
  await loadPending()
}

onMounted(loadPending)
</script>

