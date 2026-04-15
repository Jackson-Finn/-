<template>
  <div class="state panel">
    <el-skeleton animated :rows="rows" />
  </div>
</template>

<script setup>
defineProps({
  rows: {
    type: Number,
    default: 5
  }
})
</script>

<style scoped>
.state {
  padding: 22px;
}
</style>
