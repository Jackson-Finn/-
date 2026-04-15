<template>
  <div class="asset-card" :class="{ 'is-cover': isCover }">
    <div class="asset-media">
      <img v-if="previewUrl" :src="previewUrl" :alt="asset.metadata?.original_filename || 'asset'">
      <div v-else class="asset-placeholder">IMAGE</div>
      <div class="asset-topline">
        <span class="asset-badge">{{ isCover ? '封面' : stageLabel }}</span>
      </div>
    </div>

    <div class="asset-body">
      <div class="asset-name">{{ asset.metadata?.original_filename || `Asset #${asset.id}` }}</div>
      <div class="asset-meta">{{ dimensionLabel }}</div>
      <div class="asset-actions">
        <button v-if="canMakeCover" type="button" class="asset-action" @click="$emit('make-cover', asset.id)">设为封面</button>
        <button v-if="canRemove" type="button" class="asset-action danger" @click="$emit('remove', asset.id)">移除</button>
        <span v-if="!canMakeCover && !canRemove" class="asset-static">已关联</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  asset: {
    type: Object,
    required: true
  },
  isCover: {
    type: Boolean,
    default: false
  },
  canMakeCover: {
    type: Boolean,
    default: true
  },
  canRemove: {
    type: Boolean,
    default: true
  }
})

defineEmits(['make-cover', 'remove'])

const previewUrl = computed(() => props.asset.metadata?.variants?.preview || props.asset.url || '')

const stageLabel = computed(() => {
  const mapping = {
    init: '已登记',
    uploaded: '已上传',
    completed: '可用',
    synced: '已关联'
  }
  return mapping[props.asset.metadata?.stage] || '可用'
})

const dimensionLabel = computed(() => {
  const width = props.asset.metadata?.width
  const height = props.asset.metadata?.height
  if (width && height) {
    return `${width} × ${height}`
  }
  return '等待处理尺寸'
})
</script>

<style scoped>
.asset-card {
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.94);
}

.asset-card.is-cover {
  border-color: rgba(37, 86, 216, 0.24);
  box-shadow: 0 0 0 1px rgba(37, 86, 216, 0.08);
}

.asset-media {
  position: relative;
  height: 132px;
  background: linear-gradient(180deg, #eef4fb 0%, #e8eef8 100%);
}

.asset-media img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.asset-placeholder {
  width: 100%;
  height: 100%;
  display: grid;
  place-items: center;
  color: rgba(15, 23, 42, 0.26);
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.12em;
}

.asset-topline {
  position: absolute;
  left: 10px;
  top: 10px;
}

.asset-badge {
  padding: 5px 9px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(15, 23, 42, 0.06);
  font-size: 0.74rem;
  font-weight: 700;
}

.asset-body {
  padding: 12px;
  display: grid;
  gap: 8px;
}

.asset-name {
  font-size: 0.88rem;
  font-weight: 700;
  line-height: 1.4;
  word-break: break-word;
}

.asset-meta {
  color: var(--muted);
  font-size: 0.78rem;
}

.asset-actions {
  display: flex;
  gap: 10px;
}

.asset-action {
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--brand);
  font-size: 0.78rem;
  font-weight: 700;
  cursor: pointer;
}

.asset-action.danger {
  color: #b42318;
}

.asset-static {
  color: var(--muted);
  font-size: 0.78rem;
  font-weight: 600;
}
</style>
