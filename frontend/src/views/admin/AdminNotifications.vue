<template>
  <div class="grid grid-2">
    <section class="panel notify-form">
      <div class="section-header">
        <div>
          <h2 class="section-title">发布站内通知</h2>
          <p class="section-meta">支持全站通知和指定单用户通知，发布后会写入站内未读并实时推送给在线用户。</p>
        </div>
      </div>

      <el-alert
        v-if="usersError"
        type="warning"
        :closable="false"
        show-icon
        :title="usersError"
        style="margin-bottom: 16px;"
      />

      <el-form label-position="top">
        <el-form-item label="投放范围">
          <el-radio-group v-model="form.target_scope">
            <el-radio-button label="ALL">全站用户</el-radio-button>
            <el-radio-button label="USER">指定用户</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-form-item v-if="form.target_scope === 'USER'" label="目标用户">
          <el-select
            v-model="form.target_user_id"
            placeholder="选择用户"
            filterable
            clearable
            :loading="usersLoading"
            no-data-text="暂无可选用户，请先刷新用户列表"
            style="width: 100%;"
          >
            <el-option
              v-for="user in users"
              :key="user.id"
              :label="`${user.display_name} (${user.email})`"
              :value="user.id"
            />
          </el-select>
          <div class="helper-row">
            <span class="muted">当前可选 {{ users.length }} 位用户</span>
            <el-button text :loading="usersLoading" @click="loadUsers">刷新用户</el-button>
          </div>
        </el-form-item>

        <el-form-item label="通知标题">
          <el-input v-model="form.title" maxlength="255" show-word-limit />
        </el-form-item>

        <el-form-item label="通知内容">
          <el-input v-model="form.content" type="textarea" :rows="5" />
        </el-form-item>

        <el-form-item label="跳转目标">
          <el-input v-model="form.action_target" placeholder="例如：/orders、/messages?sessionId=1、/admin/reports" />
        </el-form-item>

        <el-button type="primary" :loading="submitting" @click="submitNotification">立即发布</el-button>
      </el-form>
    </section>

    <section class="panel notify-list">
      <div class="section-header">
        <div>
          <h2 class="section-title">最近发布记录</h2>
          <p class="section-meta">这里展示后台最近发布过的通知任务。</p>
        </div>
        <el-button :loading="notificationsLoading" @click="loadBroadcasts">刷新</el-button>
      </div>

      <el-alert
        v-if="notificationsError"
        type="warning"
        :closable="false"
        show-icon
        :title="notificationsError"
        style="margin-bottom: 16px;"
      />
      <el-empty v-if="!notifications.length && !notificationsLoading" description="暂时还没有通知发布记录" />
      <div v-else class="broadcast-list">
        <article v-for="item in notifications" :key="item.id" class="broadcast-item">
          <div class="broadcast-head">
            <strong>{{ item.title }}</strong>
            <el-tag effect="plain">{{ item.target_scope === 'ALL' ? '全站' : `用户 #${item.target_user_id}` }}</el-tag>
          </div>
          <p>{{ item.content }}</p>
          <div v-if="item.action_target" class="muted">跳转：{{ item.action_target }}</div>
          <span class="muted">{{ formatTime(item.created_at) }}</span>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { adminApi } from '../../api/admin'

const users = ref([])
const notifications = ref([])
const usersLoading = ref(false)
const notificationsLoading = ref(false)
const usersError = ref('')
const notificationsError = ref('')
const submitting = ref(false)
const form = reactive({
  target_scope: 'ALL',
  target_user_id: null,
  title: '',
  content: '',
  action_target: ''
})

async function loadUsers() {
  usersLoading.value = true
  usersError.value = ''
  try {
    users.value = await adminApi.notificationUsers()
  } catch (error) {
    users.value = []
    usersError.value = error.message || '用户列表加载失败'
  } finally {
    usersLoading.value = false
  }
}

async function loadBroadcasts() {
  notificationsLoading.value = true
  notificationsError.value = ''
  try {
    notifications.value = await adminApi.notifications()
  } catch (error) {
    notifications.value = []
    notificationsError.value = error.message || '通知记录加载失败'
  } finally {
    notificationsLoading.value = false
  }
}

async function loadPage() {
  await Promise.allSettled([loadUsers(), loadBroadcasts()])
}

async function submitNotification() {
  const title = form.title.trim()
  const content = form.content.trim()
  if (!title) {
    ElMessage.warning('请填写通知标题')
    return
  }
  if (!content) {
    ElMessage.warning('请填写通知内容')
    return
  }
  if (form.target_scope === 'USER' && !form.target_user_id) {
    ElMessage.warning('请选择目标用户')
    return
  }

  submitting.value = true
  try {
    await adminApi.publishNotification({
      target_scope: form.target_scope,
      target_user_id: form.target_scope === 'USER' ? form.target_user_id : null,
      title,
      content,
      action_target: form.action_target.trim() || null
    })
    ElMessage.success('通知已发布')
    form.title = ''
    form.content = ''
    form.action_target = ''
    if (form.target_scope === 'USER') {
      form.target_user_id = null
    }
    await loadBroadcasts()
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    submitting.value = false
  }
}

function formatTime(value) {
  if (!value) return '刚刚'
  return new Date(value).toLocaleString('zh-CN', {
    hour12: false,
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(loadPage)
</script>

<style scoped>
.notify-form,
.notify-list {
  padding: 22px;
}

.helper-row {
  margin-top: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.broadcast-list {
  display: grid;
  gap: 12px;
}

.broadcast-item {
  padding: 16px;
  border-radius: 18px;
  background: rgba(73, 57, 41, 0.04);
}

.broadcast-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.broadcast-item p {
  margin: 10px 0;
  line-height: 1.7;
}
</style>
