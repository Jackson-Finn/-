<template>
  <DataStateCard
    :state="state"
    title="我的收藏"
    description="收藏会进入推荐素材池"
    empty-title="还没有收藏商品"
    empty-description="当前账号还没有收藏记录。先去商品详情点一次收藏，或切换到有演示数据的买家账号查看。"
    error-title="收藏加载失败"
    :error-description="error"
    @retry="loadFavorites"
  >
    <section class="panel favorites-panel">
      <div class="section-header">
        <div>
          <h2 class="section-title">我的收藏</h2>
          <p class="section-meta">直接看商品名、卖家和价格，再点进详情继续判断。</p>
        </div>
        <el-space wrap>
          <el-tag effect="plain">{{ visibleFavorites.length }} 条收藏</el-tag>
          <el-button @click="loadFavorites">刷新</el-button>
        </el-space>
      </div>

      <div class="catalog-grid">
        <ProductCard
          v-for="item in visibleFavorites"
          :key="item.id"
          :product="item.product_summary"
        >
          <el-button type="danger" plain @click.prevent="removeFavorite(item.product_id)">取消收藏</el-button>
        </ProductCard>
      </div>
    </section>

    <ConfirmDialog
      v-model="confirmDialog.visible"
      :title="confirmDialog.title"
      :description="confirmDialog.description"
      :loading="confirmDialog.loading"
      @confirm="confirmDialog.onConfirm"
    />
  </DataStateCard>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import ConfirmDialog from '../../components/common/ConfirmDialog.vue'
import DataStateCard from '../../components/DataStateCard.vue'
import ProductCard from '../../components/ProductCard.vue'
import { tradeApi } from '../../api/trade'

const favorites = ref([])
const loading = ref(false)
const error = ref('')
const visibleFavorites = computed(() => favorites.value.filter((item) => item?.product_summary?.id))

const confirmDialog = ref({
  visible: false,
  title: '取消收藏',
  description: '',
  loading: false,
  onConfirm: null
})

async function loadFavorites() {
  loading.value = true
  error.value = ''
  try {
    favorites.value = await tradeApi.listFavorites()
  } catch (err) {
    error.value = err.message
    favorites.value = []
  } finally {
    loading.value = false
  }
}

function removeFavorite(productId) {
  confirmDialog.value = {
    visible: true,
    title: '取消收藏',
    description: '确定取消收藏这件商品吗？',
    loading: false,
    onConfirm: async () => {
      confirmDialog.value.loading = true
      try {
        await tradeApi.removeFavorite(productId)
        confirmDialog.value.visible = false
        ElMessage.success('已取消收藏')
        await loadFavorites()
      } catch (err) {
        ElMessage.error(err.message)
      } finally {
        confirmDialog.value.loading = false
      }
    }
  }
}

onMounted(loadFavorites)

const state = computed(() => {
  if (loading.value) return 'loading'
  if (error.value) return 'error'
  if (!visibleFavorites.value.length) return 'empty'
  return 'ready'
})
</script>

<style scoped>
.favorites-panel {
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
