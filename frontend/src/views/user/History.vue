<template>
  <DataStateCard
    :state="state"
    title="最近浏览加载失败"
    description="暂时无法获取你的浏览记录。"
    empty-title="还没有浏览记录"
    empty-description="当前账号还没有浏览记录。先去商品详情看看商品，或切换到有演示数据的买家账号查看。"
    :error-description="error"
    @retry="loadHistory"
  >
    <section class="panel history-panel">
      <div class="section-header">
        <div>
          <h2 class="section-title">最近浏览</h2>
          <p class="section-meta">同一商品只保留最近一次浏览，最多保留最近 50 条。</p>
        </div>
        <el-space wrap>
          <el-tag effect="plain">{{ visibleItems.length }} 条记录</el-tag>
          <el-button @click="loadHistory">刷新</el-button>
        </el-space>
      </div>

      <div class="catalog-grid">
        <ProductCard
          v-for="item in visibleItems"
          :key="item.id"
          :product="item.product_summary"
        >
          <span class="pill">浏览于 {{ formatDateTime(item.created_at) }}</span>
        </ProductCard>
      </div>
    </section>
  </DataStateCard>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'

import DataStateCard from '../../components/DataStateCard.vue'
import ProductCard from '../../components/ProductCard.vue'
import { tradeApi } from '../../api/trade'
import { formatDateTime } from '../../utils/marketplace'

const items = ref([])
const loading = ref(false)
const error = ref('')
const visibleItems = computed(() => items.value.filter((item) => item?.product_summary?.id))

async function loadHistory() {
  loading.value = true
  error.value = ''
  try {
    items.value = await tradeApi.recentHistory()
  } catch (requestError) {
    error.value = requestError.message
    items.value = []
  } finally {
    loading.value = false
  }
}

onMounted(loadHistory)

const state = computed(() => {
  if (loading.value) return 'loading'
  if (error.value) return 'error'
  if (!visibleItems.value.length) return 'empty'
  return 'ready'
})
</script>

<style scoped>
.history-panel {
  padding: 22px;
}

.catalog-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

@media (max-width: 1080px) {
  .catalog-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .catalog-grid {
    grid-template-columns: 1fr;
  }
}
</style>
