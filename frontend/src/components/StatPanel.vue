<template>
  <div class="stat">
    <div class="stat-label">{{ label }}</div>
    <div class="value">{{ value }}</div>
    <div class="muted summary">{{ description }}</div>
  </div>
</template>

<script setup>
defineProps({
  label: String,
  value: [String, Number],
  description: String
})
</script>

<style scoped>
.stat {
  min-height: 118px;
  padding: 18px;
  display: grid;
  gap: 8px;
  border: 1px solid var(--line);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.84);
}

.stat-label {
  color: var(--muted);
  font-size: 0.76rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.value {
  font-family: var(--font-ui);
  font-size: clamp(1.75rem, 3vw, 2.4rem);
  font-weight: 800;
  line-height: 1;
  letter-spacing: -0.04em;
}

.summary {
  max-width: 18ch;
  font-size: 0.84rem;
  line-height: 1.55;
}
</style>
