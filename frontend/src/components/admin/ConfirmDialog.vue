<template>
  <el-dialog :model-value="modelValue" :title="title" width="480px" @close="$emit('update:modelValue', false)">
    <div class="dialog-body">
      <p class="dialog-copy">{{ description }}</p>
      <el-input
        v-model="localNote"
        type="textarea"
        :rows="4"
        :placeholder="placeholder"
      />
    </div>
    <template #footer>
      <el-space>
        <el-button @click="$emit('update:modelValue', false)">取消</el-button>
        <el-button type="primary" :loading="loading" @click="$emit('confirm', localNote)">确认</el-button>
      </el-space>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    default: '确认操作'
  },
  description: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: '补充说明'
  },
  note: {
    type: String,
    default: ''
  },
  loading: {
    type: Boolean,
    default: false
  }
})

defineEmits(['update:modelValue', 'confirm'])

const localNote = ref('')

watch(
  () => [props.modelValue, props.note],
  () => {
    localNote.value = props.note
  },
  { immediate: true }
)
</script>

<style scoped>
.dialog-body {
  display: grid;
  gap: 12px;
}

.dialog-copy {
  margin: 0;
  color: var(--muted);
  line-height: 1.6;
}
</style>
