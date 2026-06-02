<template>
  <section class="action-card">
    <div class="price-head">
      <div>
        <p class="price-label">当前到手价</p>
        <strong class="price-value">{{ formatPrice(price) }}</strong>
        <p class="price-note">{{ priceNote }}</p>
      </div>
      <span class="status-pill" :class="`tone-${statusTone}`">{{ statusLabel }}</span>
    </div>

    <div class="primary-actions">
      <el-button class="secondary-cta" size="large" :loading="loading.session" @click="$emit('session')">联系卖家</el-button>
      <el-button type="primary" size="large" :loading="loading.order" :disabled="!canOrder" @click="$emit('order')">
        立即下单
      </el-button>
    </div>

    <div class="secondary-actions">
      <el-dropdown trigger="click">
        <button type="button" class="minor-action">
          <span>更多操作</span>
        </button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item :disabled="loading.favorite" @click="$emit('favorite')">
              {{ loading.favorite ? '处理中' : isFavorite ? '取消收藏' : '收藏' }}
            </el-dropdown-item>
            <el-dropdown-item :disabled="loading.share" @click="$emit('share')">
              {{ loading.share ? '处理中' : '分享商品' }}
            </el-dropdown-item>
            <el-dropdown-item @click="$emit('focus-report')">举报异常</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
      <p class="secondary-hint">次级动作统一收进这里，避免主交易区按钮过多。</p>
    </div>

    <p v-if="actionStatusText" class="action-feedback" :class="`tone-${actionStatusTone}`" aria-live="polite">
      {{ actionStatusText }}
    </p>

    <div class="report-box">
      <div class="report-head">
        <strong>异常说明</strong>
        <span>仅在需要时补充，平台会结合审核记录与聊天内容判断。</span>
      </div>
      <el-input
        ref="reportInputRef"
        :model-value="reportReason"
        type="textarea"
        :rows="3"
        placeholder="例如：图文不符、价格异常、疑似盗图。"
        @update:model-value="$emit('update:reportReason', $event)"
      />
      <el-button type="danger" plain :loading="loading.report" @click="$emit('report')">
        {{ loading.report ? '提交中' : '提交举报' }}
      </el-button>
    </div>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'

import { formatPrice } from '../../utils/marketplace'

const props = defineProps({
  price: { type: [Number, String], default: 0 },
  statusLabel: { type: String, default: '' },
  statusTone: { type: String, default: 'muted' },
  loading: { type: Object, default: () => ({}) },
  canOrder: { type: Boolean, default: true },
  reportReason: { type: String, default: '' },
  isFavorite: { type: Boolean, default: false },
  actionStatusText: { type: String, default: '' },
  actionStatusTone: { type: String, default: 'muted' }
})

defineEmits(['order', 'favorite', 'session', 'report', 'focus-report', 'share', 'update:reportReason'])

const reportInputRef = ref(null)
const priceNote = computed(() => (props.canOrder ? '建议先确认验货和交付方式，再完成下单。' : '当前状态下暂不支持直接下单，可先联系卖家确认。'))

function focusReportInput() {
  reportInputRef.value?.focus?.()
}

defineExpose({ focusReportInput })
</script>

<style scoped>
.action-card {
  display: grid;
  gap: 18px;
  padding: 20px;
  border-radius: 16px;
  background: var(--surface);
  border: 1px solid var(--line);
}

.price-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.price-label {
  margin: 0;
  color: var(--muted);
  font-size: 0.82rem;
  font-weight: 800;
}

.price-value {
  display: block;
  margin-top: 8px;
  font-size: 2.2rem;
  line-height: 1;
  letter-spacing: -0.06em;
}

.price-note {
  margin: 10px 0 0;
  max-width: 28ch;
  color: var(--muted);
  font-size: 0.9rem;
  line-height: 1.72;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  padding: 0 10px;
  border-radius: 999px;
  background: var(--surface-soft);
  font-size: 0.78rem;
  font-weight: 800;
  border: 1px solid var(--line);
}

.tone-positive {
  color: var(--trust);
}

.tone-warning {
  color: var(--warning);
}

.tone-danger {
  color: var(--danger);
}

.tone-muted {
  color: var(--muted-strong);
}

.primary-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.secondary-cta {
  background: var(--surface-soft);
}

.secondary-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.minor-action {
  min-height: 44px;
  min-width: 132px;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: var(--surface-soft);
  color: var(--muted-strong);
  font-weight: 800;
  cursor: pointer;
  transition:
    transform 0.16s ease,
    background-color 0.16s ease,
    opacity 0.16s ease;
}

.minor-action:active:not(:disabled) {
  transform: translateY(1px) scale(0.99);
}

.minor-action:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.minor-action:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.action-feedback {
  margin: 0;
  padding: 12px 14px;
  border-radius: 16px;
  font-size: 0.84rem;
  font-weight: 700;
  line-height: 1.6;
}

.action-feedback.tone-info {
  background: var(--accent-soft);
  color: var(--accent-strong);
}

.action-feedback.tone-success {
  background: var(--success-soft);
  color: var(--trust);
}

.action-feedback.tone-warning {
  background: var(--warning-soft);
  color: var(--warning);
}

.action-feedback.tone-danger {
  background: var(--danger-soft);
  color: var(--danger);
}

.action-feedback.tone-muted {
  background: var(--surface-soft);
  color: var(--muted-strong);
}

.secondary-hint {
  margin: 0;
  color: var(--muted);
  font-size: 0.84rem;
  line-height: 1.6;
}

.report-box {
  display: grid;
  gap: 10px;
  padding-top: 6px;
  border-top: 1px solid var(--line);
}

.report-head {
  display: grid;
  gap: 4px;
}

.report-head strong {
  font-size: 0.9rem;
}

.report-head span {
  color: var(--muted);
  font-size: 0.84rem;
  line-height: 1.65;
}

@media (max-width: 640px) {
  .price-head,
  .primary-actions,
  .secondary-actions {
    grid-template-columns: 1fr;
  }
}
</style>
