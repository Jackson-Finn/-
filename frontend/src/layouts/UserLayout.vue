<template>
  <div class="shell">
    <aside class="left">
      <AppSidebar title="Market Studio" subtitle="用户交易与推荐体验" :items="navItems" />
    </aside>
    <main class="main">
      <header class="topbar panel">
        <div>
          <div class="pill">高级版二手交易平台</div>
          <h1>交易、搜索、聊天、AI 辅助在一个工作台完成</h1>
        </div>
        <div class="actions">
          <el-popover v-if="userStore.isAuthenticated" placement="bottom-end" :width="460" trigger="click">
            <template #reference>
              <el-badge :value="uiStore.unreadNotifications" :hidden="!uiStore.unreadNotifications">
                <el-button plain>
                  通知中心
                  <el-tag size="small" effect="plain" :type="wsStatusType" style="margin-left: 8px;">
                    {{ wsStatusLabel }}
                  </el-tag>
                </el-button>
              </el-badge>
            </template>
            <NotificationCenter
              :notifications="uiStore.notifications.slice(0, 8)"
              :loading="uiStore.notificationLoading"
              :error="uiStore.notificationError"
              :unread-count="uiStore.unreadNotifications"
              :ws-status="uiStore.wsStatus"
              :last-synced-at="uiStore.lastNotificationSyncAt"
              :marking-id="uiStore.markingNotificationId"
              @refresh="uiStore.syncNotifications()"
              @mark-read="uiStore.markNotificationRead"
            />
          </el-popover>
          <RouterLink v-if="!userStore.isAuthenticated" to="/login">
            <el-button type="primary">登录</el-button>
          </RouterLink>
          <template v-else>
            <RouterLink to="/publish">
              <el-button type="primary">发布商品</el-button>
            </RouterLink>
            <RouterLink v-if="userStore.isAdmin" to="/admin">
              <el-button plain>后台</el-button>
            </RouterLink>
            <el-dropdown>
              <el-button>{{ userStore.profile?.display_name || '用户' }}</el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="router.push('/profile')">个人中心</el-dropdown-item>
                  <el-dropdown-item @click="logout">退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </div>
      </header>
      <div class="page-shell">
        <RouterView />
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'

import AppSidebar from '../components/AppSidebar.vue'
import NotificationCenter from '../components/NotificationCenter.vue'
import { useUiStore } from '../stores/ui'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()
const uiStore = useUiStore()

const navItems = computed(() => [
  { to: '/', label: '首页', icon: 'House' },
  { to: '/publish', label: '发布商品', icon: 'Plus' },
  { to: '/orders', label: '我的订单', icon: 'Tickets' },
  { to: '/favorites', label: '我的收藏', icon: 'Star' },
  { to: '/profile', label: '个人中心', icon: 'User' }
])

const wsStatusLabel = computed(() => {
  const labels = {
    OPEN: '在线',
    CONNECTING: '连接中',
    CLOSED: '离线',
    ERROR: '异常',
    IDLE: '空闲'
  }
  return labels[uiStore.wsStatus] || uiStore.wsStatus
})

const wsStatusType = computed(() => {
  const types = {
    OPEN: 'success',
    CONNECTING: 'warning',
    CLOSED: 'info',
    ERROR: 'danger',
    IDLE: 'info'
  }
  return types[uiStore.wsStatus] || 'info'
})

function logout() {
  userStore.clearSession()
  router.push('/login')
}
</script>

<style scoped>
.shell {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 280px 1fr;
}

.left {
  padding: 24px 12px 24px 24px;
}

.main {
  padding: 24px 24px 24px 12px;
}

.topbar {
  padding: 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
}

.topbar h1 {
  margin: 14px 0 0;
  font-size: 1.8rem;
  max-width: 580px;
}

.actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

@media (max-width: 960px) {
  .shell {
    grid-template-columns: 1fr;
  }

  .left {
    padding: 14px;
  }

  .main {
    padding: 0 14px 14px;
  }

  .topbar {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
