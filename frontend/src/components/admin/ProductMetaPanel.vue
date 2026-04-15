<template>
  <section class="panel meta-card">
    <div class="section-header">
      <div>
        <div class="eyebrow">{{ title }}</div>
        <h3 class="section-title">{{ headline }}</h3>
      </div>
    </div>

    <div class="meta-grid">
      <div v-for="item in items" :key="item.label" class="meta-item">
        <span>{{ item.label }}</span>
        <strong>{{ item.value || '--' }}</strong>
      </div>
    </div>

    <slot />
  </section>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    default: ''
  },
  headline: {
    type: String,
    default: ''
  },
  items: {
    type: Array,
    default: () => []
  }
})
</script>

<style scoped>
.meta-card {
  padding: 18px;
}

.meta-grid {
  display: grid;
  gap: 12px;
}

.meta-item {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 0;
  border-top: 1px solid var(--line);
}

.meta-item:first-child {
  border-top: 0;
  padding-top: 0;
}

.meta-item span {
  color: var(--muted);
  font-size: 0.84rem;
}

.meta-item strong {
  font-size: 0.88rem;
  text-align: right;
}
</style>
