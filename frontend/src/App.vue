<template>
  <RouterView />
</template>

<script setup>
import { onBeforeUnmount, onMounted, watch } from 'vue'

import { useUiStore } from './stores/ui'
import { useUserStore } from './stores/user'

const userStore = useUserStore()
const uiStore = useUiStore()

onMounted(async () => {
  if (!userStore.initialized) {
    await userStore.bootstrap()
  }
})

watch(
  () => [userStore.profile?.id, userStore.profile?.presence_status],
  async ([userId, presenceStatus]) => {
    await uiStore.connectRealtime(userId, presenceStatus || 'OFFLINE')
  },
  { immediate: true }
)

onBeforeUnmount(() => {
  uiStore.disconnectRealtime()
})
</script>
