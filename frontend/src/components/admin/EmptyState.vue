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
    default: '暂无内容'
  },
  description: {
    type: String,
    default: '暂无数据'
  }
})
</script>

<style scoped>
.state {
  padding: 16px;
}

.empty-mark {
  color: rgba(19, 23, 28, 0.22);
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.04em;
}
</style>
