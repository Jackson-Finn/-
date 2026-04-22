<template>
  <div class="grid grid-2">
    <section class="panel" style="padding: 22px;">
      <div class="section-header">
        <div>
          <h2 class="section-title">举报处理</h2>
          <p class="section-meta">先查看上下文，再做治理决定</p>
        </div>
        <el-button @click="loadReports">刷新</el-button>
      </div>

      <el-table :data="reports" @row-click="openContext" highlight-current-row>
        <el-table-column prop="id" label="举报 ID" width="90" />
        <el-table-column prop="target_type" label="目标类型" width="110" />
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.status === 'PROCESSED'" type="success" effect="light">已处理</el-tag>
            <el-tag v-else type="warning" effect="light">待处理</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="reason" label="举报原因" min-width="220" show-overflow-tooltip />
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
          <h2 class="section-title">处理工作台</h2>
          <p class="section-meta">选中举报后查看上下文、备注与操作时间线</p>
        </div>
      </div>

      <el-empty v-if="!selectedReport" description="从左侧选择一条举报开始处理" />

      <template v-else>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="举报 ID">{{ selectedReport.id }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag v-if="selectedReport.status === 'PROCESSED'" type="success" effect="light">已处理</el-tag>
            <el-tag v-else type="warning" effect="light">待处理</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="举报人">{{ selectedReport.reporter_id }}</el-descriptions-item>
          <el-descriptions-item label="目标">{{ selectedReport.target_type }} / {{ selectedReport.target_id }}</el-descriptions-item>
          <el-descriptions-item label="举报原因">{{ selectedReport.reason }}</el-descriptions-item>
          <el-descriptions-item label="处理备注">{{ selectedReport.decision || '尚未处理' }}</el-descriptions-item>
        </el-descriptions>

        <template v-if="selectedReport.status !== 'PROCESSED'">
          <el-form label-position="top" style="margin-top: 16px;">
            <el-form-item label="处理备注">
              <el-input v-model="decisionNote" type="textarea" :rows="4" placeholder="记录处理依据，便于复核与展示" />
            </el-form-item>
            <el-space wrap>
              <el-button type="primary" @click="process(true)">确认处理</el-button>
              <el-button @click="process(false)">判定无效</el-button>
            </el-space>
          </el-form>
        </template>
        <el-result v-else icon="success" title="已处理完成" :sub-title="selectedReport.decision ? `处理备注：${selectedReport.decision}` : ''" style="margin-top: 16px;" />

        <el-divider />

        <div class="section-header">
          <div>
            <h3 class="section-title">关联任务</h3>
            <p class="section-meta">和这条举报绑定的审核工作流任务</p>
          </div>
        </div>
        <el-empty v-if="!context.tasks.length" description="暂无关联任务" />
        <el-timeline v-else>
          <el-timeline-item
            v-for="task in context.tasks"
            :key="task.id"
            :timestamp="task.created_at"
          >
            <strong>{{ task.task_type }}</strong>
            <div class="muted">状态：{{ task.status }}</div>
            <div class="muted">载荷：{{ JSON.stringify(task.payload) }}</div>
          </el-timeline-item>
        </el-timeline>

        <el-divider />

        <div class="section-header">
          <div>
            <h3 class="section-title">操作时间线</h3>
            <p class="section-meta">展示举报提交与处理动作的留痕</p>
          </div>
        </div>
        <el-empty v-if="!context.operations.length" description="暂无操作记录" />
        <el-timeline v-else>
          <el-timeline-item
            v-for="operation in context.operations"
            :key="operation.id"
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

const reports = ref([])
const selectedReport = ref(null)
const context = ref({ tasks: [], operations: [] })
const decisionNote = ref('')

async function loadReports() {
  reports.value = await adminApi.reports()
  if (!selectedReport.value && reports.value.length) {
    await openContext(reports.value[0])
  }
}

async function openContext(row) {
  selectedReport.value = row
  decisionNote.value = row.decision || ''
  const ctx = await adminApi.reportContext(row.id)
  context.value = ctx
  if (ctx.report) {
    selectedReport.value = { ...row, status: ctx.report.status, decision: ctx.report.decision }
  }
}

async function process(approved) {
  if (!selectedReport.value) {
    return
  }
  await adminApi.processReport(selectedReport.value.id, {
    approved,
    note: decisionNote.value || (approved ? '已完成处理' : '判定为无效举报')
  })
  ElMessage.success('举报处理完成')
  await loadReports()
  await openContext(reports.value.find((item) => item.id === selectedReport.value.id) || selectedReport.value)
}

onMounted(loadReports)
</script>
