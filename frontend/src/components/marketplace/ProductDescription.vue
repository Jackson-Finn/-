<template>
  <section class="detail-section">
    <div class="section-header">
      <div>
        <h2 class="section-title">商品完整描述</h2>
        <p class="section-meta">卖家的使用场景、配件说明和交易备注会集中展示在这里。</p>
      </div>
    </div>

    <div class="lead-panel">
      <p>{{ description }}</p>
    </div>

    <div class="section-grid">
      <article v-for="section in sections" :key="section.title" class="story-block">
        <h3>{{ section.title }}</h3>
        <p>{{ section.body }}</p>
      </article>
    </div>
  </section>
</template>

<script setup>
defineProps({
  description: { type: String, default: '' },
  sections: { type: Array, default: () => [] }
})
</script>

<style scoped>
.detail-section {
  display: grid;
  gap: 18px;
}

.lead-panel {
  padding: 22px 24px;
  border-radius: 24px;
  background: rgba(255, 252, 247, 0.78);
  box-shadow: inset 0 0 0 1px rgba(73, 57, 41, 0.06);
}

.lead-panel p {
  margin: 0;
  font-size: 1rem;
  line-height: 1.95;
}

.section-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.story-block {
  padding: 22px;
  border-radius: 24px;
  background: rgba(73, 57, 41, 0.04);
}

.story-block h3 {
  margin: 0 0 8px;
  font-size: 1rem;
}

.story-block p {
  margin: 0;
  color: var(--muted-strong);
  line-height: 1.82;
}

@media (max-width: 960px) {
  .section-grid {
    grid-template-columns: 1fr;
  }
}
</style>
