<template>
  <section class="panel data-state-card" :class="`state-${state}`">
    <div v-if="state === 'loading'" class="state-block">
      <div class="section-header">
        <div>
          <h3 class="section-title">{{ title }}</h3>
          <p class="section-meta">{{ description }}</p>
        </div>
        <el-tag effect="plain" type="info">加载中</el-tag>
      </div>
      <el-skeleton animated :rows="rows" />
    </div>

    <el-result
      v-else-if="state === 'error'"
      icon="error"
      :title="errorTitle || title"
      :sub-title="errorDescription || description"
    >
      <template #extra>
        <el-space wrap>
          <el-button type="primary" @click="$emit('retry')">重新加载</el-button>
          <slot name="error-action" />
        </el-space>
      </template>
    </el-result>

    <el-result
      v-else-if="state === 'empty'"
      icon="info"
      :title="emptyTitle || title"
      :sub-title="emptyDescription || description"
    >
      <template #extra>
        <slot name="empty-action" />
      </template>
    </el-result>

    <slot v-else />
  </section>
</template>

<script setup>
defineProps({
  state: {
    type: String,
    default: 'ready'
  },
  title: {
    type: String,
    default: ''
  },
  description: {
    type: String,
    default: ''
  },
  emptyTitle: {
    type: String,
    default: ''
  },
  emptyDescription: {
    type: String,
    default: ''
  },
  errorTitle: {
    type: String,
    default: ''
  },
  errorDescription: {
    type: String,
    default: ''
  },
  rows: {
    type: Number,
    default: 3
  }
})

defineEmits(['retry'])
</script>

<style scoped>
.data-state-card {
  overflow: hidden;
}

.data-state-card :deep(.el-result) {
  padding: 28px 0 12px;
}

.state-block {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}
</style>
