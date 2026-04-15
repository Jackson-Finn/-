<template>
  <span class="badge" :class="toneClass">{{ label }}</span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: {
    type: String,
    default: ''
  }
})

const label = computed(() => {
  const mapping = {
    PENDING: '待审',
    APPROVED: '已通过',
    REJECTED: '已驳回',
    CHANGES_REQUESTED: '待修改',
    ACTIVE: '在售',
    NEEDS_REVISION: '待修改',
    BLOCKED: '已拦截',
    OFF_SHELF: '已下架',
    COMPLETED: '已完成'
  }
  return mapping[props.status] || props.status || '未知'
})

const toneClass = computed(() => {
  if (['APPROVED', 'ACTIVE', 'COMPLETED'].includes(props.status)) return 'is-success'
  if (props.status === 'PENDING') return 'is-warning'
  if (['CHANGES_REQUESTED', 'NEEDS_REVISION'].includes(props.status)) return 'is-info'
  if (['REJECTED', 'BLOCKED'].includes(props.status)) return 'is-danger'
  if (props.status === 'OFF_SHELF') return 'is-muted'
  return 'is-default'
})
</script>

<style scoped>
.badge {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 0.76rem;
  font-weight: 700;
  border: 1px solid transparent;
}

.is-success {
  background: var(--success-soft);
  color: #18794e;
}

.is-warning {
  background: #fff4e5;
  color: #b54708;
}

.is-info {
  background: #eaf2ff;
  color: #1d4ed8;
}

.is-danger {
  background: var(--danger-soft);
  color: #b42318;
}

.is-muted {
  background: #f4f7fb;
  color: var(--muted);
}

.is-default {
  background: #eef4fb;
  color: var(--text);
}
</style>
