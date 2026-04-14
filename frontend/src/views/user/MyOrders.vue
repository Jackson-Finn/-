<template>
  <div class="grid grid-2">
    <DataStateCard
      :state="orderState"
      title="我的订单"
      description="确认收货后即可提交评价"
      empty-title="还没有订单"
      empty-description="去首页挑选一件商品，完成下单后会出现在这里。"
      error-title="订单加载失败"
      :error-description="error"
      @retry="loadOrders"
    >
      <section class="panel" style="padding: 22px;">
        <div class="section-header">
          <div>
            <h2 class="section-title">我的订单</h2>
            <p class="section-meta">确认收货后即可提交评价</p>
          </div>
          <el-space wrap>
            <el-tag effect="plain">{{ orders.length }} 笔订单</el-tag>
            <el-button type="primary" plain @click="loadOrders">刷新</el-button>
          </el-space>
        </div>

        <el-table :data="orders">
          <el-table-column prop="id" label="订单 ID" width="100" />
          <el-table-column prop="product_id" label="商品 ID" width="100" />
          <el-table-column prop="total_amount" label="金额" />
          <el-table-column prop="status" label="状态" />
          <el-table-column label="操作" width="260">
            <template #default="{ row }">
              <el-space>
                <el-button size="small" @click="confirmOrder(row.id)">确认收货</el-button>
                <el-button size="small" @click="cancelOrder(row.id)">取消</el-button>
                <el-button size="small" type="primary" plain @click="openReview(row)">评价</el-button>
              </el-space>
            </template>
          </el-table-column>
        </el-table>
      </section>
    </DataStateCard>

    <section class="panel" style="padding: 22px;">
      <div class="section-header">
        <div>
          <h2 class="section-title">提交评价</h2>
          <p class="section-meta">仅已完成订单允许评价</p>
        </div>
      </div>

      <el-form :model="reviewForm" label-position="top">
        <el-form-item label="订单 ID">
          <el-input v-model="reviewForm.order_id" disabled />
        </el-form-item>
        <el-form-item label="评分">
          <el-rate v-model="reviewForm.rating" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input v-model="reviewForm.content" type="textarea" :rows="4" />
        </el-form-item>
        <el-button type="primary" :disabled="!reviewForm.order_id" @click="submitReview">提交评价</el-button>
      </el-form>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import DataStateCard from '../../components/DataStateCard.vue'
import { tradeApi } from '../../api/trade'

const orders = ref([])
const loading = ref(false)
const error = ref('')
const reviewForm = reactive({
  order_id: '',
  rating: 5,
  content: ''
})

async function loadOrders() {
  loading.value = true
  error.value = ''
  try {
    orders.value = await tradeApi.listOrders()
  } catch (err) {
    error.value = err.message
    orders.value = []
  } finally {
    loading.value = false
  }
}

async function confirmOrder(id) {
  await ElMessageBox.confirm('确认收货后将允许评价，是否继续？', '确认收货', {
    confirmButtonText: '确认',
    cancelButtonText: '稍后再说',
    type: 'warning'
  })

  try {
    await tradeApi.confirmOrder(id)
    ElMessage.success('订单已确认完成')
    await loadOrders()
  } catch (err) {
    ElMessage.error(err.message)
  }
}

async function cancelOrder(id) {
  await ElMessageBox.confirm('取消订单后将终止交易流程，确定继续吗？', '取消订单', {
    confirmButtonText: '取消订单',
    cancelButtonText: '保留订单',
    type: 'warning'
  })

  try {
    await tradeApi.cancelOrder(id)
    ElMessage.success('订单已取消')
    await loadOrders()
  } catch (err) {
    ElMessage.error(err.message)
  }
}

function openReview(row) {
  reviewForm.order_id = row.id
}

async function submitReview() {
  try {
    await tradeApi.createReview(reviewForm)
    ElMessage.success('评价已提交')
    reviewForm.content = ''
  } catch (err) {
    ElMessage.error(err.message)
  }
}

onMounted(loadOrders)

const orderState = computed(() => {
  if (loading.value) return 'loading'
  if (error.value) return 'error'
  if (!orders.value.length) return 'empty'
  return 'ready'
})
</script>
