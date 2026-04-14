<template>
  <div class="auth-wrap">
    <div class="panel auth-card">
      <div class="section-header">
        <div>
          <div class="pill">欢迎回来</div>
          <h2 class="section-title">登录高级版交易平台</h2>
        </div>
      </div>
      <el-form :model="form" label-position="top" @submit.prevent="onSubmit">
        <el-form-item label="邮箱">
          <el-input v-model="form.email" placeholder="admin@example.com" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" show-password />
        </el-form-item>
        <el-button type="primary" :loading="loading" @click="onSubmit">登录</el-button>
        <RouterLink to="/register" class="muted link">还没有账号？去注册</RouterLink>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { useUserStore } from '../../stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const loading = ref(false)
const form = reactive({
  email: 'admin@example.com',
  password: 'Admin123!'
})

async function onSubmit() {
  loading.value = true
  try {
    await userStore.login(form)
    ElMessage.success('登录成功')
    router.push(route.query.redirect || '/')
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-wrap {
  display: grid;
  place-items: center;
  min-height: 65vh;
}

.auth-card {
  width: min(520px, 100%);
  padding: 28px;
}

.link {
  margin-left: 16px;
}
</style>

