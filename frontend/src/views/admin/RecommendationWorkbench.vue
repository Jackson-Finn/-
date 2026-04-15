<template>
  <div class="grid">
    <section class="grid grid-4">
      <StatPanel label="素材总量" :value="summary.materials" description="浏览、收藏、下单、评价行为沉淀" />
      <StatPanel label="快照总量" :value="summary.snapshots" description="按场景输出的推荐结果快照" />
      <StatPanel label="推荐任务" :value="summary.jobs" description="重建、重算与索引相关作业" />
      <StatPanel label="AI 日志" :value="summary.ai_tasks" description="推荐增强和摘要等智能任务" />
    </section>

    <section class="grid grid-2">
      <div ref="materialChartRef" class="panel chart-card"></div>
      <div ref="sceneChartRef" class="panel chart-card"></div>
    </section>

    <section class="grid grid-2">
      <div class="panel" style="padding: 22px;">
        <div class="section-header">
          <div>
            <h2 class="section-title">运维动作</h2>
            <p class="section-meta">重建推荐和搜索索引，观察推荐系统状态变化</p>
          </div>
        </div>
        <el-space wrap>
          <el-button type="primary" @click="triggerRebuild">刷新推荐快照</el-button>
          <el-button @click="triggerReindex">重建搜索索引</el-button>
          <el-button @click="loadWorkbench">刷新工作台</el-button>
        </el-space>
      </div>

      <div class="panel" style="padding: 22px;">
        <div class="section-header">
          <div>
            <h2 class="section-title">最近作业</h2>
            <p class="section-meta">推荐刷新和搜索重建的执行留痕</p>
          </div>
        </div>
        <el-timeline>
          <el-timeline-item
            v-for="job in jobs.slice(0, 6)"
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

    <section class="grid grid-2">
      <section class="panel" style="padding: 22px;">
        <div class="section-header">
          <div>
            <h2 class="section-title">行为素材流</h2>
            <p class="section-meta">展示推荐命中的输入依据</p>
          </div>
        </div>

        <el-table :data="materials" max-height="420">
          <el-table-column prop="material_type" label="类型" width="110" />
          <el-table-column prop="user_name" label="用户" width="140" />
          <el-table-column prop="product_title" label="商品" min-width="220" show-overflow-tooltip />
          <el-table-column prop="created_at" label="时间" width="180" />
          <el-table-column label="详情" min-width="180">
            <template #default="{ row }">
              <span>{{ JSON.stringify(row.payload) }}</span>
            </template>
          </el-table-column>
        </el-table>
      </section>

      <section class="panel" style="padding: 22px;">
        <div class="section-header">
          <div>
            <h2 class="section-title">快照解释</h2>
            <p class="section-meta">展示推荐场景、用户和命中原因</p>
          </div>
        </div>

        <div v-for="snapshot in snapshots" :key="snapshot.id" class="snapshot-card">
          <div class="snapshot-head">
            <div>
              <strong>{{ snapshot.scene }}</strong>
              <div class="muted">{{ snapshot.user_name }} · {{ snapshot.item_count }} 个推荐结果</div>
            </div>
            <el-tag size="small" effect="plain">{{ snapshot.updated_at }}</el-tag>
          </div>
          <el-empty v-if="!snapshot.items.length" description="暂无快照内容" />
          <ul v-else class="snapshot-items">
            <li v-for="item in snapshot.items" :key="`${snapshot.id}-${item.product_id}`">
              <strong>{{ item.title }}</strong>
              <span class="muted">因为：{{ item.reason }}</span>
            </li>
          </ul>
        </div>
      </section>
    </section>

    <section class="panel" style="padding: 22px;">
      <div class="section-header">
        <div>
          <h2 class="section-title">AI 任务日志</h2>
          <p class="section-meta">推荐增强、聊天摘要和文案生成等智能任务留痕</p>
        </div>
      </div>
      <el-table :data="aiTasks" max-height="360">
        <el-table-column prop="task_name" label="任务" width="180" />
        <el-table-column prop="status" label="状态" width="120" />
        <el-table-column prop="prompt" label="输入" min-width="220" show-overflow-tooltip />
        <el-table-column label="输出" min-width="260">
          <template #default="{ row }">
            <span>{{ JSON.stringify(row.result) }}</span>
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

const summary = ref({ materials: 0, snapshots: 0, jobs: 0, ai_tasks: 0 })
const materials = ref([])
const snapshots = ref([])
const jobs = ref([])
const aiTasks = ref([])
const charts = ref({ materialTypes: [], snapshotScenes: [] })

const materialChartRef = ref(null)
const sceneChartRef = ref(null)

function renderCharts() {
  const materialChart = echarts.init(materialChartRef.value)
  const sceneChart = echarts.init(sceneChartRef.value)

  materialChart.setOption({
    title: { text: '推荐素材类型分布' },
    tooltip: {},
    series: [{ type: 'pie', radius: ['35%', '70%'], data: charts.value.materialTypes || [] }]
  })

  sceneChart.setOption({
    title: { text: '推荐场景快照分布' },
    tooltip: {},
    xAxis: { type: 'category', data: (charts.value.snapshotScenes || []).map((item) => item.name) },
    yAxis: { type: 'value' },
    series: [
      {
        type: 'bar',
        data: (charts.value.snapshotScenes || []).map((item) => item.value),
        itemStyle: { color: '#8c5e34' }
      }
    ]
  })
}

async function loadWorkbench() {
  const payload = await adminApi.recommendationWorkbench()
  summary.value = payload.summary
  charts.value = payload.charts
  materials.value = payload.materials
  snapshots.value = payload.snapshots
  jobs.value = payload.jobs
  aiTasks.value = payload.aiTasks
  await nextTick()
  renderCharts()
}

async function triggerRebuild() {
  const result = await adminApi.rebuildRecommendations()
  ElMessage.success(result.status === 'queued' ? `推荐快照重建已入队，作业 #${result.job_id}` : `推荐快照重建已完成，作业 #${result.job_id}`)
  await loadWorkbench()
}

async function triggerReindex() {
  const result = await adminApi.reindexSearch()
  ElMessage.success(result.status === 'queued' ? `搜索索引重建已入队，作业 #${result.job_id}` : `搜索索引重建已完成，作业 #${result.job_id}`)
  await loadWorkbench()
}

onMounted(loadWorkbench)
</script>

<style scoped>
.chart-card {
  min-height: 320px;
  padding: 16px;
}

.snapshot-card {
  padding: 16px 0;
  border-top: 1px solid rgba(36, 92, 90, 0.12);
}

.snapshot-card:first-of-type {
  border-top: none;
  padding-top: 0;
}

.snapshot-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.snapshot-items {
  margin: 12px 0 0;
  padding-left: 18px;
  display: grid;
  gap: 8px;
}

.snapshot-items li {
  display: grid;
  gap: 4px;
}
</style>
