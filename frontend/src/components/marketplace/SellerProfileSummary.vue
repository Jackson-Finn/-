<template>
  <section class="panel seller-summary">
    <div class="summary-head">
      <img v-if="seller.avatar_url" class="avatar-image" :src="seller.avatar_url" :alt="seller.display_name">
      <div v-else class="avatar">{{ avatarText }}</div>
      <div class="copy">
        <div class="eyebrow">Seller Profile</div>
        <h1>{{ seller.display_name }}</h1>
        <p>{{ seller.headline || seller.bio }}</p>
      </div>
      <div class="score-card">
        <span>信任分</span>
        <strong>{{ seller.trust_score }}</strong>
      </div>
    </div>

    <div class="badge-row">
      <span v-for="badge in seller.verification_badges" :key="badge" class="badge">{{ badge }}</span>
    </div>

    <div class="metric-grid">
      <article v-for="item in metrics" :key="item.label" class="metric">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
      </article>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'

import { sellerMetricItems } from '../../utils/marketplace'

const props = defineProps({
  seller: { type: Object, required: true }
})

const avatarText = computed(() => (props.seller.display_name || '卖家').slice(0, 1))
const metrics = computed(() => sellerMetricItems(props.seller))
</script>

<style scoped>
.seller-summary {
  padding: 24px;
  display: grid;
  gap: 18px;
}

.summary-head {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 18px;
  align-items: start;
}

.eyebrow {
  margin-bottom: 0;
}

.avatar {
  width: 72px;
  height: 72px;
  border-radius: 22px;
  display: grid;
  place-items: center;
  color: white;
  background: linear-gradient(180deg, #2f66f3 0%, #2556d8 100%);
  font-size: 1.6rem;
  font-weight: 700;
}

.avatar-image {
  width: 72px;
  height: 72px;
  border-radius: 22px;
  object-fit: cover;
  background: var(--surface-muted);
}

.copy h1 {
  margin: 0 0 8px;
  font-size: clamp(2rem, 3vw, 2.6rem);
  letter-spacing: -0.05em;
}

.copy p {
  margin: 0;
  color: var(--muted);
  max-width: 54ch;
  line-height: 1.75;
}

.score-card {
  min-width: 124px;
  padding: 16px;
  border-radius: 18px;
  background: rgba(49, 95, 84, 0.08);
  border: 1px solid var(--line);
  display: grid;
  gap: 6px;
}

.score-card span {
  color: var(--muted);
  font-size: 0.8rem;
  font-weight: 700;
}

.score-card strong {
  font-size: 2rem;
  line-height: 1;
  letter-spacing: -0.04em;
}

.badge-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.badge {
  padding: 7px 11px;
  border-radius: 999px;
  background: var(--trust-soft);
  color: var(--trust);
  font-size: 0.8rem;
  font-weight: 700;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.metric {
  padding: 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid var(--line);
  display: grid;
  gap: 6px;
}

.metric span {
  color: var(--muted);
  font-size: 0.8rem;
  font-weight: 700;
}

.metric strong {
  font-size: 1.1rem;
}

@media (max-width: 960px) {
  .summary-head {
    grid-template-columns: 1fr;
  }

  .metric-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
