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
        <strong>{{ product.stock || 1 }} 件</strong>
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
  gap: 14px;
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
  min-height: 30px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 0.74rem;
  font-weight: 800;
  border: 1px solid var(--line);
}

.category-pill {
  background: var(--surface-muted);
  color: var(--muted-strong);
}

.status-pill {
  background: var(--surface);
}

.product-code {
  color: var(--muted);
  background: var(--surface-soft);
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
  font-size: clamp(1.7rem, 2.4vw, 2.5rem);
  font-weight: 700;
  line-height: 1.12;
  letter-spacing: -0.04em;
  text-wrap: balance;
}

.hero-summary {
  margin: 0;
  max-width: 46ch;
  color: var(--muted-strong);
  font-size: 0.95rem;
  line-height: 1.75;
}

.fact-row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.fact-item {
  min-width: 132px;
  padding: 12px 14px;
  border-radius: 12px;
  background: var(--surface-soft);
  box-shadow: inset 0 0 0 1px var(--line);
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
