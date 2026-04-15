<template>
  <section class="panel-soft rail">
    <div class="rail-head">
      <div>
        <div class="eyebrow">Workflow</div>
        <h3 class="rail-title">发布流程</h3>
      </div>
      <span class="rail-status">{{ statusLabel }}</span>
    </div>

    <div class="rail-list">
      <div
        v-for="(step, index) in steps"
        :key="step.key"
        class="rail-item"
        :class="{
          'is-current': currentStep === step.key,
          'is-done': completedStepSet.has(step.key)
        }"
      >
        <div class="rail-marker">{{ index + 1 }}</div>
        <div class="rail-copy">
          <strong>{{ step.label }}</strong>
          <p>{{ step.meta }}</p>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  steps: {
    type: Array,
    default: () => []
  },
  currentStep: {
    type: String,
    default: ''
  },
  completedSteps: {
    type: Array,
    default: () => []
  },
  statusLabel: {
    type: String,
    default: '编辑中'
  }
})

const completedStepSet = computed(() => new Set(props.completedSteps))
</script>

<style scoped>
.rail {
  padding: 18px;
  display: grid;
  gap: 16px;
}

.rail-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.rail-title {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
}

.rail-status {
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid var(--line);
  color: var(--muted);
  font-size: 0.78rem;
  font-weight: 600;
}

.rail-list {
  display: grid;
  gap: 12px;
}

.rail-item {
  display: grid;
  grid-template-columns: 28px 1fr;
  gap: 12px;
  align-items: start;
}

.rail-marker {
  width: 28px;
  height: 28px;
  display: grid;
  place-items: center;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.06);
  color: var(--muted);
  font-size: 0.78rem;
  font-weight: 700;
}

.rail-copy strong {
  display: block;
  font-size: 0.92rem;
}

.rail-copy p {
  margin: 4px 0 0;
  color: var(--muted);
  font-size: 0.82rem;
  line-height: 1.55;
}

.is-current .rail-marker {
  background: var(--brand);
  color: white;
}

.is-done .rail-marker {
  background: var(--brand-soft);
  color: var(--brand);
}
</style>
