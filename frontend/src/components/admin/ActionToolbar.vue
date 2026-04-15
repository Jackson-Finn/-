<template>
  <section class="panel toolbar-card">
    <div class="section-header">
      <div>
        <div class="eyebrow">Actions</div>
        <h3 class="section-title">审核操作</h3>
      </div>
    </div>

    <div class="toolbar-actions">
      <el-button
        type="primary"
        :loading="loadingAction === 'approve'"
        :disabled="disabled || auditStatus === 'APPROVED'"
        @click="$emit('approve')"
      >
        通过
      </el-button>
      <el-button
        plain
        :loading="loadingAction === 'request_changes'"
        :disabled="disabled || auditStatus === 'CHANGES_REQUESTED'"
        @click="$emit('request-changes')"
      >
        打回修改
      </el-button>
      <el-button
        :loading="loadingAction === 'reject'"
        :disabled="disabled || auditStatus === 'REJECTED'"
        @click="$emit('reject')"
      >
        驳回
      </el-button>
      <el-button
        plain
        :loading="loadingAction === 'off_shelf'"
        :disabled="disabled || productStatus === 'OFF_SHELF'"
        @click="$emit('off-shelf')"
      >
        下架
      </el-button>
    </div>
  </section>
</template>

<script setup>
defineProps({
  disabled: {
    type: Boolean,
    default: false
  },
  loadingAction: {
    type: String,
    default: ''
  },
  auditStatus: {
    type: String,
    default: ''
  },
  productStatus: {
    type: String,
    default: ''
  }
})

defineEmits(['approve', 'request-changes', 'reject', 'off-shelf'])
</script>

<style scoped>
.toolbar-card {
  padding: 18px;
}

.toolbar-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
</style>
