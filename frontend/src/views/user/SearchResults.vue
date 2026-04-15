<template>
  <div class="search-page">
    <section class="panel search-hero">
      <div>
        <div class="eyebrow">Search</div>
        <h2 class="section-title">搜索结果</h2>
        <p class="section-meta">支持关键词、类目、成色和价格区间筛选，方便更接近真实二手交易的决策方式。</p>
      </div>

      <div class="search-stack">
        <div class="search-bar">
          <el-autocomplete
            v-model="keyword"
            :fetch-suggestions="querySuggestions"
            clearable
            placeholder="搜索商品、场景或预算"
            @select="submitSearch"
            @keyup.enter="submitSearch"
          />
          <el-button type="primary" @click="submitSearch">搜索</el-button>
          <el-button plain :loading="assistLoading" @click="applyAssistant">AI 整理条件</el-button>
        </div>

        <div class="filter-grid">
          <el-input v-model="filters.category" placeholder="类目" />
          <el-input v-model="filters.condition" placeholder="成色" />
          <el-input-number v-model="filters.price_min" :min="0" placeholder="最低价" />
          <el-input-number v-model="filters.price_max" :min="0" placeholder="最高价" />
          <el-select v-model="filters.sort" placeholder="排序">
            <el-option label="最新发布" value="newest" />
            <el-option label="价格从低到高" value="price_asc" />
            <el-option label="价格从高到低" value="price_desc" />
            <el-option label="最近更新" value="updated_desc" />
          </el-select>
          <el-input v-model="filters.delivery_method" placeholder="交付方式" />
        </div>
      </div>
    </section>

    <DataStateCard
      :state="state"
      title="搜索结果加载失败"
      description="暂时无法获取搜索结果。"
      empty-title="没有匹配的商品"
      empty-description="可以试试放宽价格或成色条件，或者回首页看看推荐流。"
      :error-description="error"
      @retry="loadResults"
    >
      <section class="panel result-panel">
        <div class="section-header">
          <div>
            <h3 class="section-title">“{{ displayKeyword }}” 的结果</h3>
            <p class="section-meta">共找到 {{ total }} 件公开可见商品。</p>
          </div>
          <p v-if="searchBrief" class="assistant-brief">{{ searchBrief }}</p>
        </div>

        <div v-if="facets.categories.length || facets.conditions.length" class="facet-row">
          <span v-for="item in facets.categories" :key="`category-${item.label}`" class="facet-pill">
            {{ item.label }} {{ item.count }}
          </span>
          <span v-for="item in facets.conditions" :key="`condition-${item.label}`" class="facet-pill muted">
            {{ item.label }} {{ item.count }}
          </span>
        </div>

        <div class="catalog-grid">
          <ProductCard v-for="item in results" :key="item.id" :product="item" />
        </div>
      </section>
    </DataStateCard>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import DataStateCard from '../../components/DataStateCard.vue'
import ProductCard from '../../components/ProductCard.vue'
import { productApi } from '../../api/products'

const route = useRoute()
const router = useRouter()

const keyword = ref('')
const filters = reactive({
  category: '',
  condition: '',
  price_min: null,
  price_max: null,
  sort: 'newest',
  delivery_method: ''
})
const results = ref([])
const total = ref(0)
const facets = ref({ categories: [], conditions: [] })
const loading = ref(false)
const assistLoading = ref(false)
const error = ref('')
const searchBrief = ref('')

const routeQuery = computed(() => ({
  keyword: Array.isArray(route.query.keyword) ? route.query.keyword[0] : route.query.keyword || '',
  category: Array.isArray(route.query.category) ? route.query.category[0] : route.query.category || '',
  condition: Array.isArray(route.query.condition) ? route.query.condition[0] : route.query.condition || '',
  price_min: Array.isArray(route.query.price_min) ? route.query.price_min[0] : route.query.price_min || '',
  price_max: Array.isArray(route.query.price_max) ? route.query.price_max[0] : route.query.price_max || '',
  sort: Array.isArray(route.query.sort) ? route.query.sort[0] : route.query.sort || 'newest',
  delivery_method: Array.isArray(route.query.delivery_method) ? route.query.delivery_method[0] : route.query.delivery_method || ''
}))

const displayKeyword = computed(() => String(routeQuery.value.keyword || '全部商品'))

async function loadResults() {
  loading.value = true
  error.value = ''
  try {
    const payload = await productApi.search(normalizedQueryParams())
    results.value = payload.items || []
    total.value = payload.total || 0
    facets.value = payload.facets || { categories: [], conditions: [] }
  } catch (requestError) {
    error.value = requestError.message
    results.value = []
    total.value = 0
    facets.value = { categories: [], conditions: [] }
  } finally {
    loading.value = false
  }
}

function normalizedQueryParams() {
  return Object.fromEntries(
    Object.entries({
      keyword: routeQuery.value.keyword || '',
      category: routeQuery.value.category || '',
      condition: routeQuery.value.condition || '',
      price_min: routeQuery.value.price_min || '',
      price_max: routeQuery.value.price_max || '',
      sort: routeQuery.value.sort || 'newest',
      delivery_method: routeQuery.value.delivery_method || ''
    }).filter(([, value]) => value !== '' && value !== null && value !== undefined)
  )
}

async function querySuggestions(queryString, cb) {
  try {
    const data = await productApi.suggest(queryString ? { keyword: queryString } : {})
    cb((data.suggestions || []).map((value) => ({ value })))
  } catch {
    cb([])
  }
}

function submitSearch() {
  router.push({
    name: 'search',
    query: Object.fromEntries(
      Object.entries({
        keyword: keyword.value.trim(),
        category: filters.category.trim(),
        condition: filters.condition.trim(),
        price_min: filters.price_min,
        price_max: filters.price_max,
        sort: filters.sort,
        delivery_method: filters.delivery_method.trim()
      }).filter(([, value]) => value !== '' && value !== null && value !== undefined)
    )
  })
}

async function applyAssistant() {
  if (!keyword.value.trim()) {
    submitSearch()
    return
  }
  assistLoading.value = true
  try {
    const result = await productApi.aiSearchAssist({ query: keyword.value.trim() })
    searchBrief.value = result.search_brief || ''
    const structured = result.structured_filters || {}
    keyword.value = structured.keyword || keyword.value
    filters.category = structured.category || filters.category
    filters.condition = structured.condition || filters.condition
    filters.price_min = structured.price_min ?? filters.price_min
    filters.price_max = structured.price_max ?? filters.price_max
    filters.sort = structured.sort || filters.sort
    submitSearch()
  } finally {
    assistLoading.value = false
  }
}

watch(
  routeQuery,
  async (value) => {
    keyword.value = String(value.keyword || '')
    filters.category = String(value.category || '')
    filters.condition = String(value.condition || '')
    filters.price_min = value.price_min ? Number(value.price_min) : null
    filters.price_max = value.price_max ? Number(value.price_max) : null
    filters.sort = String(value.sort || 'newest')
    filters.delivery_method = String(value.delivery_method || '')
    await loadResults()
  },
  { immediate: true }
)

const state = computed(() => {
  if (loading.value) return 'loading'
  if (error.value) return 'error'
  if (!results.value.length) return 'empty'
  return 'ready'
})
</script>

<style scoped>
.search-page {
  display: grid;
  gap: 20px;
}

.search-hero,
.result-panel {
  padding: 22px;
}

.search-hero,
.search-stack {
  display: grid;
  gap: 16px;
}

.search-bar {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto;
  gap: 12px;
}

.filter-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.assistant-brief {
  margin: 0;
  max-width: 48ch;
  color: var(--muted);
  line-height: 1.7;
}

.facet-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
}

.facet-pill {
  padding: 6px 10px;
  border-radius: 999px;
  background: var(--brand-soft);
  color: var(--brand-strong);
  font-size: 0.78rem;
  font-weight: 700;
}

.facet-pill.muted {
  background: rgba(73, 57, 41, 0.06);
  color: var(--muted-strong);
}

.catalog-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

@media (max-width: 1080px) {
  .filter-grid,
  .catalog-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .search-bar,
  .filter-grid,
  .catalog-grid {
    grid-template-columns: 1fr;
  }
}
</style>
