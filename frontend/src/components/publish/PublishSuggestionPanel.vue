<template>
  <section class="panel suggestion-panel">
    <div class="section-header">
      <div>
        <div class="eyebrow">AI Suggestions</div>
        <h3 class="section-title">生成建议</h3>
        <p class="section-meta">先给建议，再决定是否采用。</p>
      </div>
      <div class="suggestion-actions">
        <el-button size="small" @click="$emit('generate')">生成草稿</el-button>
        <el-button size="small" plain @click="$emit('moderate')" :disabled="!canModerate">检查风险</el-button>
      </div>
    </div>

    <div class="suggestion-block">
      <div class="suggestion-label">建议标题</div>
      <div class="suggestion-card">
        {{ aiResult?.title || 'AI 会根据关键词、类目和现有文案给出更适合发布的标题。' }}
      </div>
    </div>

    <div class="suggestion-block">
      <div class="suggestion-label">文案草稿</div>
      <div class="suggestion-card description-card">
        {{ aiResult?.description || '这里会展示更适合上架的商品描述，语气更克制，信息更完整。' }}
      </div>
    </div>

    <div class="risk-strip" :class="{ 'has-risk': riskLevel }">
      <div>
        <strong>内容检查</strong>
        <p>{{ riskText }}</p>
      </div>
      <span class="risk-level">{{ riskLevel || '未检查' }}</span>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  aiResult: {
    type: Object,
    default: () => ({})
  },
  moderation: {
    type: Object,
    default: () => ({})
  },
  canModerate: {
    type: Boolean,
    default: false
  }
})

defineEmits(['generate', 'moderate'])

const riskLevel = computed(() => props.moderation?.risk_level || '')

const riskText = computed(() => {
  if (!props.moderation?.risk_level) {
    return '在提交审核前做一次轻量检查。'
  }
  return props.moderation?.reason || props.moderation?.summary || '已返回风险结果。'
})
</script>

<style scoped>
.suggestion-panel {
  padding: 18px;
  display: grid;
  gap: 16px;
}

.suggestion-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.suggestion-block {
  display: grid;
  gap: 8px;
}

.suggestion-label {
  color: var(--muted);
  font-size: 0.76rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.suggestion-card {
  min-height: 72px;
  padding: 14px;
  border-radius: 14px;
  border: 1px solid var(--line);
  background: #f8fbff;
  line-height: 1.65;
}

.description-card {
  min-height: 118px;
}

.risk-strip {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 14px;
  border-radius: 14px;
  border: 1px solid var(--line);
  background: rgba(255, 255, 255, 0.84);
}

.risk-strip strong {
  display: block;
  font-size: 0.92rem;
}

.risk-strip p {
  margin: 4px 0 0;
  color: var(--muted);
  font-size: 0.84rem;
  line-height: 1.6;
}

.risk-level {
  padding: 6px 10px;
  border-radius: 999px;
  background: #f4f7fb;
  color: var(--muted);
  font-size: 0.76rem;
  font-weight: 700;
  white-space: nowrap;
}

.has-risk .risk-level {
  background: var(--danger-soft);
  color: #b42318;
}
</style>
