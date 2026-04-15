<template>
  <section class="panel data-state-card" :class="`state-${state}`">
    <div v-if="state === 'loading'" class="state-shell">
      <div class="state-copy">
        <p class="state-label">加载中</p>
        <h3>{{ title }}</h3>
        <p>{{ description }}</p>
      </div>
      <el-skeleton animated :rows="rows" />
    </div>

    <div v-else-if="state === 'error'" class="state-shell">
      <div class="state-copy">
        <p class="state-label tone-danger">加载异常</p>
        <h3>{{ errorTitle || title }}</h3>
        <p>{{ errorDescription || description }}</p>
      </div>
      <div class="state-actions">
        <el-button type="primary" @click="$emit('retry')">重新加载</el-button>
        <slot name="error-action" />
      </div>
    </div>

    <div v-else-if="state === 'empty'" class="state-shell">
      <div class="state-copy">
        <p class="state-label">暂时为空</p>
        <h3>{{ emptyTitle || title }}</h3>
        <p>{{ emptyDescription || description }}</p>
      </div>
      <div class="state-actions">
        <slot name="empty-action" />
      </div>
    </div>

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
  min-height: 100%;
}

.state-shell {
  display: grid;
  gap: 22px;
  padding: 28px;
}

.state-copy h3 {
  margin: 6px 0 0;
  font-size: 1.18rem;
  line-height: 1.25;
}

.state-copy p:last-child {
  margin: 10px 0 0;
  max-width: 52ch;
  color: var(--muted);
  line-height: 1.75;
}

.state-label {
  margin: 0;
  color: var(--muted-strong);
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.tone-danger {
  color: var(--danger);
}

.state-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}
</style>
