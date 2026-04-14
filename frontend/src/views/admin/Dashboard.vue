<template>
  <div class="grid">
    <section class="grid grid-4">
      <StatPanel label="商品总量" :value="overview.products" description="平台在售与草稿统计" />
      <StatPanel label="待审核" :value="overview.pending_audits" description="商品和治理任务积压" />
      <StatPanel label="订单总量" :value="overview.orders" description="交易闭环规模" />
      <StatPanel label="举报总量" :value="overview.reports" description="治理域处理负载" />
    </section>

    <section class="grid grid-2">
      <div ref="orderChartRef" class="panel chart-card"></div>
      <div ref="auditChartRef" class="panel chart-card"></div>
    </section>

    <section class="grid grid-2">
      <div class="panel" style="padding: 22px;">
        <div class="section-header">
          <div>
            <h3 class="section-title">运维动作</h3>
            <p class="section-meta">搜索重建与推荐刷新</p>
          </div>
        </div>
        <el-space wrap>
          <el-button type="primary" @click="rebuildRecommendations">刷新推荐快照</el-button>
          <el-button @click="reindexSearch">重建搜索索引</el-button>
          <el-button @click="loadDashboard">刷新概览</el-button>
        </el-space>
      </div>

      <div class="panel" style="padding: 22px;">
        <div class="section-header">
          <div>
            <h3 class="section-title">审核队列</h3>
            <p class="section-meta">统一工作流任务一览</p>
          </div>
        </div>
        <el-table :data="auditTasks">
          <el-table-column prop="id" label="任务 ID" />
          <el-table-column prop="task_type" label="类型" />
          <el-table-column prop="status" label="状态" />
        </el-table>
      </div>
    </section>

    <section class="panel" style="padding: 22px;">
      <div class="section-header">
        <div>
          <h3 class="section-title">最近操作记录</h3>
          <p class="section-meta">审核、举报和申诉处理都会留下可追踪记录</p>
        </div>
      </div>
      <el-table :data="operations">
        <el-table-column prop="action" label="动作" width="180" />
        <el-table-column prop="actor_id" label="操作者" width="100" />
        <el-table-column label="详情">
          <template #default="{ row }">
            <span>{{ JSON.stringify(row.details) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" width="180" />
      </el-table>
    </section>
  </div>
</template>

<script setup>
import * as echarts from 'echarts'
import { nextTick, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import StatPanel from '../../components/StatPanel.vue'
import { adminApi } from '../../api/admin'
const overview = ref({ products: 0, pending_audits: 0, job_count: 0 })
const auditTasks = ref([])
const operations = ref([])
const chartData = ref({})
const orderChartRef = ref(null)
const auditChartRef = ref(null)

function renderCharts() {
  const orderChart = echarts.init(orderChartRef.value)
  const auditChart = echarts.init(auditChartRef.value)

  orderChart.setOption({
    title: { text: '订单状态分布' },
    tooltip: {},
    series: [{ type: 'pie', data: chartData.value.orderStatus || [] }]
  })

  auditChart.setOption({
    title: { text: '治理结果分布' },
    xAxis: { type: 'category', data: (chartData.value.reportOutcome || []).map((item) => item.name) },
    yAxis: { type: 'value' },
    series: [{ type: 'bar', data: (chartData.value.reportOutcome || []).map((item) => item.value), itemStyle: { color: '#245c5a' } }]
  })
}

async function loadDashboard() {
  overview.value = await adminApi.overview()
  chartData.value = await adminApi.charts()
  auditTasks.value = await adminApi.auditTasks()
  operations.value = await adminApi.operations()
  await nextTick()
  renderCharts()
}

async function rebuildRecommendations() {
  await adminApi.rebuildRecommendations()
  ElMessage.success('推荐任务已触发')
}

async function reindexSearch() {
  await adminApi.reindexSearch()
  ElMessage.success('搜索重建任务已触发')
}

onMounted(loadDashboard)
</script>

<style scoped>
.chart-card {
  min-height: 320px;
  padding: 16px;
}
</style>
