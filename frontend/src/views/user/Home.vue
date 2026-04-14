<template>
  <div class="grid">
    <section class="panel hero-card">
      <div class="section-header">
        <div>
          <div class="pill">Platform + Intelligence</div>
          <h2 class="section-title">一个页面演示搜索、推荐、交易与治理型能力</h2>
          <p class="section-meta">前台围绕“发现商品 -> 判断可信度 -> 互动议价 -> 完成交易”展开。</p>
        </div>
        <el-space wrap>
          <el-autocomplete
            v-model="keyword"
            :fetch-suggestions="querySuggestions"
            clearable
            placeholder="搜索商品、描述或关键词"
            @select="loadProducts"
            @keyup.enter="loadProducts"
          />
          <el-button type="primary" @click="loadProducts">搜索</el-button>
        </el-space>
      </div>

      <el-alert
        v-if="pageError"
        :title="pageError"
        type="warning"
        show-icon
        :closable="false"
        style="margin-bottom: 18px;"
      />

      <div class="grid grid-4">
        <StatPanel label="推荐商品" :value="recommendations.length" description="首页推荐结果" />
        <StatPanel label="最近浏览" :value="history.length" description="用户行为沉淀" />
        <StatPanel label="收藏数" :value="favorites.length" description="行为素材输入推荐" />
        <StatPanel label="消息状态" :value="uiStore.wsStatus" description="实时通知与会话状态" />
      </div>
    </section>

    <section class="grid grid-2">
      <DataStateCard
        :state="recommendationState"
        title="推荐流"
        description="基于行为与规则生成的首页内容"
        empty-title="暂无推荐内容"
        empty-description="系统还在整理你的行为素材，稍后再试或刷新推荐。"
        error-title="推荐加载失败"
        :error-description="recommendationError"
        @retry="loadRecommendations"
      >
        <div class="panel" style="padding: 22px;">
        <div class="section-header">
          <div>
            <h3 class="section-title">推荐流</h3>
            <p class="section-meta">基于行为与规则生成的首页内容</p>
          </div>
          <el-button plain @click="loadRecommendations">刷新推荐</el-button>
        </div>
        <div class="grid">
          <ProductCard v-for="item in recommendations" :key="item.product_id" :product="{ ...item, id: item.product_id }">
            <div class="pill">{{ item.reason }}</div>
          </ProductCard>
        </div>
        </div>
      </DataStateCard>

      <div class="panel" style="padding: 22px;">
        <div class="section-header">
          <div>
            <h3 class="section-title">AI 发布辅助</h3>
            <p class="section-meta">用关键词生成标题和描述，再进行风险预审</p>
          </div>
        </div>
        <el-form label-position="top">
          <el-form-item label="关键词">
            <el-input v-model="aiKeywords" placeholder="例如：switch、九成新、原装配件" />
          </el-form-item>
          <el-form-item label="类目">
            <el-input v-model="aiCategory" placeholder="数码" />
          </el-form-item>
          <el-space wrap>
            <el-button type="primary" @click="generateDraft">生成草稿</el-button>
            <el-button @click="previewModeration" :disabled="!aiDraft.title">风险预审</el-button>
          </el-space>
        </el-form>
        <el-divider />
        <pre class="code">{{ aiDraft }}</pre>
        <div v-if="moderation.risk_level" class="pill">风险等级 {{ moderation.risk_level }}</div>
      </div>
    </section>

    <DataStateCard
      :state="productState"
      title="商品大厅"
      description="搜索结果与最新商品同屏展示"
      empty-title="暂无商品"
      empty-description="试试更换关键词，或者稍后刷新查看最新商品。"
      error-title="商品加载失败"
      :error-description="productError"
      @retry="loadProducts"
    >
      <section class="panel" style="padding: 22px;">
        <div class="section-header">
          <div>
            <h3 class="section-title">商品大厅</h3>
            <p class="section-meta">搜索结果与最新商品同屏展示</p>
          </div>
          <el-tag effect="plain">{{ products.length }} 件商品</el-tag>
        </div>
        <div class="grid grid-3">
          <ProductCard v-for="product in products" :key="product.id" :product="product" />
        </div>
      </section>
    </DataStateCard>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import DataStateCard from '../../components/DataStateCard.vue'
import ProductCard from '../../components/ProductCard.vue'
import StatPanel from '../../components/StatPanel.vue'
import { productApi } from '../../api/products'
import { tradeApi } from '../../api/trade'
import { useUiStore } from '../../stores/ui'

const uiStore = useUiStore()
const keyword = ref('')
const aiKeywords = ref('switch, 九成新, 原装配件')
const aiCategory = ref('数码')
const aiDraft = ref({})
const moderation = ref({})
const products = ref([])
const recommendations = ref([])
const history = ref([])
const favorites = ref([])
const productLoading = ref(false)
const productError = ref('')
const recommendationLoading = ref(false)
const recommendationError = ref('')
const pageError = ref('')

async function loadProducts() {
  productLoading.value = true
  productError.value = ''
  try {
    products.value = await productApi.list(keyword.value ? { keyword: keyword.value } : {})
  } catch (error) {
    productError.value = error.message
    throw error
  } finally {
    productLoading.value = false
  }
}

async function loadRecommendations() {
  recommendationLoading.value = true
  recommendationError.value = ''
  try {
    const data = await tradeApi.recommendHome()
    recommendations.value = data.items || []
  } catch (error) {
    recommendationError.value = error.message
    recommendations.value = []
    throw error
  } finally {
    recommendationLoading.value = false
  }
}

async function loadBehaviorData() {
  try {
    history.value = await tradeApi.recentHistory()
    favorites.value = await tradeApi.listFavorites()
  } catch {
    history.value = []
    favorites.value = []
  }
}

async function loadPage() {
  pageError.value = ''
  const results = await Promise.allSettled([loadProducts(), loadRecommendations(), loadBehaviorData()])
  const failed = results.filter((item) => item.status === 'rejected').map((item) => item.reason?.message).filter(Boolean)
  pageError.value = failed.join('；')
}

async function querySuggestions(queryString, cb) {
  try {
    const data = await productApi.suggest(queryString ? { keyword: queryString } : {})
    cb((data.suggestions || []).map((value) => ({ value })))
  } catch {
    cb([])
  }
}

async function generateDraft() {
  const result = await productApi.aiDraft({
    keywords: aiKeywords.value.split(',').map((item) => item.trim()).filter(Boolean),
    category: aiCategory.value
  })
  aiDraft.value = result
  ElMessage.success('AI 草稿已生成')
}

async function previewModeration() {
  moderation.value = await productApi.aiModeration({
    title: aiDraft.value.title || '',
    description: aiDraft.value.description || ''
  })
}

onMounted(async () => {
  await loadPage()
})

const productState = computed(() => {
  if (productLoading.value) return 'loading'
  if (productError.value) return 'error'
  if (!products.value.length) return 'empty'
  return 'ready'
})

const recommendationState = computed(() => {
  if (recommendationLoading.value) return 'loading'
  if (recommendationError.value) return 'error'
  if (!recommendations.value.length) return 'empty'
  return 'ready'
})
</script>

<style scoped>
.code {
  margin: 0;
  padding: 14px;
  border-radius: 16px;
  background: rgba(36, 92, 90, 0.08);
  overflow: auto;
}
</style>
