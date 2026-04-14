<template>
  <div class="grid grid-2">
    <div class="panel" style="padding: 22px;">
      <div class="section-header">
        <div>
          <h2 class="section-title">个人中心</h2>
          <p class="section-meta">当前登录信息与权限摘要</p>
        </div>
      </div>
      <div class="grid grid-3" style="margin-bottom: 18px;">
        <StatPanel label="身份" :value="userStore.isAdmin ? '管理员' : '普通用户'" description="当前登录角色" />
        <StatPanel label="权限点" :value="userStore.permissions.length" description="可访问功能数量" />
        <StatPanel label="通知" :value="uiStore.unreadNotifications" description="未读站内消息" />
      </div>
      <el-descriptions :column="1" border>
        <el-descriptions-item label="用户 ID">{{ userStore.profile?.id }}</el-descriptions-item>
        <el-descriptions-item label="昵称">{{ userStore.profile?.display_name }}</el-descriptions-item>
        <el-descriptions-item label="邮箱">{{ userStore.profile?.email }}</el-descriptions-item>
        <el-descriptions-item label="管理员">{{ userStore.profile?.is_admin ? '是' : '否' }}</el-descriptions-item>
      </el-descriptions>
    </div>

    <NotificationCenter
      :notifications="notifications"
      :loading="loading"
      :error="error"
      :unread-count="uiStore.unreadNotifications"
      :ws-status="uiStore.wsStatus"
      :last-synced-at="uiStore.lastNotificationSyncAt"
      :marking-id="uiStore.markingNotificationId"
      @refresh="loadNotifications"
      @mark-read="markNotificationRead"
    />
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import NotificationCenter from '../../components/NotificationCenter.vue'
import StatPanel from '../../components/StatPanel.vue'
import { interactionApi } from '../../api/interaction'
import { useUserStore } from '../../stores/user'
import { useUiStore } from '../../stores/ui'

const userStore = useUserStore()
const uiStore = useUiStore()
const notifications = ref([])
const loading = ref(false)
const error = ref('')

async function loadNotifications() {
  loading.value = true
  error.value = ''
  try {
    notifications.value = await interactionApi.listNotifications()
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

onMounted(loadNotifications)
</script>
