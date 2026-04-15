<template>
  <div class="grid">
    <section class="grid grid-4">
      <StatPanel label="事件总量" :value="summary.events" description="领域事件记录积累" />
      <StatPanel label="待执行作业" :value="summary.pending_jobs" description="队列中等待运行的作业" />
      <StatPanel label="失败作业" :value="summary.failed_jobs" description="需要人工关注的失败任务" />
      <StatPanel label="待处理审核" :value="summary.pending_audits" description="治理和审核积压情况" />
    </section>

    <section class="grid grid-2">
      <div ref="eventChartRef" class="panel chart-card"></div>
      <div ref="jobChartRef" class="panel chart-card"></div>
    </section>

    <section class="grid grid-2">
      <div class="panel" style="padding: 22px;">
        <div class="section-header">
          <div>
            <h2 class="section-title">基础设施就绪度</h2>
            <p class="section-meta">把依赖接通状态、降级模式和建议动作放到一个面板里</p>
          </div>
        </div>
        <el-table :data="readiness" max-height="360">
          <el-table-column prop="label" label="组件" min-width="120" />
          <el-table-column label="状态" width="120">
            <template #default="{ row }">
              <el-tag :type="tagType(row.status)">{{ row.status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="mode" label="模式" min-width="120" />
          <el-table-column label="说明" min-width="260">
            <template #default="{ row }">
              <div>{{ row.detail }}</div>
              <div class="muted">{{ row.action }}</div>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div class="panel" style="padding: 22px;">
        <div class="section-header">
          <div>
            <h2 class="section-title">平台状态</h2>
            <p class="section-meta">统一查看搜索引擎、存储后端和任务执行模式</p>
          </div>
          <el-button @click="loadOps">刷新</el-button>
        </div>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="运行环境">{{ runtime.app_env }}</el-descriptions-item>
          <el-descriptions-item label="搜索模式">{{ search.mode }}</el-descriptions-item>
          <el-descriptions-item label="搜索可用">{{ search.available ? '可用' : '回退中' }}</el-descriptions-item>
          <el-descriptions-item label="索引名">{{ search.index || '-' }}</el-descriptions-item>
          <el-descriptions-item label="索引文档数">{{ search.document_count ?? 0 }}</el-descriptions-item>
          <el-descriptions-item label="存储后端">{{ summary.storage_backend }}</el-descriptions-item>
          <el-descriptions-item label="AI Provider">{{ runtime.ai_provider }}</el-descriptions-item>
        </el-descriptions>
      </div>
    </section>

    <section class="grid grid-2">
      <div class="panel" style="padding: 22px;">
        <div class="section-header">
          <div>
            <h2 class="section-title">排障手册</h2>
            <p class="section-meta">给本地运行和容器联调留一份可执行清单</p>
          </div>
        </div>
        <div class="ops-runbook">
          <div>
            <h3 class="ops-subtitle">本地启动</h3>
            <pre>{{ runbook.local.join('\n') }}</pre>
          </div>
          <div>
            <h3 class="ops-subtitle">容器联调</h3>
            <pre>{{ runbook.docker.join('\n') }}</pre>
          </div>
          <div>
            <h3 class="ops-subtitle">验证清单</h3>
            <ul class="ops-list">
              <li v-for="item in runbook.verification" :key="item">{{ item }}</li>
            </ul>
          </div>
          <div>
            <h3 class="ops-subtitle">说明</h3>
            <ul class="ops-list">
              <li v-for="item in runbook.notes" :key="item">{{ item }}</li>
            </ul>
          </div>
        </div>
      </div>

      <div class="panel" style="padding: 22px;">
        <div class="section-header">
          <div>
            <h2 class="section-title">失败作业</h2>
            <p class="section-meta">集中查看失败原因和最近异常任务</p>
          </div>
        </div>
        <el-empty v-if="!failedJobs.length" description="暂无失败作业" />
        <el-timeline v-else>
          <el-timeline-item
            v-for="job in failedJobs"
            :key="job.id"
            :timestamp="job.created_at"
          >
            <strong>{{ job.job_name }}</strong>
            <div class="muted">状态：{{ job.status }}</div>
            <div class="muted">{{ JSON.stringify(job.details) }}</div>
          </el-timeline-item>
        </el-timeline>
      </div>
    </section>

    <section class="panel" style="padding: 22px;">
      <div class="section-header">
        <div>
          <h2 class="section-title">最近作业记录</h2>
          <p class="section-meta">用于观察 Celery 队列、同步回退和执行结果</p>
        </div>
      </div>
      <el-table :data="jobs" max-height="420">
        <el-table-column prop="job_name" label="作业" width="180" />
        <el-table-column prop="status" label="状态" width="120" />
        <el-table-column label="详情" min-width="260">
          <template #default="{ row }">
            <span>{{ JSON.stringify(row.details) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" width="180" />
      </el-table>
    </section>

    <section class="panel" style="padding: 22px;">
      <div class="section-header">
        <div>
          <h2 class="section-title">事件类型分布</h2>
          <p class="section-meta">帮助观察系统当前主要活跃领域事件</p>
        </div>
      </div>
      <el-table :data="events" max-height="320">
        <el-table-column prop="name" label="事件类型" />
        <el-table-column prop="value" label="数量" width="120" />
      </el-table>
    </section>
  </div>
</template>

<script setup>
import * as echarts from 'echarts'
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'

import StatPanel from '../../components/StatPanel.vue'
import { adminApi } from '../../api/admin'

const summary = ref({ events: 0, pending_jobs: 0, failed_jobs: 0, pending_audits: 0, storage_backend: 'local' })
const runtime = ref({ app_env: 'development', storage_backend: 'local', ai_provider: 'mock' })
const search = ref({ mode: 'database-fallback', available: false, index: '', document_count: 0 })
const readiness = ref([])
const runbook = ref({ local: [], docker: [], verification: [], notes: [] })
const jobs = ref([])
const failedJobs = ref([])
const events = ref([])
const charts = ref({ eventTypes: [], jobStatuses: [] })
const eventChartRef = ref(null)
const jobChartRef = ref(null)
let eventChartInstance
let jobChartInstance

function tagType(status) {
  if (status === 'READY') return 'success'
  if (status === 'DEGRADED') return 'warning'
  if (status === 'FAILED') return 'danger'
  return 'info'
}

function renderCharts() {
  if (!eventChartRef.value || !jobChartRef.value) return
  eventChartInstance?.dispose()
  jobChartInstance?.dispose()
  eventChartInstance = echarts.init(eventChartRef.value)
  jobChartInstance = echarts.init(jobChartRef.value)

  eventChartInstance.setOption({
    title: { text: '事件类型分布' },
    tooltip: {},
    series: [{ type: 'pie', radius: ['35%', '70%'], data: charts.value.eventTypes || [] }]
  })

  jobChartInstance.setOption({
    title: { text: '作业状态分布' },
    tooltip: {},
    xAxis: { type: 'category', data: (charts.value.jobStatuses || []).map((item) => item.name) },
    yAxis: { type: 'value' },
    series: [{ type: 'bar', data: (charts.value.jobStatuses || []).map((item) => item.value), itemStyle: { color: '#b0582e' } }]
  })
}

async function loadOps() {
  const payload = await adminApi.platformOps()
  summary.value = payload.summary
  runtime.value = payload.runtime
  search.value = payload.search
  readiness.value = payload.readiness || []
  runbook.value = payload.runbook || { local: [], docker: [], verification: [], notes: [] }
  jobs.value = payload.jobs
  failedJobs.value = payload.failedJobs
  events.value = payload.events
  charts.value = payload.charts
  await nextTick()
  renderCharts()
}

onMounted(loadOps)

onBeforeUnmount(() => {
  eventChartInstance?.dispose()
  jobChartInstance?.dispose()
})
</script>

<style scoped>
.chart-card {
  min-height: 320px;
  padding: 16px;
}

.ops-runbook {
  display: grid;
  gap: 18px;
}

.ops-subtitle {
  margin: 0 0 8px;
  font-size: 15px;
}

pre {
  margin: 0;
  padding: 14px 16px;
  border-radius: 12px;
  background: #f4ede5;
  color: #3c2415;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
}

.ops-list {
  margin: 0;
  padding-left: 18px;
  color: #5f4a3b;
}

.ops-list li + li {
  margin-top: 8px;
}
</style>
