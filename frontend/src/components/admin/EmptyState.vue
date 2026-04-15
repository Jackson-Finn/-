<template>
  <div class="panel state">
    <el-empty :description="description">
      <template #image>
        <div class="empty-mark">{{ title }}</div>
      </template>
      <slot />
    </el-empty>
  </div>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    default: 'EMPTY'
  },
  description: {
    type: String,
    default: '暂无数据'
  }
})
</script>

<style scoped>
.state {
  padding: 18px;
}

.empty-mark {
  color: rgba(15, 23, 42, 0.24);
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.14em;
}
</style>
