<template>
  <DataStateCard
    :state="state"
    title="我的收藏"
    description="收藏会进入推荐素材池"
    empty-title="还没有收藏商品"
    empty-description="你收藏的商品会在这里统一展示，方便后续继续对比和追踪。"
    error-title="收藏加载失败"
    :error-description="error"
    @retry="loadFavorites"
  >
    <div class="panel" style="padding: 22px;">
      <div class="section-header">
        <div>
          <h2 class="section-title">我的收藏</h2>
          <p class="section-meta">收藏会进入推荐素材池</p>
        </div>
        <el-space wrap>
          <el-tag effect="plain">{{ favorites.length }} 条收藏</el-tag>
          <el-button @click="loadFavorites">刷新</el-button>
        </el-space>
      </div>

      <el-table :data="favorites">
        <el-table-column prop="id" label="收藏 ID" />
        <el-table-column prop="product_id" label="商品 ID" />
        <el-table-column label="操作">
          <template #default="{ row }">
            <el-button type="danger" plain @click="removeFavorite(row.product_id)">取消收藏</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </DataStateCard>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import DataStateCard from '../../components/DataStateCard.vue'
import { tradeApi } from '../../api/trade'

const favorites = ref([])
const loading = ref(false)
const error = ref('')

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

async function removeFavorite(productId) {
  await ElMessageBox.confirm('确定取消收藏这件商品吗？', '取消收藏', {
    confirmButtonText: '取消收藏',
    cancelButtonText: '保留收藏',
    type: 'warning'
  })

  try {
    await tradeApi.removeFavorite(productId)
    ElMessage.success('已取消收藏')
    await loadFavorites()
  } catch (err) {
    ElMessage.error(err.message)
  }
}

onMounted(loadFavorites)

const state = computed(() => {
  if (loading.value) return 'loading'
  if (error.value) return 'error'
  if (!favorites.value.length) return 'empty'
  return 'ready'
})
</script>
