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
  () => userStore.profile?.id,
  async (userId) => {
    await uiStore.connectRealtime(userId)
  },
  { immediate: true }
)

onBeforeUnmount(() => {
  uiStore.disconnectRealtime()
})
</script>
