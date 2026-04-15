<template>
  <div class="panel state">
    <el-result icon="error" :title="title" :sub-title="description">
      <template #extra>
        <el-button type="primary" @click="$emit('retry')">重新加载</el-button>
      </template>
    </el-result>
  </div>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    default: '加载失败'
  },
  description: {
    type: String,
    default: '请稍后重试'
  }
})

defineEmits(['retry'])
</script>

<style scoped>
.state {
  padding: 8px;
}
</style>
