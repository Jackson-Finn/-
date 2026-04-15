<template>
  <section class="detail-section">
    <div class="section-header">
      <div>
        <h2 class="section-title">交易方式与交付节奏</h2>
        <p class="section-meta">快速看懂是否支持邮寄、面交、自提，以及卖家的默认交易节奏。</p>
      </div>
    </div>

    <div class="delivery-grid">
      <article v-for="item in items" :key="item.label" class="delivery-card">
        <strong>{{ item.label }}</strong>
        <p class="delivery-value">{{ item.value }}</p>
        <p v-if="item.note" class="delivery-note">{{ item.note }}</p>
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

.delivery-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.delivery-card {
  padding: 18px;
  border-radius: 22px;
  background: rgba(49, 95, 84, 0.06);
}

.delivery-card strong {
  display: block;
  margin-bottom: 10px;
  font-size: 0.96rem;
}

.delivery-value {
  margin: 0;
  font-size: 0.96rem;
  line-height: 1.7;
}

.delivery-note {
  margin: 8px 0 0;
  color: var(--muted);
  font-size: 0.84rem;
  line-height: 1.65;
}

@media (max-width: 960px) {
  .delivery-grid {
    grid-template-columns: 1fr;
  }
}
</style>
