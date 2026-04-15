<template>
  <section class="trust-panel">
    <div class="section-header">
      <div>
        <h2 class="section-title">平台保障与风险提示</h2>
        <p class="section-meta">平台态度、保障方式和风险重点都集中在这里，不再混成一层灰字。</p>
      </div>
    </div>

    <div class="trust-summary">
      <article class="trust-card">
        <span>审核状态</span>
        <strong>{{ trust.audit_label }}</strong>
        <p>{{ trust.audit_note }}</p>
      </article>
      <article class="trust-card">
        <span>平台协助</span>
        <strong>{{ trust.support_label }}</strong>
        <p>{{ trust.support_note }}</p>
      </article>
    </div>

    <div class="entry-row">
      <div class="entry-card">
        <strong>举报入口</strong>
        <p>{{ trust.report_entry }}</p>
      </div>
      <div class="entry-card">
        <strong>申诉与复核</strong>
        <p>{{ trust.dispute_entry }}</p>
      </div>
    </div>

    <div class="risk-list">
      <article v-for="item in risks" :key="item.title" class="risk-item" :class="`tone-${getRiskTone(item.level)}`">
        <div class="risk-head">
          <strong>{{ item.title }}</strong>
          <span>{{ riskLabel(item.level) }}</span>
        </div>
        <p>{{ item.detail }}</p>
      </article>
    </div>
  </section>
</template>

<script setup>
import { getRiskTone } from '../../utils/marketplace'

defineProps({
  trust: {
    type: Object,
    default: () => ({
      audit_label: '',
      audit_note: '',
      support_label: '',
      support_note: '',
      report_entry: '',
      dispute_entry: ''
    })
  },
  risks: { type: Array, default: () => [] }
})

function riskLabel(level) {
  const mapping = {
    high: '高风险提醒',
    medium: '重点关注',
    low: '常规提醒'
  }
  return mapping[(level || '').toLowerCase()] || '提示'
}
</script>

<style scoped>
.trust-panel {
  display: grid;
  gap: 18px;
}

.trust-summary,
.entry-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.trust-card,
.entry-card,
.risk-item {
  padding: 20px;
  border-radius: 24px;
}

.trust-card {
  background: rgba(49, 95, 84, 0.08);
}

.entry-card {
  background: rgba(73, 57, 41, 0.04);
}

.trust-card span,
.entry-card strong {
  display: block;
}

.trust-card span {
  margin-bottom: 10px;
  color: var(--muted);
  font-size: 0.8rem;
  font-weight: 800;
}

.trust-card strong,
.entry-card strong,
.risk-head strong {
  font-size: 1rem;
}

.trust-card p,
.entry-card p,
.risk-item p {
  margin: 8px 0 0;
  color: var(--muted-strong);
  line-height: 1.75;
}

.risk-list {
  display: grid;
  gap: 12px;
}

.risk-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.risk-head span {
  font-size: 0.78rem;
  font-weight: 800;
}

.tone-safe {
  background: rgba(49, 95, 84, 0.08);
}

.tone-safe .risk-head span {
  color: var(--trust);
}

.tone-warning {
  background: var(--warning-soft);
}

.tone-warning .risk-head span {
  color: var(--warning);
}

.tone-danger {
  background: var(--danger-soft);
}

.tone-danger .risk-head span {
  color: var(--danger);
}

@media (max-width: 960px) {
  .trust-summary,
  .entry-row {
    grid-template-columns: 1fr;
  }
}
</style>
