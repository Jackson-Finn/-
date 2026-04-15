<template>
  <section class="detail-section">
    <div class="section-header">
      <div>
        <h2 class="section-title">参数与商品说明</h2>
        <p class="section-meta">保留规整感，但不再做成后台字段表。</p>
      </div>
    </div>

    <div class="spec-list">
      <article v-for="item in items" :key="item.label" class="spec-row">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
      </article>
    </div>
  </section>
</template>

<script setup>
defineProps({
  items: { type: Array, default: () => [] }
})
</script>

<style scoped>
.detail-section {
  display: grid;
  gap: 18px;
}

.spec-list {
  display: grid;
  gap: 10px;
}

.spec-row {
  display: grid;
  grid-template-columns: 180px minmax(0, 1fr);
  gap: 16px;
  padding: 16px 0;
  border-bottom: 1px solid rgba(73, 57, 41, 0.08);
}

.spec-row:first-child {
  padding-top: 0;
}

.spec-row:last-child {
  border-bottom: 0;
  padding-bottom: 0;
}

.spec-row span {
  color: var(--muted);
  font-size: 0.82rem;
  font-weight: 800;
}

.spec-row strong {
  font-size: 0.98rem;
  line-height: 1.72;
}

@media (max-width: 760px) {
  .spec-row {
    grid-template-columns: 1fr;
    gap: 6px;
  }
}
</style>
