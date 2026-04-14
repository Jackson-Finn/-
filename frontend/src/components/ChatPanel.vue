<template>
  <div class="panel chat-panel">
    <div class="section-header">
      <div>
        <h3 class="section-title">实时会话</h3>
        <p class="section-meta">WebSocket 状态：{{ wsStatus }}</p>
      </div>
      <el-space wrap>
        <el-tag :type="statusType" effect="plain">{{ statusLabel }}</el-tag>
        <el-button type="primary" plain @click="$emit('refresh')">刷新会话</el-button>
      </el-space>
    </div>

    <el-skeleton v-if="loading && !sessions.length" animated :rows="4" />

    <el-result v-else-if="error" icon="error" title="会话加载失败" :sub-title="error">
      <template #extra>
        <el-button type="primary" @click="$emit('refresh')">重试</el-button>
      </template>
    </el-result>

    <el-empty
      v-else-if="!sessions.length"
      description="暂无会话，先在商品详情页发起"
    >
      <template #description>
        <div class="empty-copy">
          <strong>还没有会话</strong>
          <span>去商品详情页发起对话，系统会在这里展示完整的消息记录。</span>
        </div>
      </template>
    </el-empty>

    <div v-else class="chat-grid">
      <div class="session-list">
        <button
          v-for="session in sessions"
          :key="session.id"
          class="session-item"
          :class="{ active: session.id === activeSessionId }"
          @click="$emit('select-session', session.id)"
        >
          <strong>#{{ session.id }}</strong>
          <span>卖家 {{ session.seller_id }} · 买家 {{ session.buyer_id || 'N/A' }}</span>
          <el-tag size="small" effect="plain">会话</el-tag>
        </button>
      </div>

      <div class="message-box">
        <div class="message-meta">
          <div>
            <strong>消息流</strong>
            <p>选中会话后即可查看上下文消息和实时推送。</p>
          </div>
          <el-tag effect="plain">{{ messages.length }} 条消息</el-tag>
        </div>

        <el-empty v-if="!messages.length" description="当前会话暂无消息">
          <template #description>
            <div class="empty-copy">
              <strong>消息区为空</strong>
              <span>输入第一条消息即可开始对话。</span>
            </div>
          </template>
        </el-empty>

        <div class="messages">
          <div
            v-for="message in messages"
            :key="message.id"
            class="message"
            :class="{ mine: message.sender_id === currentUserId }"
          >
            <span>{{ message.content || '（空消息）' }}</span>
          </div>
        </div>

        <div class="composer">
          <el-input
            v-model="draft"
            placeholder="输入消息并发送"
            :disabled="sending || !activeSessionId"
            @keyup.enter="$emit('send-message', draft), (draft = '')"
          />
          <el-button type="primary" :loading="sending" :disabled="!draft || !activeSessionId" @click="$emit('send-message', draft), (draft = '')">
            发送
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

defineEmits(['select-session', 'send-message', 'refresh'])

const props = defineProps({
  currentUserId: Number,
  sessions: { type: Array, default: () => [] },
  messages: { type: Array, default: () => [] },
  activeSessionId: Number,
  wsStatus: { type: String, default: 'IDLE' },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  sending: { type: Boolean, default: false }
})

const draft = ref('')

const statusLabel = computed(() => {
  const labels = {
    OPEN: '在线',
    CONNECTING: '连接中',
    CLOSED: '离线',
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
</script>

<style scoped>
.chat-panel {
  padding: 20px;
}

.chat-grid {
  display: grid;
  grid-template-columns: 220px 1fr;
  gap: 16px;
}

.session-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.session-item {
  border: 1px solid var(--line);
  background: var(--surface-strong);
  border-radius: 16px;
  padding: 12px;
  text-align: left;
  display: flex;
  flex-direction: column;
  gap: 6px;
  cursor: pointer;
}

.session-item.active {
  background: rgba(176, 88, 46, 0.12);
}

.message-box {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.message-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.message-meta p {
  margin: 4px 0 0;
  color: var(--muted);
}

.messages {
  min-height: 240px;
  max-height: 320px;
  overflow: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.65);
  border-radius: 18px;
}

.message {
  max-width: 75%;
  padding: 10px 12px;
  border-radius: 14px;
  background: var(--surface-strong);
}

.message.mine {
  align-self: flex-end;
  background: rgba(36, 92, 90, 0.14);
}

.composer {
  display: flex;
  gap: 12px;
}

.empty-copy {
  display: flex;
  flex-direction: column;
  gap: 4px;
  color: var(--muted);
}

@media (max-width: 960px) {
  .chat-grid {
    grid-template-columns: 1fr;
  }
}
</style>
