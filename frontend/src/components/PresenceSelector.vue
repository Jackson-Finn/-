<template>
  <el-select
    :model-value="modelValue"
    class="presence-select"
    size="small"
    :loading="loading"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <el-option
      v-for="item in options"
      :key="item.value"
      :label="item.label"
      :value="item.value"
    />
  </el-select>
</template>

<script setup>
const options = [
  { value: 'ONLINE', label: '在线' },
  { value: 'INVISIBLE', label: '隐身' },
  { value: 'OFFLINE', label: '离线' }
]

defineProps({
  modelValue: { type: String, default: 'ONLINE' },
  loading: { type: Boolean, default: false }
})

defineEmits(['update:modelValue'])
</script>

<style scoped>
.presence-select {
  min-width: 108px;
}
</style>
