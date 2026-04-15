<template>
  <span class="status-badge" :class="`tone-${tone}`">{{ label }}</span>
</template>

<script setup>
const props = defineProps({
  label: { type: String, required: true },
  tone: { type: String, default: 'muted' }
})
</script>

<style scoped>
.status-badge {
  display: inline-flex;
  align-items: center;
  padding: 7px 12px;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 700;
  border: 1px solid transparent;
}

.tone-success {
  background: #e7f8ef;
  color: #166534;
  border-color: rgba(22, 101, 52, 0.12);
}

.tone-warning {
  background: #fff4df;
  color: #b45309;
  border-color: rgba(180, 83, 9, 0.14);
}

.tone-danger {
  background: #fdebec;
  color: #b42318;
  border-color: rgba(180, 35, 24, 0.14);
}

.tone-info {
  background: #edf4ff;
  color: #2556d8;
  border-color: rgba(37, 86, 216, 0.12);
}

.tone-muted {
  background: #f4f7fb;
  color: var(--muted);
  border-color: var(--line);
}
</style>
