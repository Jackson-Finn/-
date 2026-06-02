<template>
  <article class="product-card">
    <RouterLink :to="`/products/${product.id}`" class="media-link">
      <div class="media-shell">
        <img v-if="product.cover_image" class="cover" :src="product.cover_image" :alt="product.title || '商品图片'">
        <div v-else class="image-placeholder">
          <span>{{ product.category_name || '精选闲置' }}</span>
          <strong>{{ initials }}</strong>
        </div>
        <div class="media-badges">
          <span class="status-pill" :class="`tone-${statusMeta.tone}`">{{ statusMeta.label }}</span>
          <span v-if="product.condition_label" class="soft-pill">{{ product.condition_label }}</span>
        </div>
      </div>
    </RouterLink>

    <div class="card-copy">
      <div class="meta-row">
        <span>{{ product.category_name || '商品' }}</span>
        <span class="meta-dot"></span>
        <span>{{ product.seller_name || '平台卖家' }}</span>
      </div>
      <RouterLink :to="`/products/${product.id}`" class="title-link">
        <h3>{{ product.title || '未命名商品' }}</h3>
      </RouterLink>
      <p class="summary">{{ product.hero_summary || product.description || '卖家暂未补充更多描述。' }}</p>
      <div class="footer-row">
        <div class="price-block">
          <strong>{{ formatPrice(product.price) }}</strong>
          <span v-if="product.updated_at">更新于 {{ formatShortDate(product.updated_at) }}</span>
        </div>
        <slot />
      </div>
    </div>
  </article>
</template>

<script setup>
import { computed } from 'vue'

import { formatPrice, formatShortDate, getStatusMeta } from '../utils/marketplace'

const props = defineProps({
  product: { type: Object, required: true }
})

const initials = computed(() => (props.product.title || 'M').slice(0, 1))
const statusMeta = computed(() => getStatusMeta(props.product))
</script>

<style scoped>
.product-card {
  display: grid;
  gap: 14px;
  overflow: hidden;
  padding: 12px;
  border-radius: 16px;
  background: var(--surface);
  border: 1px solid var(--line);
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.product-card:hover {
  transform: translateY(-2px);
  border-color: rgba(31, 59, 99, 0.18);
  box-shadow: var(--shadow-soft);
}

.media-link {
  display: block;
}

.media-shell {
  position: relative;
  aspect-ratio: 4 / 3;
  overflow: hidden;
  border-radius: 12px;
  background: var(--surface-muted);
}

.cover {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.image-placeholder {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  color: var(--muted-strong);
}

.image-placeholder span {
  position: absolute;
  left: 16px;
  top: 16px;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.image-placeholder strong {
  font-size: 2.8rem;
  color: rgba(33, 26, 20, 0.25);
}

.media-badges {
  position: absolute;
  left: 14px;
  right: 14px;
  bottom: 14px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.status-pill,
.soft-pill {
  display: inline-flex;
  align-items: center;
  padding: 5px 8px;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 800;
}

.status-pill {
  background: rgba(255, 255, 255, 0.92);
  color: var(--text);
  border: 1px solid var(--line);
}

.soft-pill {
  background: rgba(255, 255, 255, 0.86);
  color: var(--muted-strong);
  border: 1px solid var(--line);
}

.tone-positive {
  color: var(--trust);
}

.tone-warning {
  color: var(--warning);
}

.tone-danger {
  color: var(--danger);
}

.tone-muted {
  color: var(--muted-strong);
}

.card-copy {
  display: grid;
  gap: 10px;
  padding: 0 2px 2px;
}

.meta-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  color: var(--muted);
  font-size: 0.8rem;
  font-weight: 700;
}

.meta-dot {
  width: 4px;
  height: 4px;
  border-radius: 999px;
  background: rgba(73, 57, 41, 0.24);
}

.title-link h3 {
  margin: 0;
  font-size: 0.98rem;
  font-weight: 700;
  line-height: 1.45;
  letter-spacing: -0.02em;
}

.summary {
  margin: 0;
  color: var(--muted);
  font-size: 0.9rem;
  line-height: 1.65;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 3.4em;
}

.footer-row {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
}

.price-block {
  display: grid;
  gap: 4px;
}

.price-block strong {
  font-size: 1.08rem;
  line-height: 1;
  letter-spacing: -0.03em;
}

.price-block span {
  color: var(--muted);
  font-size: 0.8rem;
}
</style>
