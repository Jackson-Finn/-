<template>
  <div class="shell">
    <aside class="left">
      <AppSidebar title="后台运营" subtitle="审核、治理、通知与系统设置" :items="navItems" />
    </aside>
    <main class="main">
      <header class="topbar panel">
        <div class="topbar-copy">
          <div class="eyebrow">Operations</div>
          <h1>管理后台</h1>
          <p class="topbar-meta">优先展示待处理任务、通知运营和治理动作，把技术诊断下沉到系统设置。</p>
        </div>
        <div class="actions">
          <el-popover placement="bottom-end" :width="460" trigger="click">
            <template #reference>
              <el-badge :value="uiStore.unreadNotifications" :hidden="!uiStore.unreadNotifications">
                <el-button plain>
                  未读通知
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
import { ElMessage } from 'element-plus'

import AppSidebar from '../components/AppSidebar.vue'
import NotificationCenter from '../components/NotificationCenter.vue'
import { useUiStore } from '../stores/ui'
import { useUserStore } from '../stores/user'

const uiStore = useUiStore()
const userStore = useUserStore()
const navItems = [
  { to: '/admin/audits', label: '审核中心', icon: 'DocumentChecked', activePrefix: '/admin/audits' },
  { to: '/admin/reports', label: '交易治理', icon: 'Warning', activePrefix: '/admin/reports' },
  { to: '/admin/notifications', label: '通知运营', icon: 'Bell', activePrefix: '/admin/notifications' },
  { to: '/admin/platform', label: '系统设置', icon: 'Setting', activePrefix: '/admin/platform' },
  { to: '/admin/access', label: '权限管理', icon: 'Lock', activePrefix: '/admin/access' }
]

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
</script>

<style scoped>
.shell {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 248px 1fr;
}

.left {
  padding: 24px 12px 24px 24px;
}

.main {
  padding: 24px 24px 24px 12px;
}

.topbar {
  padding: 18px 22px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
}

.topbar h1 {
  margin: 0 0 4px;
  font-family: var(--font-ui);
  font-size: clamp(1.2rem, 1.8vw, 1.55rem);
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: -0.03em;
}

.topbar-copy {
  max-width: 560px;
}

.topbar-meta {
  margin: 0;
  max-width: 44ch;
  color: var(--muted);
  font-size: 0.9rem;
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

  .left,
  .main {
    padding: 14px;
  }

  .topbar {
    flex-direction: column;
  }

  .actions {
    justify-content: flex-start;
  }
}
</style>
