<template>
  <div class="shell">
    <aside class="left">
      <AppSidebar title="Control Deck" subtitle="审核、治理与运维协同" :items="navItems" />
    </aside>
    <main class="main">
      <header class="topbar panel">
        <div>
          <div class="pill">管理中台</div>
          <h1>审核任务、治理决策、推荐与搜索运维都在这里</h1>
        </div>
        <div class="actions">
          <el-popover placement="bottom-end" :width="460" trigger="click">
            <template #reference>
              <el-badge :value="uiStore.unreadNotifications" :hidden="!uiStore.unreadNotifications">
                <el-button plain>
                  未读通知
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
          <RouterLink to="/">
            <el-button>返回前台</el-button>
          </RouterLink>
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

import AppSidebar from '../components/AppSidebar.vue'
import NotificationCenter from '../components/NotificationCenter.vue'
import { useUiStore } from '../stores/ui'

const uiStore = useUiStore()
const navItems = [
  { to: '/admin', label: '概览', icon: 'DataAnalysis' },
  { to: '/admin/products', label: '商品审核', icon: 'DocumentChecked' },
  { to: '/admin/reports', label: '举报处理', icon: 'Warning' },
  { to: '/admin/appeals', label: '申诉复核', icon: 'Checked' },
  { to: '/admin/access', label: '权限管理', icon: 'Lock' }
]

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
  max-width: 620px;
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

  .left,
  .main {
    padding: 14px;
  }
}
</style>
