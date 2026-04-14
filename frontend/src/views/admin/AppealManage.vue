<template>
  <div class="grid grid-2">
    <section class="panel" style="padding: 22px;">
      <div class="section-header">
        <div>
          <h2 class="section-title">申诉复核</h2>
          <p class="section-meta">查看原举报与申诉上下文，再做最终复核</p>
        </div>
        <el-button @click="loadAppeals">刷新</el-button>
      </div>

      <el-table :data="appeals" @row-click="openContext" highlight-current-row>
        <el-table-column prop="id" label="申诉 ID" width="90" />
        <el-table-column prop="report_id" label="原举报" width="90" />
        <el-table-column prop="status" label="状态" width="120" />
        <el-table-column prop="reason" label="申诉原因" min-width="220" show-overflow-tooltip />
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button size="small" type="primary" plain @click.stop="openContext(row)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <section class="panel" style="padding: 22px;">
      <div class="section-header">
        <div>
          <h2 class="section-title">复核工作台</h2>
          <p class="section-meta">结合原举报与处理时间线完成最终裁定</p>
        </div>
      </div>

      <el-empty v-if="!selectedAppeal" description="从左侧选择一条申诉开始复核" />

      <template v-else>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="申诉 ID">{{ selectedAppeal.id }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ selectedAppeal.status }}</el-descriptions-item>
          <el-descriptions-item label="申诉人">{{ selectedAppeal.applicant_id }}</el-descriptions-item>
          <el-descriptions-item label="申诉原因">{{ selectedAppeal.reason }}</el-descriptions-item>
          <el-descriptions-item label="复核结论">{{ selectedAppeal.decision || '尚未复核' }}</el-descriptions-item>
        </el-descriptions>

        <el-divider />

        <h3 class="section-title">原举报上下文</h3>
        <el-descriptions v-if="context.report" :column="1" border style="margin-top: 12px;">
          <el-descriptions-item label="举报 ID">{{ context.report.id }}</el-descriptions-item>
          <el-descriptions-item label="举报状态">{{ context.report.status }}</el-descriptions-item>
          <el-descriptions-item label="举报原因">{{ context.report.reason }}</el-descriptions-item>
          <el-descriptions-item label="处理备注">{{ context.report.decision || '暂无' }}</el-descriptions-item>
        </el-descriptions>

        <el-form label-position="top" style="margin-top: 16px;">
          <el-form-item label="复核备注">
            <el-input v-model="decisionNote" type="textarea" :rows="4" placeholder="记录复核依据，便于答辩展示和追踪" />
          </el-form-item>
          <el-space wrap>
            <el-button type="primary" :disabled="selectedAppeal.status !== 'PENDING'" @click="review(true)">支持申诉</el-button>
            <el-button :disabled="selectedAppeal.status !== 'PENDING'" @click="review(false)">维持原处理</el-button>
          </el-space>
        </el-form>

        <el-divider />

        <div class="section-header">
          <div>
            <h3 class="section-title">关联任务与时间线</h3>
            <p class="section-meta">申诉提交、复核和原举报处理都在这里可追溯</p>
          </div>
        </div>
        <el-timeline>
          <el-timeline-item
            v-for="task in context.tasks"
            :key="`task-${task.id}`"
            :timestamp="task.created_at"
          >
            <strong>{{ task.task_type }}</strong>
            <div class="muted">状态：{{ task.status }}</div>
            <div class="muted">{{ JSON.stringify(task.payload) }}</div>
          </el-timeline-item>
          <el-timeline-item
            v-for="operation in context.operations"
            :key="`op-${operation.id}`"
            :timestamp="operation.created_at"
          >
            <strong>{{ operation.action }}</strong>
            <div class="muted">操作人：{{ operation.actor_id ?? '系统' }}</div>
            <div class="muted">{{ JSON.stringify(operation.details) }}</div>
          </el-timeline-item>
        </el-timeline>
      </template>
    </section>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { adminApi } from '../../api/admin'

const appeals = ref([])
const selectedAppeal = ref(null)
const context = ref({ report: null, tasks: [], operations: [] })
const decisionNote = ref('')

async function loadAppeals() {
  appeals.value = await adminApi.appeals()
  if (!selectedAppeal.value && appeals.value.length) {
    await openContext(appeals.value[0])
  }
}

async function openContext(row) {
  selectedAppeal.value = row
  decisionNote.value = row.decision || ''
  context.value = await adminApi.appealContext(row.id)
}

async function review(approved) {
  if (!selectedAppeal.value) {
    return
  }
  await adminApi.reviewAppeal(selectedAppeal.value.id, {
    approved,
    note: decisionNote.value || (approved ? '申诉成立' : '维持原处理结果')
  })
  ElMessage.success('申诉已复核')
  await loadAppeals()
  await openContext(appeals.value.find((item) => item.id === selectedAppeal.value.id) || selectedAppeal.value)
}

onMounted(loadAppeals)
</script>
