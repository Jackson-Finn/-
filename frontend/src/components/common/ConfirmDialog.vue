<template>
  <Teleport to="body">
    <Transition name="dialog-pop">
      <div v-if="modelValue" class="confirm-overlay" @click.self="handleBackdropClick">
        <div class="confirm-card" role="dialog" aria-modal="true">
          <header class="card-header">
            <h2 class="card-title">{{ title }}</h2>
            <button class="close-btn" @click="$emit('update:modelValue', false)" aria-label="关闭">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M1 1L13 13M13 1L1 13" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </header>

          <div class="card-body">
            <p class="card-desc">{{ description }}</p>
            <el-input
              v-model="localNote"
              type="textarea"
              :rows="4"
              :placeholder="placeholder"
            />
          </div>

          <footer class="card-footer">
            <el-button @click="$emit('update:modelValue', false)">取消</el-button>
            <el-button type="primary" :loading="loading" @click="$emit('confirm', localNote)">确认</el-button>
          </footer>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: Boolean,
  title: { type: String, default: '确认操作' },
  description: { type: String, default: '' },
  placeholder: { type: String, default: '补充说明' },
  note: { type: String, default: '' },
  loading: { type: Boolean, default: false }
})

const emit = defineEmits(['update:modelValue', 'confirm'])

const localNote = ref('')

watch(
  () => [props.modelValue, props.note],
  () => { localNote.value = props.note },
  { immediate: true }
)

function handleBackdropClick() {
  emit('update:modelValue', false)
}
</script>

<style scoped>
/* ── 遮罩层 ────────────────────────────── */
.confirm-overlay {
  position: fixed;
  inset: 0;
  z-index: 3000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  background: rgba(37, 26, 20, 0.5);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
}

/* ── 弹窗卡片 ─────────────────────────── */
.confirm-card {
  width: 100%;
  max-width: 480px;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 30px;
  box-shadow: 0 28px 64px rgba(37, 26, 17, 0.16);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  font-family: var(--font-ui);
  overflow: hidden;
}

/* ── 头部 ──────────────────────────────── */
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 26px 56px 20px 28px;
  border-bottom: 1px solid var(--line);
}

.card-title {
  margin: 0;
  font-size: 1.08rem;
  font-weight: 700;
  color: var(--text);
  letter-spacing: -0.02em;
  line-height: 1;
}

/* ── 关闭按钮 ──────────────────────────── */
.close-btn {
  position: absolute;
  top: 24px;
  right: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  padding: 0;
  border: none;
  border-radius: 50%;
  background: transparent;
  color: var(--muted);
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.close-btn:hover {
  background: var(--surface-muted);
  color: var(--danger);
}

/* ── 内容区 ────────────────────────────── */
.card-body {
  display: grid;
  gap: 14px;
  padding: 24px 28px;
}

.card-desc {
  margin: 0;
  color: var(--muted-strong);
  font-size: 0.93rem;
  line-height: 1.7;
}

/* ── 底部按钮 ─────────────────────────── */
.card-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 28px 26px;
}

/* ── 淡入缩放动画 ─────────────────────── */
.dialog-pop-enter-active {
  transition: opacity 0.2s ease;
}
.dialog-pop-leave-active {
  transition: opacity 0.18s ease;
}
.dialog-pop-enter-from,
.dialog-pop-leave-to {
  opacity: 0;
}

.dialog-pop-enter-active .confirm-card {
  transition: transform 0.22s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.2s ease;
}
.dialog-pop-leave-active .confirm-card {
  transition: transform 0.18s ease-in, opacity 0.18s ease;
}
.dialog-pop-enter-from .confirm-card {
  transform: scale(0.92) translateY(12px);
  opacity: 0;
}
.dialog-pop-leave-to .confirm-card {
  transform: scale(0.96) translateY(6px);
  opacity: 0;
}
</style>
