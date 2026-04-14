<template>
  <div class="card panel">
    <div class="image">
      <div class="image-letter">{{ initials }}</div>
      <div class="image-badges">
        <span class="image-badge">{{ statusLabel }}</span>
        <span v-if="product.category_name" class="image-badge muted-badge">{{ product.category_name }}</span>
      </div>
    </div>
    <div class="content">
      <div class="section-header">
        <div>
          <h3 class="section-title">{{ product.title || '未命名商品' }}</h3>
          <p class="section-meta">{{ metaText }}</p>
        </div>
        <span class="pill">¥ {{ Number(product.price || 0).toFixed(2) }}</span>
      </div>
      <p class="muted summary">{{ product.description || '暂无描述，等待卖家补充更多细节。' }}</p>
      <div class="meta-row">
        <span v-if="product.stock !== undefined" class="meta-pill">库存 {{ product.stock }}</span>
        <span v-if="product.seller_name" class="meta-pill">卖家 {{ product.seller_name }}</span>
        <span v-if="product.updated_at" class="meta-pill">更新 {{ formatTime(product.updated_at) }}</span>
      </div>
      <div class="actions">
        <RouterLink :to="`/products/${product.id}`">
          <el-button type="primary">查看详情</el-button>
        </RouterLink>
        <slot />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  product: { type: Object, required: true }
})

const initials = computed(() => (props.product.title || 'M').slice(0, 1))

const statusLabel = computed(() => {
  const status = (props.product.audit_status || props.product.status || 'ACTIVE').toString()
  const mapping = {
    ACTIVE: '在售',
    PENDING: '待审',
    AUDITED: '已审',
    REJECTED: '驳回',
    OFF_SHELF: '下架'
  }
  return mapping[status] || status
})

const metaText = computed(() => {
  const status = props.product.audit_status || props.product.status || 'ACTIVE'
  const category = props.product.category_name ? ` · ${props.product.category_name}` : ''
  return `状态 ${status}${category}`
})

function formatTime(value) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
}
</script>

<style scoped>
.card {
  overflow: hidden;
}

.image {
  position: relative;
  height: 160px;
  display: grid;
  place-items: center;
  background:
    radial-gradient(circle at top left, rgba(255, 255, 255, 0.2), transparent 42%),
    linear-gradient(135deg, #b0582e, #245c5a);
  color: rgba(255, 255, 255, 0.9);
}

.image-letter {
  font-size: 3.2rem;
  font-weight: 800;
  line-height: 1;
}

.image-badges {
  position: absolute;
  right: 14px;
  bottom: 14px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.image-badge {
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.22);
  color: white;
  font-size: 0.8rem;
  backdrop-filter: blur(10px);
}

.muted-badge {
  background: rgba(255, 255, 255, 0.14);
}

.content {
  padding: 18px;
}

.summary {
  min-height: 48px;
}

.actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.meta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 14px 0 16px;
}

.meta-pill {
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(176, 88, 46, 0.08);
  color: var(--muted);
  font-size: 0.82rem;
}
</style>
