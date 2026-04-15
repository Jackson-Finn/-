import { defineStore } from 'pinia'
import { ref } from 'vue'

import { createWs, interactionApi } from '../api/interaction'

export const useUiStore = defineStore('ui', () => {
  const unreadNotifications = ref(0)
  const wsStatus = ref('IDLE')
  const notifications = ref([])
  const receivedEvents = ref([])
  const activeSocketUserId = ref(null)
  const activePresenceStatus = ref('OFFLINE')
  const notificationLoading = ref(false)
  const notificationError = ref('')
  const markingNotificationId = ref(null)
  const lastNotificationSyncAt = ref('')
  let socket = null

  async function syncNotifications() {
    notificationLoading.value = true
    notificationError.value = ''
    try {
      notifications.value = await interactionApi.listNotifications()
      unreadNotifications.value = notifications.value.filter((item) => !item.read).length
      lastNotificationSyncAt.value = new Date().toISOString()
    } catch {
      notificationError.value = '通知加载失败，请稍后重试'
      unreadNotifications.value = notifications.value.filter((item) => !item.read).length
    } finally {
      notificationLoading.value = false
    }
  }

  function disconnectRealtime() {
    socket?.close()
    socket = null
    activeSocketUserId.value = null
    activePresenceStatus.value = 'OFFLINE'
    wsStatus.value = 'CLOSED'
    receivedEvents.value = []
    notificationLoading.value = false
    notificationError.value = ''
  }

  async function markNotificationRead(id) {
    markingNotificationId.value = id
    try {
      await interactionApi.markNotificationRead(id)
      await syncNotifications()
    } finally {
      markingNotificationId.value = null
    }
  }

  async function connectRealtime(userId, presenceStatus = 'ONLINE') {
    if (!userId) {
      disconnectRealtime()
      notifications.value = []
      unreadNotifications.value = 0
      return
    }
    if (presenceStatus === 'OFFLINE') {
      disconnectRealtime()
      await syncNotifications()
      activeSocketUserId.value = userId
      activePresenceStatus.value = presenceStatus
      return
    }
    if (socket && activeSocketUserId.value === userId && activePresenceStatus.value === presenceStatus) {
      return
    }

    disconnectRealtime()
    activeSocketUserId.value = userId
    activePresenceStatus.value = presenceStatus
    wsStatus.value = 'CONNECTING'
    await syncNotifications()

    socket = createWs(
      userId,
      async (payload) => {
        receivedEvents.value.unshift(payload)
        receivedEvents.value = receivedEvents.value.slice(0, 20)

        if (payload.event === 'notification.created' || payload.event === 'notification.unread.changed') {
          await syncNotifications()
        }
      },
      (status) => {
        wsStatus.value = status
      }
    )
  }

  return {
    unreadNotifications,
    notifications,
    receivedEvents,
    wsStatus,
    notificationLoading,
    notificationError,
    markingNotificationId,
    lastNotificationSyncAt,
    activePresenceStatus,
    syncNotifications,
    connectRealtime,
    disconnectRealtime,
    markNotificationRead
  }
})
