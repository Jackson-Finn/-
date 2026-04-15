<template>
  <el-button plain @click="handleClick">{{ label }}</el-button>
</template>

<script setup>
import { useRouter } from 'vue-router'

const props = defineProps({
  to: {
    type: [String, Object],
    default: ''
  },
  label: {
    type: String,
    default: '返回列表'
  }
})

const router = useRouter()

function handleClick() {
  if (props.to) {
    router.push(props.to)
    return
  }
  router.back()
}
</script>
