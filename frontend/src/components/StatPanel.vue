<template>
  <div class="stat panel">
    <div class="pill">{{ label }}</div>
    <div class="value">{{ value }}</div>
    <div class="muted">{{ description }}</div>
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
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.value {
  font-size: 2rem;
  font-weight: 800;
}
</style>

