<template>
  <section class="header-block">
    <div class="topline">
      <span class="category-pill">{{ category }}</span>
      <span class="status-pill" :class="`tone-${status.tone}`">{{ status.label }}</span>
      <span class="product-code">编号 {{ productCode }}</span>
    </div>

    <h1 class="product-title">{{ product.title }}</h1>
    <p class="hero-summary">{{ product.hero_summary || subtitle }}</p>

    <div class="fact-row">
      <div class="fact-item">
        <span>发布时间</span>
        <strong>{{ publishedAt }}</strong>
      </div>
      <div class="fact-item">
        <span>成色</span>
        <strong>{{ product.condition_label || '待确认' }}</strong>
      </div>
      <div class="fact-item">
        <span>库存</span>
        <strong>{{ (product.stock ?? 0) }} 件</strong>
      </div>
    </div>
  </section>
</template>

<script setup>
defineProps({
  product: { type: Object, required: true },
  status: { type: Object, required: true },
  category: { type: String, default: '' },
  productCode: { type: String, required: true },
  subtitle: { type: String, default: '' },
  publishedAt: { type: String, default: '' }
})
</script>

<style scoped>
.header-block {
  display: grid;
  gap: 16px;
}

.topline {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.category-pill,
.status-pill,
.product-code {
  display: inline-flex;
  align-items: center;
  min-height: 34px;
  padding: 0 12px;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 800;
}

.category-pill {
  background: var(--surface-muted);
  color: var(--muted-strong);
}

.status-pill {
  background: rgba(255, 252, 247, 0.94);
}

.product-code {
  color: var(--muted);
  background: rgba(255, 252, 247, 0.56);
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

.product-title {
  margin: 0;
  font-size: clamp(2rem, 2.8vw, 3rem);
  font-weight: 700;
  line-height: 1.08;
  letter-spacing: -0.05em;
  text-wrap: balance;
}

.hero-summary {
  margin: 0;
  max-width: 46ch;
  color: var(--muted-strong);
  font-size: 1rem;
  line-height: 1.82;
}

.fact-row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.fact-item {
  min-width: 132px;
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 252, 247, 0.66);
  box-shadow: inset 0 0 0 1px rgba(73, 57, 41, 0.06);
  display: grid;
  gap: 5px;
}

.fact-item span {
  color: var(--muted);
  font-size: 0.78rem;
  font-weight: 800;
}

.fact-item strong {
  font-size: 0.98rem;
  line-height: 1.4;
}
</style>
