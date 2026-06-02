<template>
  <div class="grid">
    <section class="panel overview-bar">
      <div>
        <div class="eyebrow">运营总览</div>
        <h2 class="section-title">运营概览</h2>
        <p class="section-meta">把待审商品、治理动作和系统状态放在同一屏处理。</p>
      </div>
      <div class="action-grid">
        <RouterLink to="/admin/audits">
          <el-button type="primary">处理待审商品</el-button>
        </RouterLink>
        <RouterLink to="/admin/products">
          <el-button plain>查看商品列表</el-button>
        </RouterLink>
        <el-button @click="loadDashboard">刷新概览</el-button>
      </div>
    </section>

    <section class="grid grid-4">
      <StatPanel label="商品总量" :value="overview.products" description="平台当前沉淀的商品规模和可运营内容" />
      <StatPanel label="待处理" :value="overview.pending_audits" description="最先该被处理的待办，能直接反映治理压力" />
      <StatPanel label="订单总量" :value="overview.orders" description="交易闭环规模，用来判断活跃度和演示数据完整性" />
      <StatPanel label="举报总量" :value="overview.reports" description="治理域处理负载，也是后台时间线的主要来源" />
    </section>

    <section class="grid grid-2">
      <div ref="orderChartRef" class="panel chart-card"></div>
      <div ref="auditChartRef" class="panel chart-card"></div>
    </section>

    <section class="grid grid-2">
      <div class="panel" style="padding: 22px;">
        <div class="section-header">
          <div>
            <div class="eyebrow">待办队列</div>
            <h3 class="section-title">待处理商品</h3>
            <p class="section-meta">按队列顺序进入商品详情，减少运营切换成本。</p>
          </div>
          <RouterLink to="/admin/audits">
            <el-button plain>全部待办</el-button>
          </RouterLink>
        </div>
        <el-table :data="auditTasks.slice(0, 5)">
          <el-table-column prop="id" label="任务 ID" width="90" />
          <el-table-column prop="task_type" label="类型" width="150" />
          <el-table-column label="对象">
            <template #default="{ row }">
              {{ row.payload?.title || `${row.entity_type} / ${row.entity_id}` }}
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="120" />
          <el-table-column label="操作" width="140">
            <template #default="{ row }">
              <RouterLink v-if="row.entity_type === 'PRODUCT'" :to="`/admin/products/${row.entity_id}?from=audits`">
                <el-button plain size="small">处理</el-button>
              </RouterLink>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div class="panel" style="padding: 22px;">
        <div class="section-header">
          <div>
            <div class="eyebrow">系统动作</div>
            <h3 class="section-title">运营工具</h3>
            <p class="section-meta">推荐刷新、索引重建和平台诊断统一放在这里。</p>
          </div>
        </div>
        <div class="action-grid stacked">
          <el-button type="primary" @click="rebuildRecommendations">刷新推荐快照</el-button>
          <el-button @click="reindexSearch">重建搜索索引</el-button>
          <RouterLink to="/admin/platform">
            <el-button plain>查看平台运维</el-button>
          </RouterLink>
        </div>
      </div>
    </section>

    <section class="panel" style="padding: 22px;">
      <div class="section-header">
        <div>
          <div class="eyebrow">操作记录</div>
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
  const result = await adminApi.rebuildRecommendations()
  ElMessage.success(result.status === 'queued' ? `推荐任务已入队，作业 #${result.job_id}` : `推荐任务已完成，作业 #${result.job_id}`)
  await loadDashboard()
}

async function reindexSearch() {
  const result = await adminApi.reindexSearch()
  ElMessage.success(result.status === 'queued' ? `搜索重建已入队，作业 #${result.job_id}` : `搜索重建已完成，作业 #${result.job_id}`)
  await loadDashboard()
}

onMounted(loadDashboard)
</script>

<style scoped>
.overview-bar {
  padding: 20px 22px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.chart-card {
  min-height: 320px;
  padding: 16px;
}

.action-grid {
  display: grid;
  gap: 12px;
  grid-auto-flow: column;
}

.stacked {
  grid-auto-flow: row;
}

@media (max-width: 720px) {
  .overview-bar {
    align-items: flex-start;
  }

  .action-grid {
    grid-auto-flow: row;
  }
}
</style>
