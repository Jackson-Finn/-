<template>
  <div class="shell">
    <aside class="left">
      <AppSidebar title="闲置市场" subtitle="简洁但完整的交易体验" :items="navItems" />
    </aside>
    <main class="main">
      <header class="topbar panel">
        <div class="topbar-copy">
          <div class="eyebrow">二手交易平台</div>
          <h1>交易工作台</h1>
          <p class="topbar-meta">围绕商品、价格、成色和交付方式组织信息，减少无效装饰。</p>
        </div>
        <div class="actions">
          <RouterLink to="/search">
            <el-button plain>搜索与筛选</el-button>
          </RouterLink>
          <el-popover v-if="userStore.isAuthenticated" placement="bottom-end" :width="460" trigger="click">
            <template #reference>
              <el-badge :value="uiStore.unreadNotifications" :hidden="!uiStore.unreadNotifications">
                <el-button plain>
                  通知中心
                  <el-tag size="small" effect="plain" :type="presenceType" style="margin-left: 8px;">
                    {{ presenceLabel }}
                  </el-tag>
                </el-button>
              </el-badge>
            </template>
            <NotificationCenter
              :notifications="uiStore.notifications.slice(0, 8)"
              :loading="uiStore.notificationLoading"
              :error="uiStore.notificationError"
              :unread-count="uiStore.unreadNotifications"
              :presence-status="userStore.profile?.presence_status || 'OFFLINE'"
              :ws-status="uiStore.wsStatus"
              :last-synced-at="uiStore.lastNotificationSyncAt"
              :marking-id="uiStore.markingNotificationId"
              @refresh="uiStore.syncNotifications()"
              @mark-read="uiStore.markNotificationRead"
              @update-presence="updatePresenceStatus"
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
                  <el-dropdown-item @click="router.push('/profile')">我的</el-dropdown-item>
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
import { ElMessage } from 'element-plus'

import AppSidebar from '../components/AppSidebar.vue'
import NotificationCenter from '../components/NotificationCenter.vue'
import { useUiStore } from '../stores/ui'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()
const uiStore = useUiStore()

const navItems = computed(() => [
  { to: '/', label: '首页', icon: 'House' },
  { to: '/messages', label: '消息', icon: 'ChatDotRound', activePrefix: '/messages' },
  { to: '/publish', label: '发布', icon: 'UploadFilled', activePrefix: '/publish' },
  { to: '/orders', label: '订单', icon: 'Tickets', activePrefix: '/orders' },
  { to: '/profile', label: '我的', icon: 'User', activePrefix: '/profile' }
])

const presenceLabel = computed(() => {
  const labels = {
    ONLINE: '在线',
    INVISIBLE: '隐身',
    OFFLINE: '离线'
  }
  return labels[userStore.profile?.presence_status] || '离线'
})

const presenceType = computed(() => {
  const types = {
    ONLINE: 'success',
    INVISIBLE: 'warning',
    OFFLINE: 'info'
  }
  return types[userStore.profile?.presence_status] || 'info'
})

async function updatePresenceStatus(nextStatus) {
  try {
    await userStore.setPresenceStatus(nextStatus)
    ElMessage.success('消息状态已更新')
  } catch (error) {
    ElMessage.error(error.message)
  }
}

function logout() {
  userStore.clearSession()
  router.push('/login')
}
</script>

<style scoped>
.shell {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 236px 1fr;
}

.left {
  padding: 24px 12px 24px 24px;
}

.main {
  padding: 24px 24px 24px 12px;
}

.topbar {
  padding: 18px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
}

.topbar h1 {
  margin: 0 0 4px;
  font-family: var(--font-ui);
  font-size: clamp(1.15rem, 1.5vw, 1.4rem);
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: -0.02em;
}

.topbar-copy {
  max-width: 560px;
}

.topbar-meta {
  margin: 0;
  max-width: 52ch;
  color: var(--muted);
  font-size: 0.88rem;
}

.actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: flex-end;
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

  .actions {
    justify-content: flex-start;
  }
}
</style>
