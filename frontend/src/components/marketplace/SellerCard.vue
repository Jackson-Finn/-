<template>
  <section class="seller-card">
    <div class="seller-head">
      <img v-if="seller.avatar_url" :src="seller.avatar_url" :alt="seller.display_name" class="seller-avatar">
      <div class="seller-copy">
        <p class="seller-label">卖家摘要</p>
        <h3>{{ seller.display_name }}</h3>
        <p class="headline">{{ seller.headline }}</p>
      </div>
    </div>

    <p class="seller-bio">{{ seller.bio }}</p>

    <div class="badge-row">
      <span v-for="badge in seller.verification_badges" :key="badge" class="badge">{{ badge }}</span>
    </div>

    <div class="metric-grid">
      <article v-for="item in metrics" :key="item.label" class="metric-card">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
      </article>
    </div>

    <div class="trust-list">
      <article v-for="item in seller.trust_highlights || []" :key="item.title" class="trust-item">
        <strong>{{ item.title }}</strong>
        <p>{{ item.detail }}</p>
      </article>
    </div>

    <div class="seller-meta">
      <span>注册于 {{ formatDateTime(seller.created_at) }}</span>
      <span>{{ seller.response_summary }}</span>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'

import { formatDateTime, sellerMetricItems } from '../../utils/marketplace'

const props = defineProps({
  seller: { type: Object, required: true }
})

const metrics = computed(() => sellerMetricItems(props.seller))
</script>

<style scoped>
.seller-card {
  display: grid;
  gap: 18px;
  padding: 20px;
  border-radius: 16px;
  background: var(--surface);
  border: 1px solid var(--line);
}

.seller-head {
  display: flex;
  gap: 14px;
  align-items: center;
}

.seller-avatar {
  width: 72px;
  height: 72px;
  border-radius: 12px;
  object-fit: cover;
  flex-shrink: 0;
  background: var(--surface-muted);
}

.seller-copy {
  display: grid;
  gap: 6px;
}

.seller-label {
  margin: 0;
  color: var(--muted);
  font-size: 0.76rem;
  font-weight: 800;
  letter-spacing: 0.04em;
  text-transform: none;
}

.seller-copy h3 {
  margin: 0;
  font-size: 1.18rem;
  line-height: 1.2;
}

.headline,
.seller-bio {
  margin: 0;
  color: var(--muted-strong);
  line-height: 1.75;
}

.badge-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.badge {
  display: inline-flex;
  align-items: center;
  padding: 7px 11px;
  border-radius: 999px;
  background: var(--surface-soft);
  color: var(--muted-strong);
  font-size: 0.78rem;
  font-weight: 800;
  border: 1px solid var(--line);
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.metric-card {
  display: grid;
  gap: 6px;
  padding: 14px 16px;
  border-radius: 12px;
  background: var(--surface-soft);
  border: 1px solid var(--line);
}

.metric-card span {
  color: var(--muted);
  font-size: 0.78rem;
  font-weight: 800;
}

.metric-card strong {
  font-size: 1rem;
}

.trust-list {
  display: grid;
  gap: 10px;
}

.trust-item {
  padding: 14px 16px;
  border-radius: 12px;
  background: var(--surface-soft);
  border: 1px solid var(--line);
}

.trust-item strong {
  display: block;
  margin-bottom: 6px;
}

.trust-item p {
  margin: 0;
  color: var(--muted);
  line-height: 1.7;
}

.seller-meta {
  display: grid;
  gap: 4px;
  color: var(--muted);
  font-size: 0.84rem;
}

@media (max-width: 640px) {
  .metric-grid {
    grid-template-columns: 1fr;
  }
}
</style>
