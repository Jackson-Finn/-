<template>
  <div class="sidebar panel">
    <div class="brand">
      <div class="brand-badge">AM</div>
      <div class="brand-copy">
        <div class="eyebrow">Marketplace</div>
        <strong>{{ title }}</strong>
        <p>{{ subtitle }}</p>
      </div>
    </div>
    <div class="nav-group">
      <div class="nav-caption">工作区</div>
      <RouterLink
        v-for="item in primaryItems"
        :key="item.to"
        :to="item.to"
        class="nav-link"
        :class="{ 'is-active': isItemActive(item) }"
      >
        <span class="nav-icon">
          <el-icon><component :is="item.icon" /></el-icon>
        </span>
        <span>{{ item.label }}</span>
      </RouterLink>
    </div>
    <div v-if="accountItems.length" class="nav-group secondary-group">
      <div class="nav-caption">账户</div>
      <RouterLink
        v-for="item in accountItems"
        :key="item.to"
        :to="item.to"
        class="nav-link"
        :class="{ 'is-active': isItemActive(item) }"
      >
        <span class="nav-icon">
          <el-icon><component :is="item.icon" /></el-icon>
        </span>
        <span>{{ item.label }}</span>
      </RouterLink>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const props = defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, required: true },
  items: { type: Array, required: true }
})

const route = useRoute()
const primaryItems = computed(() => props.items.filter((item) => item.to !== '/profile'))
const accountItems = computed(() => props.items.filter((item) => item.to === '/profile'))

function isItemActive(item) {
  if (item.activePrefix) {
    return route.path.startsWith(item.activePrefix)
  }
  return route.path === item.to
}
</script>

<style scoped>
.sidebar {
  position: sticky;
  top: 24px;
  padding: 18px 16px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.brand {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 6px 6px 2px;
}

.brand-copy {
  min-width: 0;
}

.brand p {
  margin: 4px 0 0;
  color: var(--muted);
  font-size: 0.88rem;
  line-height: 1.45;
}

.brand-badge {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  font-weight: 700;
  background: linear-gradient(180deg, #2458de 0%, #183b9b 100%);
  color: white;
  box-shadow: 0 14px 24px rgba(37, 86, 216, 0.2);
}

.brand strong {
  display: block;
  font-size: 1.02rem;
  line-height: 1.2;
}

.nav-caption {
  padding: 0 8px;
  color: var(--muted);
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.nav-group {
  display: grid;
  gap: 6px;
}

.secondary-group {
  padding-top: 12px;
  border-top: 1px solid var(--line);
}

.nav-link {
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px 12px;
  border-radius: 14px;
  color: var(--text);
  border: 1px solid transparent;
  transition: background 0.18s ease, border-color 0.18s ease, color 0.18s ease;
}

.nav-icon {
  width: 30px;
  height: 30px;
  display: grid;
  place-items: center;
  border-radius: 10px;
  background: #f5f8fd;
  color: var(--muted);
}

.nav-link:hover,
.nav-link.is-active {
  background: #f7faff;
  border-color: rgba(37, 86, 216, 0.12);
}

.nav-link.is-active {
  color: var(--brand-strong);
}

.nav-link.is-active .nav-icon {
  background: var(--brand-soft);
  color: var(--brand);
}

.nav-link.is-active::before {
  content: "";
  position: absolute;
  left: -1px;
  top: 10px;
  bottom: 10px;
  width: 3px;
  border-radius: 999px;
  background: var(--brand);
}
</style>
