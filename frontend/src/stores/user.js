import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { authApi } from '../api/auth'
import { interactionApi } from '../api/interaction'

const TOKEN_KEY = 'advanced-marketplace-token'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem(TOKEN_KEY) || '')
  const profile = ref(null)
  const initialized = ref(false)

  const isAuthenticated = computed(() => Boolean(token.value))
  const isAdmin = computed(() => Boolean(profile.value?.is_admin))
  const permissions = computed(() => profile.value?.permissions || [])

  async function bootstrap() {
    if (!token.value) {
      initialized.value = true
      return
    }

    try {
      profile.value = await authApi.me()
    } catch {
      clearSession()
    } finally {
      initialized.value = true
    }
  }

  async function login(payload) {
    const response = await authApi.login(payload)
    token.value = response.access_token
    localStorage.setItem(TOKEN_KEY, token.value)
    profile.value = await authApi.me()
    initialized.value = true
  }

  async function register(payload) {
    await authApi.register(payload)
    await login({ email: payload.email, password: payload.password })
  }

  async function setPresenceStatus(presenceStatus) {
    if (!token.value || !profile.value) return
    const result = await interactionApi.updatePresence({ presence_status: presenceStatus })
    profile.value = {
      ...profile.value,
      presence_status: result.presence_status
    }
  }

  function clearSession() {
    token.value = ''
    profile.value = null
    localStorage.removeItem(TOKEN_KEY)
  }

  return {
    token,
    profile,
    initialized,
    permissions,
    isAdmin,
    isAuthenticated,
    bootstrap,
    login,
    register,
    setPresenceStatus,
    clearSession
  }
})
