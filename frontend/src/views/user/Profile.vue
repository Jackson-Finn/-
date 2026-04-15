<template>
  <div class="grid grid-2">
    <section class="panel mine-panel">
      <div class="section-header">
        <div>
          <h2 class="section-title">我的</h2>
          <p class="section-meta">把个人资料、收藏、浏览、我的商品和消息状态收进同一页，减少碎片入口。</p>
        </div>
      </div>

      <div class="grid grid-3 summary-grid">
        <StatPanel label="身份" :value="userStore.isAdmin ? '管理员' : '普通用户'" description="当前登录角色" />
        <StatPanel label="收藏" :value="workspace.favorites" description="候选商品数量" />
        <StatPanel label="浏览" :value="workspace.recent_history" description="最近浏览记录" />
      </div>

      <div class="grid grid-2 action-grid">
        <RouterLink class="asset-card" to="/favorites">
          <strong>{{ workspace.favorites }}</strong>
          <span>我的收藏</span>
          <p>回到候选商品继续比较。</p>
        </RouterLink>
        <RouterLink class="asset-card" to="/history">
          <strong>{{ workspace.recent_history }}</strong>
          <span>最近浏览</span>
          <p>把最近看过的商品重新收回来。</p>
        </RouterLink>
        <RouterLink class="asset-card" to="/my-products">
          <strong>卖家工作区</strong>
          <span>我的商品</span>
          <p>查看在售、审核中和待修改的商品。</p>
        </RouterLink>
        <RouterLink class="asset-card" to="/orders">
          <strong>{{ workspace.active_orders }}</strong>
          <span>进行中订单</span>
          <p>继续推进确认收货和评价。</p>
        </RouterLink>
      </div>

      <el-descriptions :column="1" border>
        <el-descriptions-item label="用户 ID">{{ userStore.profile?.id }}</el-descriptions-item>
        <el-descriptions-item label="昵称">{{ userStore.profile?.display_name }}</el-descriptions-item>
        <el-descriptions-item label="邮箱">{{ userStore.profile?.email }}</el-descriptions-item>
        <el-descriptions-item label="消息状态">{{ presenceLabel }}</el-descriptions-item>
        <el-descriptions-item label="管理员">{{ userStore.profile?.is_admin ? '是' : '否' }}</el-descriptions-item>
      </el-descriptions>
    </section>

    <NotificationCenter
      :notifications="notifications"
      :loading="loading"
      :error="error"
      :unread-count="uiStore.unreadNotifications"
      :presence-status="userStore.profile?.presence_status || 'OFFLINE'"
      :ws-status="uiStore.wsStatus"
      :last-synced-at="uiStore.lastNotificationSyncAt"
      :marking-id="uiStore.markingNotificationId"
      @refresh="loadNotifications"
      @mark-read="markNotificationRead"
      @update-presence="updatePresenceStatus"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import NotificationCenter from '../../components/NotificationCenter.vue'
import StatPanel from '../../components/StatPanel.vue'
import { interactionApi } from '../../api/interaction'
import { tradeApi } from '../../api/trade'
import { useUserStore } from '../../stores/user'
import { useUiStore } from '../../stores/ui'

const userStore = useUserStore()
const uiStore = useUiStore()
const notifications = ref([])
const workspace = ref({
  unread_messages: 0,
  unread_notifications: 0,
  favorites: 0,
  recent_history: 0,
  active_orders: 0
})
const loading = ref(false)
const error = ref('')

async function loadNotifications() {
  loading.value = true
  error.value = ''
  try {
    const [notificationList, sessions, favorites, recentHistory, orders] = await Promise.all([
      interactionApi.listNotifications(),
      interactionApi.listSessions(),
      tradeApi.listFavorites(),
      tradeApi.recentHistory(),
      tradeApi.listOrders()
    ])
    notifications.value = notificationList
    workspace.value = {
      unread_messages: sessions.reduce((total, item) => total + Number(item.unread_count || 0), 0),
      unread_notifications: notificationList.filter((item) => !item.read).length,
      favorites: favorites.length,
      recent_history: recentHistory.length,
      active_orders: orders.filter((item) => !['COMPLETED', 'CANCELLED'].includes(item.status)).length
    }
  } catch (err) {
    error.value = err.message
    notifications.value = []
  } finally {
    loading.value = false
  }
}

async function markNotificationRead(id) {
  try {
    await uiStore.markNotificationRead(id)
    await loadNotifications()
    ElMessage.success('已标记为已读')
  } catch (err) {
    ElMessage.error(err.message)
  }
}

async function updatePresenceStatus(nextStatus) {
  try {
    await userStore.setPresenceStatus(nextStatus)
    if (userStore.profile?.id) {
      await uiStore.connectRealtime(userStore.profile.id, nextStatus)
    }
    ElMessage.success('消息状态已更新')
  } catch (err) {
    ElMessage.error(err.message)
  }
}

onMounted(loadNotifications)

const presenceLabel = computed(() => {
  const labels = {
    ONLINE: '在线',
    INVISIBLE: '隐身',
    OFFLINE: '离线'
  }
  return labels[userStore.profile?.presence_status] || '离线'
})
</script>

<style scoped>
.mine-panel {
  padding: 22px;
}

.summary-grid {
  margin-bottom: 18px;
}

.action-grid {
  margin-bottom: 18px;
}

.asset-card {
  display: grid;
  gap: 6px;
  padding: 18px;
  border-radius: 22px;
  background: rgba(255, 252, 247, 0.95);
  border: 1px solid var(--line);
}

.asset-card strong {
  font-size: 1.35rem;
  line-height: 1.2;
}

.asset-card span {
  font-weight: 800;
}

.asset-card p {
  margin: 0;
  color: var(--muted);
  line-height: 1.7;
}
</style>
