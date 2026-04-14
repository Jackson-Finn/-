<template>
  <div class="notification-center">
    <div class="section-header">
      <div>
        <h3 class="section-title">通知中心</h3>
        <p class="section-meta">
          <span>未读 {{ unreadCount }}</span>
          <span v-if="lastSyncedAt"> · {{ formatTime(lastSyncedAt) }}</span>
        </p>
      </div>
      <el-space wrap>
        <el-tag :type="statusType" effect="plain">{{ wsStatusLabel }}</el-tag>
        <el-button text @click="$emit('refresh')">刷新</el-button>
      </el-space>
    </div>

    <div class="notification-summary">
      <div class="summary-chip">
        <strong>{{ unreadCount }}</strong>
        <span>未读通知</span>
      </div>
      <div class="summary-chip">
        <strong>{{ notifications.length }}</strong>
        <span>总通知数</span>
      </div>
      <div class="summary-chip">
        <strong>{{ readCount }}</strong>
        <span>已读通知</span>
      </div>
    </div>

    <el-skeleton v-if="loading" animated :rows="4" />

    <el-result
      v-else-if="error"
      icon="error"
      title="通知加载失败"
      :sub-title="error"
    >
      <template #extra>
        <el-button type="primary" @click="$emit('refresh')">重试</el-button>
      </template>
    </el-result>

    <el-empty
      v-else-if="!notifications.length"
      description="暂时没有通知，系统有新事件时会自动显示在这里"
    />

    <el-scrollbar v-else max-height="460px">
      <div class="notification-list">
        <button
          v-for="item in orderedNotifications"
          :key="item.id"
          class="notification-item"
          :class="{ unread: !item.read, marking: markingId === item.id }"
          :disabled="markingId === item.id"
          @click="$emit('mark-read', item.id)"
        >
          <div class="notification-head">
            <div class="title-block">
              <span class="status-dot" :class="{ unread: !item.read }" />
              <strong>{{ item.title || '系统通知' }}</strong>
            </div>
            <el-tag size="small" :type="item.read ? 'info' : 'warning'" effect="plain">
              {{ item.read ? '已读' : '未读' }}
            </el-tag>
          </div>
          <p class="content">{{ item.content || '无内容说明' }}</p>
          <div class="notification-meta">
            <span>{{ item.event_type || 'GENERAL' }}</span>
            <span>{{ formatTime(item.created_at || item.updated_at || '') }}</span>
          </div>
        </button>
      </div>
    </el-scrollbar>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  notifications: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  error: {
    type: String,
    default: ''
  },
  unreadCount: {
    type: Number,
    default: 0
  },
  wsStatus: {
    type: String,
    default: 'IDLE'
  },
  lastSyncedAt: {
    type: String,
    default: ''
  },
  markingId: {
    type: [Number, String, null],
    default: null
  }
})

defineEmits(['refresh', 'mark-read'])

const orderedNotifications = computed(() =>
  [...props.notifications].sort((left, right) => Number(left.read) - Number(right.read))
)

const readCount = computed(() => props.notifications.filter((item) => item.read).length)

const wsStatusLabel = computed(() => {
  const labels = {
    OPEN: '在线',
    CONNECTING: '连接中',
    CLOSED: '已断开',
    ERROR: '异常',
    IDLE: '空闲'
  }
  return labels[props.wsStatus] || props.wsStatus
})

const statusType = computed(() => {
  const types = {
    OPEN: 'success',
    CONNECTING: 'warning',
    CLOSED: 'info',
    ERROR: 'danger',
    IDLE: 'info'
  }
  return types[props.wsStatus] || 'info'
})

function formatTime(value) {
  if (!value) {
    return '刚刚'
  }

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }

  return date.toLocaleString('zh-CN', {
    hour12: false,
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped>
.notification-center {
  display: flex;
  flex-direction: column;
  gap: 14px;
  width: 100%;
}

.notification-summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.summary-chip {
  padding: 12px;
  border-radius: 16px;
  background: rgba(176, 88, 46, 0.08);
  border: 1px solid var(--line);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.summary-chip strong {
  font-size: 1.1rem;
}

.notification-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.notification-item {
  width: 100%;
  border: 1px solid var(--line);
  background: var(--surface-strong);
  border-radius: 18px;
  padding: 14px;
  text-align: left;
  display: flex;
  flex-direction: column;
  gap: 10px;
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.notification-item:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 10px 20px rgba(92, 63, 35, 0.08);
}

.notification-item.unread {
  border-color: rgba(176, 88, 46, 0.28);
  background: linear-gradient(180deg, rgba(176, 88, 46, 0.1), rgba(255, 255, 255, 0.96));
}

.notification-item.marking {
  opacity: 0.7;
}

.notification-head,
.title-block,
.notification-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.title-block {
  justify-content: flex-start;
}

.status-dot {
  width: 9px;
  height: 9px;
  border-radius: 999px;
  background: rgba(118, 98, 80, 0.4);
}

.status-dot.unread {
  background: var(--brand);
  box-shadow: 0 0 0 4px rgba(176, 88, 46, 0.12);
}

.content {
  margin: 0;
  color: var(--text);
  line-height: 1.5;
}

.notification-meta {
  color: var(--muted);
  font-size: 0.88rem;
}

@media (max-width: 960px) {
  .notification-summary {
    grid-template-columns: 1fr;
  }
}
</style>
