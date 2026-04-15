<template>
  <section class="related-section">
    <div class="section-header">
      <div>
        <p class="collection-label">{{ eyebrow }}</p>
        <h2 class="section-title">{{ title }}</h2>
        <p class="section-meta">{{ description }}</p>
      </div>
    </div>

    <DataStateCard
      :state="state"
      :title="title"
      :description="description"
      :empty-title="emptyTitle"
      :empty-description="emptyDescription"
      :error-title="errorTitle"
      :error-description="errorDescription"
      @retry="$emit('retry')"
    >
      <div class="related-grid" :class="{ featured: emphasize }">
        <ProductCard
          v-for="item in items"
          :key="item.id || item.product_id"
          :product="{ ...item, id: item.id || item.product_id }"
        >
          <span v-if="item.reason" class="reason-pill">{{ item.reason }}</span>
        </ProductCard>
      </div>
    </DataStateCard>
  </section>
</template>

<script setup>
import DataStateCard from '../DataStateCard.vue'
import ProductCard from '../ProductCard.vue'

defineProps({
  eyebrow: { type: String, default: '更多商品' },
  title: { type: String, default: '' },
  description: { type: String, default: '' },
  items: { type: Array, default: () => [] },
  state: { type: String, default: 'ready' },
  emptyTitle: { type: String, default: '' },
  emptyDescription: { type: String, default: '' },
  errorTitle: { type: String, default: '' },
  errorDescription: { type: String, default: '' },
  emphasize: { type: Boolean, default: false }
})

defineEmits(['retry'])
</script>

<style scoped>
.related-section {
  display: grid;
  gap: 16px;
}

.collection-label {
  margin: 0 0 8px;
  color: var(--muted);
  font-size: 0.74rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.related-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.related-grid.featured :deep(.product-card) {
  background: rgba(255, 252, 247, 0.98);
}

.reason-pill {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  background: var(--accent-soft);
  color: var(--accent-strong);
  font-size: 0.74rem;
  font-weight: 800;
}

@media (max-width: 960px) {
  .related-grid {
    grid-template-columns: 1fr;
  }
}
</style>
