<template>
  <section class="chat-panel">
    <div class="section-header">
      <div>
        <h3 class="section-title">沟通记录</h3>
        <p class="section-meta">已把聊天降成辅助阅读模块，方便先看重点再决定是否继续展开。</p>
      </div>
      <div class="panel-actions">
        <el-tag effect="plain" :type="statusType">{{ statusLabel }}</el-tag>
        <el-button plain @click="$emit('refresh')">刷新</el-button>
      </div>
    </div>

    <div v-if="loading && !sessions.length" class="state-copy">
      <p>正在同步当前商品的沟通记录…</p>
    </div>

    <div v-else-if="error" class="state-copy">
      <strong>会话加载失败</strong>
      <p>{{ error }}</p>
    </div>

    <div v-else-if="!sessions.length" class="state-copy">
      <strong>还没有公开沟通记录</strong>
      <p>如果你想确认成色、配件或面交细节，可以先联系卖家开启会话。</p>
    </div>

    <div v-else class="chat-shell">
      <div class="session-strip">
        <button
          v-for="session in sessions"
          :key="session.id"
          type="button"
          class="session-chip"
          :class="{ active: session.id === activeSessionId }"
          @click="$emit('select-session', session.id)"
        >
          <strong>会话 #{{ session.id }}</strong>
          <span>{{ session.product_id ? '商品沟通' : '站内沟通' }}</span>
        </button>
      </div>

      <div v-if="messages.length" class="message-stream">
        <article
          v-for="message in messages"
          :key="message.id"
          class="message"
          :class="{ mine: message.sender_id === currentUserId }"
        >
          <p>{{ message.content }}</p>
        </article>
      </div>
      <div v-else class="message-empty">当前会话还没有新的对话内容。</div>

      <div class="composer">
        <el-input
          v-model="draft"
          placeholder="补充你想确认的细节"
          :disabled="sending || !activeSessionId"
          @keyup.enter="submitDraft"
        />
        <el-button type="primary" :loading="sending" :disabled="!draft || !activeSessionId" @click="submitDraft">
          发送
        </el-button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'

const emit = defineEmits(['select-session', 'send-message', 'refresh'])

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
    OPEN: '实时在线',
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

function submitDraft() {
  if (!draft.value || !props.activeSessionId) return
  const value = draft.value
  draft.value = ''
  emit('send-message', value)
}
</script>

<style scoped>
.chat-panel {
  display: grid;
  gap: 18px;
}

.panel-actions {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.state-copy {
  padding: 22px;
  border-radius: 22px;
  background: rgba(73, 57, 41, 0.04);
}

.state-copy strong {
  display: block;
  margin-bottom: 6px;
}

.state-copy p {
  margin: 0;
  color: var(--muted);
  line-height: 1.75;
}

.chat-shell {
  display: grid;
  gap: 14px;
}

.session-strip {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.session-chip {
  padding: 12px 14px;
  border: 0;
  border-radius: 16px;
  background: rgba(73, 57, 41, 0.05);
  display: grid;
  gap: 4px;
  text-align: left;
  cursor: pointer;
}

.session-chip strong {
  font-size: 0.86rem;
}

.session-chip span {
  color: var(--muted);
  font-size: 0.8rem;
}

.session-chip.active {
  background: var(--accent-soft);
}

.message-stream {
  display: grid;
  gap: 10px;
}

.message {
  max-width: 86%;
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(73, 57, 41, 0.05);
}

.message.mine {
  justify-self: end;
  background: rgba(35, 68, 93, 0.09);
}

.message p {
  margin: 0;
  line-height: 1.75;
}

.message-empty {
  padding: 18px;
  border-radius: 18px;
  background: rgba(73, 57, 41, 0.04);
  color: var(--muted);
}

.composer {
  display: flex;
  gap: 12px;
}

@media (max-width: 760px) {
  .composer {
    flex-direction: column;
  }
}
</style>
