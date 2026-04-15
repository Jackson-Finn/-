<template>
  <div class="messages-page">
    <section class="panel page-head">
      <div>
        <div class="eyebrow">Messages</div>
        <h2 class="section-title">消息中心</h2>
        <p class="section-meta">从商品详情或卖家主页进入后，会自动定位到对应会话。</p>
      </div>
      <div class="head-actions">
        <PresenceSelector
          :model-value="userStore.profile?.presence_status || 'OFFLINE'"
          @update:model-value="updatePresenceStatus"
        />
        <el-button plain @click="loadSessions">刷新会话</el-button>
      </div>
    </section>

    <div class="messages-layout">
      <DataStateCard
        class="session-shell"
        :state="sessionState"
        title="会话加载失败"
        description="暂时无法获取消息列表。"
        empty-title="还没有会话"
        empty-description="从商品详情或卖家主页点击“联系卖家”后，会话会出现在这里。"
        :error-description="error"
        @retry="loadSessions"
      >
        <section class="panel session-panel">
          <div class="section-header">
            <div>
              <h3 class="section-title">会话列表</h3>
              <p class="section-meta">会按最近活跃时间排序。</p>
            </div>
          </div>

          <div class="session-list">
            <button
              v-for="session in sessions"
              :key="session.id"
              type="button"
              class="session-item"
              :class="{ active: session.id === activeSessionId }"
              @click="selectSession(session.id)"
            >
              <div class="session-topline">
                <strong>{{ session.counterpart_name || '卖家' }}</strong>
                <el-tag size="small" effect="plain" :type="presenceTagType(session.counterpart_presence_status)">
                  {{ presenceLabel(session.counterpart_presence_status) }}
                </el-tag>
              </div>
              <p class="session-title">{{ session.product_summary?.title || '站内会话' }}</p>
              <p class="session-preview">{{ session.last_message_preview || '还没有消息，先发第一句吧。' }}</p>
              <div class="session-foot">
                <small>{{ session.last_message_at ? formatTime(session.last_message_at) : '刚建立' }}</small>
                <el-tag v-if="session.unread_count" size="small" type="warning" effect="plain">{{ session.unread_count }} 条未读</el-tag>
              </div>
            </button>
          </div>
        </section>
      </DataStateCard>

      <section class="panel chat-panel">
        <div class="chat-head">
          <div>
            <h3 class="section-title">{{ currentSession?.product_summary?.title || '选择一个会话' }}</h3>
            <p class="section-meta">
              {{ currentSession?.counterpart_name || '会话未选中' }}
              <span v-if="currentSession"> · {{ presenceLabel(currentSession.counterpart_presence_status) }}</span>
            </p>
          </div>
          <RouterLink
            v-if="currentSession?.product_summary?.id"
            :to="`/products/${currentSession.product_summary.id}`"
          >
            <el-button plain>查看商品</el-button>
          </RouterLink>
        </div>

        <div v-if="currentSession" class="product-context">
          <img
            v-if="currentSession.product_summary?.cover_image"
            :src="currentSession.product_summary.cover_image"
            :alt="currentSession.product_summary.title"
            class="context-cover"
          >
          <div class="context-copy">
            <strong>{{ currentSession.product_summary?.title || '当前商品' }}</strong>
            <p>{{ currentSession.product_summary?.hero_summary || '进入会话后可以直接补充你想确认的细节。' }}</p>
          </div>
        </div>

        <div v-if="currentSession" class="copilot-panel">
          <div class="mini-head">
            <strong>AI 沟通助手</strong>
            <el-tag size="small" effect="plain">{{ copilot.source_mode === 'provider' ? '模型建议' : '规则建议' }}</el-tag>
          </div>
          <p class="copilot-summary">{{ copilot.summary || '正在整理当前会话摘要。' }}</p>
          <div class="copilot-grid">
            <div class="copilot-card">
              <strong>待确认事项</strong>
              <ul>
                <li v-for="item in copilot.pending_topics || []" :key="item">{{ item }}</li>
              </ul>
            </div>
            <div class="copilot-card">
              <strong>建议回复</strong>
              <div class="reply-list">
                <button
                  v-for="item in copilot.suggested_replies || []"
                  :key="item"
                  type="button"
                  class="reply-chip"
                  @click="draft = item"
                >
                  {{ item }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <div v-if="currentSession" class="message-stream">
          <article
            v-for="message in messages"
            :key="message.id"
            class="message-bubble"
            :class="{ mine: message.sender_id === userStore.profile?.id }"
          >
            <strong>{{ message.sender_name || '用户' }}</strong>
            <p>{{ message.content }}</p>
          </article>
          <div v-if="!messages.length" class="message-empty">还没有聊天内容，直接发第一条消息即可。</div>
        </div>
        <div v-else class="message-empty">从左侧选择一个会话，或先去商品详情联系卖家。</div>

        <div class="composer">
          <el-input
            v-model="draft"
            :disabled="!activeSessionId || sending"
            placeholder="补充你想确认的成色、配件、验货和交付方式"
            @keyup.enter="sendDraft"
          />
          <el-button type="primary" :loading="sending" :disabled="!activeSessionId || !draft.trim()" @click="sendDraft">
            发送
          </el-button>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useRoute } from 'vue-router'

import DataStateCard from '../../components/DataStateCard.vue'
import PresenceSelector from '../../components/PresenceSelector.vue'
import { interactionApi } from '../../api/interaction'
import { useUiStore } from '../../stores/ui'
import { useUserStore } from '../../stores/user'

const route = useRoute()
const userStore = useUserStore()
const uiStore = useUiStore()

const sessions = ref([])
const messages = ref([])
const activeSessionId = ref(null)
const loading = ref(false)
const error = ref('')
const sending = ref(false)
const draft = ref('')
const copilot = ref({})

const requestedSessionId = computed(() => {
  const raw = Array.isArray(route.query.sessionId) ? route.query.sessionId[0] : route.query.sessionId
  const value = Number(raw)
  return Number.isFinite(value) && value > 0 ? value : null
})

const currentSession = computed(() => sessions.value.find((item) => item.id === activeSessionId.value) || null)

async function loadSessions() {
  loading.value = true
  error.value = ''
  try {
    sessions.value = await interactionApi.listSessions()
    if (requestedSessionId.value && sessions.value.some((item) => item.id === requestedSessionId.value)) {
      await selectSession(requestedSessionId.value)
    } else if (!activeSessionId.value && sessions.value.length) {
      await selectSession(sessions.value[0].id)
    }
  } catch (requestError) {
    error.value = requestError.message
    sessions.value = []
  } finally {
    loading.value = false
  }
}

async function selectSession(sessionId) {
  activeSessionId.value = sessionId
  try {
    const [sessionMessages, sessionCopilot] = await Promise.all([
      interactionApi.listMessages(sessionId),
      interactionApi.chatCopilot({ session_id: sessionId })
    ])
    messages.value = sessionMessages
    copilot.value = sessionCopilot
  } catch (requestError) {
    ElMessage.error(requestError.message)
    messages.value = []
    copilot.value = {}
  }
}

async function sendDraft() {
  if (!activeSessionId.value || !draft.value.trim()) return
  sending.value = true
  const content = draft.value.trim()
  try {
    const message = await interactionApi.sendMessage(activeSessionId.value, { content })
    messages.value = [...messages.value, message]
    draft.value = ''
    await selectSession(activeSessionId.value)
    await loadSessions()
  } catch (requestError) {
    ElMessage.error(requestError.message)
  } finally {
    sending.value = false
  }
}

async function updatePresenceStatus(nextStatus) {
  try {
    await userStore.setPresenceStatus(nextStatus)
    if (userStore.profile?.id) {
      await uiStore.connectRealtime(userStore.profile.id, nextStatus)
    }
    ElMessage.success('消息状态已更新')
  } catch (requestError) {
    ElMessage.error(requestError.message)
  }
}

function presenceLabel(status) {
  const labels = {
    ONLINE: '在线',
    INVISIBLE: '隐身',
    OFFLINE: '离线'
  }
  return labels[status] || '离线'
}

function presenceTagType(status) {
  if (status === 'ONLINE') return 'success'
  if (status === 'INVISIBLE') return 'warning'
  return 'info'
}

function formatTime(value) {
  if (!value) return '刚刚'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', {
    hour12: false,
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

watch(
  requestedSessionId,
  async (sessionId) => {
    if (!sessionId || !sessions.value.some((item) => item.id === sessionId) || activeSessionId.value === sessionId) return
    await selectSession(sessionId)
  }
)

watch(
  () => uiStore.receivedEvents[0],
  async (event) => {
    if (!event || !activeSessionId.value) return
    if (event.event === 'chat.message.created' && event.payload?.session_id === activeSessionId.value) {
      await selectSession(activeSessionId.value)
      await loadSessions()
    }
  }
)

onMounted(loadSessions)

const sessionState = computed(() => {
  if (loading.value) return 'loading'
  if (error.value) return 'error'
  if (!sessions.value.length) return 'empty'
  return 'ready'
})
</script>

<style scoped>
.messages-page {
  display: grid;
  gap: 20px;
}

.page-head,
.session-panel,
.chat-panel {
  padding: 22px;
}

.page-head,
.chat-head,
.head-actions,
.session-topline {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.messages-layout {
  display: grid;
  grid-template-columns: 360px minmax(0, 1fr);
  gap: 18px;
}

.session-list,
.message-stream {
  display: grid;
  gap: 12px;
}

.session-item {
  border: 1px solid var(--line);
  border-radius: 18px;
  background: var(--surface-strong);
  padding: 14px;
  text-align: left;
  cursor: pointer;
}

.session-item.active {
  border-color: rgba(35, 68, 93, 0.24);
  background: rgba(35, 68, 93, 0.06);
}

.session-title,
.session-preview {
  margin: 8px 0 0;
}

.session-preview {
  color: var(--muted);
}

.session-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 10px;
}

.chat-panel {
  display: grid;
  gap: 16px;
}

.product-context {
  display: grid;
  grid-template-columns: 96px minmax(0, 1fr);
  gap: 14px;
  padding: 14px;
  border-radius: 20px;
  background: rgba(73, 57, 41, 0.04);
}

.context-cover {
  width: 96px;
  height: 96px;
  object-fit: cover;
  border-radius: 16px;
}

.context-copy p,
.message-bubble p {
  margin: 8px 0 0;
  line-height: 1.7;
}

.copilot-panel {
  display: grid;
  gap: 14px;
  padding: 16px 18px;
  border-radius: 20px;
  background: rgba(36, 88, 222, 0.06);
}

.mini-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.copilot-summary {
  margin: 0;
  color: var(--muted-strong);
  line-height: 1.7;
}

.copilot-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.copilot-card {
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.9);
}

.copilot-card strong {
  display: block;
  margin-bottom: 10px;
}

.copilot-card ul {
  margin: 0;
  padding-left: 18px;
}

.reply-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.reply-chip {
  border: 0;
  border-radius: 999px;
  padding: 8px 12px;
  background: var(--brand-soft);
  color: var(--brand-strong);
  font-weight: 700;
  cursor: pointer;
}

.message-bubble {
  max-width: 78%;
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(73, 57, 41, 0.05);
}

.message-bubble.mine {
  justify-self: end;
  background: rgba(35, 68, 93, 0.1);
}

.message-empty {
  padding: 18px;
  border-radius: 18px;
  background: rgba(73, 57, 41, 0.04);
  color: var(--muted);
}

.composer {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
}

@media (max-width: 960px) {
  .messages-layout,
  .composer,
  .product-context,
  .copilot-grid {
    grid-template-columns: 1fr;
  }
}
</style>
