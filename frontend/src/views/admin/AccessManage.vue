<template>
  <div class="grid grid-2">
    <section class="panel" style="padding: 22px;">
      <div class="section-header">
        <div>
          <h2 class="section-title">角色与权限</h2>
          <p class="section-meta">RBAC 多管理员能力</p>
        </div>
        <el-button @click="loadAccess">刷新</el-button>
      </div>

      <el-table :data="roles">
        <el-table-column prop="id" label="角色 ID" />
        <el-table-column prop="name" label="角色名" />
        <el-table-column prop="code" label="编码" />
      </el-table>

      <el-divider />
      <el-table :data="permissions">
        <el-table-column prop="code" label="权限点" />
        <el-table-column prop="name" label="描述" />
      </el-table>
    </section>

    <section class="panel" style="padding: 22px;">
      <div class="section-header">
        <div>
          <h2 class="section-title">用户授权</h2>
          <p class="section-meta">把角色赋给指定管理员</p>
        </div>
      </div>

      <el-form label-position="top">
        <el-form-item label="用户">
          <el-select v-model="selectedUserId" placeholder="选择用户">
            <el-option v-for="user in users" :key="user.id" :label="`${user.display_name} (${user.email})`" :value="user.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="selectedRoleIds" multiple placeholder="选择角色">
            <el-option v-for="role in roles" :key="role.id" :label="role.name" :value="role.id" />
          </el-select>
        </el-form-item>
        <el-button type="primary" @click="assignRoles">保存授权</el-button>
      </el-form>
    </section>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { adminApi } from '../../api/admin'

const roles = ref([])
const permissions = ref([])
const users = ref([])
const selectedUserId = ref()
const selectedRoleIds = ref([])

async function loadAccess() {
  roles.value = await adminApi.roles()
  permissions.value = await adminApi.permissions()
  users.value = await adminApi.users()
}

async function assignRoles() {
  await adminApi.assignRoles(selectedUserId.value, { role_ids: selectedRoleIds.value })
  ElMessage.success('角色分配已保存')
}

onMounted(loadAccess)
</script>
