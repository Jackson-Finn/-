<template>
  <section class="detail-section">
    <div class="section-header">
      <div>
        <h2 class="section-title">参数、交易方式与平台保障</h2>
        <p class="section-meta">把规格、交付方式和平台提醒整理成同一组词条，减少重复阅读。</p>
      </div>
    </div>

    <div class="fact-grid">
      <article v-for="item in items" :key="`${item.label}-${item.value}`" class="fact-card" :class="{ muted: item.tone === 'muted' }">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <p v-if="item.note">{{ item.note }}</p>
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

.fact-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.fact-card {
  padding: 18px;
  border-radius: 22px;
  background: rgba(73, 57, 41, 0.04);
}

.fact-card span {
  display: block;
  color: var(--muted);
  font-size: 0.8rem;
  font-weight: 800;
}

.fact-card strong {
  display: block;
  margin-top: 8px;
  font-size: 1rem;
  line-height: 1.55;
}

.fact-card p {
  margin: 8px 0 0;
  color: var(--muted);
  line-height: 1.65;
}

.fact-card.muted {
  background: rgba(49, 95, 84, 0.06);
}

@media (max-width: 960px) {
  .fact-grid {
    grid-template-columns: 1fr;
  }
}
</style>
